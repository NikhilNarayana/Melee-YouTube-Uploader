#!/usr/bin/env python3

from . import consts


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
