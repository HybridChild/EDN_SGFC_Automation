from datetime import datetime, time, timedelta
import csv
import board
import digitalio
import busio
import adafruit_sht31d

# --------------------------------------- Function implementations ---------------------------------------

# Function for writing to the terminal
def terminal_write(arg_string):
    # Make date/time string
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")   # Format: "2019-12-18 18:24:33"

    print(dt_string + " " + arg_string)

# Function for turning the lights on/off
def light_switch(state):
    relay1.value = not state
    relay2.value = not state

# Function to see if lights are currently on or off
def light_state():
    return not (relay1.value or relay2.value)

# Function for turning the mister on/off
def mister_switch(state):
    relay4.value = not state

# Function to see if mister is currently on or off
def mister_state():
    return not relay4.value

# Function for turning the fan on/off
def fan_switch(state):
    mosfet2.value = state

# Function to see if fan is currently on or off
def fan_state():
    return mosfet2.value

# --------------------------------------- PROGRAM START ---------------------------------------
terminal_write("Start program execution")

# Setup GPIOs
relay1 = digitalio.DigitalInOut(board.D17)
relay2 = digitalio.DigitalInOut(board.D18)
relay3 = digitalio.DigitalInOut(board.D27)
relay4 = digitalio.DigitalInOut(board.D22)
mosfet1 = digitalio.DigitalInOut(board.D26)
mosfet2 = digitalio.DigitalInOut(board.D19)

relay1.direction = digitalio.Direction.OUTPUT
relay2.direction = digitalio.Direction.OUTPUT
relay3.direction = digitalio.Direction.OUTPUT
relay4.direction = digitalio.Direction.OUTPUT
mosfet1.direction = digitalio.Direction.OUTPUT
mosfet2.direction = digitalio.Direction.OUTPUT

# Turn external hardware off (lights will be set during variable initialization)
relay3.value = True     # Unused relay
mosfet1.value = False   # Unused mosfet

mister_switch(False)
fan_switch(False)

# Create library object for SHT31D sensor using Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_sht31d.SHT31D(i2c)

# Create data log file
fieldnames = ['date/time', 'Temperature', 'Relative humidity']
with open('log_file.csv', 'w', newline='') as new_file:
    csv_writer = csv.DictWriter(new_file, delimiter='\t', fieldnames=fieldnames)
    csv_writer.writeheader()

# --------------------------------------- Define static variables ---------------------------------------
midnight = timedelta(hours=24)
light_off_time = timedelta(hours=19, minutes=30, seconds=00)    # Time when the lights will be turned off
light_on_time = timedelta(hours=7, minutes=30, seconds=00)      # Time when the lights will be turned on
log_freq = timedelta(minutes=2)               # How often the sensor data is logged
humidity_check_freq = timedelta(minutes=12)   # How often the humidity level is checked
mister_period = timedelta(minutes=3)          # For how long the mister will run (Must be less than humidity_check_freq - (itself + fan_period_mist))
fan_freq = timedelta(minutes=20)              # How often the fan will run (if humidity is ignored)
fan_period_fae = timedelta(seconds=16)        # For how long the fan will run when performing air exchange 
fan_period_mist =  timedelta(seconds=8)       # For how long the fan will run when flushing mist chamber
fan_wait_time = mister_period                 # Time from mister is turned on till the fan starts (Must be less than or equal to mister_period)
avg_cnt = 10                                  # How many samples to calculate average sensor values 

# --------------------------------------- Define working variables ---------------------------------------
temperature = sensor.temperature
humidity = sensor.relative_humidity

# Get current time
now = datetime.now()
now_delta = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)

# Set first sensor log time to 2 seconds from now
log_time = now + timedelta(seconds=2)
log_time = timedelta(hours=log_time.hour, minutes=log_time.minute, seconds=log_time.second)

# Set first fan air exchange time
fan_time = now + fan_freq
fan_time = timedelta(hours=fan_time.hour, minutes=fan_time.minute, seconds=fan_time.second)

# Set first humidity check time to one minute from now
humidity_check_time = now + timedelta(minutes=1)
humidity_check_time = timedelta(hours=humidity_check_time.hour, minutes=humidity_check_time.minute, seconds=humidity_check_time.second)

# Nullify mist off time and fan off time
fan_off_time = 0
mister_off_time = 0

# Determine if light should be on or off at the current time
light_time = 0
if (now_delta > light_off_time and now_delta < midnight) or (now_delta < light_on_time):
    # Update light time
    light_time = light_on_time

    # Turn light off
    light_switch(False)
else:
    # Update light time
    light_time = light_off_time

    # Turn light on
    light_switch(True)


# --------------------------------------- START OF PROGRAM LOOP ---------------------------------------
terminal_write("Entering Program Loop")

while True:
    # Get current time
    now = datetime.now()
    now_delta = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
    
    # Is it time to log sensor data?
    if (now_delta == log_time):
        terminal_write("Logging sensor data")

        # Update log time
        log_time = now + log_freq
        log_time = timedelta(hours=log_time.hour, minutes=log_time.minute, seconds=log_time.second)

        # Accumulate sensor data
        temperature = 0
        humidity = 0
        count = 0
        while (count < avg_cnt):
            temperature = temperature + sensor.temperature
            humidity = humidity + sensor.relative_humidity
            count = count + 1
        
        # Calculate sample average
        temperature = temperature / avg_cnt
        humidity = humidity / avg_cnt

        print("Temperature: %0.1f C" % temperature)
        print("Humidity: %0.1f %%" % humidity)

        # Make date/time string
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")   # Format: "2019-12-18 18:24:33"

        # Write data to file
        with open('log_file.csv', 'a', newline='') as logFile:
            csv_writer = csv.DictWriter(logFile, delimiter='\t', fieldnames=fieldnames)
            csv_writer.writerow({fieldnames[0] : dt_string, fieldnames[1] : temperature, fieldnames[2] : humidity})

    # Is it time to fan?
    if (now_delta == fan_time):
        terminal_write("Fan ON")

        # Update fan time
        fan_time = now + fan_freq
        fan_time = timedelta(hours=fan_time.hour, minutes=fan_time.minute, seconds=fan_time.second)

        # Turn on fan
        fan_switch(True)

        # Set time for turning off fan
        if (mister_state()):
            fan_off_time = now + fan_period_mist
        else:
            fan_off_time = now + fan_period_fae
        
        fan_off_time = timedelta(hours=fan_off_time.hour, minutes=fan_off_time.minute, seconds=fan_off_time.second)

    # Is it time to turn off fan?
    if (now_delta == fan_off_time):
        terminal_write("Fan OFF")

        # Clear fan time
        fan_off_time = 0

        # Turn off fan
        fan_switch(False)

    # Is it time to check humidity?
    if (now_delta == humidity_check_time):
        terminal_write("Checking humidity level")
        print("Humidity: %0.1f %%" % humidity)

        # Update humidity check time
        humidity_check_time = now + humidity_check_freq
        humidity_check_time = timedelta(hours=humidity_check_time.hour, minutes=humidity_check_time.minute, seconds=humidity_check_time.second)

        # Check humidity
        if (humidity < 90):
            terminal_write("Mister ON")

            # Turn mister on
            mister_switch(True)

            # Set time to turn off mister
            mister_off_time = now + mister_period
            mister_off_time = timedelta(hours=mister_off_time.hour, minutes=mister_off_time.minute, seconds=mister_off_time.second)

            # Set time to turn on fan
            fan_time = now + fan_wait_time
            fan_time = timedelta(hours=fan_time.hour, minutes=fan_time.minute, seconds=fan_time.second)

    # Is it time to turn off mister?
    if (now_delta == mister_off_time):
        terminal_write("Mister OFF")

        # Clear mister off time
        mister_off_time = 0

        # Turn off mister
        mister_switch(False)
        

    # Is it time to turn lights on?
    if (now_delta == light_time) and (light_time == light_on_time):
        terminal_write("Lights ON")

        # Update light time
        light_time = light_off_time

        # Turn on lights
        light_switch(True) # Lights on

    # Is it time to turn lights off?
    if (now_delta == light_time) and (light_time == light_off_time):
        terminal_write("Lights OFF")

        # Update light time
        light_time = light_on_time

        # Turn off lights
        light_switch(False)

# --------------------------------------- END OF PROGRAM LOOP ---------------------------------------