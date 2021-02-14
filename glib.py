#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
version 0.1
Created on Sun May 12 16:09:03 2019
version 0.2
Updated on Sun June 2 with addition of df2_cal_event


@author: persh
"""
import pickle
import os.path
import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import pendulum


class Glib:
    """
    reproduces part of the functionality of myglig.py converted to a class
    The functionality meets the needs of caldates.py and do not go beond that.
    """

    def __init__(self, scopes):

        """
        requests credentials if they are not already there
        uses the same credentials.json file for whole library.
        Could later be extended with a *kwarg argument for credentials
        if more flexibility is needed
        """
        CREDENTIALS = '/Users/persh/.credentials/credentials-myglib.json'

        self.creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, scopes)
                self.creds = flow.run_local_server(port=8083)  # changed from 8080 to avoid error
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        return

    def get_album_ids(self):
        service = build('photoslibrary', 'v1', credentials=self.creds)
        albums = {}
        hasNextPageToken = True
        nextPageToken = ""
        while (hasNextPageToken):
            results = service.albums().list(
                pageSize=15,
                fields="nextPageToken,albums(id,title,mediaItemsCount)").execute()
            items = results.get('albums', [])
            for item in items:
                albums.update({item['title']: item['id']})
            if 'nextPageToken' in results:
                hasNextPageToken = False  # should be True, but that causes infinite loop
                nextPageToken = results['nextPageToken']
            else:
                hasNextPageToken = False
        return albums

    def get_album_id(self, name):
        alb_dict = self.get_album_ids()
        return alb_dict[name]

    def photo_dates(self, album_id):
        service = build('photoslibrary', 'v1', credentials=self.creds)
        timestamps = []
        hasNextPageToken = True
        nextPageToken = ""
        while (hasNextPageToken):
            mybody = {
                "albumId": album_id,
                "pageSize": 100,
                "pageToken": nextPageToken
            }
            results = service.mediaItems().search(body=mybody).execute()
            header = results.get('mediaItems', [])
            for i in range(len(header)):
                timestamps.append(header[i]['mediaMetadata']['creationTime'])
            if 'nextPageToken' in results:
                hasNextPageToken = True
                nextPageToken = results['nextPageToken']
            else:
                hasNextPageToken = False
        return timestamps

    def gcal_list(self):
        """returns a list with name and ID of all the calendars
        """
        service = build('calendar', 'v3', credentials=self.creds)
        calendars = {}
        page_token = None
        while True:
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                calendars.update({calendar_list_entry['summary']: calendar_list_entry['id']})
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break
        return calendars

    def get_gcal_id(self, name):
        """ helper function that converts calendar name tocalendar_id
            @ I need to add to check if calendar exist in dictionary
        """
        cal_dict = self.gcal_list()
        return cal_dict[name]

    def gcal_events2_df(self, calid, start, end):

        """
        start and end are dates in ISO format: YYYY-MM-DD
        convert to datetimeformat ('2019-01-01T00:00:00Z') before calling
        """
        service = build('calendar', 'v3', credentials=self.creds)

        from_date = pendulum.parse(start)
        to_date = pendulum.parse(end)

        events_result = service.events().list(
            calendarId=calid,
            timeMin=from_date,
            timeMax=to_date,
            maxResults=200,
            singleEvents=True,
            orderBy='startTime').execute()
        events = events_result.get('items', [])

        # make a dataframe with one event per row
        res = pd.DataFrame(columns=('summary', 'start', 'finish', 'tz',))
        for event in events:
            res = res.append([{'start': event['start'].get('dateTime', event['start'].get('date')),
                               'finish': event['end'].get('dateTime', event['end'].get('date')),
                               'tz': event['start'].get('timeZone'),
                               'summary': event['summary']}],
                             ignore_index=True)
        return res.drop_duplicates()


# start of main program

if __name__ == '__main__':
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly',
              'https://www.googleapis.com/auth/photoslibrary.readonly',
              'https://www.googleapis.com/auth/spreadsheets.readonly',
              'https://www.googleapis.com/auth/calendar']
    #

    # CREDENTIALS = 'client_secret_979827616180-cc3vrfr25bihtnh0qkv3st5jnlp3asr7.apps.googleusercontent.com.json'
    ALBUM_ID = 'AE2otfvmb-axnmFTsO-3z_30MH9KJ0zYwk_7DdRz8WXw4Z-8MtwoJFEjBPiBVaHTepnDJl2k3jQl'
    # The ID and range of a sample spreadsheet.
    SPREADSHEET_ID = '1lWp2e3c0vgUmmugkwcLNNwiw8Aw-CsG5FF2RHVQg0Vw'
    # RANGE_NAME = 'Sheet1!A1:G30'
    RANGE_NAME = 'Tartegnin events'
    CALENDAR_NAME = 'Tartegnin events'

    gl = Glib(SCOPES)
    # creds = get_creds(SCOPES)

    creation_dates = gl.photo_dates(ALBUM_ID)
    print(f'Google photos albums with {len(creation_dates)} photo dates. Last 5:\n {creation_dates[0:5]}')

    album_dict = gl.get_album_ids()
    print(f'There are {len(album_dict)} albums in photos')
    for name, id in album_dict.items():
        print(name, "\t", id)

    # test of get calendar
    calendar_list = gl.gcal_list()
    print(f'There are {len(calendar_list)} calendars')
    for cal, calid in calendar_list.items():
        print(cal, "\t", calid)

    calendar_id = gl.get_gcal_id("Tartegnin events")
    print('Test of cal_id function, ', calendar_id)

    # test of gcal_events
    calendar_ID = 'dpbv5gihfs3a5hub2bch0h74t4@group.calendar.google.com'
    events = gl.gcal_events2_df(calendar_ID, '2020-01-01', '2022-01-01')
    if events.empty:
        print('No events found.')
    else:
        print(events)













