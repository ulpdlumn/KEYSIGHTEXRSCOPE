#import packages
import matplotlib.pyplot as plt
import numpy as np
import scipy
import serial
import pyvisa as visa
import socket
import time
import elliptec
import sys, os, time
import clr
from decimal import Decimal


clr.AddReference('C:\Program Files\Thorlabs\Elliptec\Thorlabs.Elliptec.ELLO_DLL.dll')

from Thorlabs.Elliptec.ELLO_DLL import *

print("Initializing and enabling device, this might take a couple seconds...")

# Connect to device,check Windows Device Manager to find out which COM port is used.
ELLDevicePort.Connect('COM1')

# Define byte address. 
min_address="0"
max_address="F"

# Build device list.
ellDevices=ELLDevices()
devices=ellDevices.ScanAddresses(min_address, max_address)

# Initialize device. 
for device in devices:
    if ellDevices.Configure(device):
        
        addressedDevice=ellDevices.AddressedDevice(device[0])

        deviceInfo=addressedDevice.DeviceInfo
        for stri in deviceInfo.Description():
            print(stri)

#have to convert characters of degrees to decimal
from decimal import Decimal
import clr # Assuming pythonnet is installed and clr is available

    # Example Python Decimal
py_decimal = Decimal('45.00')

    # Convert to string and then to System.Decimal
clr.AddReference("System") # Add reference to System assembly
from System import Decimal as NetDecimal # Alias to avoid name collision

net_decimal = NetDecimal.Parse(str(py_decimal))
print(net_decimal)
#correct IP address and network connection "GL-MT6000-bdc-5G" is required 
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
scope.write("CHAN2:DISP ON")
#setwaveform source for measurement
scope.write(":WAVeform:SOURce CHANnel8")
#setwaveform format
scope.write('waveform:format BYTE')
#scope.write('*rst')
#Set polarizer(s) at zero degrees or fast axis for each waveplate
ro.home()
#creating empty arrays for waveform data
waveform_data = []
polarization_angle = []
#Loop through each polarization state and record average waveform
for angle in [0, 90]:
    ro.set_angle(angle)
    # turn on scope averaging!
    scope.write('ACQuire:AVERage ON')
    # set the number of waves to be averaged
    scope.write('ACQuire:COUNt 4048')
    #saving averaged data
    waveform_data = scope.query_binary_values('waveform:data?',datatype='b')
    waveforms.append(waveform_data)
    #saving polarization angle for which measurement was taken
    polarization_angle = polarization_angle.append(angle)
    #set the scope to stop doing any actions to avoid crashes (time in ms)
    scope.timeout = 5000

    