# Biological Mathematical Modelling Model Lexicon

- Generated: 2026-09-29
- Entries: 25
- Machine-readable source: `models.json`

## Models

| ID | Name | Class | Domain | Confidence |
| --- | --- | --- | --- | --- |
| MODEL_MASS_ACTION | mass-action kinetic model | deterministic ODE | chemical_kinetics | high |
| MODEL_MICHAELIS_MENTEN | Michaelis-Menten enzyme model | deterministic ODE | enzyme_kinetics | high |
| MODEL_ENZYME_KINETICS | enzyme kinetics model | deterministic ODE | enzyme_kinetics | high |
| MODEL_ENZYME_INHIBITION | enzyme inhibition model | deterministic ODE | enzyme_inhibition | high |
| MODEL_HILL | Hill response model | empirical response | allostery | high |
| MODEL_SIR | SIR compartmental epidemic model | compartmental ODE | epidemiology | high |
| MODEL_SEIR | SEIR compartmental epidemic model | compartmental ODE | epidemiology | high |
| MODEL_LOGISTIC_GROWTH | logistic growth model | deterministic ODE | population_dynamics | high |
| MODEL_GOMPERTZ_GROWTH | Gompertz growth model | deterministic ODE | population_dynamics | high |
| MODEL_HODGKIN_HUXLEY | Hodgkin-Huxley neuron model | electrophysiological ODE | electrophysiology | high |
| MODEL_REPRESSILATOR | repressilator synthetic oscillator | deterministic or stochastic ODE | gene_regulation | high |
| MODEL_MAPK_CASCADE | MAPK cascade model | deterministic ODE | signal_transduction | high |
| MODEL_ERBB_SIGNALING | ErbB signaling kinetic model | mass-action ODE | signal_transduction | high |
| MODEL_METABOLIC_NETWORK | metabolic reaction network | network or ODE | metabolic_modeling | high |
| MODEL_GENOME_SCALE_KINETIC | genome-scale kinetic metabolic model | large-scale ODE | metabolic_modeling | high |
| MODEL_METABOLIC_CONTROL | metabolic control analysis model | sensitivity analysis | metabolic_modeling | high |
| MODEL_MARKOV_STATE | Markov state kinetic model | stochastic or master-equation | state_model | high |
| MODEL_REACTION_DIFFUSION | reaction-diffusion model | partial differential equation | spatial_transport | high |
| MODEL_ONE_COMPARTMENT | one-compartment pharmacokinetic model | pharmacokinetic ODE | pharmacokinetics | high |
| MODEL_BIOMARKER_KINETICS | biomarker release-clearance model | pharmacokinetic ODE | pharmacokinetics | high |
| MODEL_GENE_REGULATION | gene regulatory network model | ODE or logical | gene_regulation | high |
| MODEL_RECEPTOR_LIGAND | receptor-ligand binding model | binding equilibrium or ODE | binding_kinetics | high |
| MODEL_TEMPERATURE_DEPENDENT_KINETICS | temperature-dependent kinetic model | kinetic ODE | thermodynamics | high |
| MODEL_SIGNAL_TRANSDUCTION | signal transduction network model | ODE or logical network | signal_transduction | high |
| MODEL_DOSE_RESPONSE | dose-response model | empirical response | pharmacology | high |

## Definitions

### MODEL_MASS_ACTION — mass-action kinetic model

- **Aliases:** mass action model, law of mass action model
- **Model class:** deterministic ODE
- **Domain:** chemical_kinetics
- **Description:** Reaction network whose elementary reaction rates are proportional to the product of reactant concentrations or abundances.
- **State variables:** species_concentration
- **Parameters:** PARAM_KON, PARAM_KOFF
- **Expressions:** EXPR_MASS_ACTION, EXPR_REVERSIBLE_BINDING
- **Relations:** REL_BINDING, REL_UNBINDING, REL_CATALYSIS
- **BioModels IDs:** None
- **Sources:** biomodels, sbml, erbb_model
- **Confidence:** high

### MODEL_MICHAELIS_MENTEN — Michaelis-Menten enzyme model

- **Aliases:** Michaelis-Menten model, saturation enzyme model
- **Model class:** deterministic ODE
- **Domain:** enzyme_kinetics
- **Description:** Single-substrate enzyme reaction model using saturating velocity as a function of substrate concentration.
- **State variables:** PARAM_SUBSTRATE_CONCENTRATION, PARAM_PRODUCT_CONCENTRATION
- **Parameters:** PARAM_VMAX, PARAM_KM, PARAM_KCAT
- **Expressions:** EXPR_MICHAELIS_MENTEN, EXPR_CATALYTIC_EFFICIENCY
- **Relations:** REL_CATALYSIS
- **BioModels IDs:** None
- **Sources:** classic_mm, brenda, sabio_rk
- **Confidence:** high

### MODEL_ENZYME_KINETICS — enzyme kinetics model

- **Aliases:** enzymatic rate model, kinetic enzyme model
- **Model class:** deterministic ODE
- **Domain:** enzyme_kinetics
- **Description:** General kinetic description of enzyme-catalysed reactions, including saturation, inhibition, and catalytic efficiency.
- **State variables:** PARAM_SUBSTRATE_CONCENTRATION, PARAM_PRODUCT_CONCENTRATION, PARAM_ENZYME_CONCENTRATION
- **Parameters:** PARAM_KM, PARAM_VMAX, PARAM_KCAT, PARAM_KI
- **Expressions:** EXPR_MICHAELIS_MENTEN, EXPR_COMPETITIVE_INHIBITION, EXPR_CATALYTIC_EFFICIENCY
- **Relations:** REL_CATALYSIS, REL_COMPETITIVE_INHIBITION
- **BioModels IDs:** None
- **Sources:** brenda, sabio_rk
- **Confidence:** high

### MODEL_ENZYME_INHIBITION — enzyme inhibition model

- **Aliases:** inhibition model, competitive inhibition model
- **Model class:** deterministic ODE
- **Domain:** enzyme_inhibition
- **Description:** Enzyme kinetic model in which inhibitors modify apparent substrate affinity or maximal velocity.
- **State variables:** PARAM_SUBSTRATE_CONCENTRATION, PARAM_PRODUCT_CONCENTRATION
- **Parameters:** PARAM_KM, PARAM_VMAX, PARAM_KI, PARAM_IC50
- **Expressions:** EXPR_COMPETITIVE_INHIBITION, EXPR_HILL_INHIBITION
- **Relations:** REL_INHIBITION, REL_COMPETITIVE_INHIBITION
- **BioModels IDs:** None
- **Sources:** brenda, sabio_rk, europepmc
- **Confidence:** high

### MODEL_HILL — Hill response model

- **Aliases:** Hill model, sigmoidal response model, cooperativity model
- **Model class:** empirical response
- **Domain:** allostery
- **Description:** Empirical sigmoidal dose-response or regulation model characterized by a half-saturation constant and Hill coefficient.
- **State variables:** regulator_concentration
- **Parameters:** PARAM_HILL, PARAM_EC50, PARAM_IC50
- **Expressions:** EXPR_HILL_ACTIVATION, EXPR_HILL_INHIBITION
- **Relations:** REL_COOPERATIVITY, REL_ALLOSTERIC_ACTIVATION, REL_ALLOSTERIC_INHIBITION
- **BioModels IDs:** None
- **Sources:** europepmc, biomodels
- **Confidence:** high

### MODEL_SIR — SIR compartmental epidemic model

- **Aliases:** SIR model, susceptible-infected-recovered model
- **Model class:** compartmental ODE
- **Domain:** epidemiology
- **Description:** Population divided into susceptible, infected, and recovered compartments with transmission and recovery flows.
- **State variables:** susceptible_population, infected_population, recovered_population
- **Parameters:** PARAM_BETA, PARAM_GAMMA, PARAM_R0
- **Expressions:** EXPR_SIR_TRANSMISSION, EXPR_SIR_RECOVERY, EXPR_R0_SIR
- **Relations:** REL_INFECTION_TRANSMISSION, REL_RECOVERY
- **BioModels IDs:** None
- **Sources:** classic_sir
- **Confidence:** high

### MODEL_SEIR — SEIR compartmental epidemic model

- **Aliases:** SEIR model, exposed-infected-recovered model
- **Model class:** compartmental ODE
- **Domain:** epidemiology
- **Description:** Extension of SIR with an exposed but not yet infectious compartment.
- **State variables:** susceptible_population, exposed_population, infected_population, recovered_population
- **Parameters:** PARAM_BETA, PARAM_GAMMA, PARAM_SIGMA, PARAM_R0
- **Expressions:** EXPR_SIR_TRANSMISSION, EXPR_SEIR_LATENT, EXPR_SIR_RECOVERY
- **Relations:** REL_INFECTION_TRANSMISSION, REL_RECOVERY
- **BioModels IDs:** None
- **Sources:** classic_sir
- **Confidence:** high

### MODEL_LOGISTIC_GROWTH — logistic growth model

- **Aliases:** Verhulst model, logistic population model
- **Model class:** deterministic ODE
- **Domain:** population_dynamics
- **Description:** Population growth with a rate that declines linearly as population size approaches carrying capacity.
- **State variables:** population_size
- **Parameters:** PARAM_MU_GROWTH, PARAM_CARRYING_CAPACITY
- **Expressions:** EXPR_LOGISTIC_GROWTH
- **Relations:** REL_POSITIVE_FEEDBACK
- **BioModels IDs:** None
- **Sources:** europepmc
- **Confidence:** high

### MODEL_GOMPERTZ_GROWTH — Gompertz growth model

- **Aliases:** Gompertz model, Gompertz tumour growth model
- **Model class:** deterministic ODE
- **Domain:** population_dynamics
- **Description:** Asymmetric sigmoidal growth model frequently used for tumour and organism growth.
- **State variables:** population_size
- **Parameters:** PARAM_MU_GROWTH, PARAM_CARRYING_CAPACITY
- **Expressions:** EXPR_GOMPERTZ_GROWTH
- **Relations:** REL_POSITIVE_FEEDBACK
- **BioModels IDs:** None
- **Sources:** europepmc
- **Confidence:** high

### MODEL_HODGKIN_HUXLEY — Hodgkin-Huxley neuron model

- **Aliases:** Hodgkin-Huxley model, HH model
- **Model class:** electrophysiological ODE
- **Domain:** electrophysiology
- **Description:** Conductance-based model of action potential generation using voltage-gated sodium, potassium, and leak currents.
- **State variables:** PARAM_MEMBRANE_POTENTIAL, gating_variable
- **Parameters:** PARAM_CAPACITANCE, PARAM_CONDUCTANCE, PARAM_REVERSAL_POTENTIAL
- **Expressions:** EXPR_HH_MEMBRANE_CURRENT, EXPR_HH_IONIC_CURRENT, EXPR_HH_GATING, EXPR_NERNST
- **Relations:** REL_GATING
- **BioModels IDs:** None
- **Sources:** classic_hh, biomodels
- **Confidence:** high

### MODEL_REPRESSILATOR — repressilator synthetic oscillator

- **Aliases:** repressilator, cyclic repression oscillator
- **Model class:** deterministic or stochastic ODE
- **Domain:** gene_regulation
- **Description:** Synthetic ring of three mutually repressing genes producing oscillatory protein expression.
- **State variables:** mRNA_concentration, protein_concentration
- **Parameters:** PARAM_ALPHA_TRANSCRIPTION, PARAM_HILL, PARAM_KD_MRNA, PARAM_KD_PROT, PARAM_KT_L
- **Expressions:** EXPR_REPRESSILATOR, EXPR_MRNA_SYNTHESIS, EXPR_PROTEIN_SYNTHESIS
- **Relations:** REL_TRANSCRIPTION_REPRESSION, REL_FEEDBACK_LOOP
- **BioModels IDs:** BIOMD0000000012
- **Sources:** repressilator, biomodels
- **Confidence:** high

### MODEL_MAPK_CASCADE — MAPK cascade model

- **Aliases:** MAPK cascade, mitogen-activated protein kinase cascade model
- **Model class:** deterministic ODE
- **Domain:** signal_transduction
- **Description:** Multi-tier kinase cascade with phosphorylation, dephosphorylation, feedback, and possible oscillatory dynamics.
- **State variables:** kinase_activity, phosphorylated_state
- **Parameters:** PARAM_HILL, PARAM_KM, PARAM_VMAX, PARAM_KCAT
- **Expressions:** EXPR_MICHAELIS_MENTEN, EXPR_HILL_ACTIVATION, EXPR_HILL_INHIBITION
- **Relations:** REL_PHOSPHORYLATION, REL_DEPHOSPHORYLATION, REL_NEGATIVE_FEEDBACK, REL_SIGNAL_TRANSDUCTION
- **BioModels IDs:** BIOMD0000000010
- **Sources:** mapk_cascade, biomodels
- **Confidence:** high

### MODEL_ERBB_SIGNALING — ErbB signaling kinetic model

- **Aliases:** ErbB signaling model, EGFR signaling kinetic model
- **Model class:** mass-action ODE
- **Domain:** signal_transduction
- **Description:** Reaction-network model of ligand-receptor binding, receptor dimerization, phosphorylation, and downstream ERK/Akt activation.
- **State variables:** receptor_concentration, ligand_concentration, dimer_fraction, phosphorylated_ERK, phosphorylated_Akt
- **Parameters:** PARAM_KON, PARAM_KOFF, PARAM_KD, PARAM_IC50
- **Expressions:** EXPR_MASS_ACTION, EXPR_REVERSIBLE_BINDING
- **Relations:** REL_RECEPTOR_DIMERIZATION, REL_PHOSPHORYLATION, REL_SIGNAL_TRANSDUCTION, REL_INHIBITION
- **BioModels IDs:** None
- **Sources:** erbb_model, reactome
- **Confidence:** high

### MODEL_METABOLIC_NETWORK — metabolic reaction network

- **Aliases:** metabolic network model, reaction network
- **Model class:** network or ODE
- **Domain:** metabolic_modeling
- **Description:** Network of metabolic reactions with stoichiometry, fluxes, and optionally kinetic rate laws.
- **State variables:** metabolite_concentration, reaction_flux
- **Parameters:** PARAM_KM, PARAM_VMAX, PARAM_KCAT, PARAM_REACTION_FLUX
- **Expressions:** EXPR_MICHAELIS_MENTEN, EXPR_MASS_ACTION
- **Relations:** REL_CATALYSIS, REL_FLUX_REGULATION
- **BioModels IDs:** None
- **Sources:** biomodels, kegg
- **Confidence:** high

### MODEL_GENOME_SCALE_KINETIC — genome-scale kinetic metabolic model

- **Aliases:** genome-scale kinetic model, genome scale metabolic kinetic model
- **Model class:** large-scale ODE
- **Domain:** metabolic_modeling
- **Description:** Genome-scale metabolic network in which reaction fluxes are represented by kinetic or approximate rate laws.
- **State variables:** metabolite_concentration, enzyme_concentration, reaction_flux
- **Parameters:** PARAM_KM, PARAM_KCAT, PARAM_ELASTICITY, PARAM_REACTION_FLUX
- **Expressions:** EXPR_MICHAELIS_MENTEN, EXPR_POWER_LAW
- **Relations:** REL_CATALYSIS, REL_FLUX_REGULATION
- **BioModels IDs:** BIOMD0000000471, BIOMD0000000496, BIOMD0000000497
- **Sources:** biomodels, biomodels_search
- **Confidence:** high

### MODEL_METABOLIC_CONTROL — metabolic control analysis model

- **Aliases:** MCA model, metabolic control model
- **Model class:** sensitivity analysis
- **Domain:** metabolic_modeling
- **Description:** Framework relating local rate sensitivities and control coefficients to systemic metabolic flux control.
- **State variables:** metabolite_concentration, reaction_flux
- **Parameters:** PARAM_ELASTICITY, PARAM_REACTION_FLUX
- **Expressions:** EXPR_POWER_LAW
- **Relations:** REL_FLUX_REGULATION
- **BioModels IDs:** BIOMD0000000471
- **Sources:** biomodels
- **Confidence:** high

### MODEL_MARKOV_STATE — Markov state kinetic model

- **Aliases:** Markov state model, discrete-state kinetic model
- **Model class:** stochastic or master-equation
- **Domain:** state_model
- **Description:** System represented by discrete conformational or functional states with transition rates or probabilities.
- **State variables:** state_probability
- **Parameters:** PARAM_BINDING_PROBABILITY, PARAM_KOFF
- **Expressions:** EXPR_MARKOV_TRANSITION, EXPR_EXPONENTIAL_DECAY
- **Relations:** REL_STATE_TRANSITION, REL_UNBINDING
- **BioModels IDs:** None
- **Sources:** biomodels, europepmc
- **Confidence:** high

### MODEL_REACTION_DIFFUSION — reaction-diffusion model

- **Aliases:** reaction diffusion model, spatial kinetic model
- **Model class:** partial differential equation
- **Domain:** spatial_transport
- **Description:** Coupled model in which molecular species diffuse in space while participating in local reactions.
- **State variables:** concentration_field
- **Parameters:** PARAM_DIFFUSION
- **Expressions:** EXPR_FICK_DIFFUSION
- **Relations:** REL_DIFFUSION, REL_TRANSPORT
- **BioModels IDs:** None
- **Sources:** europepmc
- **Confidence:** high

### MODEL_ONE_COMPARTMENT — one-compartment pharmacokinetic model

- **Aliases:** one compartment model, single compartment model
- **Model class:** pharmacokinetic ODE
- **Domain:** pharmacokinetics
- **Description:** Well-mixed compartment with input, distribution volume, and first-order elimination.
- **State variables:** concentration
- **Parameters:** PARAM_CLEARANCE, PARAM_RELEASE_RATE, PARAM_HALF_LIFE, PARAM_INITIAL_CONCENTRATION
- **Expressions:** EXPR_FIRST_ORDER_CLEARANCE, EXPR_INPUT_OUTPUT_KINETICS, EXPR_EXPONENTIAL_DECAY
- **Relations:** REL_CLEARANCE, REL_TRANSPORT
- **BioModels IDs:** BIOMD0000000001
- **Sources:** europepmc, biomodels
- **Confidence:** high

### MODEL_BIOMARKER_KINETICS — biomarker release-clearance model

- **Aliases:** biomarker kinetic model, release-clearance model
- **Model class:** pharmacokinetic ODE
- **Domain:** pharmacokinetics
- **Description:** Model of biomarker entry into blood after injury and subsequent clearance, used for GFAP, UCH-L1, NF-L, and related markers.
- **State variables:** biomarker_concentration
- **Parameters:** PARAM_RELEASE_RATE, PARAM_CLEARANCE, PARAM_HALF_LIFE, PARAM_INITIAL_CONCENTRATION
- **Expressions:** EXPR_INPUT_OUTPUT_KINETICS, EXPR_FIRST_ORDER_CLEARANCE, EXPR_EXPONENTIAL_DECAY
- **Relations:** REL_CLEARANCE
- **BioModels IDs:** None
- **Sources:** europepmc
- **Confidence:** high

### MODEL_GENE_REGULATION — gene regulatory network model

- **Aliases:** GRN model, gene regulation model
- **Model class:** ODE or logical
- **Domain:** gene_regulation
- **Description:** Network of genes and regulators whose activation or repression controls expression and downstream phenotype.
- **State variables:** mRNA_concentration, protein_concentration, regulator_activity
- **Parameters:** PARAM_ALPHA_TRANSCRIPTION, PARAM_HILL, PARAM_KD_MRNA, PARAM_KD_PROT
- **Expressions:** EXPR_HILL_ACTIVATION, EXPR_HILL_INHIBITION, EXPR_MRNA_SYNTHESIS, EXPR_PROTEIN_SYNTHESIS
- **Relations:** REL_TRANSCRIPTION_ACTIVATION, REL_TRANSCRIPTION_REPRESSION, REL_FEEDBACK_LOOP
- **BioModels IDs:** BIOMD0000000012, BIOMD0000000265
- **Sources:** europepmc, biomodels, repressilator
- **Confidence:** high

### MODEL_RECEPTOR_LIGAND — receptor-ligand binding model

- **Aliases:** receptor binding model, ligand binding model
- **Model class:** binding equilibrium or ODE
- **Domain:** binding_kinetics
- **Description:** Model of ligand binding to receptors, including association, dissociation, occupancy, and downstream activation.
- **State variables:** ligand_concentration, receptor_concentration, bound_complex
- **Parameters:** PARAM_KON, PARAM_KOFF, PARAM_KD
- **Expressions:** EXPR_REVERSIBLE_BINDING, EXPR_RECEPTOR_BINDING_EQUILIBRIUM
- **Relations:** REL_BINDING, REL_UNBINDING
- **BioModels IDs:** BIOMD0000000001, BIOMD0000000002
- **Sources:** biomodels, erbb_model
- **Confidence:** high

### MODEL_TEMPERATURE_DEPENDENT_KINETICS — temperature-dependent kinetic model

- **Aliases:** Arrhenius model, temperature-dependent rate model
- **Model class:** kinetic ODE
- **Domain:** thermodynamics
- **Description:** Kinetic model in which rate constants vary with temperature through an Arrhenius-type relationship.
- **State variables:** rate_constant
- **Parameters:** PARAM_TEMPERATURE
- **Expressions:** EXPR_ARRHENIUS
- **Relations:** REL_PARAMETER_MODULATION
- **BioModels IDs:** None
- **Sources:** europepmc
- **Confidence:** high

### MODEL_SIGNAL_TRANSDUCTION — signal transduction network model

- **Aliases:** signaling network model, signal pathway model
- **Model class:** ODE or logical network
- **Domain:** signal_transduction
- **Description:** Network model of molecular interactions that propagate a signal from receptors to downstream effectors.
- **State variables:** kinase_activity, phosphorylated_state
- **Parameters:** PARAM_KON, PARAM_KOFF, PARAM_KM, PARAM_VMAX
- **Expressions:** EXPR_MASS_ACTION, EXPR_MICHAELIS_MENTEN
- **Relations:** REL_PHOSPHORYLATION, REL_DEPHOSPHORYLATION, REL_SIGNAL_TRANSDUCTION
- **BioModels IDs:** BIOMD0000000010
- **Sources:** reactome, biomodels, erbb_model
- **Confidence:** high

### MODEL_DOSE_RESPONSE — dose-response model

- **Aliases:** concentration-response model, pharmacodynamic response model
- **Model class:** empirical response
- **Domain:** pharmacology
- **Description:** Model relating administered dose or concentration to a measured biological response, often through Hill-type functions.
- **State variables:** dose_or_concentration
- **Parameters:** PARAM_EC50, PARAM_IC50, PARAM_HILL
- **Expressions:** EXPR_HILL_ACTIVATION, EXPR_HILL_INHIBITION
- **Relations:** REL_DOSE_RESPONSE
- **BioModels IDs:** None
- **Sources:** europepmc
- **Confidence:** high
