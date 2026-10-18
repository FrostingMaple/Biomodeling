# Biological Mathematical Modelling Parameter Lexicon

- Generated: 2026-09-29
- Entries: 40
- Machine-readable source: `parameters.json`

## Sources

| Source ID | Name | URL |
| --- | --- | --- |
| europepmc | Europe PMC REST API | https://www.ebi.ac.uk/europepmc/webservices/rest/search |
| biomodels | BioModels curated model repository | https://www.ebi.ac.uk/biomodels/ |
| biomodels_search | BioModels kinetic model search response | https://www.ebi.ac.uk/biomodels/search |
| sbml | Systems Biology Markup Language (SBML) | https://sbml.org/ |
| reactome | Reactome Content Service | https://reactome.org/ContentService/ |
| sabio_rk | SABIO-RK reaction kinetics database | https://sabio.h-its.org/ |
| brenda | BRENDA enzyme database | https://www.brenda-enzymes.org/ |
| kegg | KEGG pathway database | https://www.genome.jp/kegg/ |
| classic_mm | Michaelis and Menten enzyme kinetics | https://doi.org/10.1016/S0076-6879(09)63002-7 |
| classic_hh | Hodgkin and Huxley action potential model | https://doi.org/10.1113/jphysiol.1952.sp004764 |
| classic_sir | Kermack and McKendrick compartmental epidemic model | https://doi.org/10.1098/rspa.1927.0118 |
| classic_lotka_volterra | Lotka-Volterra population dynamics | https://doi.org/10.1038/140070a0 |
| repressilator | Elowitz and Leibler repressilator | https://doi.org/10.1038/35002125 |
| mapk_cascade | Kholodenko MAPK cascade oscillation model | https://doi.org/10.1046/j.1432-1327.2000.01197.x |
| erbb_model | Chen et al. ErbB signaling mass-action model | https://doi.org/10.1038/msb.2008.74 |
| hepatic_glucose | Konig et al. human hepatic glucose metabolism model | https://doi.org/10.1371/journal.pcbi.1002577 |

## Entries

| ID | Canonical name | Symbols | Category | Unit | Confidence |
| --- | --- | --- | --- | --- | --- |
| PARAM_KM | Michaelis constant | Km, K_M, K_m, KM | enzyme_kinetics | concentration | high |
| PARAM_VMAX | Maximum reaction rate | Vmax, V_max, VMAX | enzyme_kinetics | rate | high |
| PARAM_KCAT | Catalytic turnover number | kcat, k_cat, kcat/Km | enzyme_kinetics | per_time | high |
| PARAM_KCAT_KM | Catalytic efficiency | kcat_Km, kcat/Km | enzyme_kinetics | concentration_per_time | high |
| PARAM_KON | Association rate constant | kon, k_on, kf, k_f | binding_kinetics | concentration_per_time | high |
| PARAM_KOFF | Dissociation rate constant | koff, k_off, kr, k_r | binding_kinetics | per_time | high |
| PARAM_KD | Equilibrium dissociation constant | Kd, K_D, KD | binding_equilibrium | concentration | high |
| PARAM_KI | Inhibition constant | Ki, K_i, KI | enzyme_kinetics | concentration | high |
| PARAM_IC50 | Half-maximal inhibitory concentration | IC50, IC_50 | dose_response | concentration | high |
| PARAM_EC50 | Half-maximal effective concentration | EC50, EC_50 | dose_response | concentration | high |
| PARAM_HILL | Hill coefficient | n, n_H, nH | allostery | dimensionless | high |
| PARAM_BETA | Transmission or production parameter | beta, β | population_dynamics | per_time_or_context | high |
| PARAM_GAMMA | Recovery or removal rate | gamma, γ | epidemiology | per_time | high |
| PARAM_SIGMA | Latent or incubation rate | sigma, σ | epidemiology | per_time | high |
| PARAM_R0 | Basic reproduction number | R0, R_0 | epidemiology | dimensionless | high |
| PARAM_MU_GROWTH | Specific growth rate | mu, μ, r | population_dynamics | per_time | high |
| PARAM_CARRYING_CAPACITY | Carrying capacity | K, Kcap | population_dynamics | amount_or_concentration | high |
| PARAM_CLEARANCE | Clearance rate | k_clear, k_clearance, CL | pharmacokinetics | per_time_or_volume_per_time | high |
| PARAM_RELEASE_RATE | Release rate | k_release, k_rel | pharmacokinetics | amount_per_time_or_per_time | high |
| PARAM_HALF_LIFE | Half-life | t_half, t1/2, half_life | pharmacokinetics | time | high |
| PARAM_DIFFUSION | Diffusion coefficient | D, D_diff | spatial_transport | area_per_time | high |
| PARAM_MEMBRANE_POTENTIAL | Membrane potential | Vm, V_m | electrophysiology | voltage | high |
| PARAM_CONDUCTANCE | Ion channel conductance | g, g_Na, g_K, g_L | electrophysiology | conductance | high |
| PARAM_REVERSAL_POTENTIAL | Reversal potential | E, E_Na, E_K, E_L | electrophysiology | voltage | high |
| PARAM_CAPACITANCE | Membrane capacitance | Cm, C_m | electrophysiology | capacitance_per_area | high |
| PARAM_ALPHA_TRANSCRIPTION | Constitutive transcription rate | alpha, alpha0, a_tr, a0_tr | gene_expression | concentration_per_time_or_per_time | high |
| PARAM_KD_MRNA | mRNA degradation rate | kd_mRNA, k_deg_mRNA | gene_expression | per_time | high |
| PARAM_KD_PROT | Protein degradation rate | kd_prot, k_deg_prot | gene_expression | per_time | high |
| PARAM_KT_L | Translation rate | k_tl, k_tl, translation_rate | gene_expression | concentration_per_time_per_mRNA_or_per_time | high |
| PARAM_TAU_MRNA | mRNA time constant | tau_mRNA | gene_expression | time | high |
| PARAM_TAU_PROT | Protein time constant | tau_prot | gene_expression | time | high |
| PARAM_ENZYME_CONCENTRATION | Enzyme concentration | E, [E] | enzyme_kinetics | concentration | high |
| PARAM_SUBSTRATE_CONCENTRATION | Substrate concentration | S, [S] | enzyme_kinetics | concentration | high |
| PARAM_PRODUCT_CONCENTRATION | Product concentration | P, [P] | enzyme_kinetics | concentration | high |
| PARAM_REACTION_FLUX | Reaction flux | v, J, flux | metabolic_modeling | amount_per_time_per_volume | high |
| PARAM_ELASTICITY | Kinetic elasticity | epsilon, ε | metabolic_control | dimensionless | high |
| PARAM_THERMODYNAMIC_DRIVING_FORCE | Thermodynamic driving force | DeltaG, ΔG | thermodynamics | energy | high |
| PARAM_BINDING_PROBABILITY | Binding or state-transition probability | p, P, pi, π | stochastic_modeling | dimensionless | high |
| PARAM_INITIAL_CONCENTRATION | Initial concentration | C0, C_0, X0, X_0 | initial_conditions | concentration | high |
| PARAM_TEMPERATURE | Temperature | T, temperature | environmental_condition | temperature | high |

## Definitions

### PARAM_KM — Michaelis constant

- **Symbols:** Km, K_M, K_m, KM
- **Aliases:** Michaelis constant, Michaelis-Menten constant, half-saturation constant
- **Category:** enzyme_kinetics
- **Definition:** Substrate concentration at which the reaction rate is half of Vmax under a Michaelis-Menten rate law.
- **Unit:** concentration
- **Typical values:** [{"value": "reaction-specific", "unit": "M, mM, µM, nM", "context": "typically reported in kinetic tables or fitted parameter sets"}]
- **Related expressions:** EXPR_MICHAELIS_MENTEN, EXPR_COMPETITIVE_INHIBITION
- **Related models:** MODEL_MICHAELIS_MENTEN, MODEL_ENZYME_KINETICS
- **Sources:** europepmc, biomodels, sabio_rk, brenda, classic_mm
- **Confidence:** high

### PARAM_VMAX — Maximum reaction rate

- **Symbols:** Vmax, V_max, VMAX
- **Aliases:** maximum velocity, maximum reaction rate, limiting rate
- **Category:** enzyme_kinetics
- **Definition:** Asymptotic reaction velocity approached as substrate concentration becomes saturating in a Michaelis-Menten model.
- **Unit:** rate
- **Typical values:** [{"value": "reaction-specific", "unit": "substance/time", "context": "reported with enzyme amount or normalized to protein concentration"}]
- **Related expressions:** EXPR_MICHAELIS_MENTEN, EXPR_COMPETITIVE_INHIBITION
- **Related models:** MODEL_MICHAELIS_MENTEN, MODEL_ENZYME_KINETICS
- **Sources:** biomodels, sabio_rk, brenda, classic_mm
- **Confidence:** high

### PARAM_KCAT — Catalytic turnover number

- **Symbols:** kcat, k_cat, kcat/Km
- **Aliases:** turnover number, catalytic constant
- **Category:** enzyme_kinetics
- **Definition:** Number of substrate molecules converted per enzyme active site per unit time under saturating substrate conditions.
- **Unit:** per_time
- **Typical values:** [{"value": "enzyme-specific", "unit": "s^-1, min^-1", "context": "often derived as Vmax divided by enzyme concentration"}]
- **Related expressions:** EXPR_MICHAELIS_MENTEN, EXPR_CATALYTIC_EFFICIENCY
- **Related models:** MODEL_MICHAELIS_MENTEN, MODEL_ENZYME_KINETICS
- **Sources:** biomodels, sabio_rk, brenda
- **Confidence:** high

### PARAM_KCAT_KM — Catalytic efficiency

- **Symbols:** kcat_Km, kcat/Km
- **Aliases:** specificity constant, catalytic efficiency
- **Category:** enzyme_kinetics
- **Definition:** Ratio of catalytic turnover to Michaelis constant, often used as a measure of enzyme efficiency at low substrate concentration.
- **Unit:** concentration_per_time
- **Typical values:** [{"value": "enzyme-specific", "unit": "M^-1 s^-1", "context": "high values indicate efficient catalysis at low substrate"}]
- **Related expressions:** EXPR_CATALYTIC_EFFICIENCY
- **Related models:** MODEL_MICHAELIS_MENTEN
- **Sources:** brenda, sabio_rk
- **Confidence:** high

### PARAM_KON — Association rate constant

- **Symbols:** kon, k_on, kf, k_f
- **Aliases:** association rate constant, forward binding rate, binding on-rate
- **Category:** binding_kinetics
- **Definition:** Second-order rate constant governing formation of a complex from its binding partners.
- **Unit:** concentration_per_time
- **Typical values:** [{"value": "reaction-specific", "unit": "M^-1 s^-1", "context": "used in mass-action binding and receptor-ligand kinetics"}]
- **Related expressions:** EXPR_MASS_ACTION, EXPR_REVERSIBLE_BINDING
- **Related models:** MODEL_MASS_ACTION, MODEL_RECEPTOR_LIGAND
- **Sources:** biomodels, sabio_rk, erbb_model
- **Confidence:** high

### PARAM_KOFF — Dissociation rate constant

- **Symbols:** koff, k_off, kr, k_r
- **Aliases:** dissociation rate constant, reverse binding rate, binding off-rate
- **Category:** binding_kinetics
- **Definition:** First-order rate constant governing dissociation of a bound complex.
- **Unit:** per_time
- **Typical values:** [{"value": "reaction-specific", "unit": "s^-1, min^-1", "context": "used with kon to determine equilibrium binding affinity"}]
- **Related expressions:** EXPR_REVERSIBLE_BINDING, EXPR_EXPONENTIAL_DECAY
- **Related models:** MODEL_MASS_ACTION, MODEL_RECEPTOR_LIGAND, MODEL_MARKOV_STATE
- **Sources:** biomodels, sabio_rk, erbb_model
- **Confidence:** high

### PARAM_KD — Equilibrium dissociation constant

- **Symbols:** Kd, K_D, KD
- **Aliases:** dissociation constant, binding affinity constant
- **Category:** binding_equilibrium
- **Definition:** Equilibrium ratio koff/kon for a reversible binding reaction; lower values indicate tighter binding.
- **Unit:** concentration
- **Typical values:** [{"value": "reaction-specific", "unit": "M, nM, pM", "context": "used for receptor-ligand or protein-complex affinity"}]
- **Related expressions:** EXPR_REVERSIBLE_BINDING, EXPR_RECEPTOR_BINDING_EQUILIBRIUM
- **Related models:** MODEL_RECEPTOR_LIGAND, MODEL_MASS_ACTION
- **Sources:** biomodels, sabio_rk, erbb_model
- **Confidence:** high

### PARAM_KI — Inhibition constant

- **Symbols:** Ki, K_i, KI
- **Aliases:** inhibitor constant, inhibition constant
- **Category:** enzyme_kinetics
- **Definition:** Dissociation constant for inhibitor binding to free enzyme or enzyme-substrate complex in inhibition models.
- **Unit:** concentration
- **Typical values:** [{"value": "inhibitor-specific", "unit": "M, mM, µM", "context": "used in competitive, noncompetitive, and uncompetitive inhibition expressions"}]
- **Related expressions:** EXPR_COMPETITIVE_INHIBITION
- **Related models:** MODEL_ENZYME_INHIBITION
- **Sources:** biomodels, sabio_rk, brenda
- **Confidence:** high

### PARAM_IC50 — Half-maximal inhibitory concentration

- **Symbols:** IC50, IC_50
- **Aliases:** 50% inhibitory concentration, half-inhibitory concentration
- **Category:** dose_response
- **Definition:** Concentration of an inhibitor producing 50% reduction of a specified response under stated assay conditions.
- **Unit:** concentration
- **Typical values:** [{"value": "assay-specific", "unit": "M, nM, µM", "context": "requires assay, substrate, time, and endpoint context"}]
- **Related expressions:** EXPR_HILL_INHIBITION
- **Related models:** MODEL_DOSE_RESPONSE, MODEL_ENZYME_INHIBITION
- **Sources:** europepmc, erbb_model
- **Confidence:** high

### PARAM_EC50 — Half-maximal effective concentration

- **Symbols:** EC50, EC_50
- **Aliases:** 50% effective concentration, half-effective concentration
- **Category:** dose_response
- **Definition:** Concentration producing 50% of the maximal observed effect under stated experimental conditions.
- **Unit:** concentration
- **Typical values:** [{"value": "assay-specific", "unit": "M, nM, µM", "context": "requires response definition and assay context"}]
- **Related expressions:** EXPR_HILL_ACTIVATION
- **Related models:** MODEL_DOSE_RESPONSE
- **Sources:** europepmc
- **Confidence:** high

### PARAM_HILL — Hill coefficient

- **Symbols:** n, n_H, nH
- **Aliases:** Hill coefficient, cooperativity coefficient
- **Category:** allostery
- **Definition:** Empirical exponent in a Hill function that describes cooperativity or apparent ultrasensitivity.
- **Unit:** dimensionless
- **Typical values:** [{"value": "typically 1-4 in many biological systems", "unit": "dimensionless", "context": "n=1 is noncooperative; larger values indicate steeper response"}]
- **Related expressions:** EXPR_HILL_ACTIVATION, EXPR_HILL_INHIBITION
- **Related models:** MODEL_HILL, MODEL_GENE_REGULATION, MODEL_MAPK_CASCADE
- **Sources:** biomodels, repressilator, mapk_cascade
- **Confidence:** high

### PARAM_BETA — Transmission or production parameter

- **Symbols:** beta, β
- **Aliases:** infection rate, transmission rate, production rate
- **Category:** population_dynamics
- **Definition:** Context-dependent rate parameter for transmission in epidemic models or production in gene-expression models.
- **Unit:** per_time_or_context
- **Typical values:** [{"value": "model-specific", "unit": "per_time or state-dependent", "context": "must be interpreted from the enclosing model"}]
- **Related expressions:** EXPR_SIR_TRANSMISSION, EXPR_PROTEIN_SYNTHESIS
- **Related models:** MODEL_SIR, MODEL_SEIR, MODEL_REPRESSILATOR
- **Sources:** classic_sir, repressilator
- **Confidence:** high
- **Notes:** Symbol beta is used in multiple model families; semantic review must retain context-specific disambiguation.

### PARAM_GAMMA — Recovery or removal rate

- **Symbols:** gamma, γ
- **Aliases:** recovery rate, removal rate
- **Category:** epidemiology
- **Definition:** Rate at which infected individuals recover or leave the infectious compartment in SIR/SEIR models.
- **Unit:** per_time
- **Typical values:** [{"value": "disease-specific", "unit": "day^-1", "context": "inverse gives mean infectious period"}]
- **Related expressions:** EXPR_SIR_RECOVERY
- **Related models:** MODEL_SIR, MODEL_SEIR
- **Sources:** classic_sir
- **Confidence:** high

### PARAM_SIGMA — Latent or incubation rate

- **Symbols:** sigma, σ
- **Aliases:** incubation rate, latent transition rate
- **Category:** epidemiology
- **Definition:** Rate of transition from exposed to infectious compartment in SEIR-type models.
- **Unit:** per_time
- **Typical values:** [{"value": "disease-specific", "unit": "day^-1", "context": "inverse gives mean latent period"}]
- **Related expressions:** EXPR_SEIR_LATENT
- **Related models:** MODEL_SEIR
- **Sources:** classic_sir
- **Confidence:** high

### PARAM_R0 — Basic reproduction number

- **Symbols:** R0, R_0
- **Aliases:** basic reproduction number, basic reproductive ratio
- **Category:** epidemiology
- **Definition:** Expected number of secondary infections generated by one infected individual in a fully susceptible population.
- **Unit:** dimensionless
- **Typical values:** [{"value": "disease- and contact-pattern-specific", "unit": "dimensionless", "context": "for simple SIR, R0=beta/gamma"}]
- **Related expressions:** EXPR_R0_SIR
- **Related models:** MODEL_SIR, MODEL_SEIR
- **Sources:** classic_sir
- **Confidence:** high

### PARAM_MU_GROWTH — Specific growth rate

- **Symbols:** mu, μ, r
- **Aliases:** growth rate, specific growth rate
- **Category:** population_dynamics
- **Definition:** Per-capita rate of increase in population size, tumor volume, or biomass.
- **Unit:** per_time
- **Typical values:** [{"value": "system-specific", "unit": "hour^-1, day^-1", "context": "used in exponential, logistic, and Gompertz models"}]
- **Related expressions:** EXPR_LOGISTIC_GROWTH, EXPR_GOMPERTZ_GROWTH
- **Related models:** MODEL_LOGISTIC_GROWTH, MODEL_GOMPERTZ_GROWTH
- **Sources:** europepmc
- **Confidence:** high

### PARAM_CARRYING_CAPACITY — Carrying capacity

- **Symbols:** K, Kcap
- **Aliases:** carrying capacity, saturation level
- **Category:** population_dynamics
- **Definition:** Maximum population size supported by the environment in logistic and related growth models.
- **Unit:** amount_or_concentration
- **Typical values:** [{"value": "system-specific", "unit": "cells, biomass, concentration", "context": "must be distinguished from equilibrium constants symbolized by K"}]
- **Related expressions:** EXPR_LOGISTIC_GROWTH
- **Related models:** MODEL_LOGISTIC_GROWTH
- **Sources:** europepmc
- **Confidence:** high
- **Notes:** Symbol K is highly context-dependent; keep separate from Km, Kd, and inhibition constants.

### PARAM_CLEARANCE — Clearance rate

- **Symbols:** k_clear, k_clearance, CL
- **Aliases:** clearance rate, elimination rate
- **Category:** pharmacokinetics
- **Definition:** Rate constant or volume-normalized rate describing removal of a substance from a compartment.
- **Unit:** per_time_or_volume_per_time
- **Typical values:** [{"value": "compound-specific", "unit": "time^-1 or volume/time", "context": "used in one-compartment and biomarker kinetic models"}]
- **Related expressions:** EXPR_FIRST_ORDER_CLEARANCE
- **Related models:** MODEL_ONE_COMPARTMENT, MODEL_BIOMARKER_KINETICS
- **Sources:** europepmc, hepatic_glucose
- **Confidence:** high

### PARAM_RELEASE_RATE — Release rate

- **Symbols:** k_release, k_rel
- **Aliases:** release rate, input rate
- **Category:** pharmacokinetics
- **Definition:** Rate parameter describing entry or release of a substance into a measured compartment.
- **Unit:** amount_per_time_or_per_time
- **Typical values:** [{"value": "context-specific", "unit": "mass/time or time^-1", "context": "paired with clearance in input-output kinetic models"}]
- **Related expressions:** EXPR_INPUT_OUTPUT_KINETICS
- **Related models:** MODEL_ONE_COMPARTMENT, MODEL_BIOMARKER_KINETICS
- **Sources:** europepmc
- **Confidence:** high

### PARAM_HALF_LIFE — Half-life

- **Symbols:** t_half, t1/2, half_life
- **Aliases:** half-life, elimination half-life
- **Category:** pharmacokinetics
- **Definition:** Time required for a quantity to fall to half of its reference value under a specified kinetic process.
- **Unit:** time
- **Typical values:** [{"value": "compound-specific", "unit": "min, h, day", "context": "for first-order decay, t_half=ln(2)/k"}]
- **Related expressions:** EXPR_EXPONENTIAL_DECAY, EXPR_FIRST_ORDER_CLEARANCE
- **Related models:** MODEL_ONE_COMPARTMENT, MODEL_BIOMARKER_KINETICS
- **Sources:** europepmc
- **Confidence:** high

### PARAM_DIFFUSION — Diffusion coefficient

- **Symbols:** D, D_diff
- **Aliases:** diffusion coefficient, diffusivity
- **Category:** spatial_transport
- **Definition:** Proportionality constant relating diffusive flux to a concentration gradient under Fickian transport.
- **Unit:** area_per_time
- **Typical values:** [{"value": "molecule- and medium-specific", "unit": "µm^2/s, cm^2/s", "context": "used in reaction-diffusion models"}]
- **Related expressions:** EXPR_FICK_DIFFUSION
- **Related models:** MODEL_REACTION_DIFFUSION
- **Sources:** europepmc
- **Confidence:** high

### PARAM_MEMBRANE_POTENTIAL — Membrane potential

- **Symbols:** Vm, V_m
- **Aliases:** membrane potential, transmembrane voltage
- **Category:** electrophysiology
- **Definition:** Electrical potential difference across a cell membrane.
- **Unit:** voltage
- **Typical values:** [{"value": "cell- and condition-specific", "unit": "mV", "context": "central state variable in Hodgkin-Huxley models"}]
- **Related expressions:** EXPR_HH_MEMBRANE_CURRENT
- **Related models:** MODEL_HODGKIN_HUXLEY
- **Sources:** classic_hh, biomodels
- **Confidence:** high

### PARAM_CONDUCTANCE — Ion channel conductance

- **Symbols:** g, g_Na, g_K, g_L
- **Aliases:** conductance, maximal conductance
- **Category:** electrophysiology
- **Definition:** Maximum ionic conductance associated with a channel population in electrophysiological models.
- **Unit:** conductance
- **Typical values:** [{"value": "cell-type-specific", "unit": "mS/cm^2", "context": "multiplied by gating variables in Hodgkin-Huxley currents"}]
- **Related expressions:** EXPR_HH_IONIC_CURRENT
- **Related models:** MODEL_HODGKIN_HUXLEY
- **Sources:** classic_hh, biomodels
- **Confidence:** high

### PARAM_REVERSAL_POTENTIAL — Reversal potential

- **Symbols:** E, E_Na, E_K, E_L
- **Aliases:** reversal potential, Nernst potential
- **Category:** electrophysiology
- **Definition:** Membrane potential at which net ionic current for a given ion reverses direction.
- **Unit:** voltage
- **Typical values:** [{"value": "ion- and cell-specific", "unit": "mV", "context": "used in driving-force terms (Vm-Eion)"}]
- **Related expressions:** EXPR_HH_IONIC_CURRENT, EXPR_NERNST
- **Related models:** MODEL_HODGKIN_HUXLEY
- **Sources:** classic_hh
- **Confidence:** high

### PARAM_CAPACITANCE — Membrane capacitance

- **Symbols:** Cm, C_m
- **Aliases:** membrane capacitance, specific capacitance
- **Category:** electrophysiology
- **Definition:** Capacitance per unit membrane area relating charge accumulation to membrane potential.
- **Unit:** capacitance_per_area
- **Typical values:** [{"value": "commonly about 1 µF/cm^2 in many preparations", "unit": "µF/cm^2", "context": "membrane equation Cm dV/dt = -I_total"}]
- **Related expressions:** EXPR_HH_MEMBRANE_CURRENT
- **Related models:** MODEL_HODGKIN_HUXLEY
- **Sources:** classic_hh
- **Confidence:** high

### PARAM_ALPHA_TRANSCRIPTION — Constitutive transcription rate

- **Symbols:** alpha, alpha0, a_tr, a0_tr
- **Aliases:** transcription rate, basal transcription rate
- **Category:** gene_expression
- **Definition:** Rate parameter controlling production of mRNA in gene-expression models.
- **Unit:** concentration_per_time_or_per_time
- **Typical values:** [{"value": "gene- and model-specific", "unit": "nM/min or time^-1", "context": "observed in the repressilator SBML model as alpha, alpha0, a_tr, and a0_tr"}]
- **Related expressions:** EXPR_MRNA_SYNTHESIS, EXPR_REPRESSILATOR
- **Related models:** MODEL_REPRESSILATOR, MODEL_GENE_REGULATION
- **Sources:** repressilator, biomodels
- **Confidence:** high

### PARAM_KD_MRNA — mRNA degradation rate

- **Symbols:** kd_mRNA, k_deg_mRNA
- **Aliases:** mRNA degradation rate, mRNA decay rate
- **Category:** gene_expression
- **Definition:** First-order removal rate for mRNA in gene-expression models.
- **Unit:** per_time
- **Typical values:** [{"value": "gene-specific", "unit": "time^-1", "context": "observed in BIOMD0000000012 repressilator model"}]
- **Related expressions:** EXPR_MRNA_SYNTHESIS
- **Related models:** MODEL_REPRESSILATOR, MODEL_GENE_REGULATION
- **Sources:** repressilator, biomodels
- **Confidence:** high

### PARAM_KD_PROT — Protein degradation rate

- **Symbols:** kd_prot, k_deg_prot
- **Aliases:** protein degradation rate, protein decay rate
- **Category:** gene_expression
- **Definition:** First-order removal rate for protein in gene-expression models.
- **Unit:** per_time
- **Typical values:** [{"value": "protein-specific", "unit": "time^-1", "context": "observed in BIOMD0000000012 repressilator model"}]
- **Related expressions:** EXPR_PROTEIN_SYNTHESIS
- **Related models:** MODEL_REPRESSILATOR, MODEL_GENE_REGULATION
- **Sources:** repressilator, biomodels
- **Confidence:** high

### PARAM_KT_L — Translation rate

- **Symbols:** k_tl, k_tl, translation_rate
- **Aliases:** translation rate, protein synthesis rate constant
- **Category:** gene_expression
- **Definition:** Rate parameter controlling protein production from mRNA.
- **Unit:** concentration_per_time_per_mRNA_or_per_time
- **Typical values:** [{"value": "gene-specific", "unit": "model dependent", "context": "observed in BIOMD0000000012 repressilator model"}]
- **Related expressions:** EXPR_PROTEIN_SYNTHESIS, EXPR_REPRESSILATOR
- **Related models:** MODEL_REPRESSILATOR, MODEL_GENE_REGULATION
- **Sources:** repressilator, biomodels
- **Confidence:** high

### PARAM_TAU_MRNA — mRNA time constant

- **Symbols:** tau_mRNA
- **Aliases:** mRNA lifetime, mRNA time constant
- **Category:** gene_expression
- **Definition:** Characteristic time scale for mRNA turnover, often reciprocal of mRNA degradation rate.
- **Unit:** time
- **Typical values:** [{"value": "gene-specific", "unit": "min", "context": "observed in BIOMD0000000012 repressilator model"}]
- **Related expressions:** EXPR_MRNA_SYNTHESIS
- **Related models:** MODEL_REPRESSILATOR
- **Sources:** repressilator, biomodels
- **Confidence:** high

### PARAM_TAU_PROT — Protein time constant

- **Symbols:** tau_prot
- **Aliases:** protein lifetime, protein time constant
- **Category:** gene_expression
- **Definition:** Characteristic time scale for protein turnover, often reciprocal of protein degradation rate.
- **Unit:** time
- **Typical values:** [{"value": "protein-specific", "unit": "min", "context": "observed in BIOMD0000000012 repressilator model"}]
- **Related expressions:** EXPR_PROTEIN_SYNTHESIS
- **Related models:** MODEL_REPRESSILATOR
- **Sources:** repressilator, biomodels
- **Confidence:** high

### PARAM_ENZYME_CONCENTRATION — Enzyme concentration

- **Symbols:** E, [E]
- **Aliases:** enzyme concentration, catalyst concentration
- **Category:** enzyme_kinetics
- **Definition:** Concentration of catalytically active enzyme available to convert substrate to product.
- **Unit:** concentration
- **Typical values:** [{"value": "assay-specific", "unit": "nM, µM, mg/mL", "context": "used to convert Vmax to kcat"}]
- **Related expressions:** EXPR_MICHAELIS_MENTEN
- **Related models:** MODEL_ENZYME_KINETICS
- **Sources:** biomodels, sabio_rk, brenda
- **Confidence:** high

### PARAM_SUBSTRATE_CONCENTRATION — Substrate concentration

- **Symbols:** S, [S]
- **Aliases:** substrate concentration
- **Category:** enzyme_kinetics
- **Definition:** Concentration of substrate available for an enzymatic or transport reaction.
- **Unit:** concentration
- **Typical values:** [{"value": "time- and condition-dependent", "unit": "M, mM, µM", "context": "input to saturation and inhibition expressions"}]
- **Related expressions:** EXPR_MICHAELIS_MENTEN, EXPR_HILL_ACTIVATION
- **Related models:** MODEL_ENZYME_KINETICS, MODEL_ENZYME_INHIBITION
- **Sources:** biomodels, sabio_rk
- **Confidence:** high

### PARAM_PRODUCT_CONCENTRATION — Product concentration

- **Symbols:** P, [P]
- **Aliases:** product concentration
- **Category:** enzyme_kinetics
- **Definition:** Concentration of product generated by a reaction or transported across a compartment.
- **Unit:** concentration
- **Typical values:** [{"value": "time-dependent", "unit": "M, mM, µM", "context": "state variable in kinetic networks"}]
- **Related expressions:** EXPR_MASS_ACTION
- **Related models:** MODEL_ENZYME_KINETICS, MODEL_METABOLIC_NETWORK
- **Sources:** biomodels, sabio_rk
- **Confidence:** high

### PARAM_REACTION_FLUX — Reaction flux

- **Symbols:** v, J, flux
- **Aliases:** reaction flux, reaction rate, metabolic flux
- **Category:** metabolic_modeling
- **Definition:** Rate of conversion through a reaction or pathway under a specified kinetic law.
- **Unit:** amount_per_time_per_volume
- **Typical values:** [{"value": "network- and condition-specific", "unit": "mM/s, mmol/gDW/h", "context": "may be simulated, measured, or constrained"}]
- **Related expressions:** EXPR_MASS_ACTION, EXPR_MICHAELIS_MENTEN
- **Related models:** MODEL_METABOLIC_NETWORK, MODEL_GENOME_SCALE_KINETIC
- **Sources:** biomodels, biomodels_search
- **Confidence:** high

### PARAM_ELASTICITY — Kinetic elasticity

- **Symbols:** epsilon, ε
- **Aliases:** elasticity coefficient, flux control coefficient
- **Category:** metabolic_control
- **Definition:** Local sensitivity of reaction rate to a metabolite concentration in metabolic control analysis.
- **Unit:** dimensionless
- **Typical values:** [{"value": "system-specific", "unit": "dimensionless", "context": "observed in linlog metabolic models"}]
- **Related expressions:** EXPR_POWER_LAW
- **Related models:** MODEL_METABOLIC_CONTROL, MODEL_GENOME_SCALE_KINETIC
- **Sources:** biomodels
- **Confidence:** high

### PARAM_THERMODYNAMIC_DRIVING_FORCE — Thermodynamic driving force

- **Symbols:** DeltaG, ΔG
- **Aliases:** free energy change, thermodynamic driving force
- **Category:** thermodynamics
- **Definition:** Change in Gibbs free energy associated with a reaction or transition.
- **Unit:** energy
- **Typical values:** [{"value": "reaction-specific", "unit": "kJ/mol or model energy units", "context": "sign indicates favorable or unfavorable direction"}]
- **Related expressions:** EXPR_THERMODYNAMIC_DRIVING_FORCE
- **Related models:** MODEL_THERMODYNAMIC_KINETIC
- **Sources:** biomodels, europepmc
- **Confidence:** high

### PARAM_BINDING_PROBABILITY — Binding or state-transition probability

- **Symbols:** p, P, pi, π
- **Aliases:** binding probability, state probability, transition probability
- **Category:** stochastic_modeling
- **Definition:** Probability associated with binding, occupancy, or transition between discrete states.
- **Unit:** dimensionless
- **Typical values:** [{"value": "between 0 and 1", "unit": "dimensionless", "context": "must be distinguished from p-values and generic probability notation"}]
- **Related expressions:** EXPR_MARKOV_TRANSITION
- **Related models:** MODEL_MARKOV_STATE, MODEL_STOCHASTIC_BINDING
- **Sources:** biomodels
- **Confidence:** high

### PARAM_INITIAL_CONCENTRATION — Initial concentration

- **Symbols:** C0, C_0, X0, X_0
- **Aliases:** initial concentration, initial condition
- **Category:** initial_conditions
- **Definition:** Concentration assigned at the start of a simulation or observation window.
- **Unit:** concentration
- **Typical values:** [{"value": "model- and subject-specific", "unit": "M, mM, µM, ng/mL", "context": "reported in initial-condition sections or parameter tables"}]
- **Related expressions:** EXPR_EXPONENTIAL_DECAY, EXPR_INPUT_OUTPUT_KINETICS
- **Related models:** MODEL_ONE_COMPARTMENT, MODEL_BIOMARKER_KINETICS, MODEL_MASS_ACTION
- **Sources:** biomodels, europepmc
- **Confidence:** high

### PARAM_TEMPERATURE — Temperature

- **Symbols:** T, temperature
- **Aliases:** temperature
- **Category:** environmental_condition
- **Definition:** Thermodynamic temperature affecting kinetic constants, diffusion, and conformational transitions.
- **Unit:** temperature
- **Typical values:** [{"value": "assay- or environment-specific", "unit": "K or °C", "context": "often introduced through Arrhenius or Q10 relationships"}]
- **Related expressions:** EXPR_ARRHENIUS
- **Related models:** MODEL_TEMPERATURE_DEPENDENT_KINETICS, MODEL_MARKOV_STATE
- **Sources:** europepmc, biomodels
- **Confidence:** high
