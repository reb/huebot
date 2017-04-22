import time
from slackclient import SlackClient
from phue import Bridge, AllLights

# Slack setup
SLACK_BOT_ID = ''
SLACK_BOT_TOKEN = ''

# Hue setup
HUE_BRIDGE_IP = ''

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

current_state = {}

def update_state(new_state, channel):
    """
        Checks the latest state against the current state and updates
        lights accordingly
    """

    change = False
    # check for a change
    if channel not in current_state or channel in current_state and \
            current_state[channel] != new_state:
        change = True

    # check if a new failure appeared an no previous channels are failing
    if change and new_state == FAILURE and all_states(NORMAL):
        indicate_failure()

    # update state
    current_state[channel] = new_state
    print(current_state)

    # check if state went back to normal and everything is now normal
    if change and new_state == NORMAL and all_states(NORMAL):
        back_to_normal()


def all_states(state):
    """
        Returns true if everything in current_state is of the provided state
    """

    return all(state == s for s in current_state.values())


def indicate_failure():
    """
        Turn to lights to failure colors
    """

    all_lights.hue = FAILURE_HUE
    all_lights.saturation = FAILURE_SATURATION


def back_to_normal():
    """
        Set the lights back to normal
    """

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
    if 'text' in output and 'user' in output and output['user'] != SLACK_BOT_ID:
        update_state(output['text'], output['channel'])

def parse_jenkins_message(output):
    if 'attachments' in output:
        for attachment in output['attachments']:
            if attachment['color'] == '36a64f': # green color from attachment 'good' setting
                update_state(NORMAL, output['channel'])
            elif attachment['color'] == 'd00000': # red color from attachment 'danger' setting
                update_state(FAILURE, output['channel'])

def parse_slack_output(rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        Parse the output and see if any messages contain state updates.
    """
    for output in rtm_output:
        parse_test_message(output)
        parse_jenkins_message(output)

if __name__ == '__main__':

    while True: 
        try:
            hue_bridge = Bridge(HUE_BRIDGE_IP)
            all_lights = AllLights(hue_bridge)

            print("HueBot connected with Hue Bridge!")

            slack_client = SlackClient(SLACK_BOT_TOKEN)
            if slack_client.rtm_connect():
                print("HueBot connected to Slack!")
                while True:
                    parse_slack_output(slack_client.rtm_read())
                    time.sleep(1)
            else:
                print("HueBot did not connect, check bot ID and Slack token")
        except:
            # error occurred, restart in a min
            time.sleep(60)
