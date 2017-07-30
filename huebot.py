"""HueBot Slack bot connects Slack channels to Hue lights."""
from time import sleep
from traceback import print_exc
from configparser import ConfigParser
from configparser import Error as ConfigParserError
from slackclient import SlackClient
import huebot.state
import huebot.hue


slack_client = None
slack_channels = {}

# These are the colors for slack attachment messages
GOOD = '36a64f'
WARNING = 'daa038'
DANGER = 'd00000'


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

    while True:
        try:
            huebot.hue.HueLights(hue_bridge_ip, state)

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
