# -*- coding: utf-8 -*-

import time
import numpy as np
import matplotlib.pyplot as plt
import pyvisa as visa
import clr

# ============================================================
# Oscilloscope Class (Keysight EXR)
# ============================================================

class Oscilloscope:
    def __init__(self, resource):
        self.rm = visa.ResourceManager()
        self.scope = self.rm.open_resource(resource)
        self.scope.timeout = 20000
        self.initialize()

    def initialize(self):
        self.scope.write("*RST")
        self.scope.query("*OPC?")
        print("Oscilloscope initialized.")

    def enable_channel(self, channel):
        self.scope.write(f":CHAN{channel}:DISP ON")

    def set_trigger_channel(self, channel):
        self.scope.write(f":TRIGger:EDGE:SOURce CHAN{channel}")

    def set_trigger_level(self, level):
        self.scope.write(f":TRIGger:EDGE:LEVel {level}")

    def trigger_single(self):
        self.scope.write(":SINGle")

    def acquire_waveform_binary(self, channel):
        self.scope.write(f":WAVeform:SOURce CHAN{channel}")
        self.scope.write(":WAVeform:FORMat BYTE")
        self.scope.write(":WAVeform:UNSigned 1")
        self.scope.write(":WAVeform:POINts:MODE RAW")
        self.scope.write(":WAVeform:POINts MAX")

        yinc = float(self.scope.query(":WAVeform:YINCrement?"))
        yorg = float(self.scope.query(":WAVeform:YORigin?"))
        yref = float(self.scope.query(":WAVeform:YREFerence?"))

        xinc = float(self.scope.query(":WAVeform:XINCrement?"))
        xorg = float(self.scope.query(":WAVeform:XORigin?"))

        raw = self.scope.query_binary_values(
            ":WAVeform:DATA?",
            datatype="B",
            container=np.array
        )

        voltage = (raw - yref) * yinc + yorg
        time_axis = xorg + np.arange(len(voltage)) * xinc

        return time_axis, voltage


# ============================================================
# Elliptec Motor Control
# ============================================================

clr.AddReference(r"C:\Program Files\Thorlabs\Elliptec\Thorlabs.Elliptec.ELLO_DLL.dll")
from Thorlabs.Elliptec.ELLO_DLL import *

clr.AddReference("System")
from System import Decimal as NetDecimal


class ElliptecController:
    def __init__(self, comport="COM4", min_address="0", max_address="f"):
        self.comport = comport
        self.min_address = min_address
        self.max_address = max_address
        self.devices = ELLDevices()
        self.motors = {}

    def connect(self):
        print("Connecting to Elliptec...")
        ELLDevicePort.Connect(self.comport)
        print("Elliptec connected.")

    def scan_and_configure(self):
        print("Scanning for motors...")
        found = self.devices.ScanAddresses(self.min_address, self.max_address)

        for dev in found:
            if self.devices.Configure(dev):
                addr = dev[0]
                self.motors[addr] = self.devices.AddressedDevice(addr)
                print(f"Motor found at address {addr}")

        print("Detected motors:", self.motors.keys())

    def get_motor(self, addr):
        return self.motors[addr]

    def home_motor(self, motor):
        motor.Home(ELLBaseDevice.DeviceDirection.AntiClockwise)

    def move_motor_absolute(self, motor, angle_deg):
        motor.MoveAbsolute(NetDecimal.Parse(str(angle_deg)))


class DualMotorController:
    def __init__(self, ctrl, addr_A, addr_B):
        self.ctrl = ctrl
        self.motor_A = ctrl.get_motor(addr_A)
        self.motor_B = ctrl.get_motor(addr_B)

    def home_both(self):
        print("Homing motors...")
        self.ctrl.home_motor(self.motor_A)
        self.ctrl.home_motor(self.motor_B)
        time.sleep(5)


# ============================================================
# MAIN SCRIPT
# ============================================================

if __name__ == "__main__":

    # -------------------------------
    # Connect to Oscilloscope
    # -------------------------------
    scope = Oscilloscope("TCPIP0::192.168.8.225::hislip0::INSTR")

    scope.enable_channel(1)
    scope.enable_channel(8)

    scope.set_trigger_channel(1)
    scope.set_trigger_level(0.05)

    # -------------------------------
    # Connect to Elliptec
    # -------------------------------
    elliptec = ElliptecController(comport="COM4")
    elliptec.connect()
    elliptec.scan_and_configure()

    dual = DualMotorController(elliptec, addr_A="1", addr_B="2")
    dual.home_both()

    # -------------------------------
    # Measurement Angles
    # -------------------------------
    angles_A = np.arange(0, 181, 30)
    angles_B = np.arange(0, 181, 30)

    # -------------------------------
    # Storage
    # -------------------------------
    waveforms = {}
    integrals = {}

    # -------------------------------
    # Live Plot
    # -------------------------------
    plt.ion()
    fig, ax = plt.subplots()
    line, = ax.plot([], [])
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Voltage (V)")

    # -------------------------------
    # Acquisition Loop
    # -------------------------------
    for angB in angles_B:
        for angA in angles_A:

            print(f"\nMoving motors → A={angA}°, B={angB}°")

            elliptec.move_motor_absolute(dual.motor_A, angA)
            elliptec.move_motor_absolute(dual.motor_B, angB)
            time.sleep(2)

            scope.trigger_single()
            time.sleep(0.2)

            t, v = scope.acquire_waveform_binary(channel=8)

            baseline = np.mean(v[:50])
            v -= baseline

            integral = np.trapz(v, t)

            waveforms[(angA, angB)] = v
            integrals[(angA, angB)] = integral

            print(f"Integrated signal: {integral:.3e} V·s")

            line.set_data(t, v)
            ax.relim()
            ax.autoscale_view()
            ax.set_title(f"A={angA}°  B={angB}°  ∫Vdt={integral:.3e}")
            fig.canvas.draw()
            fig.canvas.flush_events()

    plt.ioff()
    plt.show()

    print("\nMeasurement complete.")
