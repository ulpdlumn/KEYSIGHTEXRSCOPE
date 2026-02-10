import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import re

# ============================================================
# USER SETTINGS
# ============================================================

data_folder = r"C:\Users\colin\Documents\252026"
baseline_end = 0.5           # ps (pre-pulse region)
integrate_squared = False    # True if detector ~ |E|^2

# -------- polarization angle extraction --------
# Angle is taken from an underscore-separated field in filename
# Example: MoS2_SHG_60_power10.csv  → angle_field_index = 2
angle_field_index = 5
# ------------------------------------------------

# ============================================================
# LOAD CSV FILES
# ============================================================

csv_files = sorted(glob.glob(os.path.join(data_folder, "*.csv")))

if len(csv_files) == 0:
    raise RuntimeError(f"No CSV files found in {data_folder}")

# ============================================================
# STEP 1 + 2: INTERACTIVE SELECTION OF INTEGRATION WINDOW
# ============================================================

df0 = pd.read_csv(csv_files[0])
t0 = df0.iloc[:, 0].values
signal0 = df0.iloc[:, 2].values

baseline0 = np.mean(signal0[t0 < baseline_end])
signal0_corr = signal0 - baseline0

plt.figure(figsize=(7, 4))
plt.plot(t0, signal0_corr)
plt.xlabel("Time (ps)")
plt.ylabel("Signal (baseline subtracted)")
plt.title("Click START then END of SHG pulse")

points = plt.ginput(2)
plt.show()

t_start = min(p[0] for p in points)
t_end   = max(p[0] for p in points)

print(f"Integration window selected: {t_start:.3f} – {t_end:.3f} ps")

# ============================================================
# MAIN INTEGRATION LOOP
# ============================================================

angles = []
intensities = []

for fname in csv_files:

    basename = os.path.basename(fname)
    name_no_ext = os.path.splitext(basename)[0]
    parts = name_no_ext.split("_")

    if len(parts) <= angle_field_index:
        print(f"Skipping file (not enough fields): {basename}")
        continue

    try:
        angle = float(parts[angle_field_index])
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

    angles.append(angle)
    intensities.append(I)

# ============================================================
# POLARIZATION PLOT
# ============================================================

angles = np.array(angles)
intensities = np.array(intensities)

if len(intensities) == 0:
    raise RuntimeError("No intensities integrated")

order = np.argsort(angles)
angles = angles[order]
intensities = intensities[order]

intensities /= intensities.max()

theta = np.deg2rad(angles)

fig = plt.figure(figsize=(6, 6))
ax = fig.add_subplot(111, projection="polar")

ax.plot(theta, intensities, "o-", lw=2)
ax.set_theta_zero_location("E")
ax.set_theta_direction(-1)
ax.set_title("SHG Polarization – Monolayer MoS₂")

plt.show()
