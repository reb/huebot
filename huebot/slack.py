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

    def __init__(self, slack_token, reporting_channel, state):
        """Connect to Slack and setup the object."""
        self.channels = {}
        self.client = SlackClient(slack_token)
        if self.client.rtm_connect():
            print("HueBot connected to Slack!")
        else:
            print("HueBot did not connect to Slack")
            raise IOError
        self.reporting_channel = reporting_channel

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

    def get_channel_description(self, channel):
        """Get the channel description for the given channel."""
        if channel not in self.channels:
            self.get_channel_name(channel)

        if not self.channels[channel]['description']:
            return self.channels[channel]['name']

        return self.channels[channel]['description']

    def get_channel_name(self, channel):
        """Get the channel name for the given channel."""
        try:
            return self.channels[channel]['name']
        except KeyError:
            try:
                return self.__request_channel_name(channel)

            except KeyError:
                return self.__request_group_name(channel)

    def __request_channel_name(self, channel):
        response = self.client.api_call('channels.info', channel=channel)
        name = response['channel']['name']
        self.channels[channel] = {
            'name': name,
            'description': self.__get_description(response['channel'])
        }
        return name

    def __request_group_name(self, group):
        response = self.client.api_call('groups.info', channel=group)
        name = response['group']['name']
        self.channels[group] = {
            'name': name,
            'description': self.__get_description(response['group'])
        }
        return name

    def __get_description(self, channel_response):
        if channel_response['purpose']['value']:
            return channel_response['purpose']['value']
        if channel_response['topic']['value']:
            return channel_response['topic']['value']
        return ''

    def read(self):
        """Read the output from the RTM stream."""
        rtm_output = self.client.rtm_read()
        for output in rtm_output:
            for parse in self.parse_functions:
                parse(output)

    def message_failure(self, channel):
        """Send a message to indicate a failure happening."""
        description = self.get_channel_description(channel)
        self.__send_message("<!here> {} has failed".format(description))

    def message_warning(self, channel):
        """Send a message to indicate a warning happening."""
        description = self.get_channel_description(channel)
        self.__send_message("{} is unstable".format(description))

    def __send_message(self, message):
        if self.reporting_channel is None:
            return

        call = {
            'channel': self.reporting_channel,
            'text': message
        }
        self.client.api_call('chat.postMessage', **call)

    @_parse
    def __test(self, output):
        """Parse user written test messages."""
        try:
            channel = output['channel']
            text = output['text']
        except KeyError:
            return False
        except TypeError:
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
            channel = output['channel']
            channel_name = self.get_channel_name(channel)
            color = output['attachments'][0]['color']
        except KeyError:
            return False
        except TypeError:
            return False

        if "-test-" in channel_name:
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
