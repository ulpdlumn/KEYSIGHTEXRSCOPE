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

# Connect to device
ELLDevicePort.Connect('COM4')

# Define byte address range
min_address = "0"
max_address = "f"

# Build and configure device list
ellDevices = ELLDevices()
devices = ellDevices.ScanAddresses(min_address, max_address)

# Store motors here
motors = {}

for device in devices:
    if ellDevices.Configure(device):
        addr = device[0]
        addressedDevice = ellDevices.AddressedDevice(addr)
        motors[addr] = addressedDevice

        deviceInfo = addressedDevice.DeviceInfo
        for stri in deviceInfo.Description():
            print(stri)

# -------------------------------------------------
# Choose the two motor addresses you want to control
# -------------------------------------------------
motor_A = motors["0"]   # first motor
motor_B = motors["1"]   # second motor

# ----------------------------------------
# Home both motors (simultaneously)
# ----------------------------------------
print("Homing motors...")
motor_A.Home(ELLBaseDevice.DeviceDirection.AntiClockwise)
motor_B.Home(ELLBaseDevice.DeviceDirection.AntiClockwise)
time.sleep(5)

# ----------------------------------------
# Rotate both motors together
# ----------------------------------------
angles_A = [45]   # motor A angles
angles_B = [90]   # motor B angles (can be different)

for angA, angB in zip(angles_A, angles_B):
    netA = NetDecimal.Parse(str(angA))
    netB = NetDecimal.Parse(str(angB))


    # Send both move commands before waiting
    motor_A.MoveAbsolute(netA)
    motor_B.MoveAbsolute(netB)

    time.sleep(2)

print("Dual-motor rotation complete.")
        
