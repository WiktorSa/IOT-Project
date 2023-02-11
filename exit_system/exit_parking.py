#!/usr/bin/env python3

import time
import RPi.GPIO as GPIO
from config import * 
from mfrc522 import MFRC522
import paho.mqtt.client as mqtt
import neopixel
import board
from PIL import Image, ImageDraw, ImageFont
import lib.oled.SSD1331 as SSD1331

broker = "10.108.33.124"
client = mqtt.Client()
pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)
disp = SSD1331.SSD1331()
fontLarge = ImageFont.truetype('./lib/oled/Font.ttf', 20)
fontSmall = ImageFont.truetype('./lib/oled/Font.ttf', 13)
MIFAREReader = MFRC522()
is_working = True


def connect_to_broker():
   client.connect(broker)
   client.on_message = read_info
   client.loop_start()
   client.subscribe("terminal1")


def send_info(message, card_id=0):
    client.publish("terminal1", f'{message} {card_id}')


def read_info(client, userdata, message):
    message_decoded = str(message.payload.decode("utf-8"))

    if message_decoded == "exit_allowed":
        print("Exit allowed")
        draw_oled(True)
        blink_blue()
        buzzer()
        stop_blink()
        empty_oled()

    elif message_decoded == "exit_not_allowed":
        print("Exit denied")
        draw_oled(False)
        blink_red()
        buzzer()
        stop_blink()
        empty_oled()


def init_display():
    disp.Init()
    disp.clear()


def add_detect_buttons():
    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=green_button_pressed_callback, bouncetime=2000)
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=red_button_pressed_callback, bouncetime=2000)
    

def green_button_pressed_callback(channel):
    send_info("exit_gate_open_button")
    draw_oled(True)
    blink_blue()
    buzzer()
    stop_blink()
    empty_oled()


def red_button_pressed_callback(channel):
    global is_working
    buzzer()
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
                card_id = get_card_id(uid)
                send_info("exit_gate_open_card", card_id)
                time.sleep(2)
                print('Place the card close to the reader to scan.')


def get_card_id(uid):
    num = 0
    for i in range(0, len(uid)):
        num += uid[i] << (i*8)

    return num


def draw_oled(is_exit_allowed):
    image1 = Image.new("RGB", (disp.width, disp.height), "WHITE")
    draw = ImageDraw.Draw(image1)
    if is_exit_allowed:
        draw.text((8, 0), u'EXIT', font=fontSmall, fill="BLACK")
        draw.text((8, 16), u'ALLOWED', font=fontSmall, fill="BLACK")
    else:
        draw.text((8, 0), u'EXIT', font=fontSmall, fill="BLACK")
        draw.text((8, 16), u'BLOCKED', font=fontSmall, fill="BLACK")
    disp.ShowImage(image1, 0, 0)


def empty_oled():
    image1 = Image.new("RGB", (disp.width, disp.height), "WHITE")
    disp.ShowImage(image1, 0, 0)


def disconnect_from_broker():
    client.loop_stop()
    client.disconnect()


def run_exit_machine():
    connect_to_broker()
    init_display()
    add_detect_buttons()
    print('Place the card close to the reader to scan.')
    try:
        read_cards()
    except KeyboardInterrupt:
        pass
    disconnect_from_broker()
    disp.clear()
    disp.reset()
    GPIO.cleanup()


if __name__ == "__main__":
    run_exit_machine()
