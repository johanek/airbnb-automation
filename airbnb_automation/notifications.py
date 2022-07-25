import logging
import requests

LOGGER = logging.getLogger('airbnb_automation')


class Notifications():
    def __init__(self, config):
        self.config = config
        if config['debug']:
            self.telegram_chat_id = config['telegram_chat_id_debug']
            self.telegram_private_chat_id = config[
                'telegram_private_chat_id_debug']
        else:
            self.telegram_chat_id = config['telegram_chat_id']
            self.telegram_private_chat_id = config['telegram_private_chat_id']

    def send_telegram_public(self, message):
        self.send_telegram(message, self.telegram_chat_id)

    def send_telegram_private(self, message):
        self.send_telegram(message, self.telegram_private_chat_id)

    def send_telegram(self, message, chat_id):
        bot_token = self.config['telegram_bot_token']
        send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=Markdown&text=' + message

        response = requests.get(send_text)

        return response.json()
