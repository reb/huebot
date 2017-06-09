"""HueBot Slack bot connects Slack channels to Hue lights."""
from time import sleep
from traceback import print_exc
from configparser import ConfigParser
from slackclient import SlackClient
from phue import Bridge, AllLights
from huebot import State


FAILURE_HUE = 0
FAILURE_SATURATION = 254

WARNING_HUE = 6865
WARNING_SATURATION = 223

NORMAL_HUE = 10991
NORMAL_SATURATION = 78

SUCCESS_HUE = 25600
SUCCESS_SATURATION = 254


slack_client = None

all_lights = None


def indicate_failure():
    """Turn to lights to failure colors."""
    all_lights.hue = FAILURE_HUE
    all_lights.saturation = FAILURE_SATURATION


def indicate_warning():
    """Turn to lights to warning colors."""
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


def parse_test_message(output):
    """Parse user written test messages."""
    if 'text' in output:
        if output['text'] == 'failure':
            State.failure(output['channel'])
        elif output['text'] == 'warning':
            State.warning(output['channel'])
        elif output['text'] == 'normal':
            State.normal(output['channel'])


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
    config = ConfigParser()
    try:
        config.read('huebot.ini')
        slack_bot_token = config['SLACK']['Token']
        hue_bridge_ip = config['HUE']['BridgeIp']
        debug = config.getboolean('GENERAL', 'Debug', fallback=False)

    except:
        print("Missing or invalid huebot.ini file")
        exit()

    State.set_on_failure(indicate_failure)
    State.set_on_warning(indicate_warning)
    State.set_on_normal(back_to_normal)

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
