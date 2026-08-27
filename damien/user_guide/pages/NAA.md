# Neutron Activation Analysis (NAA)

This page describes the NAA tools available in the software.

---

# Required Files

For NAA analyses, use a file **tubo libre** you want to compare to a gamma spectra acquired with the Ge detector:

`element_date_N.dat`

* **element** : activated sample under study
* **date** : date of the measurement
* **N** : acquisition number during the experimental day

exemples : 
* `tl300626_1.dat` for **tubo libre** data file from 30/06/26

---

# NAA_1 – Flux Comparison



1. Load the time of flight data using `Load Files`.
2. Click on `Select Analysis` and then `NAA_1 – Flux Comparison`.

The software displays a summary table comparing neutron fluxes obtained using independent measurement techniques.

Displayed quantities:

* Thermal flux determined by Neutron Activation Analysis.
* Epithermal flux determined by Neutron Activation Analysis.
* Thermal flux obtained from integration of the ToF spectrum.
* Ratios between NAA and ToF flux estimates.

Purpose:

* Validate the neutron flux reconstruction obtained from the ToF experiment.
* Compare independent experimental methods.
* Identify possible systematic discrepancies between measurements.

Output displayed in `Results`:

* Thermal flux from NAA.
* Epithermal flux from NAA.
* Thermal flux from ToF integration.
* NAA / ToF ratios.

![](../image/NAA_1.png)

---

# NAA_2 – Gamma Spectrum

# Required Files

Use a gamma spectrum acquired with the Ge detector:

`element_ccd/scd_date_N.Spe`

* **element** : activated sample under study
* **ccd/scd** : ccd (with cadmium) / scd (without cadmium)
* **date** : date of the measurement
* **N** : acquisition number during the experimental day

Example:

* `mnccd160726_1.Spe`

---

1. Click on `Select Analysis` and then `NAA_2 – Gamma Spectrum`.
2. Select the .spe file

The software displays the gamma spectrum as a histogram of detected events.

Purpose:

* Visualize the measured gamma spectrum.
* Identify characteristic photopeaks.
* Inspect spectrum quality before isotope identification.

Output:

* Counts as a function of channel number.
* Histogram representation of the Ge detector spectrum.

![](../image/NAA_2.png)


