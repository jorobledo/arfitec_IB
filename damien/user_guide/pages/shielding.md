# Shielding Analysis

This page describes the shielding characterization tools available in the software.

---

# Shielding 1 – Transmission vs B₄C Concentration

# Required Files

`x%_sbc_date_element.dat` or `element_sbc_date_N.dat` (for **tl** / **bg** / **cd**)

* **x** : concentration of the sample
* **sbc** : silicone boron carbide
* **date** : date of the experiment
* **element** : name of the reference material
* **N** : acquisition number during the experimental day

Examples:

* `tl_sbc230726.dat` for **tubo libre** data acquired on 23/07/26
* `cd_sbc230726_2.dat` for **cadmium** data acquired on 23/07/26
* `bg_sbc230726_1.dat` for **background** data acquired on 23/07/26
* `10%_sbc230726.dat` for a **10% B₄C** sample acquired on 23/07/26

comparisson files may also be loaded:

* `0%_sbc230726_silicone.dat` for a **pure silicone** sample acquired on 23/07/26
* `25%_sbc230726_elb.dat` for a hypothetic **25%** concentrated  **elastobore** sample


---

1. Load all concentration datasets using `Load Files` or `Load Folder`.
2. Select the desired concentration files in the `Loaded Files` panel.
3. Click on `Select Analysis` and then `Shielding 1 – Transmission vs B₄C Concentration`.

The software computes and displays neutron transmission in the energy domain.

Purpose:

* Study the effect of B₄C concentration on neutron attenuation.
* Compare different sample compositions.
* Evaluate the shielding efficiency of boron-loaded materials.

Output:

* Transmission as a function of neutron energy.
* Comparison between several concentrations.
* Optional comparison with reference materials.

An optional Beer–Lambert model,

$$ T(E)=exp(-Σ(E)x) $$

can be displayed to compare theoretical and experimental neutron transmission.

![](../image/shielding_1.png)

---

# Shielding 2 – ToF Transmission

# Required Files

Use the same files as for Shielding 1.

Examples:

* `0%_sbc230726_silicone.dat`
* `5%_sbc230726.dat`
* `10%_sbc230726.dat`
* `25%_sbc230726.dat`

---

1. Load all concentration datasets using `Load Files` or `Load Folder`.
2. Select the desired concentration files in the `Loaded Files` panel.
3. Click on `Select Analysis` and then `Shielding 2 – ToF Transmission`.

The software displays neutron transmission directly in the Time-of-Flight domain.

Purpose:

* Visualize attenuation in experimental coordinates.
* Compare concentration effects before energy conversion.
* Identify spectral regions most affected by absorption.

Output:

* Transmission as a function of Time-of-Flight.

![](../image/shielding_2.png)

---

# Shielding 3 – Peak Shift Analysis

# Required Files

Use the same concentration datasets as for Shielding 1.

Examples:

* `0%_sbc230726_silicone.dat`
* `5%_sbc230726.dat`
* `10%_sbc230726.dat`
* `25%_sbc230726.dat`

---

1. Load all concentration datasets using `Load Files` or `Load Folder`.
2. Select the desired concentration files in the `Loaded Files` panel.
3. Click on `Select Analysis` and then `Shielding 3 – Peak Shift Analysis`.

The software determines the position of the transmission maxima and studies their evolution with increasing B₄C concentration.

Purpose:

* Quantify spectral shifts induced by neutron absorption.
* Study the evolution of transmission peaks.
* Compare concentration-dependent spectral modifications.

Output:

* Peak positions.
* Peak position evolution as a function of B₄C concentration.

![](../image/shielding_3.png)

---

# Shielding 4 – Transmission vs B₄C Thickness

# Required Files

`thicknessmm_sbc_date_element.dat` or  `element_sbc_date_N.dat` (for **tl** / **bg** / **cd**)

* **thickness** : sample thickness in millimeters
* **sbc** : silicone boron carbide
* **date** : date of the experiment
* **element** : name of the reference material
* **N** : acquisition number during the experimental day

Examples:

* `5mm_sbc270726.dat`
* `10mm_sbc270726.dat`
* `tl_sbc270726_9.dat`

comparisson files may also be loaded:

* `4.5mm_sbc270726_elb.dat` for a **4.5 mm** thick **elastobore** sample
* `1mm_sbc270726_cd.dat` for a **1 mm** thick **cadmium** sample

---

1. Load all concentration datasets using `Load Files` or `Load Folder`.
2. Select the desired concentration files in the `Loaded Files` panel.
3. Click on `Select Analysis` and then `Shielding 4 – Transmission vs B₄C Thickness`.

The software computes and displays neutron transmission in the energy domain.

Purpose:

* Study the influence of sample thickness on attenuation.
* Compare shielding performance for a fixed B₄C concentration.
* Evaluate thickness-dependent transmission effects.

Output:

* Transmission as a function of neutron energy.
* Comparison between different sample thicknesses.
* Optional comparison with reference materials.

An optional Beer–Lambert model,

$$ T(E)=exp(-Σ(E)x) $$

can be displayed to compare theoretical and experimental neutron transmission.

![](../image/shielding_4.png)

---

# Shielding 5 – ToF Transmission (Thickness Series)

# Required Files

Use the same files as for Shielding 4.

Examples:

* `5mm_sbc270726.dat`
* `10mm_sbc270726.dat`
* `tl_sbc270726_9.dat`

---

1. Load all concentration datasets using `Load Files` or `Load Folder`.
2. Select the desired concentration files in the `Loaded Files` panel.
3. Click on `Select Analysis` and then `Shielding 5 – ToF Transmission`.

The software displays neutron transmission directly in the Time-of-Flight domain.

Purpose:

* Visualize thickness-dependent attenuation before energy conversion.
* Compare transmission behaviour for different sample thicknesses.
* Support interpretation of the corresponding energy-domain spectra.

Output:

* Transmission as a function of Time-of-Flight.

![](../image/shielding_5.png)

