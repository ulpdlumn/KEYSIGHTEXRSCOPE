
#import packages
import matplotlib.pyplot as plt
import numpy as np
import scipy
import serial
import pyvisa as visa
import socket

#delay generator paramters end my nme
target_ip = "192.168.8.150"  # Replace with the actual IP address
target_port = 5024           # Replace with the actual port number (e.g., 80 for HTTP)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((target_ip, target_port))
#set the trigger to be external or internal 
s.send(b"tsrc 0\n")
#set the trigger rate 
s.send(b"trat 50\n")
#control of each of the channels for the scope
#The channels start range from 2 to 9 and A to H respectively 
#channel A controls ....

#Establing connection to scope
rm = visa.ResourceManager()
scope = rm.open_resource('TCPIP0::192.168.8.226::hislip0::INSTR')
vRange = 1
#nanoseconds
tRange = 100E-9
trigLevel = 0.08
#trigger
ch = 1
#measurement channel
Mch = 8
avgCount = 1
#scope.write('*rst')
scope.query('*opc?')
#number of iterations
num_iteration = 3
#setting impedance of channel
scope.write(":CHANnel1:INPut DC1M")
scope.write(":CHANnel8:INPut DC1M")
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
#creating waveform to send to stepper motors
scope.write(":OUTPut:LOAD 50") # Set output impedance to 50 ohms
scope.write(":FUNCtion:SHAPe PULSE") # Select pulse waveform
scope.write(":PULSe:WIDTh 100E-6") # Set pulse width to 100 microseconds
scope.write(":VOLTage 2") # Set pulse amplitude to 2Vpeak
scope.write(":FREQuency 1000") # Set pulse frequency to 1 kHz
#enable and trigger output
scope.write("OUTPut ON")
waveforms = []
for i in range(num_iteration): 
    #data collection options
    scope.write(":ACQuire:COUNt 1")
    scope.write('acq:aver ON')
    scope.write('wav:VIEW ALL')
    scope.write('digitize')
    scope.timeout = 50000
    waveform_data = scope.query_binary_values('waveform:data?',datatype='b')
    waveforms.append(waveform_data)
    plt.plot(waveform_data, label=f'Acquisition {i+1}') # Using raw data for simplicity; scale with preamble for actual voltage/time
    plt.xlabel('Sample Index')
    plt.ylabel('Raw Data Value')
    plt.title('Oscilloscope Waveforms')
    plt.legend()
    plt.grid(True)
    plt.pause(0.1) # Pause to allow plot to update
    scope.write_ascii_values("WLISt:WAVeform:DATA somename,", waveform_data)
    scope.write("SOURce1:FUNCtion ARB") # Set function to arbitrary
    #scope.write(f"SOURce1:FUNCtion:ARBitrary:SRATe {num_points * frequency}") # Set sample rate
    #send out waveform to stepper motors

    if i == num_iteration:
     break
plt.show() # Display the final plot after all acquisitions
     

