# Analysis Plots

This page describes the available analysis plots and how to generate them.

---

# Required Files

Use a neutron acquisition dataset:

`element_date_N.dat`

* **element** : the name of the material or experimental configuration
* **date** : date of the experiment
* **N** : acquisition number during the experimental day

Examples:

* `tl300626_1.dat` for **tubo libre** data acquired on 30/06/26
* `cu300626_1.dat` for a **copper** sample acquired on 30/06/26
* `cu300626_1.grp.dat` where **grp** indicates a merged dataset created from several acquisitions to improve statistics

For most analyses, one or several files may be selected simultaneously.

---

# Grouping Comparison (Plot 1)

1. Load the desired file using `Load Files` or `Load Folder`. (ex: `tl300626_1.dat`)
2. Select a file in the `Loaded Files` panel. (file name surrounded in green if selected)
3. Click on `Select Analysis` and then `1 – Grouping Comparison`.

Purpose:

* Compare different grouping methods.
* Evaluate the influence of grouping on statistical fluctuations.
* Verify that grouping preserves the physical shape of the spectrum.

Output:

* Spectrum without grouping.
* Spectrum grouped using Method 1.
* Spectrum grouped using Method 2.

![](../image/plot1.png)

---

# Dead-Time Correction (Plot 2)

1. Load the desired file using `Load Files` or `Load Folder`. (ex: `tl300626_1.dat`)
2. Select a file in the `Loaded Files` panel. (file name surrounded in green if selected)
3. Click on `Select Analysis` and then `2 – Dead-Time Correction`.

Purpose:

* Visualize the effect of dead-time correction.
* Compare corrected and uncorrected count rates.
* Validate the detector correction procedure.

Output:

* Raw spectrum.
* Dead-time corrected spectrum.

![](../image/plot2.png)

---

# Detection Efficiency vs Energy (Plot 3)

1. Load the desired file using `Load Files` or `Load Folder`. (ex: `tl300626_1.dat`)
2. Select a file in the `Loaded Files` panel. (file name surrounded in green if selected)
3. Click on `Select Analysis` and then `3 – Detection Efficiency (Energy)`.

Purpose:

* Display the detector efficiency as a function of neutron energy.
* Understand the detector response.
* Validate efficiency corrections applied to the neutron flux.

Output:

* Detection efficiency curve in the energy domain.

![](../image/plot3.png)

---

# Detection Efficiency vs ToF (Plot 4)

1. Load the desired file using `Load Files` or `Load Folder`. (ex: `tl300626_1.dat`)
2. Select a file in the `Loaded Files` panel. (file name surrounded in green if selected)
3. Click on `Select Analysis` and then `4 – Detection Efficiency (ToF)`.

Purpose:

* Display the detector efficiency directly in the Time-of-Flight domain.
* Visualize detector response before energy conversion.

Output:

* Detection efficiency curve as a function of Time-of-Flight.

![](../image/plot4.png)

---

# Maxwellian Comparison (Plot 5)

1. Load the desired file using `Load Files` or `Load Folder`. (ex: `tl300626_1.dat`)
2. Select a file in the `Loaded Files` panel. (file name surrounded in green if selected)
3. Click on `Select Analysis` and then `5 – Maxwellian Comparison`.

Purpose:

* Compare the measured spectrum with theoretical Maxwellian distributions.
* Estimate the thermal neutron temperature range.
* Identify deviations from an ideal thermal spectrum.

Output:

* Experimental spectrum.
* Family of Maxwellian distributions.

![](../image/plot5.png)

---

# Reactor Power Comparison (Plot 9)

# Required Files

Use several acquisitions recorded at different reactor powers.

Example:

* `tl300626_1.dat`
* `tl300626_2.dat`
* `tl300626_3.dat`

Each file should correspond to a different reactor power level.

---

1. Load the desired files using `Load Files` or `Load Folder`.
2. Select all files to compare in the `Loaded Files` panel.
3. Click on `Select Analysis` and then `9 – Reactor Power Comparison`.

Purpose:

* Compare spectra recorded at different reactor powers.
* Evaluate reactor stability.
* Verify flux normalization.

Output:

* One spectrum per reactor power level.

![](../image/plot9.png)

---

# Reactor Power vs Neutron Rate (Plot 10)

# Required Files

Use several acquisitions recorded at different reactor powers.

Example:

* `tl300626_1.dat`
* `tl300626_2.dat`
* `tl300626_3.dat`

Each file should correspond to a different reactor power level.

---

1. Load the desired files using `Load Files` or `Load Folder`.
2. Select all files to compare in the `Loaded Files` panel.
3. Click on `Select Analysis` and then `10 – Reactor Power vs Neutron Rate`.

Purpose:

* Study the relationship between reactor power and neutron count rate.
* Verify detector linearity.
* Validate operating conditions during measurements.

Output:

* Reactor power versus neutron rate correlation.

![](../image/plot10.png)
