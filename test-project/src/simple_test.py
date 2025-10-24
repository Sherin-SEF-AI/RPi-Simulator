#!/usr/bin/env python3
"""
Simple test script for PiStudio
"""

import RPiSim.GPIO as GPIO
import time

print("PiStudio Simple Test")
print("Setting up GPIO...")

GPIO.setmode(GPIO.BCM)
LED_PIN = 18
GPIO.setup(LED_PIN, GPIO.OUT)

print("Blinking LED 3 times...")

for i in range(3):
    print(f"Blink {i+1}: LED ON")
    GPIO.output(LED_PIN, GPIO.HIGH)
    time.sleep(0.2)
    
    print(f"Blink {i+1}: LED OFF")
    GPIO.output(LED_PIN, GPIO.LOW)
    time.sleep(0.2)

print("Test complete!")
GPIO.cleanup()