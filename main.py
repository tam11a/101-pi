import time
import datetime
import board
import adafruit_dht
import RPi.GPIO as gpio
import threading
import sys

# Initialize the DHT device, with data pin connected to:
dhtDevice = adafruit_dht.DHT22(board.D4, use_pulseio=False)

# Define GPIO pins
GPIO_PIN_HIGH = 17
GPIO_PIN_LOW = 27

# Setup GPIO pins
gpio.setmode(gpio.BCM)
gpio.setup(GPIO_PIN_HIGH, gpio.OUT)
gpio.setup(GPIO_PIN_LOW, gpio.OUT)

filename = "temp_log.csv"
gpio_logfile = "gpio_output.log"

# Create header row in new CSV file
with open(filename, 'w') as csv:
    csv.write("Timestamp,Temperature\n")

# Open GPIO log file for writing
gpio_log = open(gpio_logfile, 'w')

# Mutex for accessing GPIO from multiple threads
gpio_mutex = threading.Lock()

# Event to synchronize threads
gpio_event = threading.Event()
gpio_event.set()  # Set event to allow the first thread to start

def read_temperature_humidity():
    while True:
        try:
            # Read temperature and humidity values
            temperature_c = dhtDevice.temperature
            humidity = dhtDevice.humidity

            # Print values
            print("Temp: {:.1f} C    Humidity: {}%".format(temperature_c, humidity))
            sys.stdout.flush()  # Flush stdout to ensure immediate output

            # Log values to CSV
            with open(filename, 'a') as csv:
                csv.write("{},{}\n".format(datetime.datetime.now(), temperature_c))

        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print(error.args[0])
        except Exception as error:
            print("Error:", error)

        time.sleep(2)  # Sleep for 2 seconds before the next reading
        gpio_event.clear()  # Clear event to allow the GPIO thread to run

def toggle_gpio():
    while True:
        gpio_event.wait()  # Wait until the event is set (i.e., temperature/humidity thread has finished)
        
        with gpio_mutex:
            # Toggle GPIO pins
            gpio.output(GPIO_PIN_HIGH, gpio.HIGH)
            gpio_log.write("GPIO {} set to HIGH\n".format(GPIO_PIN_HIGH))
            gpio_log.flush()

            time.sleep(1)

            gpio.output(GPIO_PIN_HIGH, gpio.LOW)
            gpio_log.write("GPIO {} set to LOW\n".format(GPIO_PIN_HIGH))
            gpio_log.flush()

            time.sleep(1)

            gpio.output(GPIO_PIN_LOW, gpio.HIGH)
            gpio_log.write("GPIO {} set to HIGH\n".format(GPIO_PIN_LOW))
            gpio_log.flush()

            time.sleep(1)

            gpio.output(GPIO_PIN_LOW, gpio.LOW)
            gpio_log.write("GPIO {} set to LOW\n".format(GPIO_PIN_LOW))
            gpio_log.flush()

            time.sleep(1)

        gpio_event.set()  # Set event to allow the temperature/humidity thread to run

# Create and start threads
temp_humidity_thread = threading.Thread(target=read_temperature_humidity)
gpio_thread = threading.Thread(target=toggle_gpio)

temp_humidity_thread.start()
gpio_thread.start()

# Wait for threads to finish (which will never happen, this is just to keep the main thread running)
temp_humidity_thread.join()
gpio_thread.join()

# Cleanup GPIO
gpio.cleanup()

# Close GPIO log file
gpio_log.close()
