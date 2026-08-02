"""
Demo direct flight control for Parrot Swing.

Author: Victor804
"""

import argparse
import os

from pyparrot.Minidrone import Swing


DEFAULT_SWING_ADDR = "e0:14:89:09:3d:cb"


def parse_args():
    parser = argparse.ArgumentParser(description="Connect to and optionally fly a Parrot Swing.")
    parser.add_argument(
        "--addr",
        default=os.environ.get("SWING_ADDR", DEFAULT_SWING_ADDR),
        help="Swing BLE address. Defaults to SWING_ADDR or the saved address in this file.",
    )
    parser.add_argument(
        "--connect-only",
        action="store_true",
        help="Only test the BLE connection, then disconnect without taking off.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Connection retry count.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    swing = Swing(args.addr)

    print("trying to connect")
    success = swing.connect(num_retries=args.retries)
    print("connected: %s" % success)

    if not success:
        return 1

    try:
        if args.connect_only:
            return 0

        print("sleeping")
        swing.smart_sleep(2)
        swing.ask_for_state_update()
        swing.smart_sleep(2)

        print("taking off!")
        swing.safe_takeoff(5)

        print("moving left")
        swing.fly_direct(roll=-20, pitch=0, yaw=0, vertical_movement=0, duration=1)
        swing.smart_sleep(1)

        print("moving right")
        swing.fly_direct(roll=20, pitch=0, yaw=0, vertical_movement=0, duration=1)
        swing.smart_sleep(1)

        print("turning left")
        swing.fly_direct(roll=0, pitch=0, yaw=-20, vertical_movement=0, duration=1)
        swing.smart_sleep(1)

        print("turning right")
        swing.fly_direct(roll=0, pitch=0, yaw=20, vertical_movement=0, duration=1)
        swing.smart_sleep(1)

        print("plane forward")
        swing.set_flying_mode("plane_forward")

        swing.smart_sleep(1)

        print("quadricopter")
        swing.set_flying_mode("quadricopter")

        print("landing")
        swing.safe_land(5)
        swing.smart_sleep(5)
    finally:
        print("disconnect")
        swing.disconnect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
