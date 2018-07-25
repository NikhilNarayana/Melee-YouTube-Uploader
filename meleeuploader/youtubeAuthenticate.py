#!/usr/bin/env python3

try:
    import http.client as httplib
except ImportError:
    import httplib
import httplib2
import sys
import os

from googleapiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

httplib2.RETRIES = 1

RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
                        httplib.IncompleteRead,
                        httplib.ImproperConnectionState,
                        httplib.CannotSendRequest, httplib.CannotSendHeader,
                        httplib.ResponseNotReady, httplib.BadStatusLine)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/youtube.force-ssl"
SPREADSHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"


def get_youtube_service():
    CLIENT_SECRETS_FILE = get_secrets([
        sys.prefix,
        os.path.join(sys.prefix, "local"), "/usr",
        os.path.join("/usr", "local")
    ], ["share/meleeuploader/client_secrets.json", "client_secrets.json"])

    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_UPLOAD_SCOPE)

    flow.user_agent = "Melee YouTube Uploader"
    storage = Storage(os.path.join(os.path.expanduser("~"), ".melee-oauth2-youtube.json"))
    credentials = storage.get()

    flags = argparser.parse_args(args=[])

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, flags)

    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()))


def get_spreadsheet_service():
    CLIENT_SECRETS_FILE = get_secrets([
        sys.prefix,
        os.path.join(sys.prefix, "local"), "/usr",
        os.path.join("/usr", "local")
    ], ["share/meleeuploader/client_secrets.json", "client_secrets.json"])

    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=SPREADSHEETS_SCOPE)

    flow.user_agent = "Melee YouTube Uploader"

    storage = Storage(os.path.join(os.path.expanduser("~"), ".melee-oauth2-spreadsheet.json"))
    credentials = storage.get()

    flags = argparser.parse_args(args=[])

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, flags)

    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
    return build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)


def get_retry_status_codes():
    return RETRIABLE_STATUS_CODES


def get_retry_exceptions():
    return RETRIABLE_EXCEPTIONS


def get_max_retries():
    return 10


def get_secrets(prefixes, relative_paths):
    """
    Taken from https://github.com/tokland/youtube-upload/blob/master/youtube_upload/main.py
    Get the first existing filename of relative_path seeking on prefixes directories.
    """
    try:
        return os.path.join(sys._MEIPASS, relative_paths[-1])
    except Exception:
        for prefix in prefixes:
            for relative_path in relative_paths:
                path = os.path.join(prefix, relative_path)
                if os.path.exists(path):
                    return path
