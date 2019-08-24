package main

import (
    "fmt"
    "github.com/jacobsa/go-serial/serial"
    "time"
    "hash/crc32"
    "math/rand"
    "strings"
    "strconv"
)

var letters = []rune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

func randSeq(n int) string {
    b := make([]rune, n)
    for i := range b {
        b[i] = letters[rand.Intn(len(letters))]
    }
    return string(b)
}

func test_transmission(ports []string, length int, speed int) (bool, []float64) {
    /*
    test_transmission

    Sends packets of given length from all serial devices one by one, receiving with other devices.
    Checks that the received packet CRC matches the one calculated for the sent payload.

    Raises AssertionError if CRC is invalid

    Args:
        length (int): Length of the random ASCII string to be sent as a payload

    Returns:
        bool: If test is complete, returns True

    */

    rand.Seed(time.Now().UnixNano())

    data := []byte(randSeq(length))

    delays := make([]float64, 0)

    crc32q := crc32.MakeTable(0xEDB88320)
    checksum_uint := crc32.Checksum(data, crc32q)
    checksum := []byte(strconv.FormatUint(uint64(checksum_uint), 16))
    packet := append(data, checksum...)

    //fmt.Println("data:", string(data))
    //fmt.Println("checksum:", string(checksum))
    //fmt.Println("TX:", packet, "\n")

    for _, port := range ports {

        options := serial.OpenOptions{
            PortName:        string(port),
            BaudRate:        uint(speed),
            DataBits:        8,
            StopBits:        1,
            MinimumReadSize: 4,
        }
        port, err := serial.Open(options)
        check(err)

        buf := make([]byte, 10000)

        start := time.Now()
        port.Write(packet)
        port.Read(buf)
        t := time.Now()
        elapsed := t.Sub(start)

        defer port.Close()

        check(err)

        //fmt.Println("RX:", buf[0:len(packet)])

        packet_valid := strings.HasSuffix(string(buf[0:len(packet)]), string(checksum))

        if !packet_valid{
            return false, delays
        }

        //fmt.Println("Checksum match:", packet_valid)

        //fmt.Println("Read", n)
        //fmt.Println("Delay", elapsed)
        delays = append(delays, float64(elapsed))
    }

    return true, delays
}

func test_for_speed(ports []string, length int, min_speed int, max_speed int) int{
    /*
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
    */
    var res = false
    var last_working_speed = 0
    for i := 0; i < 2; i++ {
        if (max_speed / min_speed) < 1{
            return last_working_speed
        }
        for speed := min_speed; speed < max_speed; speed = speed + int(max_speed / min_speed) {
            //fmt.Println("Testing for speed:", speed, "with packet length:", length)
            res, _ := test_transmission(ports, length, speed)
            if (res == true){
                last_working_speed = speed
            } else {
                //return last_working_speed
                min_speed = speed
                break
            }
        }
        if (res == true){
            return last_working_speed
        }
    }
    return last_working_speed
}

func test_for_length(ports []string, speed int, min_length int, max_length int) int{
    /*
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
    */
    var last_working_length = 0
    for i := 0; i < 2; i++ {
        for length := min_length; length < max_length; length++ {
            //fmt.Println("Testing for packet length:", length, "with speed:", speed)
            res, _ := test_transmission(ports, length, speed)
            if (res == true){
                last_working_length = length
                continue
            } else {
                return last_working_length
            }
        }
    }
    return last_working_length
}

func test_for_delay(ports []string, length int, speed int, samples int) float64{
    /*
    test_for_delay

    Runs several samples with given speed and packet length to find average delay between send and receive

    Args:
        device_paths (list of strings): Paths to the serial devices to be used in testing
        speed (int): Baudrate used in transmission test
        length (int): Transmission packet length
        number_of_samples (int): Number of samples to be taken

    Returns:
        int: Maximum delay from all transmission samples
    */

    delays := make([]float64, 0)
    for i := 0; i < samples; i++ {
        //fmt.Println("Testing comm delay with packet length:", length, "and speed:", speed)
        //start := time.Now()
        res, d := test_transmission(ports, length, speed)
        //fmt.Println(res, d)
        if !(res){
            break
        }
        //t := time.Now()
        //elapsed := t.Sub(start)
        
        delays = append(delays, d...)
    }

    var total float64 = 0
    var min_delay float64 = 0
    var max_delay float64 = 0
    for _, value := range delays {
        total += value
        if min_delay == 0{
            min_delay = value
        }
        if max_delay == 0{
            max_delay = value
        }
        if min_delay > value{
            min_delay = value
        }
        if max_delay < value {
            max_delay = value
        }
    }

    var avg_delay = total/float64(len(delays))

    fmt.Println("Maximum delay:", max_delay, "ms")
    fmt.Println("Average delay:", avg_delay, "ms")
    fmt.Println("Minimum delay:", min_delay, "ms")

    return avg_delay
}

func check(err error) {
    if err != nil {
        panic(err.Error())
    }
}

func main() {
    var serials = []string{"COM15"}

    //test_transmission(serials, 23, 9600)
    //fmt.Println(test_for_delay(serials, 10, 9600, 10), "ms")

    
    last_working_speed := test_for_speed(serials, 20, 9600, 1000000)
    fmt.Println("Last known working speed:", last_working_speed)
    
    last_working_length := test_for_length(serials, last_working_speed, 100, 100000)
    fmt.Println("Last known working length:", last_working_length)

    avg_delay := test_for_delay(serials, 10, last_working_speed, 10)
    fmt.Println("Average delay:", avg_delay, "ms for packet length:", 10)

    avg_delay = test_for_delay(serials, last_working_length, last_working_speed, 10)
    fmt.Println("Average delay:", avg_delay, "ms for packet length:", last_working_length)

    
    
}