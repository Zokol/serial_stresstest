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
from statistics import mean


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
            list of floats: delays of each transmission

        """
        payload = ''.join(random.choice(string.ascii_uppercase + string.digits, k=length))
        crc = hex(zlib.crc32(payload.encode("UTF-8")) & 0xffffffff)
        packet = payload + crc
        delays = []

        for sender in self.serials:

            start = time.perf_counter()
            sender.write((packet + "\r\n").encode("UTF-8"))

            for receiver in self.serials:

                if sender == receiver and len(self.serials) > 1:
                    continue

                rx_packet = receiver.readline().decode("UTF-8")
                end = time.perf_counter() - start
                delays.append(end)

                rx_crc = rx_packet[length:].strip()
                assert rx_crc == crc

                #print("RX OK, delay: " + "{0:.3f}".format(end * 1000) + "ms")

        return delays

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
                #print("Testing for speed:", speed, "with packet length:", length)
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
                #print("Testing comms for packet length:", length, "with speed:", speed)
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


def test_for_delay(device_paths, speed=9600, length=100, number_of_samples=10):
    """
    test_for_delay

    Runs several samples with given speed and packet length to find average delay between send and receive

    Args:
        device_paths (list of strings): Paths to the serial devices to be used in testing
        speed (int): Baudrate used in transmission test
        length (int): Transmission packet length
        number_of_samples (int): Number of samples to be taken

    Returns:
        int: Average delay from all transmission samples
    """

    delays = []
    try:
        for i in range(number_of_samples):
            #print("Testing comms for packet length:", length, "with speed:", speed)
            t = tester(device_paths, speed)
            d = t.test_transmission(length)
            delays += d
            t.close()
    except AssertionError:
        mean(delays)
    except Exception as e:
        mean(delays)
    print("Maximum delay:", max(delays), "ms")
    print("Average delay:", mean(delays), "ms")
    print("Minimum delay:", min(delays), "ms")

    return mean(delays)


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Runs serial test')
    parser.add_argument('serials', metavar='serials', type=str, nargs='+', help="Serial devices to be tested. Example; Windows: run.py COM10 COM11, Linux: run.py /dev/ttyUSB0 /dev/ttyUSB1")

    args = parser.parse_args()

    #serials = ["COM16", "COM19"]
    #serials = ["COM15"]
    serials = args.serials
    max_speed = test_for_speed(serials, length=2000)
    print("Maximum known working speed:", max_speed)

    max_length = test_for_length(serials, speed=max_speed)
    print("Maximum known working length:", max_length)

    avg_delay = test_for_delay(serials, speed=max_speed, length=10)
    print("Average delay:", avg_delay, "ms with packet length 10")

    avg_delay = test_for_delay(serials, speed=max_speed, length=max_length)
    print("Average delay:", avg_delay, "ms with packet length", max_length)
