# Plot Reference

This section describes the purpose of each available analysis and fitting routine implemented in the software.
All analyses are described according to their current implementation in the software. Future versions may include additional processing options.

---

# Flux Visualization

## ToF Flux

Displays the corrected neutron flux as a function of **Time-of-Flight (ToF)**.

This plot includes all detector and acquisition corrections and represents the primary experimental neutron spectrum.

Typical use:
- Verify the quality of the measurement.
- Compare different acquisitions.
- Prepare data for fitting procedures.

---

## Energy Flux

Displays the corrected neutron flux converted into the energy domain.

The plotted quantity is:

`Flux(E) × E`

This representation is commonly used for neutron spectrum analysis and allows direct comparison with theoretical Maxwellian distributions.

Typical use:
- Compare spectra in energy space.
- Visualize thermal and epithermal regions.
- Prepare cross-section calculations.

---

# Analysis Plots

## Plot 1 – Grouping Comparison

Compares spectra obtained using different grouping factors.

Purpose:
- Evaluate the influence of binning on statistical fluctuations.
- Check that grouping does not alter the physical spectrum.

---

## Plot 2 – Dead-Time Correction

Illustrates the effect of dead-time correction applied to the measured neutron counts.

Purpose:
- Validate detector correction.
- Compare corrected and uncorrected data.

---

## Plot 3 – Detection Efficiency (Energy)

Displays detector efficiency as a function of neutron energy.

Purpose:
- Understand detector response.
- Validate efficiency correction.

---

## Plot 4 – Detection Efficiency (ToF)

Displays detector efficiency directly in the Time-of-Flight domain.

Purpose:
- Visual verification before energy conversion.

---

## Plot 5 – Maxwellian Comparison

Compares the experimental neutron spectrum with a range of ideal Maxwellian distributions with increments of 5K.

Purpose:
- Evaluate thermal equilibrium.
- Estimate spectral deviations.

---

## Plot 9 – Reactor Power Comparison

Compares neutron spectra recorded at different reactor powers.

Purpose:
- Evaluate reactor stability.
- Compare flux normalization.

---

## Plot 10 – Reactor Power vs Neutron Rate

Displays the relationship between reactor power and measured neutron rate.

Purpose:
- Verify detector linearity.
- Validate reactor operating conditions.

---

## Plot 11 – Cross Section

Computes the neutron cross section using one or several reference datasets.

Purpose:
- Determine reaction cross sections.
- Compare with evaluated nuclear data.

---

# Fitting Procedures

## Plot 6 – Least-Square Maxwell Fit

Performs a grid-search least-square adjustment of a Maxwellian spectrum.

Output:
- Best-fit temperature
- Residual error

Typical use:
- Initial estimation of neutron temperature.

---

## Plot 7.1 – Maxwellian Curve Fit

Performs a nonlinear fit assuming a pure Maxwellian neutron spectrum.

Output:
- Maxwellian temperature
- Amplitude
- Goodness of fit (R²)

---

## Plot 7.2 – Maxwellian + Epithermal Fit

Fits the spectrum using a Maxwellian component together with an epithermal contribution.

Output:
- Maxwellian temperature
- Epithermal parameters
- Cutoff energy
- Goodness of fit (R²)

---

## Plot 8.1 – Energy Spectrum

Converts the fitted Maxwellian model into the energy domain.

Requirement:
- Plot 7.1 must be executed first.

Purpose:
- Compare measured and fitted energy spectra.

---

## Plot 8.2 – Energy Spectrum with Epithermal Component

Displays the fitted Maxwellian + epithermal model in the energy domain.

Requirement:
- Plot 7.2 must be executed first.

Purpose:
- Visualize the contribution of thermal and epithermal neutrons.

---

# Recommended Workflow

1. Load one or several datasets.

2. Display the corrected neutron flux.

3. Select the desired analysis.

4. If required, perform one of the fitting procedures.

5. Export the resulting figure.

---

# Notes

- Multiple datasets can be displayed simultaneously for most analyses.
- Fits are performed using the first selected dataset.
- Plots 8.1 and 8.2 require the results obtained from Plot 7.
- Cross-section calculations require reference datasets.    