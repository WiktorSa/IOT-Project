#!/usr/bin/env python3

import time
import RPi.GPIO as GPIO
from config import * 
from mfrc522 import MFRC522
import paho.mqtt.client as mqtt
import neopixel
import board

broker = "10.108.33.124"
client = mqtt.Client()
pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)
MIFAREReader = MFRC522()
is_working = True


def connect_to_broker():
   client.connect(broker)
   client.subscribe("terminal1")


def send_info(message, card_id=0):
    client.publish("terminal2", f'{message} {card_id}')


def read_info(client, userdata, message):
    message_decoded = str(message.payload.decode("utf-8"))

    if message_decoded == "exit_allowed":
        print("Exit allowed")
        blink_blue()
        buzzer()
        stop_blink()

    elif message_decoded == "exit_not_allowed":
        print("Exit denied")
        blink_red()
        buzzer()
        stop_blink()


def add_detect_buttons():
    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=green_button_pressed_callback, bouncetime=200)
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=red_button_pressed_callback, bouncetime=200)
    

def green_button_pressed_callback(channel):
    send_info("exit_gate_open_button")
    blink_blue()
    buzzer()
    stop_blink()


def red_button_pressed_callback(channel):
    global is_working
    is_working = False


def blink_green():
    pixels.fill((0, 255, 0))
    pixels.show()


def blink_blue():
    pixels.fill((0, 0, 255))
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
    while is_working: 
        (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
        if status == MIFAREReader.MI_OK:
            (status, uid) = MIFAREReader.MFRC522_Anticoll()
            if status == MIFAREReader.MI_OK:
                card_id = get_card_id()
                send_info("exit_gate_open_card", card_id)
                time.sleep(5)
                print('Place the card close to the reader to scan.')


def get_card_id(uid):
    num = 0
    for i in range(0, len(uid)):
        num += uid[i] << (i*8)

    return num


def disconnect_from_broker():
   client.disconnect()


def run_exit_machine():
    connect_to_broker()
    add_detect_buttons()
    print('Place the card close to the reader to scan.')
    read_cards()
    disconnect_from_broker()
    GPIO.cleanup()


if __name__ == "__main__":
    run_exit_machine()
