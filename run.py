"""
Serial testing template

Author: Heikki Juva
Email: heikki@juva.lu
"""

import serial
import string
import random
import zlib
import time


class tester():
    def __init__(self, device_paths, speed):
        """
        tester

        Object that initializes given serial devices and allows running communication tests between these devices

        Args:
            device_paths (list of strings): Paths to the serial devices to be used in testing
            speed (int): Baudrate used in transmission test
        """
        self.serials = []
        for device_path in device_paths:
            self.serials.append(serial.Serial(device_path, speed, timeout=1))

    def test_transmission(self, length):
        """
        test_transmission

        Sends packets of given length from all serial devices one by one, receiving with other devices.
        Checks that the received packet CRC matches the one calculated for the sent payload.

        Raises AssertionError if CRC is invalid

        Args:
            length (int): Length of the random ASCII string to be sent as a payload

        Returns:
            bool: If test is complete, returns True

        """
        payload = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        crc = hex(zlib.crc32(payload.encode("UTF-8")) & 0xffffffff)
        packet = payload + crc

        for sender in self.serials:

            #print(sender, "sending:", packet)
            start = time.perf_counter()
            sender.write((packet + "\r\n").encode("UTF-8"))

            for receiver in self.serials:

                if sender == receiver:
                    continue

                rx_packet = receiver.readline().decode("UTF-8")
                end = time.perf_counter() - start
                #print("Received:", rx_packet)

                rx_crc = rx_packet[length:].strip()
                assert rx_crc == crc

                print("RX OK, delay: " + "{0:.3f}".format(end) + "ms")

    def close(self):
        """
        close

        Closes all serial devices intialized in this object
        """
        for s in self.serials:
            s.close()


def test_for_speed(device_paths, length=2000, min_speed=9600, max_speed=12 * 10**7):
    """
    test_for_speed

    Runs iterative process to find the highest working speed

    Speed is increased after every successfull test by the relation of the min and max of the test range

    Args:
        device_paths (list of strings): Paths to the serial devices to be used in testing
        length (int): Length of the random ASCII string to be sent as a payload
        min_speed (int): Minimum limit for speed test
        max_speed (int): Maximum limit for speed test

    Returns:
        int: Last known speed that resulted in successfull test
    """
    last_working_speed = 0
    for i in range(20):
        if (max_speed / min_speed) < 1:
            break
        try:
            for speed in range(min_speed, max_speed, int(max_speed / min_speed)):
                print("Testing for speed:", speed, "with packet length:", length)
                t = tester(device_paths, speed)
                t.test_transmission(length)
                t.close()
                last_working_speed = speed
        except AssertionError:
            min_speed = last_working_speed
            continue
        except Exception as e:
            break
    print("Last known working speed:", last_working_speed)
    print("Test failed at:", speed)

    return last_working_speed


def test_for_length(device_paths, speed=9600, min_length=100, max_length=1 * 10**5):
    """
    test_for_length

    Runs iterative process to find the highest working packet length

    Length is increased after every successfull test by the relation of the min and max of the test range

    Args:
        device_paths (list of strings): Paths to the serial devices to be used in testing
        speed (int): Baudrate used in transmission test
        min_length (int): Minimum limit for length test
        max_length (int): Maximum limit for length test

    Returns:
        int: Last known length that resulted in successfull test
    """

    last_working_length = 0
    for i in range(20):
        if (max_length / min_length) < 1:
            break
        try:
            for length in range(min_length, max_length, int(max_length / min_length)):
                print("Testing comms for packet length:", length, "with speed:", speed)
                t = tester(device_paths, speed)
                t.test_transmission(length)
                t.close()
                last_working_length = length
        except AssertionError:
            min_length = last_working_length
            continue
        except Exception as e:
            break
    print("Last known working length:", last_working_length)
    print("Test failed at:", length)

    return last_working_length


if __name__ == '__main__':
    device_paths = ["COM16", "COM19"]
    max_speed = test_for_speed(device_paths, length=2000)
    test_for_length(device_paths, speed=max_speed)
