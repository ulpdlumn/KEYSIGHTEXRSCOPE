#Example tested for ELL18
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
        
# Call move methods.
addressedDevice.Home(ELLBaseDevice.DeviceDirection.AntiClockwise)
addressedDevice.MoveAbsolute(net_decimal)
        