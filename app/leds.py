"""Status LEDs (BCM pins): green=GPIO17 nut only, red=GPIO27 bolt only, blue=GPIO22 nut+bolt (priority).
Each LED: GPIO -> 330 ohm -> LED long leg, short leg -> GND. Falls back to a no-op if GPIO is unavailable."""
PINS = {"green": 17, "red": 27, "blue": 22}


class Leds:
    def __init__(self):
        self.leds, self.state, self._pending, self._n = {}, "off", "off", 0
        try:
            from gpiozero import LED, Device
            from gpiozero.pins.lgpio import LGPIOFactory
            Device.pin_factory = LGPIOFactory()
            self.leds = {k: LED(p) for k, p in PINS.items()}
        except Exception as e:                      # no GPIO / not permitted: keep the app running
            print(f"[leds] GPIO unavailable, LEDs disabled: {e}")

    @staticmethod
    def pick(nuts, bolts):
        if nuts and bolts:
            return "blue"
        return "green" if nuts else "red" if bolts else "off"

    def _apply(self, colour):
        for k, led in self.leds.items():
            led.on() if k == colour else led.off()  # exactly one on, others forced off
        self.state = colour

    def update(self, nuts, bolts, confirm=2):
        """Switch only after `confirm` consecutive frames agree, so a single missed frame doesn't flicker."""
        want = self.pick(nuts, bolts)
        self._n = self._n + 1 if want == self._pending else 1
        self._pending = want
        if want != self.state and self._n >= confirm:
            self._apply(want)

    def off(self):
        self._pending = "off"
        self._apply("off")

    def close(self):
        self.off()
        for led in self.leds.values():
            led.close()


if __name__ == "__main__":                          # wiring test: green -> red -> blue -> off
    import time
    L = Leds()
    for c in ("green", "red", "blue", "off"):
        L._apply(c)
        print("LED:", c)
        time.sleep(1.2)
    L.close()
