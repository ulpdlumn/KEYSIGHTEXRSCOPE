#import packages
import matplotlib.pyplot as plt
import numpy as np
import scipy
import serial
import pyvisa as visa
import socket
import time
import elliptec

#Connect to motorized rotation mount through usb com port
controller_1 = elliptec.Controller('COM6')
# the name of the mount(s) will be 
ro_1 = elliptec.Rotator(controller)
ro_1.change_address("1")
ro_1.save_user_data()
#Connect to scope through local network. Please note the 
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
    # turn on scope averaging
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

    