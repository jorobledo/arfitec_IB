# Recommended Workflow

This page describes the recommended sequence of operations for a typical Time-of-Flight (ToF) analysis.

---

# Step 1 – Load Experimental Data

Begin by loading one or several experimental datasets.

- Click **File → Load Files**.
- Select one or more CSV files. (use **Ctrl** for multiple files)
- Loaded datasets appear in the file list.

> **Tip:** Multiple datasets can be selected simultaneously for comparison.

---

# Step 2 – Select the Dataset(s)

Choose the dataset(s) you wish to analyze from the list.

- Single selection for individual analysis.
- Multiple selection for comparative plots. (use **Ctrl** for multiple files)

The selected datasets determine which spectra will be displayed.

---

# Step 3 – Visualize the Corrected Flux

Before performing any analysis, it is recommended to inspect the corrected neutron flux.

Two representations are available:

## ToF Flux

Displays the corrected neutron flux versus Time-of-Flight.


## Energy Flux

Displays the corrected neutron spectrum in the energy domain.

---

# Step 4 – Perform an Analysis

Select the desired analysis from the **Analysis** menu and press **OK**.

Typical analyses include:

- Grouping comparison
- Dead-time correction
- Detection efficiency
- Maxwellian comparison
- Reactor power comparison
- Cross-section calculations

Each analysis can be performed on one or several selected datasets.

---

# Step 5 – Perform a Fit (Optional)

If a physical model is required, choose one of the available fitting procedures.
(For this current version, it only fits the **first** data file selected)

---

# Step 7 – Inspect the Results

After each calculation, the software automatically displays:

- Numerical fit parameters
- Physical constants
- Statistical indicators
- Residual information (when available)

These values are also stored in the analysis history.

---

# Step 8 – Compare Multiple Measurements

Several datasets can be displayed simultaneously for most analyses.

Typical applications include:

- Different reactor powers
- Different detector configurations
- Different acquisition times
- Different samples

Comparative visualization helps identify systematic differences between experiments.

---

# Step 9 – Export the Results

Once satisfied with the analysis:

- Save the current figure.
- Export numerical results if required.
- Store figures for publication or reporting.

---

# Typical Analysis Sequence

A common workflow is:

1. Load experimental datasets.
2. Select one or several files.
3. Display the corrected ToF Flux.
4. Inspect the Energy Flux.
5. Run the desired analysis.
6. Perform a fit if required.
7. Display the fitted energy spectrum.
8. Save the figure and record the results.

---

# Notes

- Multiple datasets may be displayed simultaneously for most analyses.
- Fitting procedures are performed using the first selected dataset.
- Energy spectrum plots require previously computed fit parameters.
- Cross-section analyses require one or more reference datasets.
- The **Clear** button resets the current figure without unloading the datasets.