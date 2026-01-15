# -*- coding: utf-8 -*-

import time
import clr

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


# =========================
# Main execution
# =========================
if __name__ == "__main__":
    # Create controller and connect
    elliptec_ctrl = ElliptecController(comport="COM4", min_address="0", max_address="f")
    elliptec_ctrl.connect()
    elliptec_ctrl.scan_and_configure()

    # Choose motor addresses
    dual_ctrl = DualMotorController(elliptec_ctrl, addr_A="1", addr_B="2")

    # Home both motors
    dual_ctrl.home_both()

    # Define angles
    angles_A = [45]
    angles_B = [90]

    # Move both motors
    dual_ctrl.move_both(angles_A, angles_B, delay=2)



