#!/usr/bin/env python

import evdev
from select import select

import os
import struct
import sys
import time

IS_PI_AVAILABLE = False

# What device does the scanner attach to?
BARCODE_SCANNER_DEV = '/dev/input/event0'

# GPIO Pins
GREEN_LED_PIN = 18
RED_LED_PIN = 16
YELLOW_LED_PIN = 22

# Run Modes
SCAN_MODE = 'SCAN_MODE'
PROGRAMMING_MODE = 'PROGRAMMING_MODE'

# Control Barcodes
BEGIN_PROGRAMMING = '__BEGINPROG__'
END_PROGRAMMING = '__ENDPROG__'
RESTART_SCANNING = '__CANCEL__'
QUIT_BARCODE = 'STOP'

# Match modes
MATCH_02 = '__MATCH02__'
MATCH_03 = '__MATCH03__'
MATCH_04 = '__MATCH04__'
MATCH_05 = '__MATCH05__'
MATCH_06 = '__MATCH06__'
MATCH_07 = '__MATCH07__'
MATCH_08 = '__MATCH08__'

VALID_MATCH_MODES = [ 
    MATCH_02,
    MATCH_03,
    MATCH_04,
    MATCH_05,
    MATCH_06,
    MATCH_07,
    MATCH_08,
]
DEFAULT_MATCH_MODE = MATCH_02

# Get match mode from local storage
MODE_FP = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    'current_match_mode.txt'
)


try:
    import RPi.GPIO as GPIO
    IS_PI_AVAILABLE = True
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(True)
    GPIO.setup(GREEN_LED_PIN,GPIO.OUT)
    GPIO.setup(RED_LED_PIN,GPIO.OUT)
    GPIO.setup(YELLOW_LED_PIN,GPIO.OUT)
except RuntimeError as e:
    print("WARNING: {}".format(str(e)))


"""Functions"""
def save_stored_match_mode(new_mode):
    with open(MODE_FP, 'w') as f:
        f.write(new_mode)
        f.close()


def get_stored_match_mode():
    is_set = False
    stored_mode = DEFAULT_MATCH_MODE
    # Try to get stored mode
    if os.path.exists(MODE_FP):
        file_mode = ''
        with open(MODE_FP, 'r') as f:
            file_mode = f.read().strip()
            f.close()
        if file_mode in VALID_MATCH_MODES:
            stored_mode = file_mode
            is_set = True
    # No stored mode, so set it to default
    if not is_set:
        stored_mode = DEFAULT_MATCH_MODE
        save_stored_match_mode(DEFAULT_MATCH_MODE)
    return stored_mode


def get_match_count_for_mode(new_mode):
    if not new_mode in VALID_MATCH_MODES:
        return get_match_count_for_mode(DEFAULT_MATCH_MODE)
    if new_mode == MATCH_02:
        return 2
    if new_mode == MATCH_03:
        return 3
    if new_mode == MATCH_04:
        return 4
    if new_mode == MATCH_05:
        return 5
    if new_mode == MATCH_06:
        return 6
    if new_mode == MATCH_07:
        return 7
    if new_mode == MATCH_08:
        return 8


"""LED Functions"""
def flash_led(pin):
    print('LED at {} on'.format(pin))
    if IS_PI_AVAILABLE:
        GPIO.output(pin, GPIO.HIGH)
    else:
        print('setting pin high')
    time.sleep(1)
    print('LED off')
    if IS_PI_AVAILABLE:
        GPIO.output(pin, GPIO.LOW) 
    else:
        print('setting pin low')


def blink_led_x_times(pin, times):
    for i in range(times):
        if IS_PI_AVAILABLE:
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(.25)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(.25)
        else:
            print('blinking {} {}'.format(pin, i))


def start_led(pin):
    print('Start LED at {} on'.format(pin))
    if IS_PI_AVAILABLE:
        GPIO.output(pin, GPIO.HIGH)


def end_led(pin):
    print('End LED at {} on'.format(pin))
    if IS_PI_AVAILABLE:
        GPIO.output(pin, GPIO.LOW)


def turn_off_all_leds():
    for pin in [GREEN_LED_PIN, RED_LED_PIN, YELLOW_LED_PIN]:
        end_led(pin)


"""Program run loop"""

current_mode = SCAN_MODE
current_match_mode = get_stored_match_mode()
working_match_mode = current_match_mode
n_barcodes = get_match_count_for_mode(current_match_mode)
barcodes = []

input_device = None
while input_device is None:
    blink_led_x_times(YELLOW_LED_PIN, 1)
    if os.path.exists(BARCODE_SCANNER_DEV):
        # input_device = open(BARCODE_SCANNER_DEV, 'rb')
        input_device = evdev.InputDevice(BARCODE_SCANNER_DEV)
        
        
is_shift_active = False
def get_next_char(f):
    output = ''
    r, w, x = select([f], [], [])
    for event in f.read():
        if event.type == 1 and event.value == 1 and str(event.code) and str(event.code) != 'None':
            output = str(event.code)
            print 'get_next_char {}'.format(output)
            break
    return output


barcode = ''
building_barcode = True

for e in input_device.read_loop():
    if e.type != evdev.ecodes.EV_KEY:
        continue

    # barcode = raw_input('barcode {}->'.format(nth_barcode))

    nth_barcode = len(barcodes) + 1
    print(evdev.categorize(e))
    this_key = key_from_event(e)

    if building_barcode:
        print("This char: {} this barcode: {}".format(this_char, barcode))
        if this_char == "\n":
            building_barcode = False
        else:
            barcode = barcode + str(this_char)


    print("Mode: {}, Barcode {}: {}".format(current_mode, nth_barcode, barcode))


    if barcode == QUIT_BARCODE:
        break
    
    if barcode == BEGIN_PROGRAMMING:
        current_mode = PROGRAMMING_MODE
        barcodes = []
        turn_off_all_leds()
        start_led(RED_LED_PIN)
        continue

    if barcode == END_PROGRAMMING:
        if current_mode != PROGRAMMING_MODE:
            continue
        n_barcodes = get_match_count_for_mode(working_match_mode)
        save_stored_match_mode(working_match_mode)
        turn_off_all_leds()
        blink_led_x_times(GREEN_LED_PIN, n_barcodes)
        current_mode = SCAN_MODE
        continue
    
    if barcode == RESTART_SCANNING:
        turn_off_all_leds()
        barcodes = []
        continue

    if current_mode == SCAN_MODE:
        # Handle scanning mode
        if nth_barcode == 1:
            start_led(YELLOW_LED_PIN)

        if nth_barcode == n_barcodes:
            end_led(YELLOW_LED_PIN)

        if nth_barcode == n_barcodes:
            barcodes_match = True
            for (i, bc) in enumerate(barcodes):
                if bc != barcode:
                    barcodes_match = False
                    print("Mismatch at {}: {}\n".format(
                        i + 1,
                        bc
                    ))
            if not barcodes_match:
                print("TODO show red LED\n")
                flash_led(RED_LED_PIN)
            else:
                print("TODO show green LED\n")
                flash_led(GREEN_LED_PIN)
            barcodes = []
        else:
            barcodes.append(barcode)
    elif current_mode == PROGRAMMING_MODE:
        # Handle Programming mode
        if barcode in VALID_MATCH_MODES:
            working_match_mode = barcode

if input_device is not None:
    input_device.close()

if IS_PI_AVAILABLE:
    GPIO.cleanup([RED_LED_PIN, GREEN_LED_PIN, YELLOW_LED_PIN])
    
