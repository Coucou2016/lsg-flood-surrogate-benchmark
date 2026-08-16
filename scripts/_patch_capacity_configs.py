"""Rewrite corrupted capacity-control YAML twins from clean templates."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_lines(p: Path) -> list[str]:
    return p.read_text(encoding="utf-8").splitlines(keepends=True)


def set_key_block(lines: list[str], key: str, value: str, indent: str = "  ") -> list[str]:
    prefix = f"{indent}{key}:"
    out: list[str] = []
    done = False
    for ln in lines:
        if (not done) and ln.startswith(prefix):
            out.append(f"{prefix} {value}\n")
            done = True
        else:
            out.append(ln)
    if not done:
        raise SystemExit(f"missing key {key}")
    return out


def insert_after(lines: list[str], after_key: str, new_lines: list[str], indent: str = "  ") -> list[str]:
    prefix = f"{indent}{after_key}:"
    out: list[str] = []
    done = False
    for ln in lines:
        out.append(ln)
        if (not done) and ln.startswith(prefix):
            out.extend(new_lines)
            done = True
    if not done:
        raise SystemExit(f"missing after_key {after_key}")
    return out


def patch_file(path: Path, **kw) -> None:
    lines = load_lines(path)
    if "study_id" in kw:
        lines = set_key_block(lines, "id", kw["study_id"], indent="  ")
    if "models" in kw:
        lines = set_key_block(lines, "models", kw["models"], indent="  ")
    if "zoning" in kw:
        lines = set_key_block(lines, "zoning", kw["zoning"], indent="  ")
    if "n_zones" in kw:
        lines = set_key_block(lines, "n_zones", str(kw["n_zones"]), indent="  ")
    if "residual_eof_modes" in kw:
        lines = set_key_block(
            lines, "residual_eof_modes", str(kw["residual_eof_modes"]), indent="  "
        )
    if "min_inducing" in kw:
        lines = set_key_block(
            lines, "min_inducing_points", str(kw["min_inducing"]), indent="  "
        )
    if "force_n_modes" in kw:
        lines = [ln for ln in lines if not ln.startswith("  force_n_modes:")]
        lines = [
            ln
            for ln in lines
            if "Capacity-matched control: override North/Kaiser" not in ln
        ]
        lines = insert_after(
            lines,
            "residual_eof_modes",
            [
                "  # Capacity-matched control: override North/Kaiser retained count.\n",
                f"  force_n_modes: {kw['force_n_modes']}\n",
            ],
        )
    path.write_text("".join(lines), encoding="utf-8")
    print("ok", path.relative_to(ROOT))


def main() -> None:
    cfg = ROOT / "config"
    (cfg / "chowilla_global_matched15.yaml").write_text(
        (cfg / "chowilla_global.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (cfg / "burnett_global_matched18.yaml").write_text(
        (cfg / "burnett_global.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    for name in [
        "chowilla_hlsg_budget3",
        "chowilla_nzones_2",
        "chowilla_nzones_6",
        "chowilla_inducing_m2",
        "chowilla_inducing_m8",
        "chowilla_inducing_m28",
    ]:
        (cfg / f"{name}.yaml").write_text(
            (cfg / "chowilla.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )

    patch_file(
        cfg / "chowilla_global_matched15.yaml",
        study_id="chowilla_global_matched15",
        models="outputs/models/chowilla_global_matched15",
        zoning="none",
        force_n_modes=15,
    )
    patch_file(
        cfg / "burnett_global_matched18.yaml",
        study_id="burnett_global_matched18",
        models="outputs/models/burnett_global_matched18",
        zoning="none",
        force_n_modes=18,
    )
    patch_file(
        cfg / "chowilla_hlsg_budget3.yaml",
        study_id="chowilla_hlsg_budget3",
        models="outputs/models/chowilla_hlsg_budget3",
        zoning="residual_kmeans",
        residual_eof_modes=0,
    )
    patch_file(
        cfg / "chowilla_nzones_2.yaml",
        study_id="chowilla_nzones_2",
        models="outputs/models/chowilla_nzones_2",
        n_zones=2,
    )
    patch_file(
        cfg / "chowilla_nzones_6.yaml",
        study_id="chowilla_nzones_6",
        models="outputs/models/chowilla_nzones_6",
        n_zones=6,
    )
    patch_file(
        cfg / "chowilla_inducing_m2.yaml",
        study_id="chowilla_inducing_m2",
        models="outputs/models/chowilla_inducing_m2",
        min_inducing=2,
    )
    patch_file(
        cfg / "chowilla_inducing_m8.yaml",
        study_id="chowilla_inducing_m8",
        models="outputs/models/chowilla_inducing_m8",
        min_inducing=8,
    )
    patch_file(
        cfg / "chowilla_inducing_m28.yaml",
        study_id="chowilla_inducing_m28",
        models="outputs/models/chowilla_inducing_m28",
        min_inducing=28,
    )


if __name__ == "__main__":
    main()
