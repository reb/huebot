"""HueBot Slack bot connects Slack channels to Hue lights."""
from time import sleep
from traceback import print_exc
from configparser import ConfigParser
from configparser import Error as ConfigParserError
from slackclient import SlackClient
from phue import Bridge, AllLights
import huebot.state


FAILURE_HUE = 0
FAILURE_SATURATION = 254

WARNING_HUE = 6865
WARNING_SATURATION = 223

NORMAL_HUE = 10991
NORMAL_SATURATION = 78

SUCCESS_HUE = 25600
SUCCESS_SATURATION = 254


slack_client = None
slack_channels = {}

# These are the colors for slack attachment messages
GOOD = '36a64f'
WARNING = 'daa038'
DANGER = 'd00000'

all_lights = None


def indicate_failure():
    """Turn lights to failure colors."""
    all_lights.hue = FAILURE_HUE
    all_lights.saturation = FAILURE_SATURATION


def indicate_warning():
    """Turn lights to warning colors."""
    all_lights.hue = WARNING_HUE
    all_lights.saturation = WARNING_SATURATION


def back_to_normal():
    """Set the lights back to normal."""
    # celebrate success
    all_lights.hue = SUCCESS_HUE
    all_lights.saturation = SUCCESS_SATURATION
    sleep(1)
    # slowly transition to normal
    all_lights.transitiontime = 600
    all_lights.hue = NORMAL_HUE
    all_lights.saturation = NORMAL_SATURATION
    # reset the transitiontime
    all_lights.transitiontime = None


def get_channel_name(channel):
    """Retrieve the a channel's name from the Slack API."""
    global slack_channels

    try:
        return slack_channels[channel]
    except KeyError:
        try:
            response = slack_client.api_call('channels.info', channel=channel)
            name = response['channel']['name']
            slack_channels[channel] = name
            return name

        except KeyError:
            response = slack_client.api_call('groups.info', channel=channel)
            name = response['group']['name']
            slack_channels[channel] = name
            return name


def parse_test_message(output, state):
    """Parse user written test messages."""
    try:
        channel = get_channel_name(output['channel'])
        text = output['text']
    except KeyError:
        return False

    if text == 'failure':
        state.failure(channel)
    elif text == 'warning':
        state.warning(channel)
    elif text == 'normal':
        state.normal(channel)


def parse_jenkins_message(output, state):
    """Parse Jenkins written messages."""
    try:
        channel = get_channel_name(output['channel'])
        color = output['attachments'][0]['color']
    except KeyError:
        return False

    if "-test-" in channel:
        if color == GOOD:
            state.normal(channel)
        elif color == WARNING:
            state.warning(channel)
        elif color == DANGER:
            state.warning(channel)
    else:
        if color == GOOD:
            state.normal(channel)
        elif color == WARNING:
            state.warning(channel)
        elif color == DANGER:
            state.failure(channel)


def parse_slack_output(rtm_output, state):
    """Parse the Slack RTM API events firehose for relevant messages."""
    for output in rtm_output:
        parse_test_message(output, state)
        parse_jenkins_message(output, state)


if __name__ == '__main__':
    config = ConfigParser()
    try:
        config.read('huebot.ini')
        slack_bot_token = config['SLACK']['Token']
        hue_bridge_ip = config['HUE']['BridgeIp']
        debug = config.getboolean('GENERAL', 'Debug', fallback=False)

    except ConfigParserError:
        print("Missing or invalid huebot.ini file")
        exit()

    state = huebot.state.State()
    state.on_failure = indicate_failure
    state.on_warning = indicate_warning
    state.on_normal = back_to_normal

    while True:
        try:
            HUE_BRIDGE = Bridge(hue_bridge_ip)
            all_lights = AllLights(HUE_BRIDGE)

            print("HueBot connected with Hue Bridge!")

            slack_client = SlackClient(slack_bot_token)
            if slack_client.rtm_connect():
                print("HueBot connected to Slack!")
                while True:
                    parse_slack_output(slack_client.rtm_read(), state)
                    sleep(1)
            else:
                print("HueBot did not connect, check bot ID and Slack token")
        except KeyboardInterrupt:
            exit()
        except:
            if debug:
                raise

            # unknown error occurred, log & restart in a minute
            print_exc()
            sleep(60)
