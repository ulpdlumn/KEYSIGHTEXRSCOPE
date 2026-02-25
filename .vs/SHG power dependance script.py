import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import re
from scipy.optimize import curve_fit

data_folder = r"C:\Users\colin\Documents\2252026v2"
baseline_end = 0.5e-12           # ps (pre-pulse region)
integrate_squared = False    # True if detector ~ |E|^2
power_field_index = 3


csv_files = sorted(glob.glob(os.path.join(data_folder, "*.csv")))

if len(csv_files) == 0:
    raise RuntimeError(f"No CSV files found in {data_folder}")

df0 = pd.read_csv(csv_files[0])
t0 = df0.iloc[:, 0].values
signal0 = df0.iloc[:, 2].values

baseline0 = np.mean(signal0[t0 < baseline_end])
signal0_corr = signal0 - baseline0

plt.figure(figsize=(7, 4))
plt.plot(t0, signal0_corr)
plt.xlim(0,50E-9)
plt.xlabel("Time (ps)")
plt.ylabel("Signal (baseline subtracted)")
plt.title("Click START then END of SHG pulse")

points = plt.ginput(2)
plt.show()

t_start = min(p[0] for p in points)
t_end   = max(p[0] for p in points)

print(f"Integration window selected: {t_start:.3f} – {t_end:.3f} ps")

powers = []
intensities = []

for fname in csv_files:

    basename = os.path.basename(fname)
    name_no_ext = os.path.splitext(basename)[0]
    parts = name_no_ext.split("_")

    if len(parts) <= power_field_index:
        print(f"Skipping file (not enough fields): {basename}")
        continue

    try:
        power = float(parts[power_field_index])
    except ValueError:
        print(f"Skipping file (angle not numeric): {basename}")
        continue

    # --- load waveform ---
    df = pd.read_csv(fname)
    t = df.iloc[:, 0].values
    signal = df.iloc[:, 2].values

    # --- baseline subtraction ---
    baseline = np.mean(signal[t < baseline_end])
    signal_corr = signal - baseline

    # --- integration window ---
    mask = (t > t_start) & (t < t_end)
    if not np.any(mask):
        print(f"WARNING: empty window for {basename}")
        continue

    if integrate_squared:
        I = np.trapezoid(signal_corr[mask]**2, t[mask])
    else:
        I = np.trapezoid(signal_corr[mask], t[mask])

    powers.append(power)
    intensities.append(I)


powers = np.array(powers)
intensities = np.array(intensities)

if len(intensities) == 0:
    raise RuntimeError("No intensities integrated")

order = np.argsort(powers)
powers = powers[order]
intensities = intensities[order]

intensities /= intensities.max()

def quad_model(x, A, B):
    return A + B * x**2

# Fit to A + Bx^2
popt, pcov = curve_fit(quad_model, powers, intensities)

A_fit, B_fit = popt
print(f"Fit parameters:")
print(f"A = {A_fit:.5f}")
print(f"B = {B_fit:.5f}")

fig = plt.figure(figsize=(6, 5))
ax = fig.add_subplot(111)

# Scatter data
ax.scatter(powers, intensities, s=60, label="Data")

# Smooth curve for fit
x_fit = np.linspace(min(powers), max(powers), 500)
y_fit = quad_model(x_fit, A_fit, B_fit)

ax.plot(x_fit, y_fit, 'r-', lw=2, label="Fit: A + Bx²")

ax.set_xlabel("Power [uw]")
ax.set_ylabel("Normalized SHG Intensity [a.u]")
ax.set_title("SHG Power Dependence")
ax.legend()
ax.grid(True)

plt.tight_layout()
plt.show()
