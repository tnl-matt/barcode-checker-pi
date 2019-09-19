#!/usr/bin/env python

import evdev

import os
import struct
import sys
import time


"""Keyboard Button Mapping"""
KEY_MAP = {}
KEY_MAP[evdev.ecodes.KEY_GRAVE] = ('`', '~')
KEY_MAP[evdev.ecodes.KEY_1] = ('1', '!')
KEY_MAP[evdev.ecodes.KEY_2] = ('2', '@')
KEY_MAP[evdev.ecodes.KEY_3] = ('3', '#')
KEY_MAP[evdev.ecodes.KEY_4] = ('4', '$')
KEY_MAP[evdev.ecodes.KEY_5] = ('5', '%')
KEY_MAP[evdev.ecodes.KEY_6] = ('6', '^')
KEY_MAP[evdev.ecodes.KEY_7] = ('7', '&')
KEY_MAP[evdev.ecodes.KEY_8] = ('8', '*')
KEY_MAP[evdev.ecodes.KEY_9] = ('9', '(')
KEY_MAP[evdev.ecodes.KEY_0] = ('0', ')')
KEY_MAP[evdev.ecodes.KEY_MINUS] = ('-', '_')
KEY_MAP[evdev.ecodes.KEY_EQUAL] = ('=', '+')
KEY_MAP[evdev.ecodes.KEY_TAB] = ("\t", "\t")
KEY_MAP[evdev.ecodes.KEY_Q] = ('q', 'Q')
KEY_MAP[evdev.ecodes.KEY_W] = ('w', 'W')
KEY_MAP[evdev.ecodes.KEY_E] = ('e', 'E')
KEY_MAP[evdev.ecodes.KEY_R] = ('r', 'R')
KEY_MAP[evdev.ecodes.KEY_T] = ('t', 'T')
KEY_MAP[evdev.ecodes.KEY_Y] = ('y', 'Y')
KEY_MAP[evdev.ecodes.KEY_U] = ('u', 'U')
KEY_MAP[evdev.ecodes.KEY_I] = ('i', 'I')
KEY_MAP[evdev.ecodes.KEY_O] = ('o', 'O')
KEY_MAP[evdev.ecodes.KEY_P] = ('p', 'P')
KEY_MAP[evdev.ecodes.KEY_LEFTBRACE] = ('[', '{')
KEY_MAP[evdev.ecodes.KEY_RIGHTBRACE] = (']', '}')
KEY_MAP[evdev.ecodes.KEY_BACKSLASH] = ("\\", '|')
KEY_MAP[evdev.ecodes.KEY_A] = ('a', 'A')
KEY_MAP[evdev.ecodes.KEY_S] = ('s', 'S')
KEY_MAP[evdev.ecodes.KEY_D] = ('d', 'D')
KEY_MAP[evdev.ecodes.KEY_F] = ('f', 'F')
KEY_MAP[evdev.ecodes.KEY_G] = ('g', 'G')
KEY_MAP[evdev.ecodes.KEY_H] = ('h', 'H')
KEY_MAP[evdev.ecodes.KEY_J] = ('j', 'J')
KEY_MAP[evdev.ecodes.KEY_K] = ('k', 'K')
KEY_MAP[evdev.ecodes.KEY_L] = ('l', 'L')
KEY_MAP[evdev.ecodes.KEY_SEMICOLON] = (';', ':')
KEY_MAP[evdev.ecodes.KEY_APOSTROPHE] = ("'", '"')
KEY_MAP[evdev.ecodes.KEY_Z] = ('z', 'Z')
KEY_MAP[evdev.ecodes.KEY_X] = ('x', 'X')
KEY_MAP[evdev.ecodes.KEY_C] = ('c', 'C')
KEY_MAP[evdev.ecodes.KEY_V] = ('v', 'V')
KEY_MAP[evdev.ecodes.KEY_B] = ('b', 'B')
KEY_MAP[evdev.ecodes.KEY_N] = ('n', 'N')
KEY_MAP[evdev.ecodes.KEY_M] = ('m', 'M')
KEY_MAP[evdev.ecodes.KEY_COMMA] = (',', '<')
KEY_MAP[evdev.ecodes.KEY_DOT] = ('.', '>')
KEY_MAP[evdev.ecodes.KEY_SLASH] = ('/', '?')

IS_PI_AVAILABLE = False

# What device does the scanner attach to?
BARCODE_SCANNER_DEV = '/dev/input/event2'

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
QUIT_BARCODE = '__STOP__'

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
    if IS_PI_AVAILABLE:
        GPIO.output(pin, GPIO.HIGH)
    else:
        print('Start LED at {} on'.format(pin))


def end_led(pin):
    if IS_PI_AVAILABLE:
        GPIO.output(pin, GPIO.LOW)
    else:
        print('End LED at {} on'.format(pin))


def turn_off_all_leds():
    for pin in [
        GREEN_LED_PIN,
        RED_LED_PIN,
        YELLOW_LED_PIN,
    ]:
        end_led(pin)


"""Program run loop"""

current_mode = SCAN_MODE
current_match_mode = get_stored_match_mode()
working_match_mode = current_match_mode
n_barcodes = get_match_count_for_mode(current_match_mode)
barcodes = []

is_device_connected = False
input_device = None
while not is_device_connected:
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    blink_led_x_times(YELLOW_LED_PIN, 1)
    for device in devices:
        if device.name.startswith('Honeywell'):
            input_device = device
            is_device_connected = True
            print "Found device"
            print input_device.name
            print input_device.path


class KeyboardMonitor:
    def __init__(self):
        self.caps_active = False
        self.shift_count = 0

    def clear_shifts(self):
        self.caps_active = False
        self.shift_count = 0

    def char_from_event(self, e):
        """
        Convert a keyboard event to a character.
        The value is 0=up, 1=down, 2=hold
        """
        output = ''
        e_code, e_type, e_value = e.code, e.type, e.value

        if e_code == evdev.ecodes.KEY_ENTER and e_value == 0:
            return "\n"

        if e_code in [
            evdev.ecodes.KEY_LEFTSHIFT,
            evdev.ecodes.KEY_RIGHTSHIFT
        ]:
            if e_value == 0:
                self.shift_count -= 1
            elif e_value == 1:
                self.shift_count += 1
            return ''

        if e_code == evdev.ecodes.KEY_CAPSLOCK:
            if e_value == 0:
                self.caps_active = not self.caps_active
            return ''

        if e_code in KEY_MAP and e.value == 0:
            keys = KEY_MAP[e_code]
            if self.shift_count > 0:
                return keys[1]
            return keys[0]
        return ''


barcode = ''
monitor = KeyboardMonitor()
for e in input_device.read_loop():
    if e.type != evdev.ecodes.EV_KEY:
        continue

    this_char = monitor.char_from_event(e)

    if this_char != "\n":
        barcode = barcode + this_char
        continue
    monitor.clear_shifts()

    nth_barcode = len(barcodes) + 1

    if barcode == QUIT_BARCODE:
        barcode = ''
        break
    
    if barcode == BEGIN_PROGRAMMING:
        current_mode = PROGRAMMING_MODE
        barcode = ''
        barcodes = []
        turn_off_all_leds()
        start_led(RED_LED_PIN)
        continue

    if barcode == END_PROGRAMMING:
        if current_mode != PROGRAMMING_MODE:
            continue
        n_barcodes = get_match_count_for_mode(
            working_match_mode
        )
        save_stored_match_mode(working_match_mode)
        turn_off_all_leds()
        blink_led_x_times(GREEN_LED_PIN, n_barcodes)
        current_mode = SCAN_MODE
        barcode = ''
        continue

    if barcode == RESTART_SCANNING:
        turn_off_all_leds()
        barcodes = []
        barcode = ''
        continue

    if current_mode == SCAN_MODE:
        if nth_barcode == 1:
            start_led(YELLOW_LED_PIN)

        if nth_barcode == n_barcodes:
            end_led(YELLOW_LED_PIN)
            barcodes_match = True
            for (i, bc) in enumerate(barcodes):
                if bc != barcode:
                    barcodes_match = False
            if not barcodes_match:
                flash_led(RED_LED_PIN)
            else:
                flash_led(GREEN_LED_PIN)
            barcodes = []
        else:
            barcodes.append(barcode)
    elif current_mode == PROGRAMMING_MODE:
        # Handle Programming mode
        if barcode in VALID_MATCH_MODES:
            working_match_mode = barcode

    barcode = ''


if input_device is not None:
    input_device.close()


if IS_PI_AVAILABLE:
    GPIO.cleanup([RED_LED_PIN, GREEN_LED_PIN, YELLOW_LED_PIN])
    
