# serial_stresstest

Got new hardware, something that shows up as a serial device and talks to another serial device?

Want to know how much data you can send over the link, or how fast it can be sent, or both?

This tool takes the minimum and maximum speeds, as well as min and max packet lengths, and does CRC-based transmission testing over two or more serial devices.

Script assumes that all of the given serial devices are in the same bus. It tests TX and RX of each device on each speed and packet length to determine combination that works for all devices in the network.

## Usage

1. Change the serial device paths to match your devices and set the limits according to your hardware.

2. Run the script:
`python run.py`
