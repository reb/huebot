# huebot
Connecting [Philips Hue](www.meethue.com) lights with the build status is no easy task. Hue lights are only accessible from the local networkj, a build server is usually elsewhere.

This solution revolves around using [Slack](slack.com) as a communication layer between the two. Host this Slack bot on the local network and integrate build servers into Slack. When set up this will turn lights red when a build fails, orange if it's unstable, and flash green for a minute when it's back to normal.

## Requirements
* [Python 3](https://www.python.org/downloads/)
* [phue](https://github.com/studioimaginaire/phue)
* [slackclient](https://github.com/slackapi/python-slackclient)

## Usage
Find a machine to run this Slack bot on. A [Raspberry Pi](www.raspberrypi.org) works great. Hook it up to the local network and download this repository to it.
### Configuration
* Copy `huebot.ini.example` to `huebot.ini`
* [Create a bot user on Slack](https://my.slack.com/services/new/bot) and enter the API Token into the `[SLACK]` section under `Token`
* Enter a channel name at `ReportingChannel` under the `[SLACK]` section to have a report on why the lights turned red, else remove that line
* [Find the IP of the Hue bridge](https://www.meethue.com/api/nupnp) and enter it into the `[HUE]` section under `BridgeIp`
### First run
Start with 
```
python huebot.py
``` 
or depending on how Python 3 is installed
```
python3 huebot.py
``` 
Press the button on the Hue bridge this will setup and store the token needed to connect to the bridge in future runs.

### Setting up monitoring channels
For every build you want to monitor
* Create a channel in Slack, set the purpose or topic to describe the build
* Let the build server post to that channel
* Invite the huebot Slack bot user

### Test monitoring
If `-test-` is added to the channel name the build posting there will only cause an orange warning light when it fails.
