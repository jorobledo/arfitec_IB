# Neutron Flux Visualization

This page explains how to display neutron flux data in both the Time-of-Flight and Energy domains.

---

# Required Files

Use one or more neutron acquisition files that are name as follow:


`element_date_N.dat` 

 * **element** : the name of a different element used 
 * **date** : date of the experiment
 * **N** : order of aquisition during the experimental day

exemples : 
* `tl300626_1.dat` for **tubo libre** data file from 30/06/26
* `cu300626_1.dat` for **copper** sample data file from 30/06/26
* `cu300626_1.grp.dat`  **grp** implies this file is a merging of different files to increase the statistique


---

# Displaying the ToF Flux

1. Load the desired file using `Load  Files` or `Load Folder`. (ex : `tl300626_1.dat`)
2. Select one or multiple files in the `Loaded Files` panel using the `Ctrl` key. (file name surrounded in green if selected)
3. In the `Flux` section, click `ToF Flux`.

The software will display the neutron flux as a function of Time-of-Flight.

Available options:

* Raw
* Background Correction
* Dead-Time Correction
* Efficiency Correction
* All Corrections
* No Grouping
* Method 1 Grouping
* Method 2 Grouping
* Log X
* Log Y

![](../image/ToF_Flux.png)

---

# Displaying the Energy Flux

1. Load and select a dataset.
2. In the `Flux` section, click `Energy Flux`.

The software converts the Time-of-Flight spectrum into neutron energy and displays the reconstructed flux.

Available options:

* Flux(E)
* E × Flux(E)
* Log X
* Log Y

![](../image/energy_flux.png)

---

# Typical Workflow

For most analyses:

1. Display the ToF Flux.
2. Verify corrections and grouping.
3. Switch to Energy Flux.
4. Continue with fitting or cross-section calculations.
