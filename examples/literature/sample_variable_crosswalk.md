# Variable and Parameter Cross-Reference

## Document

| Field | Value |
| --- | --- |
| Title | Temperature and nitrogen regulation of Escherichia coli growth |
| Authors | Example Authors |
| Year | 2026 |
| Source | sample_paper.md |
| Language | en |

## Research Question

**Question:** How do nitrogen availability and temperature regulate the specific growth rate of Escherichia coli in continuous culture?

**Scope:** Continuous and batch cultures of Escherichia coli K-12 across three temperatures and a range of ammonium concentrations.

**Confidence:** high

**Evidence:**
- `B0001` (abstract): “We investigated how nitrogen availability and temperature regulate the specific growth rate of *Escherichia coli* in continuous culture.”

## Study Profile

| Dimension | Description |
| --- | --- |
| Organism or system | Escherichia coli K-12 in minimal medium |
| Study design | Batch and chemostat experiments with three independent biological replicates per condition |
| Model type | Temperature-dependent Monod model |
| Sample scale | Three temperatures and ammonium concentrations from 0.1 to 10 mM |
| Time scale | Exponential growth and continuous-culture steady state |

## Summary

- Total variables and parameters: **12**
- Controlled variable: **2**
- Dependent variable: **2**
- Derived quantity: **1**
- Independent variable: **3**
- Model parameter: **4**
- Confidence: high: 9, medium: 3

## Role and Type Overview

| Symbol | Canonical name | Author term | Role | Type | Unit | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| T | Culture temperature | temperature | Independent variable | Continuous | degrees Celsius | high |
| N_avail | Nitrogen availability | nitrogen availability | Independent variable | Categorical | Not reported | high |
| mu | Specific growth rate | specific growth rate | Dependent variable | Rate | per hour | high |
| mu_max | Maximum specific growth rate | maximum specific growth rate | Model parameter | Rate | per hour | high |
| K_s | Half-saturation constant for nitrogen | half-saturation constant for ammonium | Model parameter | Continuous | mM | high |
| S | Ammonium concentration | ammonium concentration | Independent variable | Continuous | mM | high |
| OD600 | Optical density at 600 nm | optical density at 600 nm | Derived quantity | Continuous | dimensionless absorbance units | high |
| DO | Dissolved oxygen concentration | dissolved oxygen concentration | Controlled variable | Continuous | percent saturation | high |
| D | Chemostat dilution rate | dilution rate | Controlled variable | Rate | per hour | high |
| K_capacity | Carrying capacity | carrying capacity | Model parameter | Continuous | Not reported | medium |
| Y | Biomass yield coefficient | yield coefficient | Model parameter | Constant | Not reported | medium |
| CDW | Cell dry weight | cell dry weight | Dependent variable | Continuous | Not reported | medium |

## Full Cross-Reference Table

### V001 — T: Culture temperature

| Attribute | Value |
| --- | --- |
| Author term | temperature |
| Aliases | None reported |
| Role | Independent variable |
| Type | Continuous |
| Definition | Temperature at which the culture was maintained. |
| Unit | degrees Celsius |
| Value or range | 25, 30, or 37 |
| Relationship | Hypothesized to increase the maximum specific growth rate. |
| Confidence | high |
| Notes | Treated as an experimental factor in this extraction. |

**Evidence:**
- `B0003` (methods): “*Escherichia coli* K-12 was grown in minimal medium. Ammonium chloride was the sole nitrogen source. The dilution rate was set to 0.2 per hour in chemostat cultures. Temperature was controlled at 25, 30, or 37 degrees Celsius.”

### V002 — N_avail: Nitrogen availability

| Attribute | Value |
| --- | --- |
| Author term | nitrogen availability |
| Aliases | nitrogen limitation, nitrogen-replete conditions |
| Role | Independent variable |
| Type | Categorical |
| Definition | Availability of nitrogen to the culture, operationalized through ammonium concentration and limitation state. |
| Unit | Not reported |
| Value or range | Limited versus replete; ammonium 0.1 to 10 mM |
| Relationship | Regulates the specific growth rate and the half-saturation constant. |
| Confidence | high |
| Notes | The paper combines a continuous concentration range with a limitation/replete classification. |

**Evidence:**
- `B0001` (abstract): “We investigated how nitrogen availability and temperature regulate the specific growth rate of *Escherichia coli* in continuous culture.”
- `B0001` (abstract): “We hypothesized that the maximum specific growth rate increases with temperature and that the half-saturation constant for nitrogen decreases under nitrogen limitation.”

### V003 — mu: Specific growth rate

| Attribute | Value |
| --- | --- |
| Author term | specific growth rate |
| Aliases | None reported |
| Role | Dependent variable |
| Type | Rate |
| Definition | Natural logarithm of optical density change per unit time. |
| Unit | per hour |
| Value or range | Not reported as a full range |
| Relationship | mu = d(ln OD600)/dt; modeled as a function of N_avail and T. |
| Confidence | high |
| Notes | The symbol mu follows the Monod convention used in the source. |

**Evidence:**
- `B0003` (methods): “Optical density at 600 nm was converted to cell dry weight using a calibration curve. The specific growth rate was calculated as the natural logarithm of optical density change per unit time.”

### V004 — mu_max: Maximum specific growth rate

| Attribute | Value |
| --- | --- |
| Author term | maximum specific growth rate |
| Aliases | maximum growth rate |
| Role | Model parameter |
| Type | Rate |
| Definition | Upper limit of the specific growth rate in the Monod model. |
| Unit | per hour |
| Value or range | 0.61 per hour at 30 degrees Celsius |
| Relationship | mu = mu_max S / (K_s + S); hypothesized to increase with T. |
| Confidence | high |
| Notes | Estimate is temperature-specific. |

**Evidence:**
- `B0004` (results): “At 30 degrees Celsius, the maximum specific growth rate was 0.61 per hour and the half-saturation constant for ammonium was 0.42 mM.”

### V005 — K_s: Half-saturation constant for nitrogen

| Attribute | Value |
| --- | --- |
| Author term | half-saturation constant for ammonium |
| Aliases | half-saturation constant |
| Role | Model parameter |
| Type | Continuous |
| Definition | Substrate concentration at which the specific growth rate is half of the maximum specific growth rate. |
| Unit | mM |
| Value or range | 0.42 mM at 30 degrees Celsius |
| Relationship | mu = mu_max S / (K_s + S); decreased under nitrogen limitation. |
| Confidence | high |
| Notes | The paper assumes this parameter is independent of temperature, although estimates varied. |

**Evidence:**
- `B0004` (results): “At 30 degrees Celsius, the maximum specific growth rate was 0.61 per hour and the half-saturation constant for ammonium was 0.42 mM.”

### V006 — S: Ammonium concentration

| Attribute | Value |
| --- | --- |
| Author term | ammonium concentration |
| Aliases | limiting substrate concentration, ammonium chloride concentration |
| Role | Independent variable |
| Type | Continuous |
| Definition | Concentration of the limiting nitrogen source in the medium. |
| Unit | mM |
| Value or range | 0.1 to 10 mM |
| Relationship | Input substrate concentration in the Monod equation. |
| Confidence | high |
| Notes | Distinguished from the broader nitrogen-availability variable V002. |

**Evidence:**
- `B0001` (abstract): “We hypothesized that the maximum specific growth rate increases with temperature and that the half-saturation constant for nitrogen decreases under nitrogen limitation.”

### V007 — OD600: Optical density at 600 nm

| Attribute | Value |
| --- | --- |
| Author term | optical density at 600 nm |
| Aliases | OD600 |
| Role | Derived quantity |
| Type | Continuous |
| Definition | Turbidity measurement used to estimate biomass and to calculate the specific growth rate. |
| Unit | dimensionless absorbance units |
| Value or range | Not reported |
| Relationship | Used to calculate mu and converted to cell dry weight using a calibration curve. |
| Confidence | high |
| Notes | Measurement variable rather than a modeled biological state. |

**Evidence:**
- `B0003` (methods): “Optical density at 600 nm was converted to cell dry weight using a calibration curve.”

### V008 — DO: Dissolved oxygen concentration

| Attribute | Value |
| --- | --- |
| Author term | dissolved oxygen concentration |
| Aliases | dissolved oxygen |
| Role | Controlled variable |
| Type | Continuous |
| Definition | Oxygen available in the culture medium, maintained above a threshold to avoid oxygen limitation. |
| Unit | percent saturation |
| Value or range | >30 percent saturation |
| Relationship | Held as a controlled condition. |
| Confidence | high |
| Notes | Controlled variable, not an experimental treatment. |

**Evidence:**
- `B0003` (methods): “Dissolved oxygen concentration was monitored continuously and maintained above 30 percent saturation.”

### V009 — D: Chemostat dilution rate

| Attribute | Value |
| --- | --- |
| Author term | dilution rate |
| Aliases | None reported |
| Role | Controlled variable |
| Type | Rate |
| Definition | Rate at which medium is diluted in the chemostat. |
| Unit | per hour |
| Value or range | 0.2 per hour |
| Relationship | Set as a controlled operating condition. |
| Confidence | high |
| Notes | Not reported as varying in this experiment. |

**Evidence:**
- `B0003` (methods): “The dilution rate was set to 0.2 per hour in chemostat cultures.”

### V010 — K_capacity: Carrying capacity

| Attribute | Value |
| --- | --- |
| Author term | carrying capacity |
| Aliases | None reported |
| Role | Model parameter |
| Type | Continuous |
| Definition | Maximum population or biomass level supported by the environment, estimated from the growth-curve plateau. |
| Unit | Not reported |
| Value or range | Not reported |
| Relationship | Estimated from the plateau of the growth curve. |
| Confidence | medium |
| Notes | The source does not state the unit or numerical value. |

**Evidence:**
- `B0004` (results): “The carrying capacity was estimated from the plateau of the growth curve.”

### V011 — Y: Biomass yield coefficient

| Attribute | Value |
| --- | --- |
| Author term | yield coefficient |
| Aliases | yield |
| Role | Model parameter |
| Type | Constant |
| Definition | Conversion of substrate into biomass, treated as constant during exponential growth. |
| Unit | Not reported |
| Value or range | Not reported |
| Relationship | Treated as a constant during exponential growth. |
| Confidence | medium |
| Notes | The source does not define the yield basis or unit. |

**Evidence:**
- `B0005` (discussion): “The yield coefficient was treated as a constant during exponential growth.”

### V012 — CDW: Cell dry weight

| Attribute | Value |
| --- | --- |
| Author term | cell dry weight |
| Aliases | None reported |
| Role | Dependent variable |
| Type | Continuous |
| Definition | Biomass concentration measured at the end of each experiment. |
| Unit | Not reported |
| Value or range | Not reported |
| Relationship | Calibrated against OD600. |
| Confidence | medium |
| Notes | The abstract mentions cell dry weight; the supplied methods chunk gives the calibration relationship but not the unit. |

**Evidence:**
- `B0003` (methods): “Optical density at 600 nm was converted to cell dry weight using a calibration curve.”

## Relationships

| ID | Type | From | To | Expression or claim | Evidence |
| --- | --- | --- | --- | --- | --- |
| R001 | equation | V006 | V003 | mu = mu_max * S / (K_s + S) | B0002 |
| R002 | directional | V001 | V004 | Increasing temperature is hypothesized to increase mu_max. | B0001 |
| R003 | directional | V002 | V005 | Nitrogen limitation decreases the half-saturation constant. | B0004 |

## Symbol Notes

No symbol collisions detected.

## Unresolved or Ambiguous Items

| Issue | Related variables | Evidence | Recommended action |
| --- | --- | --- | --- |
| The mechanism linking nitrogen availability to the half-saturation constant was not measured. | V002, V005 | B0006 | Treat the relationship as empirical and avoid adding an unmeasured intracellular intermediate. |
| The source assumes that the half-saturation constant is independent of temperature but reports variation across temperatures. | V001, V005 | B0005 | Record the assumption and the observed variation separately; do not encode temperature dependence as established. |

## Extraction Metadata

| Field | Value |
| --- | --- |
| Extracted at | 2026-09-28T00:00:00Z |
| Extractor | Example agent run |
| Coverage | Title, abstract, introduction, methods, results, discussion, and limitations of the supplied sample. |
| Method | Agent extraction from prepared chunks, followed by schema validation and deterministic rendering. |
| Warnings | The document is a synthetic teaching example rather than a publication.; Some units and values are not reported in the supplied text. |
