#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [
    path
    for path in sys.path
    if Path(path or ".").resolve() not in {SCRIPT_DIR, Path.cwd().resolve()}
]

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

NEUTRON_MASS_KG = 1.67492749804e-27
MEV_TO_J = 1.602176634e-13
PLANCK_CONSTANT = 6.62607015e-34


def default_input_path() -> Path:
    test_dir = Path(__file__).resolve().parent / "test_dir"
    preferred = test_dir / "myoutput.mcpl.gz"
    if preferred.exists():
        return preferred
    matches = sorted(test_dir.glob("myoutput*.mcpl.gz"))
    if matches:
        return matches[0]
    return preferred


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect neutron phase-space variables stored in an MCPL file."
    )
    default_input = default_input_path()
    parser.add_argument(
        "--input",
        type=Path,
        default=default_input,
        help=f"MCPL file to inspect (default: {default_input})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output PNG path for the phase-space summary figure.",
    )
    parser.add_argument(
        "--max-particles",
        type=int,
        default=0,
        help="Maximum number of particles to read (0 means all particles).",
    )
    parser.add_argument(
        "--lognorm-2d",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use LogNorm color scaling for 2D histograms (default: enabled).",
    )
    return parser


def find_mcpltool() -> str:
    candidates = [
        shutil.which("mcpltool"),
        "/Users/robledo/repos/kdsource_install/bin/mcpltool",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise FileNotFoundError(
        "Could not find 'mcpltool'. Add it to PATH or update inspect.py with its location."
    )


def stream_mcpl_ascii(mcpltool: str, input_path: Path, max_particles: int) -> dict[str, np.ndarray]:
    command = [mcpltool, "-n", f"-l{max_particles if max_particles > 0 else 0}", str(input_path)]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    data: dict[str, list[float]] = {
        "index": [],
        "pdgcode": [],
        "ekin_mev": [],
        "x_cm": [],
        "y_cm": [],
        "z_cm": [],
        "ux": [],
        "uy": [],
        "uz": [],
        "time_ms": [],
        "weight": [],
    }

    assert process.stdout is not None
    for raw_line in process.stdout:
        line = raw_line.strip()
        if (
            not line
            or line.startswith("#")
            or line.startswith("Opened MCPL file")
            or line.startswith("index")
        ):
            continue

        parts = line.split()
        if len(parts) < 11:
            continue

        data["index"].append(int(parts[0]))
        data["pdgcode"].append(int(parts[1]))
        data["ekin_mev"].append(float(parts[2]))
        data["x_cm"].append(float(parts[3]))
        data["y_cm"].append(float(parts[4]))
        data["z_cm"].append(float(parts[5]))
        data["ux"].append(float(parts[6]))
        data["uy"].append(float(parts[7]))
        data["uz"].append(float(parts[8]))
        data["time_ms"].append(float(parts[9]))
        data["weight"].append(float(parts[10]))

    stderr_text = process.stderr.read() if process.stderr is not None else ""
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"mcpltool failed with exit code {return_code}:\n{stderr_text}")

    arrays: dict[str, np.ndarray] = {}
    for key, values in data.items():
        if key in {"index", "pdgcode"}:
            arrays[key] = np.asarray(values, dtype=int)
        else:
            arrays[key] = np.asarray(values, dtype=float)
    return arrays


def derive_phase_space(data: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    ekin_mev = data["ekin_mev"]
    energy_joule = ekin_mev * MEV_TO_J

    speed_ms = np.sqrt(np.clip(2.0 * energy_joule / NEUTRON_MASS_KG, 0.0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        wavelength_angstrom = (PLANCK_CONSTANT / (NEUTRON_MASS_KG * speed_ms)) * 1.0e10

    theta_x_mrad = np.degrees(np.arctan2(data["ux"], data["uz"])) * (1000.0 / 57.29577951308232)
    theta_y_mrad = np.degrees(np.arctan2(data["uy"], data["uz"])) * (1000.0 / 57.29577951308232)
    r_cm = np.hypot(data["x_cm"], data["y_cm"])

    derived = dict(data)
    derived["energy_mev"] = ekin_mev
    derived["energy_mev_nonzero"] = ekin_mev[ekin_mev > 0.0]
    derived["speed_ms"] = speed_ms
    derived["wavelength_angstrom"] = wavelength_angstrom
    derived["theta_x_mrad"] = theta_x_mrad
    derived["theta_y_mrad"] = theta_y_mrad
    derived["r_cm"] = r_cm
    return derived


def weighted_quantiles(values: np.ndarray, weights: np.ndarray, quantiles: tuple[float, ...]) -> list[float]:
    if len(values) == 0:
        return [math.nan for _ in quantiles]
    order = np.argsort(values)
    sorted_values = values[order]
    sorted_weights = weights[order]
    cumulative = np.cumsum(sorted_weights)
    if cumulative[-1] == 0:
        return [math.nan for _ in quantiles]
    cumulative /= cumulative[-1]
    return [float(np.interp(q, cumulative, sorted_values)) for q in quantiles]


def print_summary(data: dict[str, np.ndarray]) -> None:
    weights = data["weight"]
    total_weight = float(np.sum(weights))
    count = len(data["index"])

    energy_q = weighted_quantiles(data["energy_mev"], weights, (0.05, 0.5, 0.95))
    time_q = weighted_quantiles(data["time_ms"], weights, (0.05, 0.5, 0.95))
    z_q = weighted_quantiles(data["z_cm"], weights, (0.05, 0.5, 0.95))
    radius_q = weighted_quantiles(data["r_cm"], weights, (0.5, 0.95))
    unique_z = np.unique(data["z_cm"])

    print(f"Particles loaded      : {count}")
    print(f"Particle type(s)      : {np.unique(data['pdgcode']).tolist()}")
    print(f"Total statistical wt. : {total_weight:.6g}")
    print(
        "Energy [MeV]          : "
        f"min={np.min(data['energy_mev']):.6g}, "
        f"p05={energy_q[0]:.6g}, median={energy_q[1]:.6g}, "
        f"p95={energy_q[2]:.6g}, max={np.max(data['energy_mev']):.6g}"
    )
    print(
        "Time [ms]             : "
        f"min={np.min(data['time_ms']):.6g}, "
        f"p05={time_q[0]:.6g}, median={time_q[1]:.6g}, "
        f"p95={time_q[2]:.6g}, max={np.max(data['time_ms']):.6g}"
    )
    print(
        "z [cm]                : "
        f"min={np.min(data['z_cm']):.6g}, "
        f"p05={z_q[0]:.6g}, median={z_q[1]:.6g}, "
        f"p95={z_q[2]:.6g}, max={np.max(data['z_cm']):.6g}"
    )
    if len(unique_z) <= 10:
        z_values = ", ".join(f"{value:.6g}" for value in unique_z)
        print(f"Unique z values [cm]  : {len(unique_z)} ({z_values})")
    else:
        print(f"Unique z values [cm]  : {len(unique_z)}")
    print(
        "Radius r=sqrt(x^2+y^2): "
        f"median={radius_q[0]:.6g} cm, p95={radius_q[1]:.6g} cm"
    )
    print(
        "Theta_x [mrad]        : "
        f"mean={np.average(data['theta_x_mrad'], weights=weights):.6g}, "
        f"std={np.sqrt(np.average((data['theta_x_mrad'] - np.average(data['theta_x_mrad'], weights=weights)) ** 2, weights=weights)):.6g}"
    )
    print(
        "Theta_y [mrad]        : "
        f"mean={np.average(data['theta_y_mrad'], weights=weights):.6g}, "
        f"std={np.sqrt(np.average((data['theta_y_mrad'] - np.average(data['theta_y_mrad'], weights=weights)) ** 2, weights=weights)):.6g}"
    )
    print(
        "Wavelength [A]        : "
        f"min={np.nanmin(data['wavelength_angstrom']):.6g}, "
        f"median={np.nanmedian(data['wavelength_angstrom']):.6g}, "
        f"max={np.nanmax(data['wavelength_angstrom']):.6g}"
    )


def make_plots(data: dict[str, np.ndarray], output_path: Path, use_lognorm_2d: bool) -> None:
    weights = data["weight"]
    total_weight = float(np.sum(weights))
    energy_mev_nonzero = data["energy_mev_nonzero"]
    positive_time = data["time_ms"][data["time_ms"] > 0.0]
    positive_time_weights = weights[data["time_ms"] > 0.0]
    low_divergence_mask = (
        (np.abs(data["theta_x_mrad"]) < 100.0)
        & (np.abs(data["theta_y_mrad"]) < 100.0)
    )
    high_divergence_mask = ~low_divergence_mask
    small_radius_mask = data["r_cm"] < 2.0
    large_radius_mask = ~small_radius_mask
    low_divergence_energy_mask = low_divergence_mask & (data["energy_mev"] > 0.0)
    high_divergence_energy_mask = high_divergence_mask & (data["energy_mev"] > 0.0)
    small_radius_energy_mask = small_radius_mask & (data["energy_mev"] > 0.0)
    large_radius_energy_mask = large_radius_mask & (data["energy_mev"] > 0.0)
    low_divergence_time_mask = low_divergence_mask & (data["time_ms"] > 0.0)
    high_divergence_time_mask = high_divergence_mask & (data["time_ms"] > 0.0)
    hist2d_kwargs = {"norm": LogNorm()} if use_lognorm_2d else {}

    fig, axes = plt.subplots(2, 4, figsize=(18, 9), constrained_layout=True)

    axes[0, 0].hist2d(
        data["x_cm"],
        data["y_cm"],
        bins=150,
        weights=weights,
        cmap="viridis",
        **hist2d_kwargs,
    )
    axes[0, 0].set_title("Spatial footprint")
    axes[0, 0].set_xlabel("x [cm]")
    axes[0, 0].set_ylabel("y [cm]")

    axes[0, 1].hist2d(
        data["theta_x_mrad"],
        data["theta_y_mrad"],
        bins=150,
        weights=weights,
        cmap="plasma",
        **hist2d_kwargs,
    )
    axes[0, 1].set_title("Angular phase space")
    axes[0, 1].set_xlabel(r"$\theta_x$ [mrad]")
    axes[0, 1].set_ylabel(r"$\theta_y$ [mrad]")

    axes[0, 2].hist2d(
        data["x_cm"],
        data["theta_x_mrad"],
        bins=150,
        weights=weights,
        cmap="magma",
        **hist2d_kwargs,
    )
    axes[0, 2].set_title("Horizontal phase space")
    axes[0, 2].set_xlabel("x [cm]")
    axes[0, 2].set_ylabel(r"$\theta_x$ [mrad]")

    if len(energy_mev_nonzero) > 0:
        energy_bins = np.logspace(
            np.log10(np.min(energy_mev_nonzero)),
            np.log10(np.max(energy_mev_nonzero)),
            120,
        )
        axes[1, 0].hist(
            energy_mev_nonzero,
            bins=energy_bins,
            weights=weights[data["energy_mev"] > 0.0],
            histtype="stepfilled",
            alpha=0.35,
            color="0.75",
            label="all neutrons",
        )
        if np.any(small_radius_energy_mask):
            axes[1, 0].hist(
                data["energy_mev"][small_radius_energy_mask],
                bins=energy_bins,
                weights=weights[small_radius_energy_mask],
                histtype="step",
                linewidth=1.5,
                color="tab:green",
                label=r"$r < 5$ cm",
            )
        if np.any(large_radius_energy_mask):
            axes[1, 0].hist(
                data["energy_mev"][large_radius_energy_mask],
                bins=energy_bins,
                weights=weights[large_radius_energy_mask],
                histtype="step",
                linewidth=1.5,
                color="tab:red",
                label=r"$r \geq 5$ cm",
            )
        axes[1, 0].set_xscale("log")
        axes[1, 0].set_yscale("log")
        axes[1, 0].legend()
    axes[1, 0].set_title("Energy by radius")
    axes[1, 0].set_xlabel("Ekin [MeV]")
    axes[1, 0].set_ylabel("Weighted counts")

    axes[0, 3].hist2d(
        data["y_cm"],
        data["theta_y_mrad"],
        bins=150,
        weights=weights,
        cmap="cividis",
        **hist2d_kwargs,
    )
    axes[0, 3].set_title("Vertical phase space")
    axes[0, 3].set_xlabel("y [cm]")
    axes[0, 3].set_ylabel(r"$\theta_y$ [mrad]")

    if len(energy_mev_nonzero) > 0:
        axes[1, 1].hist(
            energy_mev_nonzero,
            bins=energy_bins,
            weights=weights[data["energy_mev"] > 0.0],
            histtype="stepfilled",
            alpha=0.35,
            color="0.75",
            label="all neutrons",
        )
        if np.any(low_divergence_energy_mask):
            axes[1, 1].hist(
                data["energy_mev"][low_divergence_energy_mask],
                bins=energy_bins,
                weights=weights[low_divergence_energy_mask],
                histtype="step",
                linewidth=1.5,
                color="tab:blue",
                label=r"$|\theta_x|, |\theta_y| < 100$ mrad",
            )
        if np.any(high_divergence_energy_mask):
            axes[1, 1].hist(
                data["energy_mev"][high_divergence_energy_mask],
                bins=energy_bins,
                weights=weights[high_divergence_energy_mask],
                histtype="step",
                linewidth=1.5,
                color="tab:orange",
                label="remaining neutrons",
            )
        axes[1, 1].set_xscale("log")
        axes[1, 1].set_yscale("log")
        axes[1, 1].legend()
    axes[1, 1].set_title("Energy spectrum")
    axes[1, 1].set_xlabel("Ekin [MeV]")
    axes[1, 1].set_ylabel("Weighted counts")

    if len(positive_time) > 0:
        time_bins = np.logspace(np.log10(np.min(positive_time)), np.log10(np.max(positive_time)), 120)
        axes[1, 2].hist(
            positive_time,
            bins=time_bins,
            weights=positive_time_weights,
            histtype="stepfilled",
            alpha=0.85,
            color="0.8",
            label="all neutrons",
        )
        if np.any(low_divergence_time_mask):
            axes[1, 2].hist(
                data["time_ms"][low_divergence_time_mask],
                bins=time_bins,
                weights=weights[low_divergence_time_mask],
                histtype="step",
                linewidth=1.5,
                color="tab:blue",
                label=r"$|\theta_x|, |\theta_y| < 100$ mrad",
            )
        if np.any(high_divergence_time_mask):
            axes[1, 2].hist(
                data["time_ms"][high_divergence_time_mask],
                bins=time_bins,
                weights=weights[high_divergence_time_mask],
                histtype="step",
                linewidth=1.5,
                color="tab:orange",
                label="remaining neutrons",
            )
        axes[1, 2].set_xscale("log")
        axes[1, 2].set_yscale("log")
        axes[1, 2].legend()
    axes[1, 2].set_title("Time-of-flight distribution")
    axes[1, 2].set_xlabel("time [ms]")
    axes[1, 2].set_ylabel("Weighted counts")

    axes[1, 3].hist(data["z_cm"], bins=120, weights=weights, histtype="stepfilled", alpha=0.85)
    axes[1, 3].set_title("z distribution")
    axes[1, 3].set_xlabel("z [cm]")
    axes[1, 3].set_ylabel("Weighted counts")

    fig.suptitle(
        f"Neutron phase-space inspection (total statistical weight = {total_weight:.3e})",
        fontsize=16,
    )
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> int:
    args = build_parser().parse_args()
    input_path = args.input.resolve()
    if not input_path.exists():
        print(f"Input file does not exist: {input_path}", file=sys.stderr)
        return 1

    output_path = args.output.resolve() if args.output else input_path.with_name("myoutput_phase_space.png")
    mcpltool = find_mcpltool()

    data = stream_mcpl_ascii(mcpltool, input_path, args.max_particles)
    if len(data["index"]) == 0:
        print("No particles were read from the MCPL file.", file=sys.stderr)
        return 1

    phase_space = derive_phase_space(data)
    print_summary(phase_space)
    make_plots(phase_space, output_path, use_lognorm_2d=args.lognorm_2d)
    print(f"\nSaved figure           : {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
