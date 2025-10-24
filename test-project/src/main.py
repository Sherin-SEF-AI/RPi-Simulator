#!/usr/bin/env python3
"""
PiStudio Project - Python Template
"""

import RPiSim.GPIO as GPIO
import time

# Setup
GPIO.setmode(GPIO.BCM)
LED_PIN = 18
GPIO.setup(LED_PIN, GPIO.OUT)

try:
    print("Starting LED blink demo...")
    while True:
        GPIO.output(LED_PIN, GPIO.HIGH)
        print("LED ON")
        time.sleep(0.5)
        
        GPIO.output(LED_PIN, GPIO.LOW)
        print("LED OFF")
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("\nStopping...")
    
finally:
    GPIO.cleanup()
