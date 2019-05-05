''' cli '''

import getopt
import sys
import yaml
from voluptuous import Schema, Required, MultipleInvalid, Optional


def getconfig(argv):
    ''' process command line arguments '''
    try:
        opts, _ = getopt.getopt(
            argv, "c:h", ['config', 'help'])  # pylint: disable=unused-variable
        if not opts:
            raise SystemExit(usage())
    except getopt.GetoptError:
        raise SystemExit(usage())

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        elif opt in ('-c', '--config'):
            config = loadconfig(arg)
            with open(arg, 'r') as stream:
                config = yaml.load(stream, Loader=yaml.FullLoader)
        else:
            raise SystemExit(usage())

    return config


def loadconfig(filename):
    ''' load config and validate schema '''
    with open(filename, 'r') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    configschema = {
        Required('airbnb_ics'): str,
        Required('google_calendar_id'): str,
        Required('twilio_account_sid'): str,
        Required('twilio_auth_token'): str,
        Required('cleaner_number'): str,
        Required('twilio_from_number'): str,
        Required('telegram_bot_token'): str,
        Required('telegram_chat_id'): str,
        Required('telegram_private_chat_id'): str,
        Optional('telegram_chat_id_debug'): str,
        Optional('telegram_private_chat_id_debug'): str,
        Required('nello_client_id'): str,
        Required('nello_username'): str,
        Required('nello_password'): str,
        Optional('webhook_url'): str,
        Optional('enable_webhook'): bool,
        Required('debug'): bool,
    }

    try:
        schema = Schema(configschema, extra=False)
        schema(config)
    except MultipleInvalid as e:
        print("Missing values from config file!")
        print(str(e))
        sys.exit(1)

    return config


def usage():
    ''' usage info '''
    output = """
Usage:
  airbnb_automation -c configfile

Options:
  -c <configfile>   Read config from configfile"""

    return output
