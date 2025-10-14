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

angles = [45]  # You can change or expand this list
print("Homing device...")
addressedDevice.Home(ELLBaseDevice.DeviceDirection.AntiClockwise)
time.sleep(5)
#correct IP address and network connection "GL-MT6000-bdc-5G" or "Wifi pro_557544" is required 
rm = visa.ResourceManager()
scope = rm.open_resource('TCPIP0::192.168.8.226::hislip0::INSTR')
#setting up scope display and channels
vRange = 1
#nanoseconds
tRange = 100E-9
trigLevel = 0.08
#trigger
ch = 1
#measurement channel
Mch = 8
avgCount = 1
#setting impedance of channel
scope.write(":CHANnel1:INPut DC50")
scope.write(":CHANnel8:INPut DC50")
#setup up vertical and horizontal ranges
scope.write(f'channel{Mch}:range{vRange}')
scope.write(f'timebase:range{tRange}')
#trigger
scope.write(f'trigger:level channel{ch}, {trigLevel}')
#enabling a channel using the DISP command
scope.write("CHAN1:DISP ON")
scope.write("CHAN8:DISP ON")
#setwaveform source for measurement
scope.write(":WAVeform:SOURce CHANnel8")
#setwaveform format
scope.write('waveform:format BYTE')
#scope.write('*rst')
#creating empty arrays for waveform data
waveform_data = []
polarization_angle = []
angles = [45]  # You can change or expand this list
print("Homing device...")
addressedDevice.Home(ELLBaseDevice.DeviceDirection.AntiClockwise)
time.sleep(5)
#Loop through each polarization state and record average waveform
for angle in angles:
    # Convert to .NET Decimal
    net_angle = NetDecimal.Parse(str(angle))
    print(f"Moving to {angle} degrees...")
    addressedDevice.MoveAbsolute(net_angle)
    time.sleep(2)
    # turn on scope averaging!
    scope.write('ACQuire:AVERage ON')
    # set the number of waves to be averaged
    scope.write('ACQuire:COUNt 1')
    #saving averaged data
    waveform_data = scope.query_binary_values('waveform:data?',datatype='b')

plt.figure(1)
plt.plot(waveform_data)
input("Press Enter to close...")
    
    

    