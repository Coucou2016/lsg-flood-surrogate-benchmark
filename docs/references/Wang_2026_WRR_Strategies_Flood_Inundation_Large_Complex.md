## RESEARCH ARTICLE <br> 10.1029/2025WR042481

## Key Points:

- The LSG model is applied to the Lower Brisbane River floodplain influenced by urbanization, tides, dam regulation, and multiple tributaries
- Initial implementation shows limited accuracy, but finer low-fidelity resolution substantially improved model performance
- Between the two variants, LSG-TS outperformed LSG-Max, confirming its potential for predicting inundation in large, complex floodplains


## Correspondence to:

W. Wang,
www1@student.unimelb.edu.au

## Citation:

Wang, W., Wang, Q. J., \& Nathan, R. (2026). Strategies for predicting flood inundation in a large and complex floodplain based on low-fidelity hydrodynamic models. Water Resources Research, 62, e2025WR042481. https:// doi.org/10.1029/2025WR042481

Received 6 OCT 2025
Accepted 19 APR 2026

## Author Contributions:

Conceptualization: Wen Wang, Quan
J. Wang, Rory Nathan Data curation: Wen Wang
Formal analysis: Wen Wang
Investigation: Wen Wang
Methodology: Wen Wang, Quan J. Wang, Rory Nathan
Project administration: Quan J. Wang
Resources: Quan J. Wang
Software: Wen Wang
Supervision: Quan J. Wang, Rory Nathan
Validation: Wen Wang
Visualization: Wen Wang
Writing - original draft: Wen Wang
Writing - review \& editing: Wen Wang, Quan J. Wang, Rory Nathan

## © 2026. The Author(s).

This is an open access article under the terms of the Creative Commons Attribution License, which permits use, distribution and reproduction in any medium, provided the original work is properly cited.

# Strategies for Predicting Flood Inundation in a Large and Complex Floodplain Based on Low-Fidelity Hydrodynamic Models 

Wen Wang ${ }^{1,2}$ (D), Quan J. Wang ${ }^{1,3}$ (D), and Rory Nathan ${ }^{1}$ (D)<br>¹Department of Infrastructure Engineering, The University of Melbourne, Parkville, VIC, Australia, ${ }^{2}$ Australian Bureau of Meteorology, Brisbane, QLD, Australia, ${ }^{3}$ College of Hydrology and Water Resources, Hohai University, Nanjing, China


#### Abstract

Accurate and computationally efficient flood inundation prediction is critical for effective flood risk management. While high-fidelity hydrodynamic models provide detailed representations of flood processes, their computational demands limit real-time flood forecasting or ensemble applications. To address this, surrogate models have been developed to deliver faster predictions with acceptable accuracy. Among them, the Low-Fidelity, Spatial Analysis and Gaussian Process Learning (LSG) model has demonstrated superior performance with reasonable computational cost, effectively simulating flood dynamics in complex floodplains. However, its ability to handle large-scale floodplains with intricate flow interactions and upstream dam releases remains untested. This study investigates the feasibility of applying the LSG model to the Lower Brisbane River floodplain, which presents additional challenges due to extensive urbanization, dam regulation, tidal influences, and many interacting tributaries. These conditions lead to backwater effects from the main river channel into the tributaries, further complicating flood behavior. Initial implementation in this study exhibited limited accuracy, prompting further investigation. Higher low-fidelity resolution was found to significantly improve model performance. To predict maximum flood surfaces, we developed and investigated two LSG model variants: (a) LSG-Max trained directly on maximum flood surfaces; (b) LSG-TS trained on time series data and deriving maximum flood surfaces from the predicted flood evolution. Evaluation against historical and synthetic flood events showed that LSG-TS consistently outperforms LSG-Max due to its richer training information. These findings demonstrate that the LSG modeling approach can offer effective strategies for predicting flood inundation in large and complex floodplains.


## 1. Introduction

Floods are among the most frequent and devastating natural disasters globally, causing significant loss of life, extensive damage to infrastructure, and widespread economic disruption. As the frequency and intensity of flood events continue to rise under the influence of climate change, the need for accurate and timely flood inundation predictions has become increasingly critical for effective flood risk management, emergency response, and community resilience.

Physically based hydrodynamic models, which solve the shallow water equations, are extensively utilized for complex flood process modeling. The most common models used in practice are high-fidelity two-dimensional (2D) hydrodynamic models, which simulate flood inundation processes with high spatial and temporal resolutions (Razavi et al., 2012; Teng et al., 2017). These high-fidelity models can accurately represent the interactions between flow, terrain, and infrastructure, capturing critical dynamics such as channel overflows, floodplain inundation, and backwater effects. However, high-fidelity models require substantial computational resources, especially when applied over long durations, in complex systems, or across large spatial domains. This computational burden poses a major challenge for real-time applications and probabilistic risk assessments, especially in operational environments that demand rapid decision-making (Dazzi et al., 2021; Fraehr et al., 2022; Hop et al., 2024; Murphy et al., 2016; Teng et al., 2019).

To address this computational limitation, surrogate modeling approaches have emerged as effective alternatives to conventional hydrodynamic modeling. Surrogate models aim to approximate outputs of high-fidelity models using simplified representations that are significantly faster to run. Once trained, surrogate models can generate predictions within seconds to minutes, offering a substantial reduction in computational time compared to highfidelity simulations that may require hours or days. This efficiency makes surrogate models particularly well-
suited for time-sensitive applications. Although surrogate modeling may lead to a drop in predictive accuracy, this limitation can be ameliorated by training the model with well-structured and representative data sets (Contreras et al., 2020; Donnelly et al., 2022; Fraehr et al., 2022).

Several surrogate modeling methodologies have been developed and applied in recent years. A common industry practice is to link a pre-canned library of flood maps with river levels or discharges and apply interpolation to derive flood surfaces. However, such interpolation methods have limited capability to emulate complex and dynamic nature of flood behavior (Wang et al., 2022). More sophisticated data-driven surrogate models, including artificial neural networks, support vector machines, long short-term memory networks (LSTM), convolutional neural networks, and Gaussian process (GP) models, have been widely explored due to their flexibility and predictive capabilities (Chu et al., 2020; Donnelly et al., 2022; Fraehr et al., 2024; Kabir et al., 2020; Wang et al., 2025; Zhou et al., 2021; Zhu et al., 2021). Reduced-order models, which are typically considered lowfidelity models, simplify the underlying physical equations or processes, significantly lowering computational costs at the expense of predictive accuracy and detail. Another widely adopted low-fidelity approach is to reduce the spatial resolution of hydrodynamic models, which achieves efficiency gains while still retaining the original hydrodynamic solution scheme. Hybrid models integrate data-driven techniques with physical principles, aiming to take the advantages of both data-driven surrogate and low-fidelity approaches. The suitability of each surrogate modeling approach depends heavily on the specific modeling objectives and the availability of training data.

Among recent advances in surrogate modelling for flood prediction, the Low-fidelity, Spatial analysis, and Gaussian process learning (LSG) model has shown considerable promise (Fraehr et al., 2022, 2023a, 2023b; Lu et al., 2025). This hybrid approach integrates low-fidelity hydrodynamic simulations, spatial analytical techniques, and Gaussian process learning to emulate the behaviour of high-fidelity models. By combining datadriven methods with low-fidelity models, the LSG model aims to deliver high predictive accuracy while maintaining fast computational efficiency. Recent research (Fraehr et al., 2022, 2023a, 2023b) has demonstrated that the LSG model achieves substantial computational efficiency gains without material loss of accuracy compared to traditional high-fidelity hydrodynamic models. These studies highlight the effectiveness of the LSG model in capturing both spatial patterns and temporal dynamics of flooding, making it particularly suitable for real-time flood forecasting applications.

Although the LSG model has shown promising results in simulating flood dynamics in reasonably complex floodplains, its performance in floodplains with more intricate flow interactions, including extensive urbanisation, large-scale dam regulation, and strong tidal influences, remains largely unexplored. The lack of model evaluation in such challenging conditions raises questions about its generalisability and reliability for real-world implementation in large, complex, and regulated river systems.

This study addresses this gap by evaluating the feasibility of applying the LSG model to the Lower Brisbane River floodplain in Queensland, Australia. The Lower Brisbane River is a large, hydrodynamically complex system that poses significant challenges for flood modelling. It is heavily urbanised, with dense residential and commercial development along its floodplain, particularly in Brisbane's inner suburbs. Ipswich, although a smaller local government area next to Brisbane, also has significant development along flood-prone corridors. The floodplain includes multiple tributaries that join the main river along its lower reaches. During major flood events, these tributaries can be significantly impacted by backwater effects from the main channel, where elevated river levels impede outflows, causing localized inundation. Additionally, the floodplain is influenced by tides and storm surge from Moreton Bay and regulated dam releases from Wivenhoe and Somerset Dams, which together contribute to complex compound flooding dynamics. In addition to its hydrodynamic complexity, the region has a long history of major flood events, the most recent occurred in 2011 and 2022. These factors make the Lower Brisbane River floodplain a compelling test case for assessing the robustness of the LSG model under real-world conditions.

This study also provides an opportunity to investigate how the spatial resolution of the low-fidelity model affects the predictive performance of the LSG model. Although low-fidelity simulations are a key component of the LSG approach, the influence of low-fidelity resolution on surrogate accuracy has not been systematically studied in previous research. Understanding this relationship is crucial for balancing model performance with computational efficiency, especially when dealing with large domains or limited resources. In addition to investigating model feasibility and resolution effects, this study explores the optimal way to train the LSG model for predicting maximum flood inundation, a key metric for flood hazard assessment and emergency planning. Two different LSG variants are developed and investigated. The first, referred to as LSG-TS, is trained on a time series of flood

![](https://cdn.mathpix.com/cropped/3772807b-80ff-4020-8ccf-79b9b3e27705-03.jpg?height=516&width=1393&top_left_y=312&top_left_x=583)
Figure 1. Schematic overview of the LSG model. Solid arrows denote the training stage, while dashed arrows denote the prediction stage. High-fidelity inundation data are used to train the Gaussian Process-based LSG model, which is then applied with new low-fidelity model outputs to generate high-fidelity predictions.

surfaces and derives the maximum flood extent from the predicted flood evolution. The second, known as LSGMax, is trained directly on the maximum flood surface from each event. The training strategy itself is investigated by comparing models trained using only synthetic events against those trained with a combination of synthetic and historical events. The performance of both variants is evaluated using both historical and synthetic flood events across the Lower Brisbane River floodplain. The results are intended to provide insights into strategies for applying the LSG model in large and complex floodplains, highlighting its suitability for operational use and informing future improvements in model design and implementation.

The remainder of this paper is structured as follows. Section 2 outlines the LSG modelling approach and details the development of the LSG-TS and LSG-Max variants. Section 3 presents the study area and describes overall modelling workflow. Section 4 provides a comprehensive evaluation of model performance across a set of validation events. Section 5 discusses the findings, limitations, and implications for future work, and Section 6 concludes the paper with final remarks.

## 2. LSG Modeling Approach

In this section, we describe the methodological approach used to develop and investigate the proposed inundation modeling. We begin by introducing the LSG model, outlining its general structure and core components, including the purpose of spatial analysis and the role of Gaussian process regression. Then we present two LSG model variants: LSG-TS, which utilizes time series flood surfaces, and LSG-Max, which focuses on maximum flood surfaces.

### 2.1. LSG Model

The LSG model is designed as a computationally efficient surrogate model for flood inundation prediction (Fraehr et al., 2022, 2023a, 2023b). It aims to accurately emulate the outputs of high-fidelity hydrodynamic models while significantly reducing simulation time and computational cost. The LSG model comprises three main components: a low-fidelity hydrodynamic simulation, dimensionality reduction using Empirical Orthogonal Function (EOF) analysis, and predictive modeling via Gaussian process regression (see Figure 1).

In this study, we use the term "low-fidelity simulations" to refer to hydrodynamic model simulations undertaken by the high-fidelity model, but at spatial resolutions that are much coarser (up to 10 times coarser) than would typically be adopted. These simulations maintain the overall dynamics of flooding processes but with coarser spatial detail or smoothed boundary conditions. The use of a coarser-resolution (low-fidelity) model enables the rapid generation of inundation data sets for training the LSG model and provides the low-fidelity information required during subsequent LSG predictions. By contrast, the high-fidelity simulations are run at fine spatial resolution with detailed configuration, providing accurate benchmark outputs for training and validation. Despite their simplifications, low-fidelity models still provide physically meaningful approximations that can be upskilled in the LSG model.

To handle the high complexity and dimensionality of spatial-temporal flood outputs, EOF analysis is employed. It decomposes spatial-temporal flood data into a set of EOF spatial patterns and corresponding temporal expansion coefficients (ECs). Mathematically, a flood surface is expressed as a linear combination of spatial patterns and temporal coefficients (Jolliffe \& Cadima, 2016). To reduce the complexity and dimensionality of the LSG model, only the significant modes that explain the majority of the variance are retained. EOF analysis allows for significant data reduction while preserving essential flood characteristics. The high-fidelity flood inundation results are decomposed into EOF spatial patterns and temporal ECs. These EOF spatial patterns are then used to extract corresponding temporal ECs from the low-fidelity results.

The retained set of temporal ECs from the high-fidelity model is then used as the outputs for Gaussian process regression learning, while the corresponding ECs from the low-fidelity model serve as inputs. The GP model is a non-linear and non-parametric machine learning method that models the relationship between input and output variables as a Gaussian distribution over functions. It offers a probabilistic framework for making predictions along with uncertainty estimates, defined by a mean and covariance (Rasmussen \& Williams, 2006).

$$
\begin{equation*}
f(x) \sim \operatorname{GP}\left(m(x), k\left(x, x^{\prime}\right)\right) \tag{1}
\end{equation*}
$$

where $m(x)$ is the mean function, which is often set to zero for simplicity, and $k\left(x, x^{\prime}\right)$ is the covariance function, also called kernel function. An exponential kernel is adopted in this study for consistency with the baseline LSG formulation, noting that Lu et al. (2025) demonstrated that the robustness of the LSG model under extrapolation can be improved by employing alternative kernels, but the model is generally robust to kernel choice for regular flood events.

For new events, the low-fidelity model is executed, and EOF analysis is performed to derive the low-fidelity temporal ECs using the previously retained EOF spatial patterns. The trained GP model then predicts the corresponding high-fidelity temporal ECs from the low-fidelity temporal EC inputs. These predicted ECs are then combined with the retained EOF spatial patterns by reversing EOF analysis to reconstruct the full high-fidelity flood inundation simulations. This approach enables the LSG model to predict flood inundation with high spatial fidelity and significantly lower computational cost compared to traditional hydrodynamic simulations.

### 2.2. LSG-TS and LSG-Max Variants

To investigate the effectiveness of the LSG model for different types of flood prediction tasks, two LSG model variants are developed: the time series-based LSG model (LSG-TS) and the maximum-based LSG model (LSG-Max).

The LSG-TS model variant, which represents the standard LSG configuration, is designed to capture the temporal evolution of flood inundation. It is trained using time series data of flood extents and water depths. The inclusion of temporal dynamics allows the LSG-TS model variant to learn how inundation patterns evolve over time in response to varying boundary conditions. EOF analysis is performed on the full time series of flood inundation data. Each flood event is thus represented by a sequence of ECs, capturing the temporal evolution of inundation. This approach allows the GP model to learn a set of mapping functions between low-fidelity and high-fidelity temporal ECs, which represent the flood propagation over time. This variant is particularly suited for applications requiring continuous tracking of flood inundation behavior over time. In this study, the resulting time series of flood surfaces are used to derive the maximum flood surface, supporting assessment of the most severe flood impacts.

In contrast, the LSG-Max model variant is designed to directly predict the maximum extent of flood inundation. It is trained only on the maximum envelope of flood surfaces from a large number of flood events. EOF decomposition is applied to the spatial maps of maximum flood inundation across all events. For each event, the dominant ECs are used as inputs to the GP regression model. This approach simplifies training but ignores temporal flood dynamics. By using only the maximum inundation outputs from hydrodynamic simulations, LSGMax simplifies the learning process into a static spatial prediction task.

The key difference between the two model variants lies in how they handle the input and output variables. LSGTS simulates a complete time series of flood surfaces from which the maximum flood surface is subsequently derived, whereas LSG-Max directly models a single flood surface representing the maximum inundation extent

![](https://cdn.mathpix.com/cropped/3772807b-80ff-4020-8ccf-79b9b3e27705-05.jpg?height=950&width=1725&top_left_y=312&top_left_x=181)
Figure 2. Brisbane River Catchment and Lower Brisbane River model domain.

for the entire simulation period. Both variants are built on the same underlying LSG model, that is, they both make use of low-fidelity simulations, EOF-based spatial reduction and Gaussian process regression, but the two model variants are trained on different aspects of flood behavior and data availability.

## 3. Case Study and Experimental Design

In this section, we apply the LSG model to a case study in the Lower Brisbane River floodplain to illustrate the experimental design for assessing low-fidelity model resolution, as well as the LSG model training and prediction process in a real-world complex flood modeling application.

### 3.1. Study Area

The Lower Brisbane River catchment, located in southeast Queensland, Australia, is selected as the study area (see Figure 2). It is a large and hydrodynamically complex system, presenting significant challenges for flood modeling. The floodplain of the Lower Brisbane River extends over an area, that is, approximately $2,000 \mathrm{~km}^{2}$, and consists of a diverse landscape that includes densely urbanized areas (the City of Brisbane and Ipswich), semiurban developments, and rural floodplains. The total catchment area contributing flows to the floodplain is around $13,500 \mathrm{~km}^{2}$, approximately half of which is regulated by Wivenhoe and Somerset Dams. These dams are arranged in a cascade system, with Somerset Dam located upstream of Wivenhoe Dam. Flows released from Somerset are captured by Wivenhoe, which then controls downstream releases during flood events. In this study, simulations adopt outflows from Wivenhoe Dam as an upstream boundary condition for modeling flood dynamics in the lower catchment.

The Lower Brisbane River receives inflows from several tributaries and creeks, including the Bremer River, Warrill Creek, Lockyer Creek, Laidley Creek, Purga Creek and Oxley Creek. These waterways contribute to localized flood peaks and interact with the main river channel in highly dynamic and non-linear ways. Ultimately, all flows discharge into Moreton Bay on the Coral Sea. The estuarine section of the river is subject to tidal influence, affecting flood behavior over the lower 80 km of the mainstream during high-flow conditions.

These interacting flood processes-a combination of regulated upstream releases, mainstream discharge, tributary inflows, backwater tributary effects, and tidal influence-result in complex flood behavior and frequent compound flooding across the floodplain. This hydrodynamic complexity poses significant challenges for traditional surrogate modeling and highlights the need for advanced techniques that can handle both spatial and temporal flood dynamics effectively.

In addition to its complexity, the region has experienced multiple major flood events, most notably the 2010-2011 Brisbane floods, which resulted 33 fatalities (Holmes, 2012). Broader assessments indicate an excess of AUD $\$ 6.7$ billion in direct damage, with the total cost rising to approximately AUD $\$ 14.1$ billion when indirect impacts are considered (Deloitte Access Economics, 2016). The availability of high-resolution hydrodynamic model outputs further strengthens the case for selecting the Lower Brisbane River floodplain as a challenging test case for evaluating the performance of the LSG model under complex real-world dynamics.

### 3.2. Hydrological and Hydrodynamic Models

The hydrological and hydrodynamic models described in this section simulate flood behavior across a range of historical and synthetic events. These simulations provide essential flood outputs, including flows, water depths and extents, that are used to generate the training and validation data sets for the LSG model.

### 3.2.1. Hydrological Model

The hydrological modeling of the Brisbane River catchment was undertaken using the URBS (Unified River Basin Simulator) hydrological modeling suite (Carroll, 2012), developed and implemented by the agency responsible for operating the two dams (Seqwater). The URBS model simulates rainfall-runoff generation and flow routing across both gauged and ungauged sub-catchments, making it well-suited for large, complex river systems.

The model covers the entire Brisbane River catchment and includes a detailed representation of major tributaries and regulated systems. It accounts for spatial and temporal variations in rainfall, catchment response, and antecedent soil moisture conditions, enabling realistic simulation of inflow hydrographs under a wide range of flood scenarios.

Model calibration was conducted using observed streamflow and rainfall data from multiple historical flood events as part of the Brisbane River Catchment Flood Study (BRCFS; Aurecon, 2015). The calibrated URBS hydrological model provides inflow hydrographs that are applied as boundary conditions for the hydrodynamic model, including regulated releases from Wivenhoe Dam and tributary and sub-catchment inflows applied at multiple locations across the model domain. Downstream tidal levels at the mouth of the Brisbane River in Moreton Bay are imposed as the downstream boundary condition. For historical events, gauged regulated releases from Wivenhoe Dam are used directly as the dam-release boundary condition. For synthetic design events, URBS is applied within a Monte Carlo simulation framework to generate a large ensemble of flood events capturing variability in rainfall patterns, antecedent soil moisture conditions, and dam operating behavior. The resulting inflow hydrographs to Wivenhoe Dam are then routed through a dam operation and storage-release representation to generate corresponding Wivenhoe release hydrographs, which are used as inflow boundary conditions for the hydrodynamic simulations. These simulated events are subsequently classified and selected to construct the training and validation data sets used in the LSG model.

### 3.2.2. High-Fidelity Hydrodynamic Model

A detailed 1D/2D hydrodynamic model was developed in TUFLOW as part of the BRCFS to simulate flood behavior across the Lower Brisbane River and its major tributaries (BMT WBM, 2016). This high-fidelity model served as the reference model for generating training and validation data for the LSG model.

This high-fidelity model employs a two-dimensional (2D) computational grid with 30 m resolution, using TUFLOW's CPU-based implicit solver to solve the full 2D shallow water equations. Model outputs are written to results grids at 15 m resolution (half the cell size) using TUFLOW's default output interpolation scheme. Although these outputs are provided at 15 m resolution, the numerical solution is fully governed by the 30 m computational grid and is not affected by the output interpolation. All LSG training and prediction were performed using the 15 m resolution output grids, which provide a smoother spatial representation of simulated water
levels and flood extents while retaining the underlying 30 m hydrodynamic solution. The hydrodynamic model adopts a coupled 1D-2D configuration, with the Lower Brisbane River mainstream represented using a fully twodimensional (2D) grid, while tributaries including Lockyer Creek, the upper Bremer River, and their upstream reaches are simulated using one-dimensional (1D) channel elements. The 1D and 2D domains are dynamically coupled at channel-floodplain interfaces, enabling bidirectional exchange of mass and momentum based on local water levels and hydraulic connectivity. Overbank flows and surface runoff are routed directly within the 2D grid, ensuring mass conservation across the coupled system. The model integrates high-resolution LiDAR-derived topography, detailed bathymetric data, and explicit representation of hydraulic structures, including bridges, culverts, and levees.

The model domain covers the full extent of the Lower Brisbane River, from Wivenhoe Dam to the river mouth, and includes major tributaries such as the Bremer River, and Warrill, Lockyer, Laidley and Oxley Creeks. The boundary conditions, defined using hydrographs from the URBS hydrological model, include gauged regulated releases from Wivenhoe and Somerset Dams, lateral inflows from major tributaries, localized internal inflows for URBS sub-catchments within the model domain, and downstream tidal levels at the mouth of the Brisbane River in Moreton Bay. The model was calibrated and validated against five well-documented historical flood events (1974, 1996, 1999, 2011, and 2013), as well as observed tidal data, to ensure accurate simulation of flood levels and flow patterns.

The comprehensive model structure and robust calibration provide for an accurate and detailed representation of floodplain dynamics. It provides the physically meaningful and representative flood simulations used to train the LSG model across the floodplain.

### 3.2.3. Low-Fidelity Hydrodynamic Models

To support LSG model development, low-fidelity hydrodynamic models were constructed as separate simulations by systematically reducing the computational grid resolution of the high-fidelity model. This process is distinct from the 15 m result grids produced from the 30 m high-fidelity simulation, which are generated using TUFLOW's default output interpolation and do not alter the numerical solution. The low-fidelity models therefore represent independent model configurations with coarser spatial resolution. This approach retains the broader hydraulic behavior of the system while significantly reducing computational demands. In addition to using coarser computational grids, small-scale urban hydraulic structures and other detailed internal features were removed from the low-fidelity models to improve computational efficiency. While these features influence localized flow behavior, their effects are largely aggregated at coarser spatial resolutions. Within the LSG model, any resulting loss of local detail in the low-fidelity simulations is compensated through learning from highfidelity model outputs during training, enabling accurate flood inundation predictions to be recovered at the high-fidelity scale. These simplifications enable the low-fidelity models to run rapidly, making them well-suited for near real-time flood prediction and operational applications.

During the initial implementation of the LSG model, its predictive performance was found to be suboptimal across several validation events. This prompted further investigation into potential sources of error that could be limiting model accuracy. Given the hydrodynamic complexity of the Lower Brisbane River floodplain, one hypothesized cause for the poor performance of the low fidelity model was the coarse spatial resolution of the adopted hydrodynamic inputs. It was speculated that a coarser resolution might inadequately represent key hydraulic features, such as tributary interactions, flow constrictions, and floodplain connectivity, which are critical to accurate flood prediction.

To explore this hypothesis, an experiment was conducted to explore the sensitivity of the results to different spatial resolutions. Two low-fidelity hydrodynamic models were developed by systematically coarsening the original high-fidelity model, which has a spatial resolution of 30 m . One low-fidelity model was constructed at a resolution of 120 m (results grids written at 60 m , i.e., half the grid cell size), and the other at 300 m (results grids at 150 m ), allowing a comparative assessment of the impact of spatial resolution on LSG model performance. Each low-fidelity model was used independently to train the LSG model, ensuring that all other aspects of the modeling workflow remained unchanged to isolate the effects of resolution.

This experimental design enabled a direct comparison of predictive accuracy between the two low-fidelity resolutions. The results provide key insights into the role of spatial detail in LSG model performance and inform the choice of low-fidelity model resolution for model implementation.

### 3.3. Flood Events for Training and Validation

The training and validation data sets for the LSG models were developed through a systematic selection process. This approach ensured that the chosen flood events captured the full range of hydrological variability and frequency characteristics present in the Brisbane River catchment.

A total of 47 synthetic flood events were derived using the URBS hydrological model to support the development and evaluation of the LSG model. The Monte Carlo simulation framework incorporates variability in rainfall patterns, soil moisture conditions, and dam operations. Thousands of synthetic design events were generated through repeated stochastic simulation. From this large ensemble, a representative subset of 47 events was selected to ensure coverage of a broad range of plausible flood scenarios while keeping computational demand manageable. These synthetic floods were categorized into 11 annual exceedance probability (AEP) classes, ranging from 1 in 2 to 1 in 500 . Each AEP class includes 4-7 events, ensuring sufficient variability in both spatial and temporal flood dynamics for effective LSG model training.

These 47 synthetic design floods were then input to the high-fidelity hydrodynamic model to generate highresolution flood surfaces (see Appendix A). These outputs served as a critical component of the training and validation data for both LSG-TS and LSG-Max model variants. In addition to the synthetic events, four historical flood events (1996, 1999, 2011, and 2013) were also included in the data set to incorporate observed flood behavior into the LSG model training and validation (see Appendix A).

For the LSG-TS model variant, eight events were used for training, including six synthetic design events selected from AEP classes ranging between 1 in 20 and 1 in 100, along with two historical events ( 1999 and 2011). These historical events were selected to represent contrasting flood magnitudes under regulated conditions, with the 1999 event being a relatively minor flood and the 2011 event representing a major flood associated with substantial regulated releases from Wivenhoe Dam. This combination enables the model to learn temporal flood dynamics across a wide range of event severities. This subset was chosen to balance representativeness and computational efficiency for generating high-fidelity simulations, rather than to optimize the minimum number of required training events, as training on all 47 events would be time-consuming given the large volume of time series data. Full time series of flood surfaces were available for these events at a $2-\mathrm{hr}$ temporal resolution, allowing the model to learn the temporal progression of flood behavior across the full spatial domain.

In contrast, the LSG-Max model variant was trained using 47 flood events, including 45 synthetic design events and the same two historical events. Unlike LSG-TS model variant that simulates the complete time series of the flood event, LSG-Max extracts only the maximum flood depth and extent for each event. This approach enabled the model to generalize across a broad and diverse set of maximum flood scenarios, providing a robust basis for static spatial flood prediction.

To investigate the influence of training data set composition, both model variants were also trained using synthetic events only. This enabled a direct comparison with models trained using a combination of both synthetic and historical events, providing insights into the value of historical events to support model generalizability and predictive skill.

To ensure an unbiased evaluation, two synthetic design events (VE1 and VE2) were selected from the remaining pool of 47 design events not used for training and withheld exclusively for model validation, together with the two historical validation events (VE3: 1996 and VE4: 2013). All validation events are of moderate magnitude; notably, the 1996 event occurred without regulated releases from Wivenhoe Dam, providing an independent test of model performance under differing operational conditions.

Together, these synthetic and historical flood events provided a diverse and representative data set, enabling robust training and validation of the LSG model for practical flood modeling applications.

![](https://cdn.mathpix.com/cropped/3772807b-80ff-4020-8ccf-79b9b3e27705-09.jpg?height=465&width=1589&top_left_y=312&top_left_x=248)
Figure 3. Implementation process of the LSG model in this study. The LSG model comprises three main components: a low-fidelity hydrodynamic simulation, dimensionality reduction using Empirical Orthogonal Function analysis, and predictive modeling via Gaussian process regression.

### 3.4. Overall Modeling Workflow

The implementation of the LSG model for the Lower Brisbane River floodplain is illustrated in Figure 3, while a comprehensive description of the modeling approach is provided in Section 2.

Hydrological inputs were generated using the URBS model for both Monte Carlo design events and historical flood events. The resulting hydrographs, representing boundary conditions, were then used to drive high-fidelity and low-fidelity hydrodynamic simulations. The high-fidelity simulations produced reference flood outputs, including both time series and maximum flood surfaces. These outputs were used to train two LSG model variants-LSG-TS and LSG-Max.

As part of the LSG model, EOF decomposition was applied to high-fidelity outputs to extract dominant EOF spatial patterns and their associated temporal ECs. These EOF patterns were then used to derive the corresponding temporal ECs from the low-fidelity outputs, enabling consistent dimensionality reduction across fidelity levels. For the LSG-TS model variant, the first 100 ECs were retained from the full time series to capture key spatialtemporal variations. For the LSG-Max model variant, 47 ECs were retained, corresponding to the number of training events used (i.e., one maximum flood map per event). This approach ensured that the LSG model preserved the full variance of peak flood conditions.

A Gaussian process regression model was then trained to learn the relationship between low-fidelity ECs and the corresponding high-fidelity ECs. GP hyperparameters were optimized using the L-BFGS-B algorithm, a quasiNewton optimisation method well-suited for bounded optimisation problems. The current LSG model used an exponential kernel in the GP regression model to define the covariance structure between inputs.

Once trained, the LSG models were used to predict flood inundation outcomes using a data set not used in training, which included two historical (1996 and 2013 floods) and two synthetic events. These LSG model predictions were then compared to corresponding outputs from the high-fidelity hydrodynamic model to evaluate predictive accuracy.

All data preprocessing, model development, and evaluation procedures were conducted using Python. Dimensionality reduction was performed using EOF analysis, implementing through Principal Component Analysis available in the sklearn.decomposition module. The Gaussian process learning component of the LSG model was built using the GPflow library, which provides scalable and flexible tools for Gaussian process regression.

### 3.5. Model Performance Evaluation

The performance of the LSG models was evaluated by comparing their predictions to those generated by the highfidelity model. The evaluation focused on both predictive accuracy and computational efficiency. To assess these, a set of quantitative metrics was employed, including the Root Mean Square Error (RMSE), Critical Success Index (CSI), model runtime and speed-up ratio.

Predictive accuracy was assessed using RMSE, and CSI, which were applied to the predicted peak water depths and maximum flood extents. These metrics enabled a detailed comparison with high-fidelity model results for the
validation events. RMSE was computed to quantify differences between predicted and reference water depths across all spatial grid cells. It reflects the average magnitude of prediction errors, with lower values indicating higher accuracy (Equation 2; Dawson et al., 2007).

$$
\begin{equation*}
\text { RMSE }=\sqrt{\frac{\sum_{i=1}^{n}\left(\hat{h}_{i}-h_{i}\right)^{2}}{n}} \tag{2}
\end{equation*}
$$

where $n$ is the total number of grid cells, $\hat{h}_{i}$ is the predicted peak water depth of the LSG model, $h_{i}$ is the reference peak water depth of the high-fidelity model

CSI was employed to assess the spatial accuracy of maximum flood extent predictions, using a binary threshold of inundation (e.g., depth $\geq 0.03 \mathrm{~m}$ ). It quantified the proportion of correctly predicted maximum inundated areas relative to the total area covered by predicted and reference maximum flood extents (Equation 3; Jolliffe \& Stephenson, 2012; Stephens et al., 2014).

$$
\begin{equation*}
\mathrm{CSI}=\frac{H}{H+M+F} \tag{3}
\end{equation*}
$$

where $H$ is the number of correctly predicted flooded cells (hits), $M$ is the number of missed flooded cells, and $F$ is the number of falsely predicted flooded cells.

Computational efficiency was quantified using both model runtime and speed-up ratio. Runtime refers to the total simulation time required to generate flood predictions. To further illustrate efficiency gains, the speed-up ratio was calculated to quantify the relative improvement in efficiency by comparing LSG model runtime to that of the high-fidelity model (Equation 4; Lu et al., 2025).

$$
\begin{equation*}
\text { Speed-up ratio }=\frac{T_{\mathrm{HF}}}{T_{\mathrm{LSG}}} \tag{4}
\end{equation*}
$$

where $T_{\mathrm{HF}}$ is the runtime of the high-fidelity model and $T_{\mathrm{LSG}}$ is the runtime of the LSG model.
Together, these metrics provided a comprehensive assessment of the LSG model's ability to replicate high-fidelity flood predictions accurately while significantly reducing computational cost. The results demonstrate the model's reliability and its ability to generalize to other flood events, supporting its use in practical flood modeling applications.

## 4. Results

This section evaluates how the use of low-fidelity model inputs at two spatial resolutions affects LSG model performance. We then compare the performance of the two LSG model variants-LSG-TS and LSG-Max-across four independent validation events (VE), including two synthetic flood events (VE1 and VE2) and two historical events (VE3: 1996 and VE4: 2013). Model performance is evaluated using RMSE, CSI, runtime and speed-up ratio metrics as described in Section 3.5, and the influence of different training data sets is also assessed.

### 4.1. Influence of Low-Fidelity Resolution

An experimental analysis was undertaken to assess the influence of low-fidelity model resolution on the predictive performance of the LSG model. Two low-fidelity hydrodynamic models, LF120 (120 m resolution) and LF300 ( 300 m resolution), were derived by systematically coarsening the original high-fidelity model. The primary objective was to determine whether the spatial resolution of low-fidelity inputs significantly affects LSG model accuracy.

The results demonstrate that the adopted spatial resolution has a strong impact on the performance of the lowfidelity model, especially for the LSG-TS configuration. Across most validation events, the LSG-TS models trained with LF120 inputs consistently outperformed those using LF300, achieving lower RMSE values and higher CSI scores. As shown in Figure 4, the smaller blue bubbles, representing LF120 inputs for LSG-TS, are

![](https://cdn.mathpix.com/cropped/3772807b-80ff-4020-8ccf-79b9b3e27705-11.jpg?height=760&width=1395&top_left_y=312&top_left_x=581)
Figure 4. Performance metrics comparison for low-fidelity models at 120 m (LF120) and 300 m (LF300) resolution for LSGTS (left) and LSG-Max (right). Colors denote validation events (VE1-VE4), and bubble size represents low-fidelity resolution $($ LF120 $=$ small , LF300 $=$ large $)$. Higher Critical Success Index values and lower Root Mean Square Error values indicate better model performance.

clustered toward the bottom right of the plots, indicating higher predictive accuracy. For example, in VE2, the LSG-TS model variant achieves improved performance with LF120 model (RMSE $=0.079$, CSI $=0.944$ ), compared to the much coarser LF300 model (RMSE $=0.115, \mathrm{CSI}=0.936 \mathrm{CSI}$ ). The benefit of higher-resolution input was even more pronounced in VE4, where the LSG-TS model variant trained with 8 events reduced RMSE from 0.413 to 0.132 and improved CSI from 0.791 to 0.889 . Similar trends are also observed in other validation events, where the finer-resolution LF120 inputs appear to capture more detailed spatial-temporal flood dynamics, leading to more accurate predictions.

To further verify the influence of low-fidelity resolution, water depth time series are extracted from five representative locations along the Lower Brisbane River (see Figure 5), all situated within the main channels or major tributaries where model discrepancies are typically largest as shown in Figure 6. These hydrographs, derived from the low-fidelity models, are compared against reference outputs from the high-fidelity model. At Loc1 and Loc3, LF120 exhibits an apparent minimum depth ( $\sim 10 \mathrm{~m}$ ), which is consistent with coarsening-related smoothing of channel and terrain representation and reduced sensitivity to shallow-water drawdown. At the downstream Loc5, the larger deviation in LF300 likely reflects resolution limitations in representing low-gradient downstream hydraulics and backwater and tidal influences, suggesting that a minimum low-fidelity resolution may be required in downstream regions. The comparison reveals that the LF120 model produces time series more closely aligned with the high-fidelity results than the LF300 model. This improvement in temporal accuracy helps explain why LSG-TS models using LF120 inputs consistently outperformed those using LF300, particularly in capturing the dynamic progression of flood events.

However, this trend is not uniform for the LSG-Max model variant. In several instances, such as VE3 and VE4 (the historical 1996 and 2013 floods), the LF300 models yield comparable or slightly better results than the LF120 models, especially for RMSE. Figure 4 also indicates that LSG-Max exhibits more stable spatial matching for validation events, particularly VE3 and VE4. These historical events are characterized by complex, event-specific temporal dynamics. LSG-TS explicitly incorporates time-series information and is therefore more sensitive to variations in hydrograph shape, event duration, and timing mismatches present in historical floods, which can lead to increased spatial variability. In contrast, LSG-Max relies on static maximum flood depth and extent, resulting in more stable spatial matching when evaluated against peak inundation patterns. The results suggest that while finer low-fidelity resolution (LF120) can substantially enhance performance in dynamic flood predictions (LSG-TS),

![](https://cdn.mathpix.com/cropped/3772807b-80ff-4020-8ccf-79b9b3e27705-12.jpg?height=1929&width=1401&top_left_y=310&top_left_x=577)
Figure 5. Hydrograph comparisons at five selected locations in the Lower Brisbane River floodplain for low-fidelity models at 120 m (LF120) and 300 m (LF300) resolutions across four training events (TE1-TE4). The time series are taken from locations within the main channels and major tributaries, where model discrepancies are typically most pronounced.

its benefits may be less pronounced in static predictions (LSG-Max). Accordingly, Section 4.2-4.6 present results for the LF120 model only, as this configuration provides the most informative basis for assessing model behavior.

![](https://cdn.mathpix.com/cropped/3772807b-80ff-4020-8ccf-79b9b3e27705-13.jpg?height=1331&width=1404&top_left_y=310&top_left_x=577)
Figure 6. Comparison of peak water depth errors for LSG-TS and LSG-Max models using LF120 across all validation events. Red areas indicate overestimation of flood depths, while blue areas indicate underestimation. Darker shades correspond to larger magnitudes of error.

### 4.2. Peak Water Depths

Prediction of peak water depths is critical for assessing flood severity. The LSG-TS model variant, trained using a combination of synthetic and historical events with the LF120 configuration, consistently achieves the lower RMSE values than LSG-Max. It demonstrates strong agreement with high-fidelity outputs.

Across all validation events, the LSG-TS model variant reduces RMSE to well below 0.15 m , with values ranging from 0.079 to 0.132 m as illustrated in Table 1 and Figure 4 (small bubbles). In VE1, RMSE is reduced to 0.081 m , and in VE2 to 0.079 m , highlighting the model's ability to accurately predict peak depths across diverse flood scenarios. Even in historical flood events-1996 and 2013-LSG-TS again maintains better numerical performance compared to LSG-Max.

By comparison, the LSG-Max model variant, although developed specifically for predicting only maximum flood surfaces, also provides reasonable estimates of peak water depths, with RMSE values remaining under 0.25 m (see Table 1 and Figure 4 small bubbles). In VE1, LSG-Max achieves an RMSE of 0.115 m , while in VE2 it attains an RMSE of 0.145 m , demonstrating reliable performance across validation events even without temporal input. Compared to LSG-TS, LSG-Max shows greater variability in water depth predictions, particularly with larger errors along the river channels (see Figure 6). While effective in approximating broad spatial patterns, its depth estimates tend to be less precise, especially in areas with complex flow regimes or steep depth gradients.

Table 1
Comparison of LSG Model Performance Against Corresponding Low-Fidelity Models
| Val event | Model | Based on LF120 |  |  |  | Based on LF300 |  |  |  |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
|  |  | RMSE | CSI | $\Delta$ RMSE versus LF | $\Delta$ CSI versus LF | RMSE | CSI | $\Delta$ RMSE versus LF | $\Delta$ CSI versus LF |
| VE1 | LSG-TS | 0.081 | 0.925 | 87\% | 28\% | 0.157 | 0.923 | 89\% | 87\% |
|  | LSG-Max | 0.115 | 0.917 | 82\% | 27\% | 0.134 | 0.911 | 91\% | 85\% |
|  | LF | 0.629 | 0.721 | - | - | 1.454 | 0.493 | - | - |
| VE2 | LSG-TS | 0.079 | 0.944 | 89\% | 26\% | 0.115 | 0.936 | 94\% | 81\% |
|  | LSG-Max | 0.145 | 0.933 | 81\% | 25\% | 0.120 | 0.916 | 94\% | 78\% |
|  | LF | 0.751 | 0.748 | - | - | 1.901 | 0.516 | - | - |
| VE3 | LSG-TS | 0.132 | 0.889 | 79\% | 23\% | 0.413 | 0.791 | 71\% | 61\% |
|  | LSG-Max | 0.217 | 0.868 | 65\% | 20\% | 0.201 | 0.903 | 86\% | 84\% |
|  | LF | 0.621 | 0.724 | - | - | 1.40 | 0.492 | - | - |
| VE4 | LSG-TS | 0.123 | 0.888 | 80\% | 21\% | 0.237 | 0.831 | 84\% | 62\% |
|  | LSG-Max | 0.244 | 0.904 | 60\% | 23\% | 0.241 | 0.908 | 83\% | 77\% |
|  | LF | 0.609 | 0.732 | - | - | 1.445 | 0.512 | - | - |


These results demonstrate that both LSG-TS and LSG-Max can replicate peak water levels with reasonable accuracy. LSG-TS outperforms LSG-Max across all cases, benefiting from richer training data set, but both demonstrate significant improvements over low-fidelity inputs.

### 4.3. Maximum Flood Extents

The CSI metric is used to evaluate the spatial accuracy of flood extent predictions. Both LSG-TS and LSG-Max models demonstrate strong performance in reproducing high-fidelity flood extent patterns, with CSI values above 0.86 (see Table 1 and Figure 7).

The LSG-TS model generally achieves slightly higher CSI scores compared to the LSG-Max model across most validation events. As shown in Table 1 and Figure 4 (small bubbles), CSI values reach 0.925 in VE1 and 0.944 in VE2, indicating strong agreement with high-fidelity flood extents. The LSG-Max model also performs comparably well, with CSI values ranging between 0.868 and 0.933 . Notably, in VE4, the LSG-Max model slightly outperforms LSG-TS for CSI. This performance is consistent with the results shown in Figure 7. For VE1 to VE3, the area of agreement (blue) is slightly larger in LSG-TS compared to LSG-Max, whereas for VE4, it is slightly smaller. This suggests that the LSG-Max can deliver comparable spatial accuracy in predicting maximum flood extents, despite its simpler and static design. These findings confirm that both LSG-TS and LSG-Max models are capable of producing spatially reliable flood extent predictions.

### 4.4. Comparison With Low-Fidelity Model Outputs

To assess the added value of the LSG models, each model is assessed against its corresponding low-fidelity counterpart at the same resolution: LSG120 with LF120 at 120 m , and LSG300 with LF300 at 300 m . This comparison illustrates the accuracy improvement achieved by the LSG model over using the low-fidelity model alone, particularly in replicating high-fidelity flood behavior.

Across all validation events, both LSG-TS and LSG-Max models substantially outperformed the corresponding low-fidelity models (see Table 1). When benchmarked against LF300, the LSG models achieve large gains, reducing RMSE by $70 \%-90 \%$ and increasing CSI by $60 \%-85 \%$. Even with higher-quality LF120 inputs, the LSG models still deliver additional improvements, reducing RMSE by $60 \%-80 \%$ and increasing CSI by $20 \%-30 \%$. These results demonstrate the LSG model is an effective approach, delivering substantial improvements over the baseline low-fidelity model.

![](https://cdn.mathpix.com/cropped/3772807b-80ff-4020-8ccf-79b9b3e27705-15.jpg?height=1686&width=1404&top_left_y=310&top_left_x=577)
Figure 7. Comparison of maximum flood extents for LSG-TS and LSG-Max models using LF120 across all validation events. White areas indicate locations that remain dry in both HF and LSG models. Yellow areas are inundated in LSG predictions only, red areas are inundated in HF simulations only, and blue areas represent agreement between HF and LSG (flooded in both).

### 4.5. Impact of Training Data Set Size

The predictive accuracy of the LSG models is strongly influenced by the quality and composition of the training data set. In this study, both LSG-TS and LSG-Max in the LF120 configuration are trained using synthetic events only or a combination of synthetic and historical events. Because LSG-TS and LSG-Max are trained on data sets with different sizes and data structures, the training performance is presented to illustrate model-specific learning behavior rather than to provide a direct quantitative comparison between the two variants.

![](https://cdn.mathpix.com/cropped/3772807b-80ff-4020-8ccf-79b9b3e27705-16.jpg?height=770&width=1393&top_left_y=312&top_left_x=583)
Figure 8. Performance comparison of different training data sets for LSG-TS and LSG-Max using LF120. Colors denote validation events (VE1-VE4). The size of each bubble indicates the size of the training data sets: larger bubbles represent data sets that include both synthetic and historical events, while smaller bubbles represent data sets with only synthetic events. Higher Critical Success Index values and lower Root Mean Square Error values indicate better model performance.

Including historical events in the training data set leads to clear improvements in model performance for most validation cases, with the effect being particularly pronounced for the LSG-TS configuration. As shown in Figure 8, larger bubbles (representing data sets that include synthetic and historical events), generally appear further toward the bottom right than smaller ones (representing data sets that include synthetic events only) for the same models and validation events, indicating lower RMSE and higher CSI. For example, in VE3 (1996), RMSE improves from 0.157 to 0.132 , and CSI increased from 0.870 to 0.889 . A similar improvement is seen in VE2 and VE4. These enhancements suggest that the inclusion of historical events allows the LSG-TS model to capture more realistic flood dynamics, improving its ability to generalize to real-world conditions. However, in VE1, adding historical events led to a slight increase in RMSE and a marginal drop in CSI, though overall performance remains comparable. This suggests that while historical events generally improve generalizability, their impact may vary depending on alignment with the validation scenario.

A similar trend was observed for the LSG-Max configuration, though the effect is slightly more modest compared to LSG-TS. Although LSG-Max focuses on static predictions of maximum flood surfaces, the inclusion of historical events still leads to measurable improvements for most validation events. For instance, in VE4 (2013), adding historical events reduces the RMSE from 0.285 to 0.244 and slightly improves the CSI from 0.902 to 0.904 . This improvement indicates that even in static maximum condition modeling, incorporating the variability of real events can support better generalization of the model. As shown in Figure 8, the LSG-TS results (left panel) generally exhibit lower RMSE and higher CSI values than the corresponding LSG-Max results (right panel) across different training data sets, indicating the superior overall accuracy of the time series-based approach.

These results demonstrate the importance of incorporating historical flood events into the training data set, particularly for improving the generalizability of the LSG model (Fraehr et al., 2025). While synthetic events provide broad probabilistic coverage, historical events introduce realistic flood dynamics that strengthen model learning. Furthermore, including a larger and more diverse events in the training data set has the potential to improve predictive accuracy. However, this potential gain must be balanced against the increased computational cost of simulating and processing additional high-fidelity events. An optimal training data set should therefore consider both performance improvements and resource efficiency.

Table 2
Computational Efficiency Comparison Between Low-Fidelity, LSG and High-Fidelity Models
| Model | Runtime | Speed-up radio |
| :--- | :--- | :--- |
| LF120 | 25 min | 28.80 |
| LF300 | 12 min | 60.00 |
| LF120 + LSG-TS | 25.7 min | 28.02 |
| LF120 + LSG-Max | 25.1 min | 28.69 |
| LF300 + LSG-TS | 12.7 min | 56.69 |
| LF300 + LSG-Max | 12.1 min | 59.50 |
| HF | $12 \mathrm{hr}(720 \mathrm{~min})$ | - |


Note. Runtime results are shown as means.

### 4.6. Computational Efficiency

In addition to predictive performance, computational efficiency is a key consideration in evaluating the practicality of the LSG model. The runtime performance of the LSG models is benchmarked against both low-fidelity and high-fidelity models to quantify improvements in computational efficiency.

The LSG model demonstrates substantial speed improvements over highfidelity hydrodynamic simulations. A single simulation using the highfidelity model required approximately 12 hr to complete a 10 -day flood event using a computer with $16 \times$ CPU @ 3.70 GHz and 64 GB RAM, whereas the entire LSG workflow, including low-fidelity simulation, EOF analysis, and Gaussian process prediction, reduces this to within half an hour.

The low-fidelity simulations dominate the total runtime, with approximately 25 min for LF120 and 12 min for LF300 using the TUFLOW CPU solver (see Table 2). In contrast, the subsequent surrogate prediction step adds only a few seconds, which represents a negligible difference between the LSG-TS and LSG-Max runtimes. Overall, the total runtime of the LF120 model was about 25-26 min and around 12-13 min for the LF300 model, leading to speedup ratios of $30-60$ times relative to the high-fidelity model. These results highlight that the efficiency of the LSG approach is governed primarily by the choice of low-fidelity resolution, while the surrogate modeling step itself incurs minimal additional computational burden.

The computational efficiency of the LSG model could be further enhanced by adopting faster hydraulic solvers or hardware acceleration. For example, running the low-fidelity model on GPUs or other rapid hydrodynamic tools would substantially reduce preprocessing time and enable even faster end-to-end predictions.

Overall, the LSG model achieves substantial computational efficiency gains with high predictive accuracy relative to traditional high-fidelity hydrodynamic models. This makes LSG modeling highly suitable for near realtime forecasting, emergency response, and large-scale scenario analysis.

## 5. Discussion

This study demonstrates the effectiveness of both the LSG-TS and LSG-Max model variants. LSG-TS and LSGMax differ fundamentally in how training information is utilized. LSG-Max is designed to predict maximum flood extent and peak flood metrics and relies on a single data surface per event (maximum flood inundation), which typically requires a larger number of events to achieve robust performance. In contrast, LSG-TS exploits the full flood time series, allowing substantially more information to be extracted from each event and reducing the number of underlying events required for training. Investigating both LSG-TS and LSG-Max is therefore highly valuable, as they represent contrasting trade-offs between peak-focused accuracy and data efficiency. LSG-Max provides a direct and computationally efficient formulation for peak flood metrics, while LSG-TS offers the potential to reduce high-fidelity modeling effort by making more effective use of time series data. This distinction is particularly important in practical applications where generating high-fidelity training data is computationally expensive and the number of available events is limited. Accordingly, the comparison between LSG-TS and LSG-Max is therefore intended to inform model selection based on data availability, computational cost, and forecasting objectives, rather than to provide a strict like-for-like comparison under identical training data sets. Because of these fundamentally different data requirements, the training data sets for LSG-TS and LSGMax differ by design. Enforcing identical training data sets would not be meaningful in this context and would undermine the intended use of each model variant. Instead, consistency is ensured through the use of the same independent validation events and evaluation metrics for both models. The results show that both approaches can achieve comparable accuracy for maximum flood metrics, while their relative performance depends on the resolution of the low-fidelity inputs, with LSG-Max performing more robustly for coarser low-fidelity configurations and LSG-TS benefiting more from finer-resolution low-fidelity information.

The superior performance of LSG-TS suggests that time series-based training not only improves numerical accuracy but also enables the model to better capture hydrodynamic complexity across both synthetic and historical events, including situations that are not represented in the training data. Notably, under the LF120 configuration, the LSG-TS model variant still performs well for the validation event VE3 (the 1996 flood event), which occurred
without regulated release from Wivenhoe Dam, despite the training data set being dominated by events with regulated releases. This behaviour is not observed for LF300, likely because the coarser low-fidelity representation limits the effectiveness of temporal inputs in capturing variability in hydrograph shape and flow dynamics. This is particularly critical in floodplains influenced by complex interactions, including dam operations, tidal influence and backwater effects.

While the LSG model demonstrates promising performance, its accuracy can still be improved. One potential enhancement lies in the application of zonal EOF analysis, where the spatial domain is divided into hydrologically or topographically consistent sub-regions and the EOF decomposition is undertaken separately for each zone. This approach has the potential to capture localised flood dynamics more effectively than a single, domain-wide EOF analysis, and may be particularly beneficial for large and complex floodplains such as the Lower Brisbane River. Additionally, increasing the size and diversity of the training data set used in the LSG model could further improve performance by enhancing its ability to generalise across a broader range of flood scenarios. However, this approach requires a substantial number of additional simulations which will lead to increased computational costs during the model development phase. Taken individually or in combination, these strategies offer promising opportunities to improve the robustness and accuracy of the LSG model, especially when applied to large, heterogeneous floodplains.

Finally, while this paper focuses on operationally relevant performance in a complex real-world domain, future work could further strengthen generalisability through evaluation on classical benchmark test cases to isolate model behaviour under controlled hydraulic conditions and facilitate comparison across modelling approaches. In addition, benchmark-style comparisons of the LSG model against state-of-the-art surrogate methods have recently been reported by Fraehr et al. (2024), providing further evidence of the effectiveness of the LSG model across multiple case studies.

## 6. Summary and Conclusion

Flood inundation prediction in large and hydrodynamically complex floodplains remains a major challenge. High-fidelity hydrodynamic models are capable of representing these complex dynamics in detail, but their high computational demands restrict their use for real-time forecasting simulations. This creates a critical need for alternative modeling approaches that can capture essential flood behavior while being computationally efficient enough for operational application.

To address this challenge, this study investigated the Low-fidelity, Spatial analysis, and Gaussian process learning (LSG) model in the Lower Brisbane River catchment. A suite of synthetic and historical flood events was simulated using low-fidelity hydrodynamic models at two spatial resolutions ( 120 and 300 m ). These low-fidelity simulations were combined with dimensionality reduction via EOF analysis and Gaussian process regression learning to emulate the outputs of the high-fidelity model. Two LSG variants: LSG-TS (time series-based) and LSG-Max (maximum-based), were investigated, with emphasis on developing strategies for applying the modeling approach to large and complex floodplains and understanding how low-fidelity resolution influences predictive accuracy.

The results demonstrate that the LSG model can provide accurate flood predictions across a large, hydrodynamically complex floodplain, showing strong potential for operational use where computational efficiency is needed. This study also shows that predictive performance can be sensitive to the resolution of the low-fidelity model. The 120 m low-fidelity simulations produced robust results, whereas adoption of the coarser 300 m resolution led to a marked deterioration in accuracy. This comparison highlights the importance of retaining sufficient spatial detail in the low-fidelity model, as excessive coarsening may reduce predictive skill. Model performance can also be strengthened by the inclusion of historical events in addition to design events in the training data set, which improves the ability to generalize to flood events beyond those used in training.

In terms of model variants, LSG-TS consistently outperforms LSG-Max. Its improved performance is attributed to the use of full time series data, which captures the temporal dynamics of flood propagation and provides a significantly larger training data set. Nonetheless, LSG-Max remains a valuable option when temporal information is less critical. Its predictive accuracy could be further improved through strategies such as increasing the size and variability of the training data set.

Future work should further investigate the limits of low-fidelity resolution, as the comparison between 120 and 300 m models demonstrated that excessive coarsening can lead to a clear loss of predictive skill. In addition, the application of zonal EOF techniques offers potential to better capture localized flood dynamics and further enhance model accuracy in large and complex floodplains.

## Appendix A: List of 51 Flood Events With 47 Synthetic Events (1-47) and 4 Historical Events (48-51)

| Flood event | Synthetic/historical | AEP | Storm duration (hr) | Application |
| :--- | :--- | :--- | :--- | :--- |
| FE1 | Synthetic | 2 | 12 | LSG-Max Training |
| FE2 | Synthetic | 2 | 12 | LSG-Max Training |
| FE3 | Synthetic | 2 | 18 | LSG-Max Training |
| FE4 | Synthetic | 2 | 24 | LSG-Max Training |
| FE5 | Synthetic | 2 | 48 | LSG-Max Training |
| FE6 | Synthetic | 2 | 72 | LSG-Max Training |
| FE7 | Synthetic | 2 | 120 | LSG-Max Training |
| FE8 | Synthetic | 5 | 12 | LSG-Max Training |
| FE9 | Synthetic | 5 | 24 | LSG-Max Training |
| FE10 | Synthetic | 5 | 36 | LSG-Max Training |
| FE11 | Synthetic | 5 | 96 | LSG-Max Training |
| FE12 | Synthetic | 5 | 120 | LSG-Max Training |
| FE13 | Synthetic | 5 | 168 | LSG-Max Training |
| FE14 | Synthetic | 10 | 24 | LSG-Max Training |
| FE15 | Synthetic | 10 | 36 | LSG-Max Training |
| FE16 | Synthetic | 10 | 120 | LSG-Max Training |
| FE17 | Synthetic | 10 | 168 | LSG-Max Training |
| FE18 | Synthetic | 10 | 168 | LSG-Max Training |
| FE19 | Synthetic | 20 | 18 | LSG-Max Training |
| FE20 | Synthetic | 20 | 18 | LSG-Max Training, LSG-TS Training |
| FE21 (VE1) | Synthetic | 20 | 24 | LSG-Max Validation, LSG-TS Validation |
| FE22 | Synthetic | 20 | 48 | LSG-Max Training, LSG-TS Training |
| FE23 | Synthetic | 20 | 96 | LSG-Max Training |
| FE24 | Synthetic | 20 | 120 | LSG-Max Training |
| FE25 | Synthetic | 50 | 48 | LSG-Max Training |
| FE26 (VE2) | Synthetic | 50 | 48 | LSG-Max Validation, LSG-TS Validation |
| FE27 | Synthetic | 50 | 48 | LSG-Max Training, LSG-TS Training |
| FE28 | Synthetic | 50 | 72 | LSG-Max Training |
| FE29 | Synthetic | 50 | 120 | LSG-Max Training |
| FE30 | Synthetic | 50 | 120 | LSG-Max Training, LSG-TS Training |
| FE31 | Synthetic | 100 | 12 | LSG-Max Training |
| FE32 | Synthetic | 100 | 18 | LSG-Max Training, LSG-TS Training |
| FE33 | Synthetic | 100 | 48 | LSG-Max Training |
| FE34 | Synthetic | 100 | 96 | LSG-Max Training, LSG-TS Training |
| FE35 | Synthetic | 100 | 120 | LSG-Max Training |
| FE36 | Synthetic | 200 | 24 | LSG-Max Training |
| FE37 | Synthetic | 200 | 48 | LSG-Max Training |

## Acknowledgments

We thank Department of Environment, Tourism, Science, and Innovation for the provision of the Brisbane River Catchment Flood Study reports and the hydrological and high-fidelity hydrodynamic models developed as part of the flood study. Open access publishing facilitated by The University of Melbourne, as part of the Wiley - The University of Melbourne agreement via the Council of Australasian University Librarians.

## Appendix A <br> Continued

| Flood event | Synthetic/historical | AEP | Storm duration (hr) | Application |
| :--- | :--- | :--- | :--- | :--- |
| FE38 | Synthetic | 200 | 48 | LSG-Max Training |
| FE39 | Synthetic | 200 | 96 | LSG-Max Training |
| FE40 | Synthetic | 200 | 96 | LSG-Max Training |
| FE41 | Synthetic | 200 | 96 | LSG-Max Training |
| FE42 | Synthetic | 200 | 120 | LSG-Max Training |
| FE43 | Synthetic | 500 | 24 | LSG-Max Training |
| FE44 | Synthetic | 500 | 72 | LSG-Max Training |
| FE45 | Synthetic | 500 | 72 | LSG-Max Training |
| FE46 | Synthetic | 500 | 168 | LSG-Max Training |
| FE47 | Synthetic | 500 | 168 | LSG-Max Training |
| FE48 | Historical, 1999 | - | - | LSG-Max Training |
| FE49 | Historical, 2011 | - | - | LSG-Max Training |
| FE50 (VE3) | Historical, 1996 | - | - | LSG-Max Validation, LSG-TS Validation |
| FE51 (VE4) | Historical, 2013 | - | - | LSG-Max Validation, LSG-TS Validation |

## Conflict of Interest

The authors declare no conflicts of interest relevant to this study.

## Availability Statement

The hydrological (URBS) and hydrodynamic (TUFLOW) models, together with the data used for the highfidelity and low-fidelity simulations in this study, are licensed by the Queensland Government, Australia (Queensland Government, 2017). Access is available upon request via the Queensland Government website: https://www.business.qld.gov.au/industries/mining-energy-water/water/maps-data/modelling/brisbane-river-ca tchment. The LSG model is coded using Python (version 3.9) and is available from the data repository https://doi. org/10.26188/24312658 (Fraehr, 2024).

## References

Aurecon. (2015). Brisbane River Catchment Flood Study: Comprehensive hydrologic assessment. Draft final hydrological report.
BMT WBM. (2016). Brisbane River Catchment Flood Study: Comprehensive hydraulic assessment. Hydraulics report.
Carroll, D. G. (2012). URBS (Unified river basin simulator): A rainfall runoff routing model for flood forecasting and design, version 5.0 user manual. In $D C P M$.
Chu, H., Wu, W., Wang, Q., Nathan, R., \& Wei, J. (2020). An ANN-based emulation modelling framework for flood inundation modelling: Application, challenges and future directions. Environmental Modelling \& Software, 124, 104587. https://doi.org/10.1016/j.envsoft.2019.10 4587
Contreras, M. T., Gironás, J., \& Escauriaza, C. (2020). Forecasting flood hazards in real time: A surrogate model for hydrometeorological events in an Andean watershed. Natural Hazards and Earth System Sciences, 20(12), 3261-3277. https://doi.org/10.5194/nhess-20-3261-2020
Dawson, C. W., Abrahart, R. J., \& See, L. M. (2007). HydroTest: A web-based toolbox of evaluation metrics for the standardised assessment of hydrological forecasts. Environmental Modelling \& Software, 22(7), 1034-1052. https://doi.org/10.1016/j.envsoft.2006.06.008
Dazzi, S., Shustikova, I., Domeneghetti, A., Castellarin, A., \& Vacondio, R. (2021). Comparison of two modelling strategies for 2D large-scale flood simulations. Environmental Modelling \& Software, 146, 105225. https://doi.org/10.1016/j.envsoft.2021.105225
Deloitte Access Economics. (2016). The economic cost of the social impact of natural disasters. Australian Business Roundtable for Disaster Resilience \& Safer Communities.
Donnelly, J., Abolfathi, S., Pearson, J., Chatrabgoun, O., \& Daneshkhah, A. (2022). Gaussian process emulation of spatio-temporal outputs of a 2D inland flood model. Water Research, 225, 119100. https://doi.org/10.1016/j.watres.2022.119100
Fraehr, N. (2024). Surrogate flood model comparison—Datasets and python code. https://doi.org/10.26188/24312658.v1
Fraehr, N., Wang, Q. J., Wu, W., \& Nathan, R. (2022). Upskilling low-fidelity hydrodynamic models of flood inundation through spatial analysis and Gaussian Process learning. Water Resources Research, 58(8), e2022WR032248. https://doi.org/10.1029/2022WR032248
Fraehr, N., Wang, Q. J., Wu, W., \& Nathan, R. (2023a). Development of a fast and accurate hybrid model for floodplain inundation simulations. Water Resources Research, 59(6), e2022WR033836. https://doi.org/10.1029/2022WR033836
Fraehr, N., Wang, Q. J., Wu, W., \& Nathan, R. (2023b). Supercharging hydrodynamic inundation models for instant flood insight. Nature Water, 1(10), 1-9-843. https://doi.org/10.1038/s44221-023-00132-2

Fraehr, N., Wang, Q. J., Wu, W., \& Nathan, R. (2024). Assessment of surrogate models for flood inundation: The physics-guided LSG model vs. state-of-the-art machine learning models. Water Research, 252, 121202. https://doi.org/10.1016/j.watres.2024.121202
Fraehr, N., Wang, Q. J., Wu, W., \& Nathan, R. (2025). Generation and selection of training events for surrogate flood inundation models. Journal of Environmental Management, 373, 123570. https://doi.org/10.1016/j.jenvman.2024.123570
Holmes, C. E. (2012). Queensland floods commission of inquiry. Retrieved from www.floodcommission.qld.gov.au
Hop, F. J., Linneman, R., Schnitzler, B., Bomers, A., \& Booij, M. J. (2024). Real time probabilistic inundation forecasts using a LSTM neural network. Journal of Hydrology, 635, 131082. https://doi.org/10.1016/j.jhydrol.2024.131082
Jolliffe, I. T., \& Cadima, J. (2016). Principal component analysis: A review and recent developments. Philosophical Transactions of the Royal Society A: Mathematical, Physical \& Engineering Sciences, 374(2065), 20150202. https://doi.org/10.1098/rsta.2015.0202
Jolliffe, I. T., \& Stephenson, D. B. (2012). Forecast verification: A practitioner's guide in atmospheric science. John Wiley \& Sons. https://doi. org/10.1002/9781119960003
Kabir, S., Patidar, S., Xia, X., Liang, Q., Neal, J., \& Pender, G. (2020). A deep convolutional neural network model for rapid prediction of fluvial flood inundation. Journal of Hydrology, 590, 125481. https://doi.org/10.1016/j.jhydrol.2020.125481
Lu, J., Wang, Q. J., Fraehr, N., Xiang, X., \& Wu, X. (2025). Choice of Gaussian process kernels used in LSG models for flood inundation predictions. Journal of Hydrology, 655, 132949. https://doi.org/10.1016/j.jhydrol.2025.132949
Murphy, A. T., Gouldby, B., Cole, S. J., Moore, R. J., \& Kendall, H. (2016). Real-time flood inundation forecasting and mapping for key railway infrastructure: A UK case study. In E3S web of conferences.
Queensland Government. (2017). Brisbane River Catchment Flood Study: Hydrological and hydrodynamic models and data. Retrieved from https://www.business.qld.gov.au/industries/mining-energy-water/water/maps-data/modelling/brisbane-river-catchment
Rasmussen, C. E., \& Williams, C. K. (2006). Gaussian processes for machine learning (Vol. 1). Springer. https://doi.org/10.1142/S01290657040 01899
Razavi, S., Tolson, B. A., \& Burn, D. H. (2012). Review of surrogate modeling in water resources. Water Resources Research, 48(7). https://doi. org/10.1029/2011WR011527
Stephens, E., Schumann, G., \& Bates, P. (2014). Problems with binary pattern measures for flood model evaluation. Hydrological Processes, 28(18), 4928-4937. https://doi.org/10.1002/hyp. 9979
Teng, J., Jakeman, A. J., Vaze, J., Croke, B. F. W., Dutta, D., \& Kim, S. (2017). Flood inundation modelling: A review of methods, recent advances and uncertainty analysis. Environmental Modelling \& Software, 90, 201-216. https://doi.org/10.1016/j.envsoft.2017.01.006
Teng, J., Vaze, J., Kim, S., Dutta, D., Jakeman, A., \& Croke, B. (2019). Enhancing the capability of a simple, computationally efficient, conceptual flood inundation model in hydrologically complex terrain. Water Resources Management, 33(2), 831-845. https://doi.org/10.1007/s11269-01 8-2146-7
Wang, W., Wang, Q., Nathan, R., \& Velasco-Forero, C. (2022). Rapid prediction of flood inundation by interpolation between flood library maps for real-time applications. Journal of Hydrology, 609, 127735. https://doi.org/10.1016/j.jhydrol.2022.127735
Wang, W., Wang, Q. J., \& Nathan, R. (2025). Gaussian process regression on multiple drivers and attributes for rapid prediction of maximum flood inundation extent and depth. Journal of Hydrology, 649, 132476. https://doi.org/10.1016/j.jhydrol.2024.132476
Zhou, Y., Wu, W., Nathan, R., \& Wang, Q. J. (2021). A rapid flood inundation modelling framework using deep learning with spatial reduction and reconstruction. Environmental Modelling \& Software, 143, 105112. https://doi.org/10.1016/j.envsoft.2021.105112
Zhu, H., Leandro, J., \& Lin, Q. (2021). Optimization of artificial neural network (ANN) for maximum flood inundation forecasts. Water, 13(16), 2252. https://doi.org/10.3390/w13162252

