#!/usr/bin/env python3

import os
import sys
from datetime import datetime

from . import consts
from . import youtube as yt


def pre_upload(opts):
    if opts.mprefix and opts.msuffix:
        opts.mtype = " ".join((opts.mprefix, opts.mtype, opts.msuffix))
    elif opts.mprefix:
        opts.mtype = " ".join((opts.mprefix, opts.mtype))
    elif opts.msuffix:
        opts.mtype = " ".join((opts.mtype, opts.msuffix))
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
    tags = list(consts.melee_tags) if consts.melee else list(consts.ult_tags)
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
                consts.youtube.playlistItems().insert(
                    part="snippet",
                    body=dict(
                        snippet=dict(
                            playlistId=opts.pID,
                            resourceId=dict(
                                kind='youtube#video',
                                videoId=vid)))).execute()
                print("Added to playlist")
            except Exception as e:
                print("Failed to add to playlist")
                print(e)
        if consts.sheets:
            totalTime = datetime.now() - opts.then
            values = [[
                str(datetime.now()),
                str(totalTime), f"https://www.youtube.com/watch?v={vid}",
                opts.ename,
                opts.titleformat,
                title,
                str(consts.loadedQueue)
            ]]
            sheetbody = {"values": values}
            try:
                consts.sheets.spreadsheets().values().append(
                    spreadsheetId=consts.spreadsheetID,
                    range=consts.rowRange,
                    valueInputOption="USER_ENTERED",
                    body=sheetbody).execute()
                print("Added data to spreadsheet")
            except Exception as e:
                print("Failed to write to spreadsheet")
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
