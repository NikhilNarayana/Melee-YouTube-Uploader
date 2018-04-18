#!/usr/bin/env python3

try:
    import http.client as httplib
except ImportError:
    import httplib
import httplib2
import os

from googleapiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

httplib2.RETRIES = 1

RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
                        httplib.IncompleteRead, httplib.ImproperConnectionState,
                        httplib.CannotSendRequest, httplib.CannotSendHeader,
                        httplib.ResponseNotReady, httplib.BadStatusLine)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = "client_secrets.json"

MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   {}

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""".format(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        CLIENT_SECRETS_FILE)))

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

YOUTUBE_UPLOAD_SCOPE = """https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/youtube.force-ssl"""
SPREADSHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"


def get_youtube_service():
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_UPLOAD_SCOPE, message=MISSING_CLIENT_SECRETS_MESSAGE)

    flow.user_agent = "FRC YouTube Uploader"
    storage = Storage("oauth2-youtube.json")
    credentials = storage.get()

    flags = argparser.parse_args(args=[])

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, flags)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


def get_spreadsheet_service():
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=SPREADSHEETS_SCOPE, message=MISSING_CLIENT_SECRETS_MESSAGE)
    flow.user_agent = "FRC YouTube Uploader"

    storage = Storage("oauth2-spreadsheet.json")
    credentials = storage.get()

    flags = argparser.parse_args(args=[])

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, flags)

    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?''version=v4')
    return build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)


def get_retry_status_codes():
    return RETRIABLE_STATUS_CODES


def get_retry_exceptions():
    return RETRIABLE_EXCEPTIONS


def get_max_retries():
    return 10
