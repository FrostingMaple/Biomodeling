# Biological Mathematical Modelling Expression Lexicon

- Generated: 2026-09-29
- Entries: 28
- Machine-readable source: `expressions.json`

## Entries

| ID | Name | Domain | Confidence |
| --- | --- | --- | --- |
| EXPR_MASS_ACTION | mass-action rate law | chemical_kinetics | high |
| EXPR_MICHAELIS_MENTEN | Michaelis-Menten rate law | enzyme_kinetics | high |
| EXPR_CATALYTIC_EFFICIENCY | catalytic efficiency | enzyme_kinetics | high |
| EXPR_COMPETITIVE_INHIBITION | competitive inhibition rate law | enzyme_inhibition | high |
| EXPR_HILL_ACTIVATION | Hill activation function | dose_response | high |
| EXPR_HILL_INHIBITION | Hill inhibition function | dose_response | high |
| EXPR_REVERSIBLE_BINDING | reversible bimolecular binding | binding_kinetics | high |
| EXPR_RECEPTOR_BINDING_EQUILIBRIUM | receptor binding equilibrium | binding_equilibrium | high |
| EXPR_EXPONENTIAL_DECAY | first-order exponential decay | kinetics | high |
| EXPR_FIRST_ORDER_CLEARANCE | first-order clearance kinetics | pharmacokinetics | high |
| EXPR_INPUT_OUTPUT_KINETICS | input-output compartment kinetics | pharmacokinetics | high |
| EXPR_LOGISTIC_GROWTH | logistic growth | population_dynamics | high |
| EXPR_GOMPERTZ_GROWTH | Gompertz growth | population_dynamics | high |
| EXPR_SIR_TRANSMISSION | SIR transmission term | epidemiology | high |
| EXPR_SIR_RECOVERY | SIR recovery term | epidemiology | high |
| EXPR_SEIR_LATENT | SEIR latent transition | epidemiology | high |
| EXPR_R0_SIR | basic reproduction number for simple SIR | epidemiology | high |
| EXPR_FICK_DIFFUSION | Fickian diffusion | spatial_transport | high |
| EXPR_ARRHENIUS | Arrhenius temperature dependence | thermodynamics | high |
| EXPR_NERNST | Nernst equilibrium potential | electrophysiology | high |
| EXPR_HH_MEMBRANE_CURRENT | Hodgkin-Huxley membrane current balance | electrophysiology | high |
| EXPR_HH_IONIC_CURRENT | Hodgkin-Huxley ionic current | electrophysiology | high |
| EXPR_HH_GATING | Hodgkin-Huxley gating kinetics | electrophysiology | high |
| EXPR_MRNA_SYNTHESIS | mRNA synthesis and degradation | gene_expression | high |
| EXPR_PROTEIN_SYNTHESIS | protein synthesis and degradation | gene_expression | high |
| EXPR_REPRESSILATOR | repressilator ring oscillator | gene_regulation | high |
| EXPR_MARKOV_TRANSITION | Markov state transition | state_model | high |
| EXPR_POWER_LAW | power-law rate law | metabolic_modeling | high |

## Expressions

### EXPR_MASS_ACTION — mass-action rate law

- **Expression:** `v = k * product_i [X_i]^{n_i}`
- **LaTeX:** `v = k \prod_i [X_i]^{n_i}`
- **Parameters:** PARAM_KON, PARAM_KOFF
- **Response variables:** PARAM_REACTION_FLUX
- **Assumptions:** Elementary reactions are treated as stochastic or deterministic events with rate proportional to reactant abundance.
- **Related models:** MODEL_MASS_ACTION, MODEL_CHEMICAL_REACTION_NETWORK
- **Sources:** biomodels, sabio_rk
- **Confidence:** high

### EXPR_MICHAELIS_MENTEN — Michaelis-Menten rate law

- **Expression:** `v = Vmax * [S] / (Km + [S])`
- **LaTeX:** `v = \frac{V_{max}[S]}{K_m+[S]}`
- **Parameters:** PARAM_VMAX, PARAM_KM, PARAM_SUBSTRATE_CONCENTRATION
- **Response variables:** PARAM_REACTION_FLUX
- **Assumptions:** Single-substrate enzyme reaction; quasi-steady-state assumption for enzyme-substrate complex; no inhibition or cooperativity.
- **Related models:** MODEL_MICHAELIS_MENTEN, MODEL_ENZYME_KINETICS
- **Sources:** classic_mm, brenda, sabio_rk, biomodels
- **Confidence:** high

### EXPR_CATALYTIC_EFFICIENCY — catalytic efficiency

- **Expression:** `efficiency = kcat / Km`
- **LaTeX:** `\eta = \frac{k_{cat}}{K_m}`
- **Parameters:** PARAM_KCAT, PARAM_KM
- **Response variables:** PARAM_KCAT_KM
- **Assumptions:** Used to compare enzyme efficiency in the low-substrate regime of a Michaelis-Menten model.
- **Related models:** MODEL_MICHAELIS_MENTEN
- **Sources:** brenda, sabio_rk
- **Confidence:** high

### EXPR_COMPETITIVE_INHIBITION — competitive inhibition rate law

- **Expression:** `v = Vmax * [S] / (Km * (1 + [I]/Ki) + [S])`
- **LaTeX:** `v = \frac{V_{max}[S]}{K_m(1+[I]/K_i)+[S]}`
- **Parameters:** PARAM_VMAX, PARAM_KM, PARAM_KI, PARAM_SUBSTRATE_CONCENTRATION
- **Response variables:** PARAM_REACTION_FLUX
- **Assumptions:** Inhibitor binds free enzyme reversibly and competes with substrate; standard rapid-equilibrium or steady-state derivation.
- **Related models:** MODEL_ENZYME_INHIBITION
- **Sources:** brenda, sabio_rk, europepmc
- **Confidence:** high

### EXPR_HILL_ACTIVATION — Hill activation function

- **Expression:** `response = basal + (max - basal) * X^n / (K^n + X^n)`
- **LaTeX:** `R = R_{base} + (R_{max}-R_{base})\frac{X^n}{K^n+X^n}`
- **Parameters:** PARAM_HILL, PARAM_EC50
- **Response variables:** response
- **Assumptions:** Empirical sigmoidal relation; n describes apparent cooperativity; mechanism not uniquely identified by the fit.
- **Related models:** MODEL_HILL, MODEL_DOSE_RESPONSE, MODEL_GENE_REGULATION
- **Sources:** europepmc, biomodels
- **Confidence:** high

### EXPR_HILL_INHIBITION — Hill inhibition function

- **Expression:** `response = basal + (max - basal) * K^n / (K^n + X^n)`
- **LaTeX:** `R = R_{base} + (R_{max}-R_{base})\frac{K^n}{K^n+X^n}`
- **Parameters:** PARAM_HILL, PARAM_IC50
- **Response variables:** response
- **Assumptions:** Empirical decreasing sigmoidal relation used for inhibition or repression; mechanism must be supported separately.
- **Related models:** MODEL_HILL, MODEL_DOSE_RESPONSE, MODEL_GENE_REGULATION
- **Sources:** europepmc, biomodels, repressilator
- **Confidence:** high

### EXPR_REVERSIBLE_BINDING — reversible bimolecular binding

- **Expression:** `d[AB]/dt = kon*[A]*[B] - koff*[AB]`
- **LaTeX:** `\frac{d[AB]}{dt}=k_{on}[A][B]-k_{off}[AB]`
- **Parameters:** PARAM_KON, PARAM_KOFF, PARAM_KD
- **Response variables:** binding_complex_concentration
- **Assumptions:** Bimolecular association and first-order dissociation; concentrations treated as deterministic and well mixed.
- **Related models:** MODEL_MASS_ACTION, MODEL_RECEPTOR_LIGAND
- **Sources:** biomodels, erbb_model
- **Confidence:** high

### EXPR_RECEPTOR_BINDING_EQUILIBRIUM — receptor binding equilibrium

- **Expression:** `fraction_bound = [L] / (Kd + [L])`
- **LaTeX:** `f = \frac{[L]}{K_d+[L]}`
- **Parameters:** PARAM_KD
- **Response variables:** fraction_bound
- **Assumptions:** Equilibrium binding with a single independent binding site and no cooperativity.
- **Related models:** MODEL_RECEPTOR_LIGAND
- **Sources:** biomodels, erbb_model
- **Confidence:** high

### EXPR_EXPONENTIAL_DECAY — first-order exponential decay

- **Expression:** `X(t) = X0 * exp(-k*t)`
- **LaTeX:** `X(t)=X_0e^{-kt}`
- **Parameters:** PARAM_INITIAL_CONCENTRATION, PARAM_HALF_LIFE
- **Response variables:** X(t)
- **Assumptions:** First-order removal with a constant rate coefficient and no production input.
- **Related models:** MODEL_ONE_COMPARTMENT, MODEL_BIOMARKER_KINETICS, MODEL_MARKOV_STATE
- **Sources:** europepmc, biomodels
- **Confidence:** high

### EXPR_FIRST_ORDER_CLEARANCE — first-order clearance kinetics

- **Expression:** `dC/dt = input - k_clear * C`
- **LaTeX:** `\frac{dC}{dt}=I(t)-k_{clear}C`
- **Parameters:** PARAM_CLEARANCE, PARAM_RELEASE_RATE, PARAM_INITIAL_CONCENTRATION
- **Response variables:** concentration
- **Assumptions:** One well-mixed compartment; first-order clearance; input function must be specified separately.
- **Related models:** MODEL_ONE_COMPARTMENT, MODEL_BIOMARKER_KINETICS
- **Sources:** europepmc, hepatic_glucose
- **Confidence:** high

### EXPR_INPUT_OUTPUT_KINETICS — input-output compartment kinetics

- **Expression:** `dC/dt = k_release * D(t) - k_clear * C`
- **LaTeX:** `\frac{dC}{dt}=k_{release}D(t)-k_{clear}C`
- **Parameters:** PARAM_RELEASE_RATE, PARAM_CLEARANCE
- **Response variables:** concentration
- **Assumptions:** Requires a defined input or damage function D(t) and a single measured compartment.
- **Related models:** MODEL_BIOMARKER_KINETICS, MODEL_ONE_COMPARTMENT
- **Sources:** europepmc
- **Confidence:** high

### EXPR_LOGISTIC_GROWTH — logistic growth

- **Expression:** `dN/dt = r*N*(1 - N/K)`
- **LaTeX:** `\frac{dN}{dt}=rN\left(1-\frac{N}{K}\right)`
- **Parameters:** PARAM_MU_GROWTH, PARAM_CARRYING_CAPACITY
- **Response variables:** population_size
- **Assumptions:** Growth rate decreases linearly with population size; carrying capacity is constant in the analysed interval.
- **Related models:** MODEL_LOGISTIC_GROWTH
- **Sources:** europepmc
- **Confidence:** high

### EXPR_GOMPERTZ_GROWTH — Gompertz growth

- **Expression:** `dN/dt = r*N*ln(K/N)`
- **LaTeX:** `\frac{dN}{dt}=rN\ln\left(\frac{K}{N}\right)`
- **Parameters:** PARAM_MU_GROWTH, PARAM_CARRYING_CAPACITY
- **Response variables:** population_size
- **Assumptions:** Asymmetric sigmoidal growth with initially fast relative growth and a smooth approach to carrying capacity.
- **Related models:** MODEL_GOMPERTZ_GROWTH
- **Sources:** europepmc
- **Confidence:** high

### EXPR_SIR_TRANSMISSION — SIR transmission term

- **Expression:** `new_infections = beta * S * I / N`
- **LaTeX:** `\text{new infections}=\beta\frac{SI}{N}`
- **Parameters:** PARAM_BETA
- **Response variables:** susceptible_population, infected_population
- **Assumptions:** Homogeneous mixing and frequency- or density-dependent transmission as specified by the model.
- **Related models:** MODEL_SIR, MODEL_SEIR
- **Sources:** classic_sir
- **Confidence:** high

### EXPR_SIR_RECOVERY — SIR recovery term

- **Expression:** `new_recoveries = gamma * I`
- **LaTeX:** `\text{new recoveries}=\gamma I`
- **Parameters:** PARAM_GAMMA
- **Response variables:** infected_population
- **Assumptions:** Per-capita recovery rate is constant and recovery confers immunity in the simplest SIR form.
- **Related models:** MODEL_SIR, MODEL_SEIR
- **Sources:** classic_sir
- **Confidence:** high

### EXPR_SEIR_LATENT — SEIR latent transition

- **Expression:** `new_infectious = sigma * E`
- **LaTeX:** `\text{new infectious}=\sigma E`
- **Parameters:** PARAM_SIGMA
- **Response variables:** exposed_population, infected_population
- **Assumptions:** Exposed individuals are not infectious and transition at a constant per-capita rate.
- **Related models:** MODEL_SEIR
- **Sources:** classic_sir
- **Confidence:** high

### EXPR_R0_SIR — basic reproduction number for simple SIR

- **Expression:** `R0 = beta / gamma`
- **LaTeX:** `R_0=\frac{\beta}{\gamma}`
- **Parameters:** PARAM_R0, PARAM_BETA, PARAM_GAMMA
- **Response variables:** R0
- **Assumptions:** Closed homogeneous SIR population with no vaccination, waning immunity, or vital dynamics.
- **Related models:** MODEL_SIR
- **Sources:** classic_sir
- **Confidence:** high

### EXPR_FICK_DIFFUSION — Fickian diffusion

- **Expression:** `dC/dt = D * laplacian(C) + reaction`
- **LaTeX:** `\frac{\partial C}{\partial t}=D\nabla^2C+R(C)`
- **Parameters:** PARAM_DIFFUSION
- **Response variables:** concentration
- **Assumptions:** Isotropic homogeneous medium and Fickian flux proportional to the concentration gradient.
- **Related models:** MODEL_REACTION_DIFFUSION
- **Sources:** europepmc
- **Confidence:** high

### EXPR_ARRHENIUS — Arrhenius temperature dependence

- **Expression:** `k(T) = A * exp(-Ea / (R*T))`
- **LaTeX:** `k(T)=Ae^{-E_a/(RT)}`
- **Parameters:** PARAM_TEMPERATURE
- **Response variables:** rate_constant
- **Assumptions:** Single activated process with a temperature-independent pre-exponential factor over the analysed interval.
- **Related models:** MODEL_TEMPERATURE_DEPENDENT_KINETICS
- **Sources:** europepmc
- **Confidence:** high

### EXPR_NERNST — Nernst equilibrium potential

- **Expression:** `E_ion = (R*T/(z*F)) * ln([ion_out]/[ion_in])`
- **LaTeX:** `E_{ion}=\frac{RT}{zF}\ln\frac{[ion]_{out}}{[ion]_{in}}`
- **Parameters:** PARAM_REVERSAL_POTENTIAL, PARAM_TEMPERATURE
- **Response variables:** reversal_potential
- **Assumptions:** Ideal electrochemical equilibrium for a single permeant ion.
- **Related models:** MODEL_HODGKIN_HUXLEY
- **Sources:** classic_hh
- **Confidence:** high

### EXPR_HH_MEMBRANE_CURRENT — Hodgkin-Huxley membrane current balance

- **Expression:** `Cm * dVm/dt = -I_Na - I_K - I_L + I_ext`
- **LaTeX:** `C_m\frac{dV_m}{dt}=-I_{Na}-I_K-I_L+I_{ext}`
- **Parameters:** PARAM_CAPACITANCE, PARAM_MEMBRANE_POTENTIAL, PARAM_CONDUCTANCE, PARAM_REVERSAL_POTENTIAL
- **Response variables:** membrane_potential
- **Assumptions:** Space-clamped membrane patch; ionic currents follow Hodgkin-Huxley gating and linear driving-force terms.
- **Related models:** MODEL_HODGKIN_HUXLEY
- **Sources:** classic_hh, biomodels
- **Confidence:** high

### EXPR_HH_IONIC_CURRENT — Hodgkin-Huxley ionic current

- **Expression:** `I_ion = gbar * m^a * h^b * (Vm - E_ion)`
- **LaTeX:** `I_{ion}=\bar{g}m^ah^b(V_m-E_{ion})`
- **Parameters:** PARAM_CONDUCTANCE, PARAM_REVERSAL_POTENTIAL, PARAM_MEMBRANE_POTENTIAL
- **Response variables:** ionic_current
- **Assumptions:** Gating variables are bounded between zero and one and follow first-order voltage-dependent kinetics.
- **Related models:** MODEL_HODGKIN_HUXLEY
- **Sources:** classic_hh
- **Confidence:** high

### EXPR_HH_GATING — Hodgkin-Huxley gating kinetics

- **Expression:** `dx/dt = alpha_x(V)*(1-x) - beta_x(V)*x`
- **LaTeX:** `\frac{dx}{dt}=\alpha_x(V)(1-x)-\beta_x(V)x`
- **Parameters:** None
- **Response variables:** gating_variable
- **Assumptions:** Two-state gating with voltage-dependent forward and backward rate functions.
- **Related models:** MODEL_HODGKIN_HUXLEY
- **Sources:** classic_hh
- **Confidence:** high

### EXPR_MRNA_SYNTHESIS — mRNA synthesis and degradation

- **Expression:** `dm/dt = transcription(m) - kd_mRNA*m`
- **LaTeX:** `\frac{dm}{dt}=T(m)-k_{d,mRNA}m`
- **Parameters:** PARAM_ALPHA_TRANSCRIPTION, PARAM_KD_MRNA, PARAM_TAU_MRNA
- **Response variables:** mRNA_concentration
- **Assumptions:** Transcription and first-order degradation are separated; regulation is encoded in the transcription term.
- **Related models:** MODEL_GENE_REGULATION, MODEL_REPRESSILATOR
- **Sources:** repressilator, biomodels
- **Confidence:** high

### EXPR_PROTEIN_SYNTHESIS — protein synthesis and degradation

- **Expression:** `dp/dt = k_tl*m - kd_prot*p`
- **LaTeX:** `\frac{dp}{dt}=k_{tl}m-k_{d,prot}p`
- **Parameters:** PARAM_KT_L, PARAM_KD_PROT, PARAM_TAU_PROT
- **Response variables:** protein_concentration
- **Assumptions:** Translation is proportional to mRNA abundance and protein removal is first order.
- **Related models:** MODEL_GENE_REGULATION, MODEL_REPRESSILATOR
- **Sources:** repressilator, biomodels
- **Confidence:** high

### EXPR_REPRESSILATOR — repressilator ring oscillator

- **Expression:** `dm_i/dt = alpha0 + alpha/(1+p_j^n) - kd_mRNA*m_i; dp_i/dt = k_tl*m_i - kd_prot*p_i`
- **LaTeX:** `\frac{dm_i}{dt}=\alpha_0+\frac{\alpha}{1+p_j^n}-k_{d,mRNA}m_i;\quad \frac{dp_i}{dt}=k_{tl}m_i-k_{d,prot}p_i`
- **Parameters:** PARAM_ALPHA_TRANSCRIPTION, PARAM_HILL, PARAM_KD_MRNA, PARAM_KD_PROT, PARAM_KT_L
- **Response variables:** mRNA_concentration, protein_concentration
- **Assumptions:** Three repressors form a cyclic negative-feedback ring; Hill repression is used as a phenomenological regulatory function.
- **Related models:** MODEL_REPRESSILATOR, MODEL_GENE_REGULATION
- **Sources:** repressilator, biomodels
- **Confidence:** high

### EXPR_MARKOV_TRANSITION — Markov state transition

- **Expression:** `dP_i/dt = sum_j k_ji*P_j - sum_j k_ij*P_i`
- **LaTeX:** `\frac{dP_i}{dt}=\sum_j k_{ji}P_j-\sum_j k_{ij}P_i`
- **Parameters:** PARAM_BINDING_PROBABILITY
- **Response variables:** state_probability
- **Assumptions:** Discrete states, Markov property, and conservative transition rates between modelled states.
- **Related models:** MODEL_MARKOV_STATE
- **Sources:** biomodels
- **Confidence:** high

### EXPR_POWER_LAW — power-law rate law

- **Expression:** `v = v0 * product_i (X_i/X_i0)^{epsilon_i}`
- **LaTeX:** `v=v_0\prod_i\left(\frac{X_i}{X_{i0}}\right)^{\varepsilon_i}`
- **Parameters:** PARAM_ELASTICITY, PARAM_REACTION_FLUX
- **Response variables:** PARAM_REACTION_FLUX
- **Assumptions:** Local linearization around a reference steady state; used in linlog metabolic models such as BIOMD0000000471.
- **Related models:** MODEL_METABOLIC_CONTROL, MODEL_GENOME_SCALE_KINETIC
- **Sources:** biomodels
- **Confidence:** high

### EXPR_THERMODYNAMIC_DRIVING_FORCE — thermodynamic driving-force relation

- **Expression:** `DeltaG = DeltaG0 + R*T*ln(Q)`
- **Parameters:** PARAM_THERMODYNAMIC_DRIVING_FORCE, PARAM_TEMPERATURE
- **Related models:** MODEL_THERMODYNAMIC_KINETIC
- **Sources:** biomodels, europepmc
