"""Philips Hue interactions for HueBot."""
from time import sleep
from phue import Bridge, AllLights


FAILURE_HUE = 0
FAILURE_SATURATION = 254

WARNING_HUE = 6865
WARNING_SATURATION = 223

NORMAL_HUE = 10991
NORMAL_SATURATION = 78

SUCCESS_HUE = 25600
SUCCESS_SATURATION = 254


class HueLights:
    """Hue lights connection object."""

    def __init__(self, hue_bridge_ip, state):
        """Connect to Hue bridge and set up callback handlers in state."""
        self.bridge = Bridge(hue_bridge_ip)
        self.all_lights = AllLights(self.bridge)

        print("HueBot connected with Hue Bridge!")

        state.on_failure = self.indicate_failure
        state.on_warning = self.indicate_warning
        state.on_normal = self.back_to_normal

    def indicate_failure(self):
        """Turn lights to failure colors."""
        self.all_lights.hue = FAILURE_HUE
        self.all_lights.saturation = FAILURE_SATURATION

    def indicate_warning(self):
        """Turn lights to warning colors."""
        self.all_lights.hue = WARNING_HUE
        self.all_lights.saturation = WARNING_SATURATION

    def back_to_normal(self):
        """Set the lights back to normal."""
        # celebrate success
        self.all_lights.hue = SUCCESS_HUE
        self.all_lights.saturation = SUCCESS_SATURATION
        sleep(1)
        # slowly transition to normal
        self.all_lights.transitiontime = 600
        self.all_lights.hue = NORMAL_HUE
        self.all_lights.saturation = NORMAL_SATURATION
        # reset the transitiontime
        self.all_lights.transitiontime = None
