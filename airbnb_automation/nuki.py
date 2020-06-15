import logging
import requests

LOGGER = logging.getLogger('airbnb_automation')
OPENER_MODES = {
  0: "uninitialized",
  1: "pairing",
  2: "door",
  3: "continuous",
  4: "maintenance",
}

OPENER_ACTIONS = {
  1: "activate rto",
  2: "deactivate rto",
  3: "electric strike actuation",
  6: "activate cm",
  7: "deactivate cm",
}

class Nuki():
  def __init__(self, config):
      self.config = config
      self.api_base = 'https://api.nuki.io'

      self.header =  {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer {}'.format(self.config['nuki_api_key'])
      }

  def opener_mode(self):
    opener = self._get_smartlock()[0]
    return(self._opener_mode(opener['state']['mode']))

  def battery_critical(self):
    opener = self._get_smartlock()[0]
    return(opener['state']['batteryCritical'])

  def set_opener_mode(self, mode):
    if mode not in ['continuous', 'disabled']:
      LOGGER.warning('{} is not a valid opener mode'.format(mode))
      LOGGER.warning('Valid modes: continuous or disabled')
      return False

    if mode == 'continuous':
      action = 6
    else:
      action = 7

    body = {
      "action": action
    }

    result = requests.post('{}/smartlock/{}/action'.format(self.api_base, self.smartlock_id()), headers=self.header, json=body)
    if result.status_code != 204:
      LOGGER.info('error setting opener mode {}'.format(mode))
      LOGGER.info(result.json())
      return False

    return True

  def smartlock_id(self):
    opener = self._get_smartlock()[0]
    return opener['smartlockId']

  def log(self):
    result = requests.get('{}/smartlock/{}/log'.format(self.api_base, self.smartlock_id()), headers=self.header)
    return result.json()

  def _opener_mode(self, val):
    return OPENER_MODES[val]

  def _get_smartlock(self):
    result = requests.get('{}/smartlock'.format(self.api_base), headers=self.header)
    return result.json()