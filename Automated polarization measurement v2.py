# -*- coding: utf-8 -*-

import socket
import time
import clr
import pyvisa as visa
import serial

#class to control EXR scope for collecting waveforms from detector 
import matplotlib.pyplot as plt
import numpy as np
import scipy
import serial
import pyvisa as visa
import socket
import time

class Oscilloscope:
    def __init__(self, ip_address='192.168.8.225', interface='hislip0'):
        """
        Initialize connection to the oscilloscope.
        """
        self.ip_address = ip_address
        self.interface = interface
        self.rm = visa.ResourceManager()
        self.scope = None

    def connect(self):
        """
        Connect to the oscilloscope via TCP/IP.
        """
        try:
            resource_str = f'TCPIP0::{self.ip_address}::{self.interface}::INSTR'
            self.scope = self.rm.open_resource(resource_str)
            print(f"Connected to scope at {self.ip_address}")
        except Exception as e:
            print("Failed to connect to scope:", e)

    def reset(self):
        """
        Reset the oscilloscope and wait until operation is complete.
        """
        if self.scope is None:
            print("Scope not connected. Call connect() first.")
            return
        try:
            self.scope.write('*RST')
            opc = self.scope.query('*OPC?')
            print("Scope reset complete:", opc)
        except Exception as e:
            print("Error during scope reset:", e)

    def write(self, command):
        """
        Send a command to the oscilloscope.
        """
        if self.scope:
            self.scope.write(command)
        else:
            print("Scope not connected.")

    def query(self, command):
        """
        Query the oscilloscope and return the response.
        """
        if self.scope:
            return self.scope.query(command)
        else:
            print("Scope not connected.")
            return None

    def close(self):
        """
        Close the connection to the scope.
        """
        if self.scope:
            self.scope.close()
            print("Scope connection closed.")

    def ScopeChannels(self, channel, state=True):
        if self.scope is None:
            print("scope not connected")
            return
        state_str = "ON" if state else "OFF"
        try:

            self.scope.write(f"CHAN{channel}:DISP {state_str}")
            self.scope.write(f"CHAN{channel}:INPut DC50")
        except Exception as e:
            print(f"Error setting channel {channel} display:", e)

    def trigger(self, channel_trig):
        self.scope.write(f"TRIGger:EDGE:SOUrce CHAN{channel_trig}")
    def triggerlevel(self, channel_trig, value):    
        self.scope.write(f"TRIGger:LEVel CHAN{channel_trig}, {value}")

    def acquire_waveform_binary(self, channel):
        """
        Acquire waveform from specified channel using binary transfer.
        Returns waveform in volts (numpy array).
        """
        self.scope.write(f":WAVeform:SOURce CHAN{channel}")
        self.scope.write(":WAVeform:FORMat BYTE")
        self.scope.write(":WAVeform:UNSigned 1")
        self.scope.write(":WAVeform:POINts:MODE RAW")
        self.scope.write(":WAVeform:POINts MAX")

        y_increment = float(self.scope.query(":WAVeform:YINCrement?"))
        y_origin    = float(self.scope.query(":WAVeform:YORigin?"))
        y_reference = float(self.scope.query(":WAVeform:YREFerence?"))

        raw = self.scope.query_binary_values(
            ":WAVeform:DATA?",
            datatype='B',
            container=np.array
        )

        waveform = (raw - y_reference) * y_increment + y_origin
        return waveform

# Add reference to the Thorlabs Elliptec DLL
clr.AddReference(r'C:\Program Files\Thorlabs\Elliptec\Thorlabs.Elliptec.ELLO_DLL.dll')
from Thorlabs.Elliptec.ELLO_DLL import *

# Add reference to .NET System library (for .NET Decimal)
clr.AddReference("System")
from System import Decimal as NetDecimal


class ElliptecController:
    def __init__(self, comport="COM4", min_address="0", max_address="f"):
        self.comport = comport
        self.min_address = min_address
        self.max_address = max_address
        self.ellDevices = ELLDevices()
        self.motors = {}

    def connect(self):
        print("Initializing and enabling device, this might take a couple seconds...")
        ELLDevicePort.Connect(self.comport)
        print(f"Connected to {self.comport}")

    def scan_and_configure(self):
        print("Scanning for devices...")
        devices = self.ellDevices.ScanAddresses(self.min_address, self.max_address)

        for device in devices:
            if self.ellDevices.Configure(device):
                addr = device[0]
                addressedDevice = self.ellDevices.AddressedDevice(addr)
                self.motors[addr] = addressedDevice

                deviceInfo = addressedDevice.DeviceInfo
                for line in deviceInfo.Description():
                    print(line)

        print(f"Found {len(self.motors)} motor(s).")

    def get_motor(self, address):
        if address not in self.motors:
            raise ValueError(f"Motor with address {address} not found.")
        return self.motors[address]

    def home_motor(self, motor):
        motor.Home(ELLBaseDevice.DeviceDirection.AntiClockwise)

    def move_motor_absolute(self, motor, angle_deg):
        net_angle = NetDecimal.Parse(str(angle_deg))
        motor.MoveAbsolute(net_angle)


class DualMotorController:
    def __init__(self, elliptec_controller, addr_A, addr_B):
        self.ctrl = elliptec_controller
        self.motor_A = self.ctrl.get_motor(addr_A)
        self.motor_B = self.ctrl.get_motor(addr_B)

    def home_both(self):
        print("Homing motors...")
        self.ctrl.home_motor(self.motor_A)
        self.ctrl.home_motor(self.motor_B)
        time.sleep(5)

    def move_both(self, angles_A, angles_B, delay=2):
        if len(angles_A) != len(angles_B):
            raise ValueError("angles_A and angles_B must have the same length.")

        for angA, angB in zip(angles_A, angles_B):
            print(f"Moving Motor A to {angA}°, Motor B to {angB}°")

            self.ctrl.move_motor_absolute(self.motor_A, angA)
            self.ctrl.move_motor_absolute(self.motor_B, angB)

            time.sleep(delay)

        print("Dual-motor rotation complete.")

# Main execution
if __name__ == "__main__":
    # Connect to EXR scope
    scope = Oscilloscope(ip_address='192.168.8.225')
    scope.connect()
    # Channel setup
    scope.ScopeChannels(7, True)
    scope.ScopeChannels(8, True)
    #trigger
    scope.trigger(7)
    scope.triggerlevel(7, 0.6)
    # Connecting to polarizer 
    elliptec_ctrl = ElliptecController(comport="COM4", min_address="0", max_address="f")
    elliptec_ctrl.connect()
    elliptec_ctrl.scan_and_configure()

    # Choose motor addresses
    dual_ctrl = DualMotorController(elliptec_ctrl, addr_A="1", addr_B="2")

    # Home both motors
    dual_ctrl.home_both()

    # rotation of polarizers
    start_angle_A = 0
    end_angle_A = start_angle_A + 5
    start_angle_B = start_angle_A+40
    end_angle_B = start_angle_B + 5

    #steps for rotation of polarizers
    step_A = 5
    step_B = step_A

    #creating list of angles for polarizers to rotate through
    angles_A = list(range(start_angle_A, end_angle_A + step_A, step_A))
    angles_B = list(range(start_angle_B, end_angle_B + step_B, step_B))

    # waveform data
    waveform_data = {}

    #plot Setup
    plt.ion()
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=1)
    ax.set_xlabel("Sample Index")
    ax.set_ylabel("Voltage (V)")
    ax.set_title("Live Waveform")
    plt.show()

    # Sweep through all angle combinations
    for angB in angles_B:
        for angA in angles_A:

            print(f"Motor A → {angA}°, Motor B → {angB}°")

            elliptec_ctrl.move_motor_absolute(dual_ctrl.motor_A, angA)
            elliptec_ctrl.move_motor_absolute(dual_ctrl.motor_B, angB)
            time.sleep(2)

            # Trigger & Acquire
            scope.write("*TRG")
            time.sleep(0.2)

            waveform = scope.acquire_waveform_binary(channel=7)
            waveform_data[(angA, angB)] = waveform

            print("Waveform acquired")
            line.set_data(np.arange(len(waveform)), waveform)
            ax.relim()
            ax.autoscale_view()
            ax.set_title(f"Waveform | A={angA}°  B={angB}°")
            fig.canvas.draw()
            fig.canvas.flush_events()

    print("Scan complete.")


