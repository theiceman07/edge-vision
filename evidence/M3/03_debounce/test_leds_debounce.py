import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from leds import Leds  # noqa: E402  (no GPIO needed: the class falls back to a no-op)


def feed(leds, frames, confirm=2):
    for nuts, bolts in frames:
        leds.update(nuts, bolts, confirm=confirm)
    return leds.state


def test_pick_priority():
    assert Leds.pick(1, 0) == "green" and Leds.pick(0, 2) == "red"
    assert Leds.pick(1, 1) == "blue"          # both -> blue wins
    assert Leds.pick(0, 0) == "off"


def test_single_bad_frame_does_not_switch():
    leds = Leds()
    assert feed(leds, [(1, 0)] * 3) == "green"
    assert feed(leds, [(0, 0)]) == "green"    # one missed frame: LED stays
    assert feed(leds, [(1, 0)]) == "green"    # and recovers without flicker


def test_n_consecutive_frames_switch():
    leds = Leds()
    feed(leds, [(1, 0)] * 3)
    assert feed(leds, [(0, 0)] * 2) == "off"  # confirm=2 consecutive frames switch it
    assert feed(leds, [(0, 1)] * 2) == "red"


def test_confirm_n_is_respected():
    leds = Leds()
    feed(leds, [(1, 0)] * 4, confirm=4)
    assert feed(leds, [(0, 1)] * 3, confirm=4) == "green"   # 3 of 4 required frames: not yet
    assert feed(leds, [(0, 1)], confirm=4) == "red"
