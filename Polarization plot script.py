import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from glob import glob
from scipy.optimize import curve_fit


data_folder = "\colin\Documents\252026"       # folder with CSV files
file_pattern = "*.csv"     # file pattern
normalize_each = True      # normalize each scan before averaging

# MoS2 SHG model (D3h symmetry)
def mos2_shg(theta, A, theta0):
    return A * np.cos(3 * (theta - theta0))**2


# Load data
angles_all = []
intensities_all = []

csv_files = sorted(glob(f"{data_folder}/{file_pattern}"))

for file in csv_files:
    df = pd.read_csv(file)

    angle_deg = df.iloc[:, 0].values
    intensity = df.iloc[:, 1].values

    # Convert to radians
    theta = np.deg2rad(angle_deg)

    if normalize_each:
        intensity = intensity / intensity.max()

    angles_all.append(theta)
    intensities_all.append(intensity)

# Convert to arrays
angles_all = np.array(angles_all)
intensities_all = np.array(intensities_all)


