# -*- coding: utf-8 -*-
# Import packages
import matplotlib
matplotlib.use('TkAgg')  # ensures plotting works interactively in Visual Studio
import matplotlib.pyplot as plt
import numpy as np
import serial
import pyvisa as visa
import socket
import time
import elliptec
import sys, os
import clr
from datetime import datetime

# ----------------------------------------
# Add reference to Thorlabs Elliptec DLL
# ----------------------------------------
clr.AddReference(r'C:\Program Files\Thorlabs\Elliptec\Thorlabs.Elliptec.ELLO_DLL.dll')
from Thorlabs.Elliptec.ELLO_DLL import *

# Add reference to .NET System library (for .NET Decimal)
clr.AddReference("System")
from System import Decimal as NetDecimal

# ----------------------------------------
# Initialization
# ----------------------------------------
print("Initializing and enabling device, this might take a couple seconds...")

ELLDevicePort.Connect('COM1')

# Scan and configure devices
ellDevices = ELLDevices()
devices = ellDevices.ScanAddresses("0", "F")

for device in devices:
    if ellDevices.Configure(device):
        addressedDevice = ellDevices.AddressedDevice(device[0])
        deviceInfo = addressedDevice.DeviceInfo
        for stri in deviceInfo.Description():
            print(stri)

# ----------------------------------------
# Polarization angle sweep configuration
# ----------------------------------------
angles = [0, 30, 45, 60, 90]  # degrees to test
save_folder = r"C:\Users\L136_L2\Documents\WaveformData"  # <-- change to your preferred folder
os.makedirs(save_folder, exist_ok=True)

# ----------------------------------------
# Home the device before rotation
# ----------------------------------------
print("Homing device...")
addressedDevice.Home(ELLBaseDevice.DeviceDirection.AntiClockwise)
time.sleep(5)

# ----------------------------------------
# Setup oscilloscope
# ----------------------------------------
rm = visa.ResourceManager()
scope = rm.open_resource('TCPIP0::192.168.8.226::hislip0::INSTR')

vRange = 1
tRange = 100E-9
trigLevel = 0.08
ch = 1      # trigger channel
Mch = 8     # measurement channel
avgCount = 1

scope.write(":CHANnel1:INPut DC50")
scope.write(":CHANnel8:INPut DC50")
scope.write(f'channel{Mch}:range {vRange}')
scope.write(f'timebase:range {tRange}')
scope.write(f'trigger:level channel{ch}, {trigLevel}')
scope.write("CHAN1:DISP ON")
scope.write("CHAN8:DISP ON")
scope.write(":WAVeform:SOURce CHANnel8")
scope.write('waveform:format BYTE')

# ----------------------------------------
# Data collection
# ----------------------------------------
plt.ion()
plt.figure(figsize=(8,5))

for angle in angles:
    net_angle = NetDecimal.Parse(str(angle))
    print(f"Moving to {angle} degrees...")
    addressedDevice.MoveAbsolute(net_angle)
    time.sleep(2)

    # Enable averaging
    scope.write('ACQuire:AVERage ON')
    scope.write(f'ACQuire:COUNt {avgCount}')

    # Acquire waveform
    wf = scope.query_binary_values('waveform:data?', datatype='b')
    wf = np.array(wf, dtype=np.float32)

    # Generate time axis (you can adjust sampling rate if known)
    dt = tRange / len(wf)
    time_axis = np.arange(len(wf)) * dt

    # Save to CSV file
    filename = os.path.join(save_folder, f"waveform_{angle}deg.csv")
    np.savetxt(filename, np.column_stack((time_axis, wf)), delimiter=',', header='Time(s),Amplitude', comments='')
    print(f"Saved waveform for {angle} deg to {filename}")

    # Plot live
    plt.clf()
    plt.plot(time_axis * 1e9, wf, label=f'{angle} deg')
    plt.xlabel('Time (ns)')
    plt.ylabel('Amplitude (a.u.)')
    plt.title('Waveform at Different Polarization Angles')
    plt.legend()
    plt.grid(True)
    plt.pause(0.5)

plt.ioff()
plt.show(block=True)

print("\nAll waveforms collected and saved successfully!")
