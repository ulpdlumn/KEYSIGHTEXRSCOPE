# -*- coding: utf-8 -*-

import time
import os
import numpy as np
import matplotlib.pyplot as plt
import pyvisa as visa
import clr
import random

# ============================================================
# Oscilloscope Class (Keysight EXR)
# ============================================================

class Oscilloscope:
    def __init__(self, resource):
        self.rm = visa.ResourceManager()
        self.scope = self.rm.open_resource(resource)
        self.scope.timeout = 60000
        self.initialize()

    def initialize(self):
        self.scope.write("*RST")
        self.scope.query("*OPC?")
        print("Oscilloscope initialized.")

    def enable_channel(self, channel):
        self.scope.write(f":CHAN{channel}:DISP ON")

    def disable_channel(self, channel):
        self.scope.write(f":CHAN{channel}:DISP OFF")

    def set_trigger_channel(self, channel):
        self.scope.write(f":TRIGger:EDGE:SOURce CHAN{channel}")

    def set_trigger_level(self, ch, level):
        self.scope.write(f":TRIGger:LEVEL CHAN{ch}, {level}")

    def set_averaging(self, count=256):
        print(f"Setting averaging to {count} waveforms...")
        self.scope.write(":ACQuire:TYPE AVERage")
        self.scope.write(f":ACQuire:COUNt {count}")
        self.scope.write(":ACQuire:AVERage ON")
        self.scope.query("*OPC?")
        print("Averaging enabled.")

    def trigger_single_blocking(self):
        self.scope.write(":SINGle")
        self.scope.query("*OPC?")

    def acquire_waveform_binary(self, channel):
        """Acquire waveform using 16-bit signed format for full resolution."""
        self.scope.write(f":WAVeform:SOURce CHAN{channel}")
        self.scope.write(":WAVeform:FORMat WORD")
        self.scope.write(":WAVeform:UNSigned 0")
        self.scope.write(":WAVeform:POINts:MODE RAW")
        self.scope.write(":WAVeform:POINts MAX")

        # Scaling parameters
        yinc = float(self.scope.query(":WAVeform:YINCrement?"))
        yorg = float(self.scope.query(":WAVeform:YORigin?"))
        yref = float(self.scope.query(":WAVeform:YREFerence?"))
        xinc = float(self.scope.query(":WAVeform:XINCrement?"))
        xorg = float(self.scope.query(":WAVeform:XORigin?"))

        raw = self.scope.query_binary_values(
            ":WAVeform:DATA?",
            datatype='h',      # signed 16-bit
            is_big_endian=True,
            container=np.array
        )

        voltage = (raw - yref) * yinc + yorg
        time_axis = xorg + np.arange(len(voltage)) * xinc

        return time_axis, voltage

    def set_channel_input_impedance(self, channel, impedance):
        if impedance in [50, '50']:
            self.scope.write(f":CHANnel{channel}:INPut DC50")
            print(f"Channel {channel} input impedance set to 50 Ω")
        elif impedance in ['1M', '1m', 1000000]:
            self.scope.write(f":CHANnel{channel}:INPut DC1M")
            print(f"Channel {channel} input impedance set to 1 MΩ")
        else:
            raise ValueError("Impedance must be 50 or '1M'")

    def invert_channel(self, channel, state):
        if state in ['ON', 1]:
            self.scope.write(f":CHANnel{channel}:INVert ON")
            print(f"Channel {channel} inversion: ON")
        elif state in ['OFF', 0]:
            self.scope.write(f":CHANnel{channel}:INVert OFF")
            print(f"Channel {channel} inversion: OFF")
        else:
            raise ValueError("state must be 'ON', 'OFF', 1, or 0")

# ============================================================
# Elliptec Motor Control
# ============================================================

clr.AddReference(r"C:\Program Files\Thorlabs\Elliptec\Thorlabs.Elliptec.ELLO_DLL.dll")
from Thorlabs.Elliptec.ELLO_DLL import *
clr.AddReference("System")
from System import Decimal as NetDecimal

class ElliptecController:
    def __init__(self, comport="COM4"):
        self.comport = comport
        self.devices = ELLDevices()
        self.motors = {}

    def connect(self):
        print("Connecting to Elliptec...")
        ELLDevicePort.Connect(self.comport)
        print("Connected.")

    def scan_and_configure(self):
        print("Scanning for motors...")
        found = self.devices.ScanAddresses("0", "3")
        for dev in found:
            if self.devices.Configure(dev):
                addr = dev[0]
                self.motors[addr] = self.devices.AddressedDevice(addr)
                print(f"Motor detected at address {addr}")
        if not self.motors:
            raise RuntimeError("No motors detected.")

    def move_motor_absolute(self, motor, angle_deg):
        motor.MoveAbsolute(NetDecimal.Parse(str(angle_deg)))
        

# ============================================================
# MAIN SCRIPT
# ============================================================

if __name__ == "__main__":

    plt.ion()
    fig, ax = plt.subplots()
    scatter = ax.scatter([], [])
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title("Live Waveform (Scatter)")

    # --------------------------------------------------------
    # Create output folder
    # --------------------------------------------------------
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_folder = rf"C:\Users\colin\Documents\Polarization_Measurements\Run_{timestamp}"
    os.makedirs(output_folder, exist_ok=True)
    print(f"Saving data to:\n{output_folder}")

    # --------------------------------------------------------
    # Connect Oscilloscope
    # --------------------------------------------------------
    scope = Oscilloscope("TCPIP0::192.168.8.225::hislip0::INSTR")
    scope.invert_channel(8, "ON")
    scope.disable_channel(1)
    scope.enable_channel(7)
    scope.enable_channel(8)
    scope.set_trigger_channel(7)
    scope.set_trigger_level(7, 0.4)
    scope.set_averaging(256)
    scope.set_channel_input_impedance(7, 50)
    scope.set_channel_input_impedance(8, 50)

    # --------------------------------------------------------
    # Connect Motors
    # --------------------------------------------------------
    elliptec = ElliptecController("COM4")
    elliptec.connect()
    elliptec.scan_and_configure()
    print("Detected motors:", elliptec.motors.keys())

    motor_C = elliptec.motors["0"]
    motor_A = elliptec.motors["1"]
    motor_B = elliptec.motors["2"]

    print("Homing motors...")
    motor_A.Home(ELLBaseDevice.DeviceDirection.AntiClockwise)
    motor_B.Home(ELLBaseDevice.DeviceDirection.AntiClockwise)
    time.sleep(5)

    # --------------------------------------------------------
    # Fixed Motor Angles
    #C = 1st 1064 HWP (laser power), B = 532 nm HWP (analyzer), A = 2nd 1064 nm HWP (polariation before surface)
    
    # --------------------------------------------------------
    fixed_angle_C = -11.039
    fixed_angle_B = 110
    fixed_angle_A = 65
    print(f"Setting Motor B to fixed angle: {fixed_angle_B}°")
    elliptec.move_motor_absolute(motor_B, fixed_angle_B)
    elliptec.move_motor_absolute(motor_C, fixed_angle_C)
    elliptec.move_motor_absolute(motor_A, fixed_angle_A)
    time.sleep(2.5)

    # --------------------------------------------------------
    # Measurement Angles (Motor A)
    # --------------------------------------------------------
    angles_A = np.arange(0, 180, 5)

    # --------------------------------------------------------
    # Acquisition Loop
    # --------------------------------------------------------
    for angA in angles_A:
        elliptec.move_motor_absolute(motor_A, angA)
        time.sleep(1.5)

        scope.trigger_single_blocking()
        t, v = scope.acquire_waveform_binary(8)  # channel 8

        # baseline removal
        baseline = np.mean(v[:50])
        v -= baseline

        # Save waveform
        filename = f"B_{fixed_angle_B}_A_{angA}.csv"
        filepath = os.path.join(output_folder, filename)
        np.savetxt(filepath, np.column_stack((t, v)), delimiter=",",
                   header="Time (s), Voltage (V)", comments="")

        # Update live scatter plot
        scatter.set_offsets(np.column_stack((t, v)))
        plt.xlim(0,80E-9)
        plt.ylim(0,0.5)
        ax.set_title(f"B={fixed_angle_B}°, A={angA}°")
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.01)

    # --------------------------------------------------------
    # Clean shutdown
    # --------------------------------------------------------
    try:
        scope.scope.close()
        scope.rm.close()
    except:
        pass

    try:
        ELLDevicePort.Disconnect()
    except:
        pass

    print("Measurement complete and shutdown finished.")