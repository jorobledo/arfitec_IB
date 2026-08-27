# Spectrum Fitting

This page explains how to fit neutron spectra using Maxwellian models.

---

# Required Files

Use a neutron acquisition dataset:

`element_date_N.dat` 

 * **element** : the name of a different element used 
 * **date** : date of the experiment
 * **N** : order of aquisition during the experimental day


exemples : 
* `tl300626_1.dat` for **tubo libre** data file from 30/06/26
* `cu300626_1.dat` for **copper** sample data file from 30/06/26
* `cu300626_1.grp.dat`  **grp** implies this file is a merging of different files to increase the statistique

Once loaded please select only `one` file for the fit


---

# Least-Square Maxwell Fit (Plot 6)

1. Load the desired file using `Load  Files` or `Load Folder`. (ex : `tl300626_1.dat`)
2. Select a file in the `Loaded Files` panel. (file name surrounded in green if selected)
3. Click on `Select fit` and then `6 – Least-Square Maxwell Fit`.

Output displayed in `Fit Results & Stats`:

* Best-fit temperature
* Residual error

This fit is useful as an initial estimate.

![](../image/plot6.png)

---

# Maxwellian Curve Fit (Plot 7.1)

1. Load the desired file using `Load  Files` or `Load Folder`. (ex : `tl300626_1.dat`)
2. Select a file in the `Loaded Files` panel. (file name surrounded in green if selected)
3. Click on `Select fit` and then `7.1 – Curve Fit Maxwell (ToF)`.

Output displayed in `Fit Results & Stats`:

* Temperature
* Amplitude
* R² coefficient

![](../image/plot7_1.png)

---

# Maxwellian + Epithermal Fit (Plot 7.2)

1. Load the desired file using `Load  Files` or `Load Folder`. (ex : `tl300626_1.dat`)
2. Select a file in the `Loaded Files` panel. (file name surrounded in green if selected)
3. Click on `Select fit` and then `7.2 – Curve Fit Maxwell (ToF + Epi)`.

Output displayed in `Fit Results & Stats`:

* Thermal component
* Epithermal component
* R² coefficient

![](../image/plot7_2.png)

---

# Energy Spectrum Modeling (Plot 8)


1. Load the desired file using `Load  Files` or `Load Folder`. (ex : `tl300626_1.dat`)
2. Select a file in the `Loaded Files` panel. (file name surrounded in green if selected)
3. Click on `Select fit` and then `8 – Energy Spectrum`.

Output displayed in `Fit Results & Stats`:

* Thermal component
* Epithermal component
* R² coefficient

Available options:

* Flux(E)
* E × Flux(E)
* Maxwellian fit
* ToF converted fit from plot 7
* ToF converted fit with epithermal contribution from plot 7
* Log X
* Log Y

![](../image/plot8.png)