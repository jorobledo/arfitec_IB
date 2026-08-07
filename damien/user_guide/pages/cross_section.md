# Cross Section Calculation (Plot 11)

This page explains how to compute neutron cross sections using transmission measurements.

---

# Required Files

A cross-section calculation always requires:

* One **tubo libre** file (`tl`)
* One sample file

File naming convention:

`element_date_N.dat`

Examples:

* `tl300626_1.dat` for the reference (**tubo libre**) measurement
* `cu300626_1.dat` for a **copper** sample
* `zf091224_1_grp` for a **saphire** sample **grouped** with other data files

Optional reference datasets may also be loaded for comparison:

* `sigtot-zafiro-FCantargi.dat` for the **saphire**
* `Cu_txs_ncrystal.dat` for the **copper**

---

# Loading the Data

1. Load the desired files using `Load Files` or `Load Folder`.
2. Select first the `tl` file.
3. Select the `sample` file immediately after.

Example:

1. `tl300626_1.dat`
2. `cu300626_1.dat`

The order is important because the software uses the first selected file as the transmission reference.

---

# Generating the Cross Section

1. Click on `Select Analysis`.
2. Select `11 – Cross Section`.

The software computes the transmission:

$$
T(E)=\frac{I(E)}{I_0(E)}
$$

where:

* $I_0(E)$ is the neutron spectrum measured with the **tubo libre** configuration.
* $I(E)$ is the neutron spectrum measured with the **sample**.

The transmission is then converted into a microscopic cross section using the material parameters defined by the user.

---

# Physical Parameters

Material properties can be modified in the `Physical Parameters` menu.

Available parameters include:

* Sample thickness
* Atomic mass

These parameters are used during the conversion from transmission to cross section.

The cross section must be reloaded to see the changes 

---

# Amplification Factor

An amplification slider is available to improve visual comparison between experimental and reference curves.

Purpose:

* Enhance weak resonance structures.
* Facilitate comparison with evaluated nuclear data.
* Improve visual fitting of experimental results.

The amplification factor only affects the display and does not modify the underlying calculation.

---

# Grouping Options

The experimental data can be displayed using different grouping methods.

Available options:

* Method 1
* Method 2

Grouping reduces statistical fluctuations and improves readability.

---

# Method 2 Grouping Factor

When using `Method 2`, the grouping level can be adjusted using the dedicated slider.

A larger grouping factor:

* Reduces statistical noise.
* Produces a smoother cross-section curve.

A smaller grouping factor:

* Preserves spectral resolution.
* Reveals fine resonance structures.

The optimal value depends on the sample and the available statistics.

---

# Typical Workflow

1. Load a `tl` reference file.
2. Load the sample file.
3. Adjust the material properties in `Physical Parameters` if necessary.
4. Select first the `tl` file, then the sample file.
5. Open `11 – Cross Section`.
6. Load one or more reference datasets for validation.
7. Select the desired grouping method.
8. Adjust the Method 2 grouping factor if required.
9. Use the amplification slider to improve comparison.

Output:

* Experimental neutron cross section.
* Optional reference cross sections.
* Comparison between evaluated and experimental data.

![](../image/plot11.png)

