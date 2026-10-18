# Biological Mathematical Modelling Relation Lexicon

- Generated: 2026-09-29
- Entries: 31
- Machine-readable source: `relations.json`

## Entries

| ID | Canonical name | Type | Direction | Confidence |
| --- | --- | --- | --- | --- |
| REL_ACTIVATION | activation | regulatory | directed | high |
| REL_INHIBITION | inhibition | regulatory | directed | high |
| REL_POSITIVE_FEEDBACK | positive feedback | network_motif | cyclic | high |
| REL_NEGATIVE_FEEDBACK | negative feedback | network_motif | cyclic | high |
| REL_PHOSPHORYLATION | phosphorylation | post_translational_modification | directed | high |
| REL_DEPHOSPHORYLATION | dephosphorylation | post_translational_modification | directed | high |
| REL_BINDING | binding | molecular_interaction | directed_or_bidirectional | high |
| REL_UNBINDING | unbinding or dissociation | molecular_interaction | directed_or_bidirectional | high |
| REL_CATALYSIS | catalysis | chemical_transformation | directed | high |
| REL_REVERSIBLE_REACTION | reversible reaction | chemical_transformation | bidirectional | high |
| REL_TRANSCRIPTION_ACTIVATION | transcriptional activation | gene_regulation | directed | high |
| REL_TRANSCRIPTION_REPRESSION | transcriptional repression | gene_regulation | directed | high |
| REL_TRANSLATION | translation | gene_expression | directed | high |
| REL_DEGRADATION | degradation | turnover | directed | high |
| REL_CLEARANCE | clearance | pharmacokinetics | directed | high |
| REL_TRANSPORT | transport | spatial_transport | directed | high |
| REL_DIFFUSION | diffusion | spatial_transport | directed_by_gradient | high |
| REL_ALLOSTERIC_ACTIVATION | allosteric activation | allostery | directed | high |
| REL_ALLOSTERIC_INHIBITION | allosteric inhibition | allostery | directed | high |
| REL_COMPETITIVE_INHIBITION | competitive inhibition | enzyme_inhibition | directed | high |
| REL_RECEPTOR_DIMERIZATION | receptor dimerization | signal_transduction | directed | high |
| REL_SIGNAL_TRANSDUCTION | signal transduction | signal_transduction | directed | high |
| REL_FLUX_REGULATION | flux regulation | metabolic_regulation | directed | high |
| REL_PARAMETER_MODULATION | parameter modulation | model_relation | directed_or_association | high |
| REL_DOSE_RESPONSE | dose-response relation | pharmacology | directed | high |
| REL_INFECTION_TRANSMISSION | infection transmission | epidemiology | directed | high |
| REL_RECOVERY | recovery or removal | epidemiology | directed | high |
| REL_STATE_TRANSITION | state transition | state_model | directed_or_bidirectional | high |
| REL_GATING | voltage-dependent gating | electrophysiology | directed | high |
| REL_COOPERATIVITY | cooperativity | allostery | directed | high |
| REL_FEEDBACK_LOOP | feedback loop | network_motif | cyclic | high |

## Definitions

### REL_ACTIVATION — activation

- **Aliases:** activates, activation, up-regulates, upregulates, stimulates, promotes
- **Relation type:** regulatory
- **Direction:** directed
- **Definition:** A source entity increases the activity, rate, or effective level of a target entity.
- **Evidence required:** Use only when the source states an increase, activation, stimulation, or promoting relation.
- **Related expressions:** EXPR_HILL_ACTIVATION
- **Related models:** MODEL_GENE_REGULATION, MODEL_SIGNAL_TRANSDUCTION
- **Sources:** europepmc, reactome
- **Confidence:** high

### REL_INHIBITION — inhibition

- **Aliases:** inhibits, inhibition, suppresses, represses, down-regulates, downregulates, blocks
- **Relation type:** regulatory
- **Direction:** directed
- **Definition:** A source entity decreases the activity, rate, or effective level of a target entity.
- **Evidence required:** Use when the source explicitly reports inhibition, repression, suppression, or blocking.
- **Related expressions:** EXPR_HILL_INHIBITION, EXPR_COMPETITIVE_INHIBITION
- **Related models:** MODEL_GENE_REGULATION, MODEL_ENZYME_INHIBITION, MODEL_SIGNAL_TRANSDUCTION
- **Sources:** europepmc, reactome
- **Confidence:** high

### REL_POSITIVE_FEEDBACK — positive feedback

- **Aliases:** positive feedback loop, self-activation, autocatalysis
- **Relation type:** network_motif
- **Direction:** cyclic
- **Definition:** A pathway or product increases an upstream component or its own production, reinforcing the response.
- **Evidence required:** Requires a source description of a loop, feedback, or self-reinforcement; do not infer from correlation alone.
- **Related expressions:** EXPR_LOGISTIC_GROWTH
- **Related models:** MODEL_GENE_REGULATION, MODEL_MAPK_CASCADE
- **Sources:** europepmc, reactome
- **Confidence:** high

### REL_NEGATIVE_FEEDBACK — negative feedback

- **Aliases:** negative feedback loop, feedback inhibition, autoinhibition
- **Relation type:** network_motif
- **Direction:** cyclic
- **Definition:** A pathway or product decreases an upstream component or its own production, stabilizing or oscillating the response.
- **Evidence required:** Requires an explicit feedback or feedback-inhibition statement.
- **Related expressions:** EXPR_HILL_INHIBITION
- **Related models:** MODEL_MAPK_CASCADE, MODEL_GENE_REGULATION
- **Sources:** europepmc, reactome
- **Confidence:** high

### REL_PHOSPHORYLATION — phosphorylation

- **Aliases:** phosphorylates, phosphorylation
- **Relation type:** post_translational_modification
- **Direction:** directed
- **Definition:** A kinase or modifying enzyme adds a phosphate group to a target molecule.
- **Evidence required:** Evidence should identify the modifier and target or state that the modification occurs.
- **Related expressions:** EXPR_MASS_ACTION
- **Related models:** MODEL_SIGNAL_TRANSDUCTION, MODEL_MAPK_CASCADE, MODEL_ERBB_SIGNALING
- **Sources:** europepmc, reactome, erbb_model
- **Confidence:** high

### REL_DEPHOSPHORYLATION — dephosphorylation

- **Aliases:** dephosphorylates, dephosphorylation
- **Relation type:** post_translational_modification
- **Direction:** directed
- **Definition:** A phosphatase or modifying enzyme removes a phosphate group from a target molecule.
- **Evidence required:** Evidence should identify the phosphatase and target when available.
- **Related expressions:** EXPR_MASS_ACTION
- **Related models:** MODEL_SIGNAL_TRANSDUCTION, MODEL_MAPK_CASCADE
- **Sources:** europepmc, reactome
- **Confidence:** high

### REL_BINDING — binding

- **Aliases:** binds, binding, associates, forms complex
- **Relation type:** molecular_interaction
- **Direction:** directed_or_bidirectional
- **Definition:** Two or more entities form a bound complex or measurable association.
- **Evidence required:** Use for explicit binding or complex-formation statements; distinguish from statistical association.
- **Related expressions:** EXPR_MASS_ACTION, EXPR_REVERSIBLE_BINDING
- **Related models:** MODEL_MASS_ACTION, MODEL_RECEPTOR_LIGAND
- **Sources:** biomodels, reactome, erbb_model
- **Confidence:** high

### REL_UNBINDING — unbinding or dissociation

- **Aliases:** unbinds, dissociates, dissociation, release
- **Relation type:** molecular_interaction
- **Direction:** directed_or_bidirectional
- **Definition:** A bound complex separates into its components or a ligand leaves a binding site.
- **Evidence required:** Requires explicit dissociation, release, or unbinding evidence.
- **Related expressions:** EXPR_REVERSIBLE_BINDING, EXPR_EXPONENTIAL_DECAY
- **Related models:** MODEL_MASS_ACTION, MODEL_RECEPTOR_LIGAND, MODEL_MARKOV_STATE
- **Sources:** biomodels, erbb_model
- **Confidence:** high

### REL_CATALYSIS — catalysis

- **Aliases:** catalyzes, catalyses, enzyme conversion, enzymatic conversion
- **Relation type:** chemical_transformation
- **Direction:** directed
- **Definition:** An enzyme accelerates conversion of substrate to product without being consumed in the net reaction.
- **Evidence required:** Evidence should identify enzyme, substrate, and product when stated.
- **Related expressions:** EXPR_MICHAELIS_MENTEN, EXPR_MASS_ACTION
- **Related models:** MODEL_ENZYME_KINETICS, MODEL_METABOLIC_NETWORK
- **Sources:** biomodels, sabio_rk, brenda
- **Confidence:** high

### REL_REVERSIBLE_REACTION — reversible reaction

- **Aliases:** reversible, forward and reverse reaction, bidirectional conversion
- **Relation type:** chemical_transformation
- **Direction:** bidirectional
- **Definition:** A reaction can proceed in both forward and reverse directions under the modelled conditions.
- **Evidence required:** Requires explicit reversible notation or reversible kinetic terms.
- **Related expressions:** EXPR_REVERSIBLE_BINDING, EXPR_MASS_ACTION
- **Related models:** MODEL_MASS_ACTION, MODEL_ENZYME_KINETICS
- **Sources:** biomodels, sabio_rk
- **Confidence:** high

### REL_TRANSCRIPTION_ACTIVATION — transcriptional activation

- **Aliases:** transcription activation, activates transcription, promoter activation, gene activation
- **Relation type:** gene_regulation
- **Direction:** directed
- **Definition:** A regulator increases transcription of a target gene or promoter.
- **Evidence required:** Evidence must connect the regulator to transcription, promoter activity, or mRNA production.
- **Related expressions:** EXPR_HILL_ACTIVATION, EXPR_MRNA_SYNTHESIS
- **Related models:** MODEL_GENE_REGULATION, MODEL_REPRESSILATOR
- **Sources:** europepmc, biomodels
- **Confidence:** high

### REL_TRANSCRIPTION_REPRESSION — transcriptional repression

- **Aliases:** transcription repression, represses transcription, gene repression, promoter repression
- **Relation type:** gene_regulation
- **Direction:** directed
- **Definition:** A regulator decreases transcription of a target gene or promoter.
- **Evidence required:** Evidence must connect the regulator to repression of transcription or mRNA production.
- **Related expressions:** EXPR_HILL_INHIBITION, EXPR_MRNA_SYNTHESIS
- **Related models:** MODEL_GENE_REGULATION, MODEL_REPRESSILATOR
- **Sources:** europepmc, biomodels, repressilator
- **Confidence:** high

### REL_TRANSLATION — translation

- **Aliases:** protein synthesis from mRNA, translates, translation
- **Relation type:** gene_expression
- **Direction:** directed
- **Definition:** An mRNA template directs synthesis of a protein product.
- **Evidence required:** Requires mRNA-to-protein production evidence or a modelling definition.
- **Related expressions:** EXPR_PROTEIN_SYNTHESIS
- **Related models:** MODEL_GENE_REGULATION, MODEL_REPRESSILATOR
- **Sources:** biomodels, repressilator
- **Confidence:** high

### REL_DEGRADATION — degradation

- **Aliases:** degrades, degradation, decay, turnover
- **Relation type:** turnover
- **Direction:** directed
- **Definition:** A molecular species is removed, destroyed, or turned over.
- **Evidence required:** Requires an explicit degradation, decay, or turnover statement.
- **Related expressions:** EXPR_EXPONENTIAL_DECAY
- **Related models:** MODEL_GENE_REGULATION, MODEL_METABOLIC_NETWORK
- **Sources:** biomodels, europepmc
- **Confidence:** high

### REL_CLEARANCE — clearance

- **Aliases:** cleared, clearance, elimination, removal from compartment
- **Relation type:** pharmacokinetics
- **Direction:** directed
- **Definition:** A substance is removed from a compartment by clearance or elimination processes.
- **Evidence required:** Requires compartment, substance, and clearance or elimination context.
- **Related expressions:** EXPR_FIRST_ORDER_CLEARANCE, EXPR_INPUT_OUTPUT_KINETICS
- **Related models:** MODEL_ONE_COMPARTMENT, MODEL_BIOMARKER_KINETICS
- **Sources:** europepmc, hepatic_glucose
- **Confidence:** high

### REL_TRANSPORT — transport

- **Aliases:** transports, transport, uptake, efflux, import, export
- **Relation type:** spatial_transport
- **Direction:** directed
- **Definition:** An entity moves between compartments or across a membrane.
- **Evidence required:** Requires a source statement of transport, uptake, efflux, import, or export.
- **Related expressions:** EXPR_FICK_DIFFUSION
- **Related models:** MODEL_REACTION_DIFFUSION, MODEL_TRANSPORT
- **Sources:** reactome, europepmc, biomodels
- **Confidence:** high

### REL_DIFFUSION — diffusion

- **Aliases:** diffuses, diffusion, spatial spreading
- **Relation type:** spatial_transport
- **Direction:** directed_by_gradient
- **Definition:** A substance spreads in space in response to a concentration gradient.
- **Evidence required:** Use only when diffusion or spatial transport is explicitly modelled or measured.
- **Related expressions:** EXPR_FICK_DIFFUSION
- **Related models:** MODEL_REACTION_DIFFUSION
- **Sources:** europepmc
- **Confidence:** high

### REL_ALLOSTERIC_ACTIVATION — allosteric activation

- **Aliases:** allosteric activation, cooperative activation, positive cooperativity
- **Relation type:** allostery
- **Direction:** directed
- **Definition:** Binding at one site increases activity or affinity at another site, often producing sigmoidal response.
- **Evidence required:** Requires allosteric, cooperative, or sigmoidal activation evidence.
- **Related expressions:** EXPR_HILL_ACTIVATION
- **Related models:** MODEL_HILL, MODEL_ALLOSTERY
- **Sources:** europepmc, biomodels
- **Confidence:** high

### REL_ALLOSTERIC_INHIBITION — allosteric inhibition

- **Aliases:** allosteric inhibition, negative cooperativity
- **Relation type:** allostery
- **Direction:** directed
- **Definition:** Binding at one site decreases activity or affinity at another site.
- **Evidence required:** Requires allosteric or cooperative inhibition evidence.
- **Related expressions:** EXPR_HILL_INHIBITION
- **Related models:** MODEL_HILL, MODEL_ALLOSTERY
- **Sources:** europepmc, biomodels
- **Confidence:** high

### REL_COMPETITIVE_INHIBITION — competitive inhibition

- **Aliases:** competitive inhibition, competes with substrate
- **Relation type:** enzyme_inhibition
- **Direction:** directed
- **Definition:** An inhibitor competes with substrate binding and increases the apparent Km without changing Vmax in the standard model.
- **Evidence required:** Requires competitive inhibition, substrate competition, or equivalent kinetic evidence.
- **Related expressions:** EXPR_COMPETITIVE_INHIBITION
- **Related models:** MODEL_ENZYME_INHIBITION
- **Sources:** sabio_rk, brenda, europepmc
- **Confidence:** high

### REL_RECEPTOR_DIMERIZATION — receptor dimerization

- **Aliases:** dimerization, receptor dimerization, forms dimers
- **Relation type:** signal_transduction
- **Direction:** directed
- **Definition:** Receptor monomers associate into dimers or higher-order receptor complexes.
- **Evidence required:** Requires explicit dimerization or receptor-complex formation evidence.
- **Related expressions:** EXPR_MASS_ACTION, EXPR_REVERSIBLE_BINDING
- **Related models:** MODEL_RECEPTOR_LIGAND, MODEL_ERBB_SIGNALING
- **Sources:** erbb_model, reactome
- **Confidence:** high

### REL_SIGNAL_TRANSDUCTION — signal transduction

- **Aliases:** signaling cascade, signal transduction, pathway activation
- **Relation type:** signal_transduction
- **Direction:** directed
- **Definition:** A signal is propagated through molecular interactions to produce a downstream response.
- **Evidence required:** Requires a source-supported chain or pathway relation; do not infer missing intermediates.
- **Related expressions:** EXPR_HILL_ACTIVATION
- **Related models:** MODEL_SIGNAL_TRANSDUCTION, MODEL_ERBB_SIGNALING, MODEL_MAPK_CASCADE
- **Sources:** reactome, erbb_model, mapk_cascade
- **Confidence:** high

### REL_FLUX_REGULATION — flux regulation

- **Aliases:** regulates flux, flux control, metabolic regulation
- **Relation type:** metabolic_regulation
- **Direction:** directed
- **Definition:** A regulator changes the rate or flux through a metabolic reaction or pathway.
- **Evidence required:** Requires flux, pathway rate, or metabolic regulation evidence.
- **Related expressions:** EXPR_MICHAELIS_MENTEN, EXPR_POWER_LAW
- **Related models:** MODEL_METABOLIC_NETWORK, MODEL_GENOME_SCALE_KINETIC
- **Sources:** biomodels, hepatic_glucose
- **Confidence:** high

### REL_PARAMETER_MODULATION — parameter modulation

- **Aliases:** modulates parameter, parameter dependence, sensitivity
- **Relation type:** model_relation
- **Direction:** directed_or_association
- **Definition:** A condition or variable changes the value or effective influence of a model parameter.
- **Evidence required:** Requires an explicit parameter change, sensitivity, or modulation statement.
- **Related expressions:** None
- **Related models:** MODEL_GENERAL_KINETIC
- **Sources:** europepmc, biomodels
- **Confidence:** high

### REL_DOSE_RESPONSE — dose-response relation

- **Aliases:** dose response, concentration response, dose-dependent effect
- **Relation type:** pharmacology
- **Direction:** directed
- **Definition:** A measured effect changes as a function of dose or concentration.
- **Evidence required:** Requires the dose or concentration range and measured response.
- **Related expressions:** EXPR_HILL_ACTIVATION, EXPR_HILL_INHIBITION
- **Related models:** MODEL_DOSE_RESPONSE
- **Sources:** europepmc, erbb_model
- **Confidence:** high

### REL_INFECTION_TRANSMISSION — infection transmission

- **Aliases:** transmission, infection event, susceptible to infected
- **Relation type:** epidemiology
- **Direction:** directed
- **Definition:** A susceptible individual becomes infected through contact or transmission.
- **Evidence required:** Requires transmission structure or infection-flow evidence.
- **Related expressions:** EXPR_SIR_TRANSMISSION, EXPR_SEIR_LATENT
- **Related models:** MODEL_SIR, MODEL_SEIR
- **Sources:** classic_sir
- **Confidence:** high

### REL_RECOVERY — recovery or removal

- **Aliases:** recovery, removal from infected compartment
- **Relation type:** epidemiology
- **Direction:** directed
- **Definition:** An infected individual recovers, becomes non-infectious, or leaves the infected compartment.
- **Evidence required:** Requires recovery or removal-flow evidence.
- **Related expressions:** EXPR_SIR_RECOVERY
- **Related models:** MODEL_SIR, MODEL_SEIR
- **Sources:** classic_sir
- **Confidence:** high

### REL_STATE_TRANSITION — state transition

- **Aliases:** transitions to, state transition, conformational transition
- **Relation type:** state_model
- **Direction:** directed_or_bidirectional
- **Definition:** A modelled system changes from one discrete state to another with an associated rate or probability.
- **Evidence required:** Requires named states and a transition, rate, or probability statement.
- **Related expressions:** EXPR_MARKOV_TRANSITION
- **Related models:** MODEL_MARKOV_STATE
- **Sources:** biomodels
- **Confidence:** high

### REL_GATING — voltage-dependent gating

- **Aliases:** gating, activation gate, inactivation gate
- **Relation type:** electrophysiology
- **Direction:** directed
- **Definition:** A voltage- or ligand-dependent variable controls opening or inactivation of an ion channel.
- **Evidence required:** Requires gating-variable or channel-state evidence.
- **Related expressions:** EXPR_HH_GATING
- **Related models:** MODEL_HODGKIN_HUXLEY
- **Sources:** classic_hh, biomodels
- **Confidence:** high

### REL_COOPERATIVITY — cooperativity

- **Aliases:** cooperative binding, cooperativity, sigmoidal binding
- **Relation type:** allostery
- **Direction:** directed
- **Definition:** Binding or activity at one site changes the affinity or response at another site.
- **Evidence required:** Requires cooperative or sigmoidal-response evidence.
- **Related expressions:** EXPR_HILL_ACTIVATION, EXPR_HILL_INHIBITION
- **Related models:** MODEL_HILL, MODEL_ALLOSTERY
- **Sources:** europepmc, biomodels
- **Confidence:** high

### REL_FEEDBACK_LOOP — feedback loop

- **Aliases:** feedback loop, closed-loop regulation
- **Relation type:** network_motif
- **Direction:** cyclic
- **Definition:** A regulatory path returns to affect its own upstream component, producing stabilization, amplification, or oscillation.
- **Evidence required:** Requires explicit loop or feedback description.
- **Related expressions:** EXPR_HILL_ACTIVATION, EXPR_HILL_INHIBITION
- **Related models:** MODEL_MAPK_CASCADE, MODEL_GENE_REGULATION
- **Sources:** europepmc, mapk_cascade
- **Confidence:** high
