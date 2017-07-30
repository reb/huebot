"""HueBot Slack bot connects Slack channels to Hue lights."""
from time import sleep
from traceback import print_exc
from configparser import ConfigParser
from configparser import Error as ConfigParserError
import huebot.state
import huebot.hue
import huebot.slack


if __name__ == '__main__':
    config = ConfigParser()
    try:
        config.read('huebot.ini')
        slack_token = config['SLACK']['Token']
        hue_bridge_ip = config['HUE']['BridgeIp']
        debug = config.getboolean('GENERAL', 'Debug', fallback=False)

    except ConfigParserError:
        print("Missing or invalid huebot.ini file")
        exit()

    state = huebot.state.State()

    while True:
        try:
            huebot.hue.HueLights(hue_bridge_ip, state)
            slack = huebot.slack.Slack(slack_token, state)

            while(True):
                slack.read()
                sleep(1)

        except KeyboardInterrupt:
            exit()
        except:
            if debug:
                raise

            # unknown error occurred, log & restart in a minute
            print_exc()
            sleep(60)
