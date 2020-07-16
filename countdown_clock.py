import datetime
import RPi.GPIO as GPIO
import subprocess
from collections import deque
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306


class RestTimer:
    def __init__(self):
        # setting up screen for use
        self.serial = i2c(port=1, address=0x3C)
        self.device = ssd1306(self.serial)

        #  Input pins:
        # left stick pins
        self.left_pin = 27
        self.right_pin = 23
        self.center_pin = 4
        self.up_pin = 17
        self.down_pin = 22

        # right side button pins
        self.a_pin = 5
        self.b_pin = 6

        # referring to pins by the Broadcom SOC channel
        GPIO.setmode(GPIO.BCM)

        # Inputs with pull-up
        GPIO.setup(self.a_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.b_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.left_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.right_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.up_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.down_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.center_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # segmented display rows for countdown in minutes/seconds
        self.row1 = deque(maxlen=5)
        self.row2 = deque(maxlen=5)
        self.row3 = deque(maxlen=5)
        self.row4 = deque(maxlen=5)
        self.row5 = deque(maxlen=5)
        self.short_rows = [self.row1, self.row2, self.row3, self.row4, self.row5]

        # segmented display rows for total time in hours/minutes/seconds
        self.row6 = deque(maxlen=8)
        self.row7 = deque(maxlen=8)
        self.row8 = deque(maxlen=8)
        self.row9 = deque(maxlen=8)
        self.row10 = deque(maxlen=8)
        self.long_rows = [self.row6, self.row7, self.row8, self.row9, self.row10]

        self.start_time = datetime.datetime.now()

        # tracking last selected rest time
        self.rest_time = 1.0

    def pick_rest_time(self):
        # menu and time selection for the self.countdown method
        while True:
            with canvas(self.device) as draw:
                # draw the info text
                draw.text((5, 5), 'Select rest time:', fill='white')
                draw.text((5, 15), '<' + str(self.rest_time) + '> minutes', fill='white')
                draw.text((5, 25), 'left/right to change rest time', fill='white')
                draw.text((5, 35), 'a-start/resume', fill='white')
                draw.text((5, 45), 'b-back/pause', fill='white')

                # left/right to increase/decrease time
                if not GPIO.input(self.left_pin):
                    self.rest_time -= .5
                    if self.rest_time < 1:
                        self.rest_time = 1.0

                if not GPIO.input(self.right_pin):
                    self.rest_time += .5
                    if self.rest_time > 10:
                        self.rest_time = 10.0

                # a to confirm, b to exit
                if not GPIO.input(self.a_pin):
                    self.countdown(self.rest_time)

                if not GPIO.input(self.b_pin):
                    break

    def countdown(self, minutes):
        # counts down based on time selected in self.pick_rest_time, has a pause function
        stop_time = datetime.datetime.now() + datetime.timedelta(seconds=int(minutes * 60))
        last_check = None
        paused = False
        seconds_remaining = 0
        while datetime.datetime.now() < stop_time:
            if not paused:
                time_left = (stop_time - datetime.datetime.now()).seconds
                if last_check is None or last_check > time_left:
                    last_check = time_left
                    minute = time_left // 60
                    second = time_left - minute * 60
                    seconds_remaining += minute * 60
                    seconds_remaining += second
                    if minute < 10:
                        minute = '0' + str(minute)
                    else:
                        minute = str(minute)
                    if second in range(0, 10):
                        second = '0' + str(second)
                    else:
                        second = str(second)
                    time = minute + ':' + second
                    self.segment_display(time, self.short_rows)
                    self.display_time_left()
                elif last_check == time_left:
                    self.display_time_left()

                if not GPIO.input(self.b_pin):
                    paused = True
                    seconds_remaining = (stop_time - datetime.datetime.now()).seconds

            elif paused:
                stop_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds_remaining)
                time_left = (stop_time - datetime.datetime.now()).seconds
                minute = time_left // 60
                second = time_left - minute * 60
                if minute < 10:
                    minute = '0' + str(minute)
                else:
                    minute = str(minute)
                if second in range(0, 10):
                    second = '0' + str(second)
                else:
                    second = str(second)
                time = minute + ':' + second
                self.segment_display(time, self.short_rows)
                self.display_time_left()

                if not GPIO.input(self.b_pin):
                    break

                if not GPIO.input(self.a_pin):
                    paused = False

    @staticmethod
    def segment_display(time_as_string, rows):
        # 7 segment style display for numbers
        for digit in time_as_string:
            if digit == '0':
                rows[0].append('XXX')
                rows[1].append('X_X')
                rows[2].append('X_X')
                rows[3].append('X_X')
                rows[4].append('XXX')
            if digit == '1':
                rows[0].append('__X')
                rows[1].append('__X')
                rows[2].append('__X')
                rows[3].append('__X')
                rows[4].append('__X')
            if digit == '2':
                rows[0].append('XXX')
                rows[1].append('__X')
                rows[2].append('XXX')
                rows[3].append('X__')
                rows[4].append('XXX')
            if digit == '3':
                rows[0].append('XXX')
                rows[1].append('__X')
                rows[2].append('XXX')
                rows[3].append('__X')
                rows[4].append('XXX')
            if digit == '4':
                rows[0].append('X_X')
                rows[1].append('X_X')
                rows[2].append('XXX')
                rows[3].append('__X')
                rows[4].append('__X')
            if digit == '5':
                rows[0].append('XXX')
                rows[1].append('X__')
                rows[2].append('XXX')
                rows[3].append('__X')
                rows[4].append('XXX')
            if digit == '6':
                rows[0].append('X__')
                rows[1].append('X__')
                rows[2].append('XXX')
                rows[3].append('X_X')
                rows[4].append('XXX')
            if digit == '7':
                rows[0].append('XXX')
                rows[1].append('__X')
                rows[2].append('_X_')
                rows[3].append('_X_')
                rows[4].append('_X_')
            if digit == '8':
                rows[0].append('XXX')
                rows[1].append('X_X')
                rows[2].append('XXX')
                rows[3].append('X_X')
                rows[4].append('XXX')
            if digit == '9':
                rows[0].append('XXX')
                rows[1].append('X_X')
                rows[2].append('XXX')
                rows[3].append('__X')
                rows[4].append('__X')
            if digit == ':':
                rows[0].append('___')
                rows[1].append('_X_')
                rows[2].append('___')
                rows[3].append('_X_')
                rows[4].append('___')

    def display_time_left(self):
        # drawing each line of the 7 segment style display with minutes/seconds
        start_x = 3
        start_y = 8
        with canvas(self.device) as draw:
            temp_y = start_y
            for row in self.short_rows:
                temp_x = start_x
                temp_y += 7
                for segment in row:
                    temp_x += 3
                    for character in segment:
                        if character == 'X':
                            draw.rectangle((temp_x, temp_y, temp_x + 6, temp_y + 6), outline='white', fill='white')
                            temp_x += 7
                        else:
                            temp_x += 7

    def display_time_total(self):
        # drawing each line of the 7 segment style display with hours/minutes/seconds
        start_x = 0
        start_y = 13
        with canvas(self.device) as draw:
            temp_y = start_y
            for row in self.long_rows:
                temp_x = start_x
                temp_y += 5
                for segment in row:
                    temp_x += 3
                    for character in segment:
                        if character == 'X':
                            draw.rectangle((temp_x, temp_y, temp_x + 4, temp_y + 4), outline='white', fill='white')
                            temp_x += 4
                        else:
                            temp_x += 4

    def total_time(self):
        # displays total run time
        while True:
            total = (datetime.datetime.now() - self.start_time).seconds
            hours = total // 60 // 60
            minutes = (total // 60) - (hours * 60)
            seconds = total % 60

            if seconds < 10:
                seconds = '0' + str(seconds)
            else:
                seconds = str(seconds)
            if minutes < 10:
                minutes = '0' + str(minutes)
            else:
                minutes = str(minutes)
            hours = '0' + str(hours)
            time = hours + ':' + minutes + ':' + seconds
            self.segment_display(time, self.long_rows)
            self.display_time_total()

            if not GPIO.input(self.b_pin):
                break

    def shutdown(self):
        stop = datetime.datetime.now() + datetime.timedelta(seconds=3)
        while datetime.datetime.now() < stop:
            with canvas(self.device) as draw:
                draw.text((30, 40), 'Goodbye', fill='white')
        self.device.cleanup()
        subprocess.call(['sudo', 'shutdown', '-h', 'now'])

    def menu(self):
        # main menu
        pointer = 0
        try:
            options = [self.pick_rest_time, self.total_time, self.shutdown]
            while True:
                with canvas(self.device) as draw:
                    draw.text((20, 10), 'Rest Timer', fill='white')
                    draw.text((20, 25), 'Workout Length', fill='white')
                    draw.text((20, 40), 'Shutdown', fill='white')
                    draw.text((20, 55), 'center-select', fill='white')

                    if pointer == 0:
                        draw.text((10, 10), '>', fill='white')
                    elif pointer == 1:
                        draw.text((10, 25), '>', fill='white')
                    elif pointer == 2:
                        draw.text((10, 40), '>', fill='white')

                    # up/down  to select
                    if not GPIO.input(self.up_pin):
                        pointer -= 1
                        if pointer < 0:
                            pointer = len(options) - 1

                    if not GPIO.input(self.down_pin):
                        pointer += 1
                        if pointer >= len(options):
                            pointer = 0

                    # center click to confirm
                    if not GPIO.input(self.center_pin):
                        # running the selected menu item
                        options[pointer]()

        except KeyboardInterrupt:
            self.device.cleanup()


rt = RestTimer()
rt.menu()
