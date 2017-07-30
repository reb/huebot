"""Slack interactions module for HueBot."""
from slackclient import SlackClient

# These are the colors for slack message attachments
GOOD = '36a64f'
WARNING = 'daa038'
DANGER = 'd00000'


def _parse(func):
    """
    Indicate that the function parses the Slack RTM API output.

    Expected is that it takes one line of the RTM output and handles
    any potential state changes using the self.state object.
    """
    func._parse_func = True
    return func


class Slack:
    """Object to connect to Slack and react to messages."""

    def __init__(self, slack_token, state):
        """Connect to Slack and setup the object."""
        self.channels = {}
        self.client = SlackClient(slack_token)
        if self.client.rtm_connect():
            print("HueBot connected to Slack!")
        else:
            print("HueBot did not connect to Slack")
            raise IOError

        self.state = state
        self.state.on_new_failure = self.message_failure
        self.state.on_new_warning = self.message_warning

        # Retrieve parse functions
        self.parse_functions = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            try:
                if attr._parse_func:
                    self.parse_functions.append(attr)
            except AttributeError:
                pass

    def get_channel_name(self, channel):
        """Get the channel name for the given channel."""
        try:
            return self.channels[channel]
        except KeyError:
            try:
                return self.__retrieve_channel_name(channel)

            except KeyError:
                return self.__retrieve_group_name(channel)

    def __retrieve_channel_name(self, channel):
        response = self.client.api_call('channels.info', channel=channel)
        name = response['channel']['name']
        self.channels[channel] = name
        return name

    def __retrieve_group_name(self, group):
        response = self.client.api_call('groups.info', channel=group)
        name = response['group']['name']
        self.channels[group] = name
        return name

    def read(self):
        """Read the output from the RTM stream."""
        rtm_output = self.client.rtm_read()
        for output in rtm_output:
            for parse in self.parse_functions:
                parse(output)

    def message_failure(self, channel):
        """Send a message to indicate a failure happening."""
        print("Things failed")

    def message_warning(self, channel):
        """Send a message to indicate a failure happening."""
        print("Things are unstable")

    @_parse
    def __test(self, output):
        """Parse user written test messages."""
        try:
            channel = self.get_channel_name(output['channel'])
            text = output['text']
        except KeyError:
            return False

        if text == 'failure':
            self.state.failure(channel)
        elif text == 'warning':
            self.state.warning(channel)
        elif text == 'normal':
            self.state.normal(channel)

    @_parse
    def __jenkins(self, output):
        """Parse Jenkins written messages."""
        try:
            channel = self.get_channel_name(output['channel'])
            color = output['attachments'][0]['color']
        except KeyError:
            return False

        if "-test-" in channel:
            if color == GOOD:
                self.state.normal(channel)
            elif color == WARNING:
                self.state.warning(channel)
            elif color == DANGER:
                self.state.warning(channel)
        else:
            if color == GOOD:
                self.state.normal(channel)
            elif color == WARNING:
                self.state.warning(channel)
            elif color == DANGER:
                self.state.failure(channel)
