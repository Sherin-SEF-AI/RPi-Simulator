#!/usr/bin/env python3
"""
PiStudio Example: LED Blink

Simple LED blinking example demonstrating basic GPIO output.
"""

import RPiSim.GPIO as GPIO
import time

# Configuration
LED_PIN = 18
BLINK_COUNT = 10
BLINK_DELAY = 0.5

def main():
    """Main function"""
    print("PiStudio LED Blink Example")
    print(f"LED Pin: GPIO{LED_PIN}")
    print(f"Blink Count: {BLINK_COUNT}")
    print(f"Delay: {BLINK_DELAY}s")
    print("-" * 30)
    
    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_PIN, GPIO.OUT)
    
    try:
        for i in range(BLINK_COUNT):
            # Turn LED on
            GPIO.output(LED_PIN, GPIO.HIGH)
            print(f"Blink {i+1}: LED ON")
            time.sleep(BLINK_DELAY)
            
            # Turn LED off
            GPIO.output(LED_PIN, GPIO.LOW)
            print(f"Blink {i+1}: LED OFF")
            time.sleep(BLINK_DELAY)
            
        print("Blink sequence complete!")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        
    finally:
        GPIO.cleanup()
        print("GPIO cleanup complete")

if __name__ == "__main__":
    main()