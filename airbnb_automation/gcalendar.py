from __future__ import print_function
import pickle
import os.path
import re

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from icalevents import icalevents
from datetime import datetime, timedelta
from dateutil import parser
import pytz
import logging 

LOGGER = logging.getLogger('airbnb_automation')

SCOPES = ['https://www.googleapis.com/auth/calendar']

class GCalendar():

  def __init__(self, config):
    self.config = config

    # Authenticate to Google Calendar
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    self.service = build('calendar', 'v3', credentials=creds, cache_discovery=False)

  def get_private_calendar(self, days=180):

    icsurl = self.config['airbnb_ics']
    result = []

    events = icalevents.events(icsurl, start=datetime.now(), end=datetime.now() + timedelta(days=days))
    for event in events:
      if event.summary == 'Airbnb (Not available)':
        continue
      check_in_date = event.description.split('\n')[0].split(': ')[1]
      check_out_date = event.description.split('\n')[1].split(': ')[1]
      summary = re.sub(r' \(.*', '', event.summary)

      result.append({
        'summary': summary,
        'check_in': self.check_in_time(check_in_date, 'CZ'),
        'check_out': self.check_out_time(check_out_date, 'CZ'),
      })
    return result

  def check_in_time(self, check_in_date, location):
    date = datetime.strptime(check_in_date, '%d-%m-%Y')
    if location == 'CZ':
      check_in_time = pytz.timezone('Europe/Prague').localize(date).replace(hour=15).astimezone(pytz.utc)
    else:
      check_in_time = pytz.timezone('Europe/London').localize(date).replace(hour=15).astimezone(pytz.utc)

    return check_in_time.isoformat()

  def check_out_time(self, check_out_date, location):
    date = datetime.strptime(check_out_date, '%d-%m-%Y')
    if location == 'CZ':
      check_out_time = pytz.timezone('Europe/Prague').localize(date).replace(hour=12).astimezone(pytz.utc)
    else:
      check_out_time = pytz.timezone('Europe/London').localize(date).replace(hour=12).astimezone(pytz.utc)

    return check_out_time.isoformat()

  def get_public_calendar(self):
      # Call the Calendar API
      now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
      events_result = self.service.events().list(calendarId=self.config['google_calendar_id'], timeMin=now,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
      events = events_result.get('items', [])
      return events

  def create_public_event(self, event):
    calendar_event = {
      "summary": event['summary'],
      "start": {
        "dateTime": event['check_in']
      },
      "end": {
        "dateTime": event['check_out']
      }
    }
    self.service.events().insert(calendarId=self.config['google_calendar_id'], body=calendar_event).execute()
