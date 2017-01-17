import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime

def take_n(it, n):
    v = 0
    for i in it:
        yield i
        if v >= n:
            break
        v = v + 1

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Py Cal'

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def list_calendars(service):
    page_tok = None
    while True:
        cal_list = service.calendarList().list(pageToken = page_tok).execute()
        for i in cal_list['items']:
            yield (i['id'], i['summary'])
        page_tok = cal_list.get('pageToken')
        if not page_tok:
            break

def internalize(event):
    iso_str = event['start'].get('dateTime', event['start'].get('date'))
    t_loc = iso_str.find('T')
    if t_loc >= 0:
        iso_str = iso_str[:iso_str.find('-', t_loc)]
        ret_time = datetime.datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S")
    else:
        ret_time = datetime.datetime.strptime(iso_str, "%Y-%m-%d")
    return (ret_time, event['summary'])

def first_n_evts(service, n_evts, *calendars):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    evts = []
    for cal in calendars:
        events_res = service.events().list(
                calendarId=cal, timeMin=now, maxResults=n_evts, singleEvents=True, 
                orderBy='startTime').execute()
        evts += list(map(internalize, events_res.get('items', [])))

    sorted_ev = sorted(evts, key = lambda x: x[0])
    yield from take_n(sorted_ev, n_evts)


def main():
    creds = get_credentials()
    http = creds.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http = http)

    with open(os.path.expanduser('~') + '/cal-ids.txt') as conf:
        for i in first_n_evts(service, 10, *map(str.strip, conf)):
            print(i[1], "on", i[0].strftime("%A, %-d %B at %H:%M"))

if __name__ == "__main__":
    main()
