import lgpio
import time

# Pin assignments (BOARD numbers you gave)
CLK = 11   # Rotary encoder pin A (CLK)
DT = 16    # Rotary encoder pin B (DT)
SW = 18    # Switch

# Map BOARD to BCM
BOARD_TO_BCM = {
    11: 17,   # CLK
    16: 23,   # DT
    18: 24,   # SW
}

CLK = BOARD_TO_BCM[CLK]
DT = BOARD_TO_BCM[DT]
SW = BOARD_TO_BCM[SW]

# Open gpiochip
chip = lgpio.gpiochip_open(0)

# Setup pins (inputs only, no pull-ups in lgpio)
lgpio.gpio_claim_input(chip, CLK)
lgpio.gpio_claim_input(chip, DT)
lgpio.gpio_claim_input(chip, SW)

last_clk = lgpio.gpio_read(chip, CLK)
last_button_time = 0
BUTTON_DEBOUNCE = 0.05   # seconds
ROTARY_DEBOUNCE = 0.002  # seconds

print("Rotary encoder ready. Press Ctrl+C to exit.")

try:
    while True:
        clk_state = lgpio.gpio_read(chip, CLK)
        dt_state = lgpio.gpio_read(chip, DT)

        # Rotary detection
        if clk_state != last_clk:
            time.sleep(ROTARY_DEBOUNCE)
            if clk_state == 1:  # rising edge
                if dt_state != clk_state:
                    print("Rotated → CLOCKWISE")
                else:
                    print("Rotated → COUNTERCLOCKWISE")
            last_clk = clk_state

        # Button detection
        button_state = lgpio.gpio_read(chip, SW)
        if button_state == 0:  # pressed
            now = time.time()
            if (now - last_button_time) > BUTTON_DEBOUNCE:
                print("Button pressed!")
                last_button_time = now

        time.sleep(0.001)

except KeyboardInterrupt:
    print("\nExiting...")
finally:
    lgpio.gpiochip_close(chip)
