#!/usr/bin/env python3

try:
    import http.client as httplib
except ImportError:
    import httplib
import httplib2
import os
import sys
import errno
from decimal import Decimal

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from oauth2client.file import Storage
from oauth2client.tools import run_flow
from oauth2client.client import flow_from_clientsecrets

httplib2.RETRIES = 1

RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
                        httplib.IncompleteRead,
                        httplib.ImproperConnectionState,
                        httplib.CannotSendRequest, httplib.CannotSendHeader,
                        httplib.ResponseNotReady, httplib.BadStatusLine)

RETRIABLE_STATUS_CODES = [500, 502, 504]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/youtube.force-ssl"
SPREADSHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"


def upload(yt, body, file):
    vid = None
    ret = None
    while not vid:
        insert_request = yt.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=MediaFileUpload(file,
                                       chunksize=104857600,
                                       resumable=True),)
        ret, vid = upload_service(insert_request)
    return ret, vid


def upload_service(insert_request):
        response = None
        retry_exceptions = get_retry_exceptions()
        retry_status_codes = get_retry_status_codes()
        ACCEPTABLE_ERRNO = (errno.EPIPE, errno.EINVAL, errno.ECONNRESET)
        try:
            ACCEPTABLE_ERRNO += (errno.WSAECONNABORTED,)
        except AttributeError:
            pass  # Not windows
        while True:
            try:
                status, response = insert_request.next_chunk()
                if status is not None:
                    percent = Decimal(int(status.resumable_progress) / int(status.total_size))
                    print(f"{round(100 * percent, 2)}% uploaded")
            except HttpError as e:
                if e.resp.status in retry_status_codes:
                    print(f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}")
                elif "503" in e.content:
                    print("Backend Error: will attempt to retry upload")
                    return False, None
            except retry_exceptions as e:
                print(f"A retriable error occurred: {e}")

            except Exception as e:
                if e in ACCEPTABLE_ERRNO:
                    print("Retriable Error occured, retrying now")
                else:
                    print(e)
                pass
            if response:
                if "id" in response:
                    print(f"Video link is https://www.youtube.com/watch?v={response['id']}")
                    return True, response['id']
                else:
                    print(response)
                    print(status)
                    return False, None


def get_youtube_service():
    CLIENT_SECRETS_FILE = get_secrets((
        os.path.expanduser("~"),
        sys.prefix,
        os.path.join(sys.prefix, "local"), "/usr",
        os.path.join("/usr", "local")
    ), ("client_secrets.json", ".client_secrets.json", "share/meleeuploader/client_secrets.json"))

    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_UPLOAD_SCOPE)

    flow.user_agent = "Melee YouTube Uploader"
    storage = Storage(os.path.join(os.path.expanduser("~"), ".smash-oauth2-youtube.json"))
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)

    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()))


def get_partner_service():
    CLIENT_SECRETS_FILE = get_secrets((
        os.path.expanduser("~"),
        sys.prefix,
        os.path.join(sys.prefix, "local"), "/usr",
        os.path.join("/usr", "local")
    ), ("client_secrets.json", ".client_secrets.json", "share/meleeuploader/client_secrets.json"))

    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=("https://www.googleapis.com/auth/youtubepartner", "https://www.googleapis.com/auth/youtube",))

    flow.user_agent = "Melee YouTube Uploader"
    storage = Storage(os.path.join(os.path.expanduser("~"), ".smash-oauth2-partner.json"))
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)

    return build(
        "youtubePartner",
        "v1",
        http=credentials.authorize(httplib2.Http()))


def get_spreadsheet_service():
    CLIENT_SECRETS_FILE = get_secrets((
        os.path.expanduser("~"),
        sys.prefix,
        os.path.join(sys.prefix, "local"), "/usr",
        os.path.join("/usr", "local")
    ), ("client_secrets.json", ".client_secrets.json", "share/meleeuploader/client_secrets.json"))

    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=SPREADSHEETS_SCOPE)

    flow.user_agent = "Melee YouTube Uploader"

    storage = Storage(os.path.join(os.path.expanduser("~"), ".smash-oauth2-spreadsheet.json"))
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)

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
