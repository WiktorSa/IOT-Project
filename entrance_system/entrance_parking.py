#!/usr/bin/env python3

# pylint: disable=no-member

import time
import RPi.GPIO as GPIO
from config import *  # pylint: disable=unused-wildcard-import
from mfrc522 import MFRC522
from datetime import datetime
import paho.mqtt.client as mqtt
import neopixel
import board

broker = "10.108.33.124"
client = mqtt.Client()
pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)
MIFAREReader = MFRC522()
is_working = True

num_dict = {90010080054: [datetime.now(), True]}
total_parking_places = 10
free_parking_places = 10


def connect_to_broker():
   client.connect(broker)
   client.subscribe("terminal2")


def send_info(message):
    client.publish("terminal1", f'{message}')


def read_info(client, userdata, message):
    message_decoded = list(str(message.payload.decode("utf-8")))

    if message_decoded[0] == "exit_gate_open_card":
        card_id = int(message_decoded[1])
        if card_id in num_dict.keys() and num_dict[card_id][1]:
            num_dict[card_id][1] = False
            send_info("exit_allowed")

            if free_parking_places == total_parking_places:
                print("WARNING - can't add new free place")
            else:
                free_parking_places += 1

        else:
            send_info("exit_not_allowed")

    elif message_decoded[0] == "exit_gate_open_button":
        if free_parking_places == total_parking_places:
            print("WARNING - can't add new free place")
        else:
            free_parking_places += 1


def add_detect_buttons():
    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=green_button_pressed_callback, bouncetime=200)
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=red_button_pressed_callback, bouncetime=200)
    

def green_button_pressed_callback(channel):
    if free_parking_places == 0:
        print("WARNING - all places are taken")
    else:
        free_parking_places -= 1
    blink_green()
    buzzer()
    stop_blink()


def red_button_pressed_callback(channel):
    global is_working
    is_working = False


def blink_green():
    pixels.fill((0, 255, 0))
    pixels.show()


def blink_red():
    pixels.fill((255, 0, 0))
    pixels.show()


def stop_blink():
    pixels.fill((0, 0, 0))
    pixels.show()


def buzzer():
    GPIO.output(buzzerPin, False)
    time.sleep(1)
    GPIO.output(buzzerPin, True)


def read_cards():
    global is_working
    global free_parking_places
    global total_parking_places
    last_scan = datetime.timestamp(datetime.now()) - 1	
    while is_working:
        if datetime.timestamp(datetime.now()) - last_scan > 1.0:
            (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
            if status == MIFAREReader.MI_OK:
                (status, uid) = MIFAREReader.MFRC522_Anticoll()
                if status == MIFAREReader.MI_OK:
                    dt = datetime.now()
                    num = get_card_id(uid)
                  
                    print(f"Card read UID: {num}")
                    if num_dict.get(num) and num_dict[num][1]:
                        blink_red()
                        buzzer()
                        stop_blink()
                        print(f'The card {num} was already used to enter the parking lot.')
                    else:
                        if free_parking_places > 0:
                            num_dict[num] = [dt, True]
                            free_parking_places -= 1
                            print(f'Client {num} entered the parking lot.')
                            blink_green()
                            buzzer()
                            stop_blink()
                        else:
                            print('Sorry, there are no free parking places.')
                            blink_red()
                            buzzer()
                            stop_blink()
                
                    last_scan = datetime.timestamp(datetime.now())
                    print('Place the card close to the reader to scan.')


def get_card_id(uid):
    num = 0
    for i in range(0, len(uid)):
        num += uid[i] << (i*8)

    return num


def disconnect_from_broker():
   client.disconnect()


def run_entrance_machine():
    connect_to_broker()
    add_detect_buttons()
    print('Place the card close to the reader to scan.')
    read_cards()
    disconnect_from_broker()
    GPIO.cleanup()


if __name__ == "__main__":
    run_entrance_machine()
    GPIO.cleanup()  # pylint: disable=no-member
    