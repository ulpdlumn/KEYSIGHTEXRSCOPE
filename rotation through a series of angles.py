# -*- coding: utf-8 -*-
# Import packages
import matplotlib.pyplot as plt
import numpy as np
import serial
import pyvisa as visa
import socket
import time
import elliptec
import sys, os
import clr

# Add reference to the Thorlabs Elliptec DLL
clr.AddReference(r'C:\Program Files\Thorlabs\Elliptec\Thorlabs.Elliptec.ELLO_DLL.dll')
from Thorlabs.Elliptec.ELLO_DLL import *

# Add reference to .NET System library (for .NET Decimal)
clr.AddReference("System")
from System import Decimal as NetDecimal

print("Initializing and enabling device, this might take a couple seconds...")

# Connect to device (adjust COM port as needed)
ELLDevicePort.Connect('COM1')

# Define byte address range
min_address = "0"
max_address = "F"

# Build and configure device list
ellDevices = ELLDevices()
devices = ellDevices.ScanAddresses(min_address, max_address)

for device in devices:
    if ellDevices.Configure(device):
        addressedDevice = ellDevices.AddressedDevice(device[0])
        deviceInfo = addressedDevice.DeviceInfo
        for stri in deviceInfo.Description():
            print(stri)

# ----------------------------------------
# Rotate through specific polarization angles
# ----------------------------------------

angles = [45, 55, 76, 80 ,99]  # You can change or expand this list
print("Homing device...")
addressedDevice.Home(ELLBaseDevice.DeviceDirection.AntiClockwise)
time.sleep(5)

for angle in angles:
    # Convert to .NET Decimal
    net_angle = NetDecimal.Parse(str(angle))

    print(f"Moving to {angle} degrees...")
    addressedDevice.MoveAbsolute(net_angle)
    time.sleep(2)

print("Rotation sequence complete.")

