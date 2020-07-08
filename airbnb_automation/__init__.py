import logging
from datetime import datetime, timedelta
from dateutil import parser
import pytz
from babel.dates import format_date, format_time
from icalendar import vDatetime
import time

import airbnb
from airbnb_automation.gcalendar import GCalendar
from airbnb_automation.notifications import Notifications
from airbnb_automation.nuki import Nuki

LOGGER = logging.getLogger('airbnb_automation')


class Airbnb():
    def __init__(self, config):
        self.config = config
        self.debug = config['debug']
        self.notifications = Notifications(config)
        self.cal = GCalendar(config)
        self.airbnb_api = airbnb.Api(access_token=config['airbnb_oauth_token'])
        self.nuki = Nuki(config)

    def daily_nuki_opener_status(self):
        message = 'Nuki Opener Mode: {}\n'.format(self.nuki.opener_mode())
        self.notifications.send_telegram_private(message)

    def weekly_nuki_battery_status(self):
        message = 'Nuki Battery Critical: {}'.format(
            self.nuki.battery_critical())
        self.notifications.send_telegram_private(message)

    def weekly_messages(self):
        messages = []

        events = self.cal.get_public_calendar()
        for event in events:
            start = parser.parse(event['start']['dateTime'])
            end = parser.parse(event['end']['dateTime'])
            now = datetime.now().astimezone(pytz.utc)
            if now > start:
                if end < now + timedelta(days=7):
                    messages.append("{} odjíždí {}. ".format(
                        event['summary'],
                        format_date(end, 'EEE d MMM', locale='cs_CZ')))
            elif start < now + timedelta(days=7):
                messages.append("{} přijíždí {} a odjíždí {}.".format(
                    event['summary'],
                    format_date(start, 'EEE d MMM', locale='cs_CZ'),
                    format_date(end, 'EEE d MMM', locale='cs_CZ')))

        if len(messages) == 0:
            # message_EN = "No visitors arriving or leaving this week"
            message = "Tento týden nepřijíždí ani neodjíždí žádní hosté."
        else:
            message = "Hosté tento týden: "
            message += " ".join(messages)

        # notifications.send_sms(config['cleaner_number'], message)
        self.notifications.send_telegram_public(message)

    def cleaning_reminder(self):
        events = self.cal.get_public_calendar()
        check_out = None
        check_in = None
        difference = timedelta(days=60)

        for event in events:
            start = parser.parse(event['start']['dateTime'])
            end = parser.parse(event['end']['dateTime']).replace(hour=0)
            now = datetime.now().astimezone(pytz.utc)
            # Check out day is not today, and is less than 1 day away
            if (end > now) and (end < now + timedelta(days=1)):
                check_out = event
            else:
                if (start - now) < difference:
                    difference = start - now
                    check_in = event

        if check_out:
            message = "Připomenutí: {} odjíždí zítra v {}.".format(
                check_out['summary'],
                format_time(
                    parser.parse(check_out['end']['dateTime']),
                    'H:mm',
                    locale='cs_CZ'))
            if check_in:
                check_in_time = parser.parse(check_in['start']['dateTime'])
                message += " Příští host ({}) přijíždí {}".format(
                    check_in['summary'],
                    format_date(check_in_time, 'EEE d MMM', locale='cs_CZ'))

            # notifications.send_sms(config['cleaner_number'], message)
            self.notifications.send_telegram_public(message)

    def check_in_time(self, check_in_date):
        date = datetime.strptime(check_in_date, '%Y-%m-%d')
        check_in_time = pytz.timezone('Europe/Prague').localize(date).replace(
            hour=15).astimezone(pytz.utc)
        return check_in_time.isoformat()

    def check_out_time(self, check_out_date):
        date = datetime.strptime(check_out_date, '%Y-%m-%d')
        check_out_time = pytz.timezone('Europe/Prague').localize(date).replace(
            hour=12).astimezone(pytz.utc)
        return check_out_time.isoformat()

    def get_reservations(self):
        calendar = self.airbnb_api.get_listing_calendar(
            self.config['airbnb_listing_id'], calendar_months=6)
        reservations = []

        for day in calendar['calendar']['days']:
            if not day['available'] and day['reservation']:
                reservation = day['reservation']
                event = {
                    'summary': reservation['guest']['full_name'],
                    'check_in': self.check_in_time(reservation['start_date']),
                    'check_out': self.check_out_time(reservation['end_date']),
                }
                reservations.append(event)

        reservations = list({v['summary']: v for v in reservations}.values())

        return reservations

    def calendar_sync(self):
        reservations = self.get_reservations()
        public_events = self.cal.get_public_calendar()

        for event in reservations:
            matching_public_events = [
                d for d in public_events if d['summary'] == event['summary']
            ]
            if len(matching_public_events) == 0:
                LOGGER.info(
                    "Public calendar entry for {} not found, creating".format(
                        event['summary']))
                self.cal.create_public_event(event)

                message = "Synced entry for {} to public calendar".format(
                    event['summary'])
                self.notifications.send_telegram_private(message)

                # Send message for cleaner to see bookings
                start_date = parser.parse(event['check_in'])
                end_date = parser.parse(event['check_out'])
                message_public = "Nová rezervace potvrzena: {} {} až {}".format(
                    event['summary'], format_date(start_date, locale='cs_CZ'),
                    format_date(end_date, locale='cs_CZ'))
                self.notifications.send_telegram_public(message_public)

            else:
                LOGGER.info(
                    "Public calendar entry for {} already exists".format(
                        event['summary']))

    def nuki_sync(self):
        # Enable nuki continuous mode on check in day
        events = self.cal.get_public_calendar()
        check_in_day = False
        for event in events:
            if datetime.today().date() == parser.parse(
                    event['start']['dateTime']).date():
                check_in_day = True
                message = "{} is checking in today, setting Nuki to continuous mode".format(
                    event['summary'])
                LOGGER.info(message)
                self.notifications.send_telegram_private(message)
                self.nuki.set_opener_mode('continuous')
                time.sleep(
                    10
                )  # allow opener mode to change before any reporting on this happens
                self.daily_nuki_opener_status()

    def nuki_notifications_from_log(self):
        logs = self.nuki.log()
        for log in logs:
            log_time = parser.parse(log['date'])
            cz_log_time = log_time.astimezone(pytz.timezone('Europe/Prague'))
            if log_time + timedelta(minutes=5) > datetime.now().astimezone(
                    pytz.utc):
                message = "Nuki opened door at {:d}:{:02d}".format(
                    cz_log_time.hour, cz_log_time.minute)
                if log['action'] == 3:
                    message += " for {} due to swipe".format(log['name'])
                elif log['action'] == 224:
                    message += " for ring to open"
                self.notifications.send_telegram_private(message)
            else:
                break
