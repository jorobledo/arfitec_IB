# Plot Reference

This section describes the purpose of each available analysis and fitting routine implemented in the software.

All analyses are described according to their current implementation. Future versions may include additional processing options and fitting models.

---

# Flux Visualization

## ToF Flux

Displays the neutron flux as a function of **Time-of-Flight (ToF)**.

Several correction levels can be displayed:

* Raw data
* Background correction
* Dead-time correction
* All corrections

Different grouping methods are available:

* No grouping
* Method 1
* Method 2

Purpose:

* Verify measurement quality.
* Compare correction procedures.
* Study the influence of grouping on statistical fluctuations.
* Prepare data for spectrum analysis and fitting.

### Example on usage:

1. load file `cu250626_1_grp_grp.dat`.
2. Select the file by clicking it in the `Loaded Files` section.
3. Finally, in the `Flux` box on the left, press `ToF Flux` to see the ToF visualization of the flux.

---

## Energy Flux

Displays the corrected neutron flux converted into the energy domain.

The neutron energy is calculated from the Time-of-Flight measurement using the Jacobian.

Purpose:

* Visualize the neutron spectrum in energy space.
* Compare thermal and epithermal regions.
* Prepare spectrum modeling and cross-section calculations.

Display options:

* Flux(E)
* E × Flux(E)
* Log X
* Log Y

---

# Analysis Plots

## Plot 1 – Grouping Comparison

Compares spectra obtained using different grouping methods.

Purpose:

* Evaluate the influence of grouping on statistical fluctuations.
* Verify that grouping preserves the physical spectrum shape.


### Example on usage:
To test this feature, load file `example.txt`.  In the `Anaysis` box:

    - Select Analysis -> Time of Flight (ToF) Experiment -> 1. Grouping Comparison


---

## Plot 2 – Dead-Time Correction

Illustrates the effect of dead-time correction applied to measured neutron counts.

Purpose:

* Validate detector correction.
* Compare corrected and uncorrected spectra.

---

## Plot 3 – Detection Efficiency (Energy)

Displays detector efficiency as a function of neutron energy.

Purpose:

* Understand detector response.
* Validate efficiency corrections applied to the neutron flux.

---

## Plot 4 – Detection Efficiency (ToF)

Displays detector efficiency in the Time-of-Flight domain.

Purpose:

* Visual verification of detector response before energy conversion.

---

## Plot 5 – Maxwellian Comparison

Compares the experimental neutron spectrum with a set of ideal Maxwellian distributions.

Purpose:

* Evaluate thermal equilibrium.
* Estimate the neutron temperature range.
* Identify deviations from an ideal thermal spectrum.

---

## Plot 9 – Reactor Power Comparison

Compares neutron spectra recorded at different reactor powers.

Purpose:

* Evaluate reactor stability.
* Compare flux normalization between measurements.

---

## Plot 10 – Reactor Power vs Neutron Rate

Displays the relationship between reactor power and measured neutron rate.

Purpose:

* Verify detector linearity.
* Validate reactor operating conditions.

---

## Plot 11 – Cross Section

Computes neutron cross sections using one or several reference datasets.

Purpose:

* Determine reaction cross sections.
* Compare results with evaluated nuclear data.

---

# Fitting Procedures

## Plot 6 – Least-Square Maxwell Fit

Performs a least-square search of the Maxwellian parameters.

Output:

* Best-fit temperature
* Residual error

Purpose:

* Obtain an initial estimate of the neutron temperature.

---

## Plot 7.1 – Maxwellian Curve Fit

Performs a nonlinear fit assuming a pure Maxwellian neutron spectrum.

Output:

* Maxwellian temperature
* Amplitude
* Goodness of fit (R²)

---

## Plot 7.2 – Maxwellian + Epithermal Fit

Performs a nonlinear fit including both thermal and epithermal components.

Output:

* Maxwellian temperature
* Epithermal parameters
* Cutoff energy
* Goodness of fit (R²)

---

## Plot 8 – Energy Spectrum Modeling

Displays the reconstructed neutron spectrum in the energy domain using the parameters obtained from Plot 7.

Available display options:

* Flux(E)
* E × Flux(E)
* Maxwellian component
* Epithermal component
* Log X
* Log Y

Purpose:

* Compare measured and fitted spectra.
* Visualize thermal and epithermal contributions.
* Study the reconstructed neutron energy distribution.

---

# Recommended Workflow

1. Load one or several datasets.

2. Inspect the neutron flux in the Time-of-Flight domain.

3. Verify detector corrections and efficiency curves.

4. Perform Maxwellian comparison (Plot 5).

5. Execute the desired fitting procedure (Plot 6 or Plot 7).

6. Visualize the reconstructed energy spectrum using Plot 8.

7. Export the resulting figures if required.

---


# Neutron Activation Analysis (NAA)

## NAA_1 – Flux Comparison

Displays a summary table comparing neutron flux values obtained from different experimental methods.

The following quantities are reported:

* Thermal neutron flux measured by Neutron Activation Analysis (NAA).
* Epithermal neutron flux measured by Neutron Activation Analysis (NAA).
* Thermal neutron flux obtained from Time-of-Flight spectrum integration.
* Epithermal neutron flux obtained from Time-of-Flight spectrum integration.

Purpose:

* Compare independent flux determination methods.
* Validate the consistency between NAA measurements and ToF analysis.
* Quantify discrepancies between experimental techniques.

Typical use:

* Verification of neutron flux reconstruction.
* Validation of detector calibration and spectrum processing.
* Cross-check of experimental results before further analysis.
 
 ---

## NAA_2 – Gamma Spectrum

Displays a gamma-ray spectrum imported from a `.Spe` file.

The spectrum is shown as a histogram of counts versus channel number or calibrated energy.

Purpose:

* Visualize measured gamma spectra.
* Identify characteristic photopeaks.
* Evaluate spectrum quality before isotope identification.

Features:

* Automatic selection of `.Spe` files.
* Histogram display.
* Peak visualization.

---


# Shielding Analysis

## Shielding 1 – Transmission vs B₄C Concentration

Displays the neutron transmission as a function of neutron energy for samples containing different B₄C concentrations.

Additional reference materials may be displayed for comparison.

Purpose:

* Study the influence of B₄C concentration on neutron attenuation.
* Compare transmission behaviour between shielding materials.
* Evaluate the effectiveness of boron loading.

Typical use:

* Material characterization.
* Comparison of shielding performances.

---

## Shielding 2 – ToF Transmission

Displays neutron transmission in the Time-of-Flight domain for the different B₄C concentrations.

Purpose:

* Visualize attenuation directly in experimental coordinates.
* Identify spectral regions most affected by shielding.

---

## Shielding 3 – Peak Shift Analysis

Displays the evolution of transmission peak positions as a function of B₄C concentration.

Purpose:

* Study spectral modifications induced by neutron absorption.
* Quantify peak displacement with increasing boron content.
* Compare the behaviour of different sample compositions.


---

## Shielding 4 – Transmission vs B₄C Thickness

Displays the neutron transmission as a function of neutron energy for samples containing 25% B₄C and different thicknesses.

Additional reference materials may be displayed for comparison.

Purpose:

* Study the influence of sample thickness on neutron attenuation.
* Compare thickness effects with material-dependent effects.
* Evaluate shielding performance for a fixed composition.

Typical use:

* Optimization of shielding design.
* Thickness comparison studies.

---

## Shielding 5 – ToF Transmission (Thickness Series)

Displays neutron transmission in the Time-of-Flight domain for samples with different thicknesses and a fixed B₄C concentration of 25%.

Purpose:

* Compare thickness-dependent effects directly in ToF space.


# Notes

* Multiple datasets can be displayed simultaneously for most analyses.
* Fits are performed using the first selected dataset.
* Cross-section calculations require one or more reference datasets.
* Display options are updated automatically according to the selected plot.
