#!/usr/bin/env python3
"""Convert local PDFs to Markdown via MinerU (OpenXLab) API, with local fallback.

Token is read from MINERU_TOKEN / MINERU_API_TOKEN env vars, or from
.secrets/mineru_token.txt (gitignored). Never hardcode or log the token.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path

import requests

API_BASE = "https://mineru.net/api/v4"
DEFAULT_TOKEN_FILE = Path(".secrets/mineru_token.txt")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_token(explicit: str | None = None) -> str:
    if explicit:
        return explicit.strip()
    for key in ("MINERU_TOKEN", "MINERU_API_TOKEN"):
        val = os.environ.get(key, "").strip()
        if val:
            return val
    token_path = _repo_root() / DEFAULT_TOKEN_FILE
    if token_path.is_file():
        return token_path.read_text(encoding="utf-8").strip()
    raise SystemExit(
        "MinerU token not found. Set MINERU_TOKEN or create .secrets/mineru_token.txt"
    )


def _auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "*/*",
    }


def request_batch_upload(
    token: str,
    files: list[Path],
    *,
    model_version: str = "vlm",
    language: str = "en",
    enable_formula: bool = True,
    enable_table: bool = True,
) -> tuple[str, list[str]]:
    url = f"{API_BASE}/file-urls/batch"
    payload = {
        "files": [
            {"name": p.name, "data_id": p.stem.replace(" ", "_")[:120]} for p in files
        ],
        "model_version": model_version,
        "language": language,
        "enable_formula": enable_formula,
        "enable_table": enable_table,
    }
    resp = requests.post(url, headers=_auth_headers(token), json=payload, timeout=60)
    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text[:500]}
    if resp.status_code != 200 or body.get("code") != 0:
        raise RuntimeError(
            f"file-urls/batch failed HTTP {resp.status_code}: "
            f"code={body.get('code')} msg={body.get('msg')} body={body}"
        )
    data = body["data"]
    return data["batch_id"], data["file_urls"]


def upload_files(paths: list[Path], urls: list[str]) -> None:
    if len(paths) != len(urls):
        raise RuntimeError(f"URL count {len(urls)} != file count {len(paths)}")
    for path, put_url in zip(paths, urls):
        with path.open("rb") as fh:
            resp = requests.put(put_url, data=fh, timeout=600)
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"PUT upload failed for {path.name}: HTTP {resp.status_code} "
                f"body={resp.text[:300]}"
            )


def poll_batch(
    token: str,
    batch_id: str,
    *,
    timeout_s: float = 1800.0,
    interval_s: float = 8.0,
) -> list[dict]:
    url = f"{API_BASE}/extract-results/batch/{batch_id}"
    t0 = time.time()
    last_states: list[str] = []
    while True:
        resp = requests.get(url, headers=_auth_headers(token), timeout=60)
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text[:500]}
        if resp.status_code != 200 or body.get("code") != 0:
            raise RuntimeError(
                f"extract-results failed HTTP {resp.status_code}: "
                f"code={body.get('code')} msg={body.get('msg')} body={body}"
            )
        results = body["data"].get("extract_result") or []
        states = [r.get("state", "?") for r in results]
        if states != last_states:
            print(f"[mineru] batch={batch_id} states={states}", flush=True)
            last_states = states
        if results and all(s in ("done", "failed") for s in states):
            return results
        if time.time() - t0 > timeout_s:
            raise TimeoutError(f"batch {batch_id} timed out after {timeout_s}s; last={states}")
        time.sleep(interval_s)


def download_and_extract_zip(zip_url: str, dest_md: Path, assets_dir: Path) -> None:
    resp = requests.get(zip_url, timeout=300)
    if resp.status_code != 200:
        raise RuntimeError(f"zip download HTTP {resp.status_code} for {zip_url}")
    dest_md.parent.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = zf.namelist()
        md_candidates = [n for n in names if n.endswith("full.md") or n.endswith(".md")]
        if not md_candidates:
            raise RuntimeError(f"No markdown in zip; members={names[:20]}")
        # Prefer full.md
        md_name = next((n for n in md_candidates if n.endswith("full.md")), md_candidates[0])
        md_text = zf.read(md_name).decode("utf-8", errors="replace")
        header = (
            "<!-- extraction_method: MinerU API (mineru.net /api/v4/file-urls/batch) -->\n"
            f"<!-- source_zip_member: {md_name} -->\n\n"
        )
        dest_md.write_text(header + md_text, encoding="utf-8")
        # Extract images / assets
        for name in names:
            if name.endswith("/") or name.endswith(".md"):
                continue
            # Keep relative structure under assets_dir
            rel = Path(name)
            # Flatten common images/ prefix into assets_dir
            if "images" in rel.parts:
                out = assets_dir / rel.name
            else:
                out = assets_dir / rel.name
            out.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(name) as src, out.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def local_pdf_fallback(pdf_path: Path, dest_md: Path, reason: str) -> None:
    """Best-effort text extraction when MinerU fails."""
    dest_md.parent.mkdir(parents=True, exist_ok=True)
    pages_text: list[str] = []
    method = "unknown"
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        for i, page in enumerate(reader.pages):
            t = page.extract_text() or ""
            pages_text.append(f"\n\n## Page {i + 1}\n\n{t}")
        method = "pypdf"
    except Exception as exc:  # noqa: BLE001
        pages_text.append(f"\n\n(local extraction also failed: {type(exc).__name__}: {exc})")
        method = "failed"
    header = (
        f"<!-- extraction_method: LOCAL_FALLBACK ({method}) -->\n"
        f"<!-- mineru_failure: {reason.replace('--', '- -')} -->\n"
        f"<!-- source_pdf: {pdf_path.name} -->\n\n"
        f"# Local text extract of `{pdf_path.name}`\n\n"
        "> **Note:** This file was produced by a local PDF text extractor because "
        "MinerU API conversion failed. Layout, equations, and figures are incomplete.\n"
    )
    dest_md.write_text(header + "".join(pages_text), encoding="utf-8")
    print(f"[fallback] wrote {dest_md} via {method}", flush=True)


def convert_batch(
    pdfs: list[Path],
    out_mds: list[Path],
    assets_dirs: list[Path],
    *,
    token: str,
    model_version: str,
    language: str,
) -> list[dict]:
    reports: list[dict] = []
    try:
        batch_id, urls = request_batch_upload(
            token, pdfs, model_version=model_version, language=language
        )
        print(f"[mineru] batch_id={batch_id} n_urls={len(urls)}", flush=True)
        upload_files(pdfs, urls)
        results = poll_batch(token, batch_id)
    except Exception as exc:  # noqa: BLE001
        reason = f"{type(exc).__name__}: {exc}"
        print(f"[mineru] FAILED: {reason}", flush=True)
        for pdf, md, assets in zip(pdfs, out_mds, assets_dirs):
            local_pdf_fallback(pdf, md, reason)
            reports.append(
                {
                    "pdf": str(pdf),
                    "md": str(md),
                    "method": "local_fallback",
                    "error": reason,
                }
            )
        return reports

    by_name = {r.get("file_name"): r for r in results}
    for pdf, md, assets in zip(pdfs, out_mds, assets_dirs):
        r = by_name.get(pdf.name)
        if r is None and len(results) == 1:
            r = results[0]
        if r is None:
            reason = f"no extract_result for {pdf.name}; keys={list(by_name)}"
            local_pdf_fallback(pdf, md, reason)
            reports.append(
                {"pdf": str(pdf), "md": str(md), "method": "local_fallback", "error": reason}
            )
            continue
        state = r.get("state")
        if state != "done" or not r.get("full_zip_url"):
            reason = f"state={state} err_msg={r.get('err_msg')}"
            local_pdf_fallback(pdf, md, reason)
            reports.append(
                {"pdf": str(pdf), "md": str(md), "method": "local_fallback", "error": reason}
            )
            continue
        try:
            download_and_extract_zip(r["full_zip_url"], md, assets)
            reports.append(
                {
                    "pdf": str(pdf),
                    "md": str(md),
                    "assets": str(assets),
                    "method": "mineru",
                    "state": state,
                }
            )
            print(f"[mineru] OK -> {md}", flush=True)
        except Exception as exc:  # noqa: BLE001
            reason = f"zip extract failed: {type(exc).__name__}: {exc}"
            local_pdf_fallback(pdf, md, reason)
            reports.append(
                {"pdf": str(pdf), "md": str(md), "method": "local_fallback", "error": reason}
            )
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdf",
        action="append",
        dest="pdfs",
        required=True,
        help="Input PDF path (repeatable)",
    )
    parser.add_argument(
        "--out-md",
        action="append",
        dest="out_mds",
        required=True,
        help="Output markdown path (same order as --pdf)",
    )
    parser.add_argument(
        "--assets-dir",
        action="append",
        dest="assets_dirs",
        default=None,
        help="Assets directory (default: <stem>_assets next to md)",
    )
    parser.add_argument("--model-version", default="vlm")
    parser.add_argument("--language", default="en")
    parser.add_argument("--report-json", default=None)
    args = parser.parse_args()

    pdfs = [Path(p) for p in args.pdfs]
    out_mds = [Path(p) for p in args.out_mds]
    if len(pdfs) != len(out_mds):
        raise SystemExit("--pdf and --out-md counts must match")
    if args.assets_dirs:
        assets_dirs = [Path(p) for p in args.assets_dirs]
        if len(assets_dirs) != len(pdfs):
            raise SystemExit("--assets-dir count must match --pdf")
    else:
        assets_dirs = [
            md.with_name(md.stem.replace(".from_pdf", "") + "_assets") for md in out_mds
        ]

    for p in pdfs:
        if not p.is_file():
            raise SystemExit(f"PDF not found: {p}")

    token = load_token()
    reports = convert_batch(
        pdfs,
        out_mds,
        assets_dirs,
        token=token,
        model_version=args.model_version,
        language=args.language,
    )
    if args.report_json:
        Path(args.report_json).write_text(
            json.dumps(reports, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(json.dumps(reports, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
