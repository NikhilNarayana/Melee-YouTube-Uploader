#!/usr/bin/env python3

import os
import sys
import pickle
from datetime import datetime

from . import consts
from . import youtube as yt

import requests


def pre_upload(opts):
    if opts.mmid == "Grand Finals" and any(x.lower() in opts.msuffix.lower() for x in ("Set 2", "Reset")):
        opts.msuffix = ""
    opts.p1 = opts.p1.split("[L]")[0].strip()
    opts.p2 = opts.p2.split("[L]")[0].strip()
    if opts.mprefix and opts.msuffix:
        opts.mtype = " ".join((opts.mprefix, opts.mmid, opts.msuffix))
    elif opts.mprefix:
        opts.mtype = " ".join((opts.mprefix, opts.mmid))
    elif opts.msuffix:
        opts.mtype = " ".join((opts.mmid, opts.msuffix))
    chars_exist = all(x for x in [opts.p1char, opts.p2char])
    title = make_title(opts, chars_exist)
    if len(title) > 100:
        opts.p1char = minify_chars(opts.p1char)
        opts.p2char = minify_chars(opts.p2char)
        title = make_title(opts, chars_exist)
        if len(title) > 100:
            opts.mtype = minify_mtype(opts)
            title = make_title(opts, chars_exist)
            if len(title) > 100:
                opts.mtype = minify_mtype(opts, True)
                title = make_title(opts, chars_exist)
                if len(title) > 100:
                    title = make_title(opts, chars_exist, True)
                    if len(title) > 100:
                        title = make_title(opts, False, True)
                        if len(title) > 100:
                            # I can only hope no one ever goes this far
                            print("Title is greater than 100 characters after minifying all options")
                            print(title)
                            print(f"Title Length: {len(title)}")
                            print("Killing this upload now\n\n")
                            return False
    print(f"Uploading {title}")
    if opts.descrip:
        descrip = f"Bracket: {opts.bracket}\n\n{opts.descrip}\n\n{consts.credit}" if opts.bracket else f"{opts.descrip}\n\n{consts.credit}"
    else:
        descrip = f"Bracket: {opts.bracket}\n\n{consts.credit}" if opts.bracket else consts.credit
    tags = list(consts.tags)
    if consts.custom:
        tags = []
    tags.extend((*opts.p1char, *opts.p2char, opts.ename, opts.ename_min, opts.p1, opts.p2))
    if opts.tags:
        tags.extend([x.strip() for x in opts.tags.split(",")])
    body = dict(
        snippet=dict(
            title=title,
            description=descrip,
            tags=tags,
            categoryID=20
        ),
        status=dict(
            privacyStatus=opts.privacy)
    )
    ret, vid = yt.upload(consts.youtube, body, opts.file)
    if ret:
        if opts.pID[:2] == "PL":
            try:
                yt.add_to_playlist(opts.pID, vid)
            except Exception as e:
                print("Failed to add to playlist")
                print(e)
        print("DONE\n")
    else:
        print(vid)
    return ret


def minify_chars(pchars):
    for i in range(len(pchars)):
        if pchars[i] in consts.minchars:
            pchars[i] = consts.minchars[pchars[i]]
    if all(x in pchars for x in ("Fox", "Falco")):
        pchars.remove("Fox")
        pchars.remove("Falco")
        pchars.insert(0, "Spacies")
    return pchars


def make_title(opts, chars_exist, min_ename=False):
    if min_ename:
        return opts.titleformat.format(ename=opts.ename_min, round=opts.mtype, p1=opts.p1, p2=opts.p2, p1char='/'.join(opts.p1char), p2char='/'.join(opts.p2char)) if chars_exist else consts.titleformat_min[opts.titleformat].format(ename=opts.ename_min, round=opts.mtype, p1=opts.p1, p2=opts.p2)
    else:
        return opts.titleformat.format(ename=opts.ename, round=opts.mtype, p1=opts.p1, p2=opts.p2, p1char='/'.join(opts.p1char), p2char='/'.join(opts.p2char)) if chars_exist else consts.titleformat_min[opts.titleformat].format(ename=opts.ename, round=opts.mtype, p1=opts.p1, p2=opts.p2)


def minify_mtype(opts, middle=False):
    for k, v in consts.min_match_types.items():
        opts.mprefix = opts.mprefix.replace(k, v)
        opts.mprefix = opts.mprefix.replace(k.lower(), v)
        opts.msuffix = opts.msuffix.replace(k, v)
        opts.msuffix = opts.msuffix.replace(k.lower(), v)
        if middle:
            opts.mmid = opts.mmid.replace(k, v)
    if opts.mprefix and opts.msuffix:
        opts.mtype = " ".join((opts.mprefix, opts.mmid, opts.msuffix))
    elif opts.mprefix:
        opts.mtype = " ".join((opts.mprefix, opts.mmid))
    elif opts.msuffix:
        opts.mtype = " ".join((opts.mmid, opts.msuffix))
    else:
        opts.mtype = opts.mmid
    return opts.mtype


def toggle_worker():
        if not consts.stop_thread:
            print("Stopping Uploads")
            consts.stop_thread = True
            consts.firstrun = False
        else:
            print("Ready to Upload")
            consts.stop_thread = False
            consts.firstrun = True


def read_queue():
    queue = None
    with open(consts.queue_values, "rb") as f:
        queue = pickle.load(f)
    return queue


def write_queue(val):
    with open(consts.queue_values, "wb") as f:
        f.write(pickle.dumps(val))


def create_playlist(name):
    ret = consts.youtube.playlists().insert(
        part='snippet,status',
        body = {
            "snippet": {
                "title": name
            },
            "status": {
                "privacyStatus": "public"
            }
        }
    ).execute()

    return ret['id'] or ret

def get_playlist_video_views(playlist_link):
    if not consts.youtube:
        consts.youtube = yt.get_youtube_service()

    f = playlist_link.find("PL")
    if f == -1:
        print(f"{playlist_link} is not a valid playlist_link")
        return
    pID = playlist_link[f:f + 34]
    ret = consts.youtube.playlistItems().list(
        part="snippet",
        maxResults="25",
        playlistId=pID
    ).execute()

    vIDs = []
    for item in ret['items']:
        vIDs.append(item['snippet']['resourceId']['videoId'])
    
    ret = consts.youtube.videos().list(
        part="snippet,statistics",
        id=",".join(vIDs)
    ).execute()['items']
    
    views = {}
    for vID, item in zip(vIDs, ret):
        if (vID == item['id']):
            views[vID] = {"title": item["snippet"]["title"], "viewCount": item["statistics"]["viewCount"]}
            f"{item['snippet']['title']};https://www.youtube.com/watch?v={vID};{item['statistics']['viewCount']}"
    
    return views
