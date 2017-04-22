"""HueBot Slack bot connects Slack channels to Hue lights."""
import time
import configparser
from slackclient import SlackClient
from phue import Bridge, AllLights


NORMAL = 'normal'
NORMAL_HUE = 7316
NORMAL_SATURATION = 204

SUCCESS_HUE = 25600
SUCCESS_SATURATION = 254

FAILURE = 'failure'
FAILURE_HUE = 0
FAILURE_SATURATION = 254

slack_client = None

all_lights = None


class State:
    """Static class that tracks and handles state changes."""

    _failures = set()

    @staticmethod
    def _on_failure():
        pass

    @staticmethod
    def _on_normal():
        pass

    @classmethod
    def set_on_failure(cls, callback):
        """Set the method to be executed when the status changes to failure."""
        cls._on_failure = callback

    @classmethod
    def set_on_normal(cls, callback):
        """Set the method to be executed when the status changes to normal."""
        cls._on_normal = callback

    def observe(func):
        """
        Decorate functions with an observer pattern.

        Checks the failure status before and after executing the decorated
        function. If it changed, execute the proper callback.
        """
        def add_observer(*args):
            """Check the failure status and handle accordingly."""
            failure_before = State.is_failure()
            func(*args)
            print("failures:", State._failures)
            failure_after = State.is_failure()

            if failure_before and not failure_after:
                State._on_normal()

            if not failure_before and failure_after:
                State._on_failure()

        return add_observer

    @classmethod
    @observe
    def failure(cls, key):
        """Add a failure for the given key."""
        cls._failures.add(key)

    @classmethod
    @observe
    def normal(cls, key):
        """Remove any status for the given key."""
        try:
            cls._failures.remove(key)
        except KeyError:
            pass

    @classmethod
    def is_failure(cls):
        """Return the current failure status."""
        return len(cls._failures) > 0


def indicate_failure():
    """Turn to lights to failure colors."""
    all_lights.hue = FAILURE_HUE
    all_lights.saturation = FAILURE_SATURATION


def back_to_normal():
    """Set the lights back to normal."""
    # celebrate success
    all_lights.hue = SUCCESS_HUE
    all_lights.saturation = SUCCESS_SATURATION
    time.sleep(1)
    # slowly transition to normal
    all_lights.transitiontime = 600
    all_lights.hue = NORMAL_HUE
    all_lights.saturation = NORMAL_SATURATION
    # reset the transitiontime
    all_lights.transitiontime = None


def parse_test_message(output):
    """Parse user written test messages."""
    if 'text' in output and output['text'] in (NORMAL, FAILURE):
        # update_state(output['text'], output['channel'])
        if output['text'] == NORMAL:
            notify = State.normal
        elif output['text'] == FAILURE:
            notify = State.failure

        notify(output['channel'])


def parse_jenkins_message(output):
    """Parse Jenkins written messages."""
    if 'attachments' in output:
        for attachment in output['attachments']:
            # green color from attachment 'good' setting
            if attachment['color'] == '36a64f':
                State.normal(output['channel'])
            # red color from attachment 'danger' setting
            elif attachment['color'] == 'd00000':
                State.failure(output['channel'])


def parse_slack_output(rtm_output):
    """Parse the Slack RTM API events firehose for relevant messages."""
    for output in rtm_output:
        parse_test_message(output)
        parse_jenkins_message(output)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    try:
        config.read('huebot.ini')
        slack_bot_token = config['SLACK']['Token']
        hue_bridge_ip = config['HUE']['BridgeIp']
        debug = config.getboolean('GENERAL', 'Debug', fallback=False)

    except:
        print("Missing or invalid huebot.ini file")
        exit()

    State.set_on_normal(back_to_normal)
    State.set_on_failure(indicate_failure)

    while True:
        try:
            HUE_BRIDGE = Bridge(hue_bridge_ip)
            all_lights = AllLights(HUE_BRIDGE)

            print("HueBot connected with Hue Bridge!")

            slack_client = SlackClient(slack_bot_token)
            if slack_client.rtm_connect():
                print("HueBot connected to Slack!")
                while True:
                    parse_slack_output(slack_client.rtm_read())
                    time.sleep(1)
            else:
                print("HueBot did not connect, check bot ID and Slack token")
        except KeyboardInterrupt:
            exit()
        except:
            if debug:
                raise

            # unknown error occurred, restart in a minute
            time.sleep(60)
