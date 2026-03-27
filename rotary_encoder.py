import lgpio
import time
import threading

class RotaryEncoder:
    """
    Rotary encoder event handler using lgpio.
    Usage:
        encoder = RotaryEncoder(clk_pin, dt_pin, sw_pin)
        encoder.on_rotate = lambda direction: print("Rotated", direction)
        encoder.on_button = lambda: print("Button pressed!")
        encoder.start()
        ...
        encoder.stop()
    """
    def __init__(self, clk_board=11, dt_board=16, sw_board=18,
                 board_to_bcm=None,
                 button_debounce=0.05, rotary_debounce=0.002, sample_interval=0.001,
                 long_press_threshold=1.0):
        if board_to_bcm is None:
            board_to_bcm = {11: 17, 16: 23, 18: 24}

        self.CLK = board_to_bcm[clk_board]
        self.DT  = board_to_bcm[dt_board]
        self.SW  = board_to_bcm[sw_board]

        self.button_debounce = button_debounce
        self.rotary_debounce = rotary_debounce
        self.sample_interval = sample_interval

        self._chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_input(self._chip, self.CLK)
        lgpio.gpio_claim_input(self._chip, self.DT)
        lgpio.gpio_claim_input(self._chip, self.SW)

        self.last_clk = lgpio.gpio_read(self._chip, self.CLK)
        self.last_button_time = 0
        self._long_press_threshold = long_press_threshold
        self._last_button_state = lgpio.gpio_read(self._chip, self.SW)
        self._button_press_time = None

        self.on_rotate = None  # callback(direction: str: 'CLOCKWISE'/'COUNTERCLOCKWISE')
        self.on_button = None  # callback()
        self.on_long_press = None  # callback() — fired after holding for long_press_threshold seconds
        self._running = False
        self._thread = None

    def _poll_loop(self):
        while self._running:
            clk_state = lgpio.gpio_read(self._chip, self.CLK)
            dt_state = lgpio.gpio_read(self._chip, self.DT)

            # Rotary detection
            if clk_state != self.last_clk:
                time.sleep(self.rotary_debounce)
                if clk_state == 1:  # rising edge
                    if dt_state != clk_state:
                        if self.on_rotate:
                            self.on_rotate('CLOCKWISE')
                    else:
                        if self.on_rotate:
                            self.on_rotate('COUNTERCLOCKWISE')
                self.last_clk = clk_state

            # Button detection (edge-triggered with long-press support)
            button_state = lgpio.gpio_read(self._chip, self.SW)
            now = time.time()
            if button_state != self._last_button_state:
                time.sleep(self.button_debounce)
                button_state = lgpio.gpio_read(self._chip, self.SW)
                if button_state != self._last_button_state:
                    if button_state == 0:  # falling edge — button pressed
                        self._button_press_time = now
                    else:  # rising edge — button released
                        if self._button_press_time is not None:
                            held = now - self._button_press_time
                            if held >= self._long_press_threshold:
                                if self.on_long_press:
                                    self.on_long_press()
                            else:
                                if self.on_button:
                                    self.on_button()
                            self._button_press_time = None
                    self._last_button_state = button_state
                    self.last_button_time = now

            time.sleep(self.sample_interval)

    def start(self):
        """Start polling in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop polling and release GPIO."""
        self._running = False
        if self._thread:
            self._thread.join()
        lgpio.gpiochip_close(self._chip)
