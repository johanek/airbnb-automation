import logging
from datetime import datetime, timedelta
from dateutil import parser
import pytz
from babel.dates import format_date, format_time
from pynello.public import Nello
from icalendar import vDatetime

from airbnb_automation.gcalendar import GCalendar
from airbnb_automation.notifications import Notifications

LOGGER = logging.getLogger('airbnb_automation')

def weekly_message(config):
  cal = GCalendar(config)
  notifications = Notifications(config)

  messages = []

  events = cal.get_public_calendar()
  for event in events:
    start = parser.parse(event['start']['dateTime'])
    end = parser.parse(event['end']['dateTime'])
    now = datetime.now().astimezone(pytz.utc)
    if now > start:
      if end < now + timedelta(days=7):
        messages.append("{} odjizdi {}. ".format(event['summary'], format_date(end, 'EEE d MMM', locale='cs_CZ')))
    elif start < now + timedelta(days=7):
        messages.append("{} prijizdi {} a odjizdi {}.".format(event['summary'], format_date(start, 'EEE d MMM', locale='cs_CZ'), format_date(end, 'EEE d MMM', locale='cs_CZ')))
  
  if len(messages) == 0:
    message_EN = "No visitors arriving or leaving this week"
    message = "Tento tyden neprijizdi ani neodjizdi zadni hoste."
  else:
    message = "Hoste tento tyden: "
    message += " ".join(messages)

  # notifications.send_sms(config['cleaner_number'], message)
  notifications.send_telegram_public(message)

def cleaning_reminder(config):
  cal = GCalendar(config)
  notifications = Notifications(config)
  events = cal.get_public_calendar()
  check_out = None
  check_in = None
  difference = timedelta(days=60)

  for event in events:
    start = parser.parse(event['start']['dateTime'])
    end = parser.parse(event['end']['dateTime']).replace(hour=0)
    now = datetime.now().astimezone(pytz.utc)
    if end < now + timedelta(days=1):
      check_out = event
    else:
      if (start - now) < difference:
        difference = start - now
        check_in = event

  if check_out:
    message = "Pripomenuti: {} odjizdi zitra v {}.".format(check_out['summary'], format_time(parser.parse(check_out['end']['dateTime']), 'H:mm', locale='cs_CZ'))
    if check_in:
      check_in_time = parser.parse(check_in['start']['dateTime'])
      message += " Pristi host ({}) prijizdi {}".format(check_in['summary'], format_date(check_in_time, 'EEE d MMM', locale='cs_CZ'))

    # notifications.send_sms(config['cleaner_number'], message)
    notifications.send_telegram_public(message)

def calendar_sync(config):
  cal = GCalendar(config)
  notifications = Notifications(config)

  private_events = cal.get_private_calendar()
  public_events = cal.get_public_calendar()

  for event in private_events:
    matching_public_events = [d for d in public_events if d['summary'] == event['summary']]
    if len(matching_public_events) == 0:
      LOGGER.info("Public calendar entry for {} not found, creating".format(event['summary']))
      cal.create_public_event(event)
      message = "Synced entry for {} to public calendar".format(event['summary'])
      notifications.send_telegram_private(message)
    else:
      LOGGER.info("Public calendar entry for {} already exists".format(event['summary']))

def nello_sync(config):
  nello = Nello(client_id=config['nello_client_id'], username=config['nello_username'], password=config['nello_password'])
  cal = GCalendar(config)
  notifications = Notifications(config)
  

  # Delete old time windows
  LOGGER.info("Getting Nello time windows")
  time_windows = nello.main_location.list_time_windows()['data']

  LOGGER.info("Deleting expired Nello time windows")
  for window in time_windows:
    if window['state'] == "closed":
      LOGGER.info("Nello time window for {} in past, deleting".format(window['name']))
      nello.main_location.delete_time_window(window['id'])
      notifications.send_telegram_private("Deleted Nello entry for {}".format(window['name']))

  # Create time windows for visitors
  LOGGER.info("Creating Nello time windows")
  events = cal.get_public_calendar()
  for event in events:
    matching_windows = [d for d in time_windows if d['name'] == event['summary']]
    if len(matching_windows) == 0:
      LOGGER.info("Nello time window for {} not found, creating".format(event['summary']))
      window_start = parser.parse(event['start']['dateTime']).replace(hour=15)
      window_end = window_start.replace(hour=20)
      now_ical = vDatetime(datetime.now()).to_ical().decode('utf-8')
      window_start_ical = vDatetime(window_start.astimezone(pytz.utc)).to_ical().decode('utf-8')
      window_end_ical = vDatetime(window_end.astimezone(pytz.utc)).to_ical().decode('utf-8')
      window = 'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:airbnbautomation\r\nBEGIN:VEVENT\r\nDTSTAMP:{}Z\r\nDTSTART:{}Z\r\nDTEND:{}Z\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n'.format(now_ical, window_start_ical, window_end_ical)
      nello.main_location.create_time_window(event['summary'], window)

      notifications.send_telegram_private("Created Nello time window for {} on {}".format(event['summary'], format_date(window_start, 'd MMM')))
    else:
      LOGGER.info("Nello time window for {} already exists".format(event['summary']))
