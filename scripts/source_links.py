"""Normalize provider destinations without turning articles or forum tabs into stores."""
import re,urllib.parse

def canonical_listing(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password:return None
    host=p.hostname.lower();path=p.path.rstrip('/')
    if host.endswith('.itch.io'):
        parts=path.strip('/').split('/')
        if not parts[0]:return None
        path='/'+parts[0]
    elif host=='itch.io':return None
    elif host in ['www.moddb.com','moddb.com','www.indiedb.com','indiedb.com']:
        match=re.match(r'^/(mods|games)/([^/]+)(?:/.*)?$',path)
        if not match:return None
        path='/'+match[1]+'/'+match[2]
    elif host in ['www.gog.com','gog.com']:
        match=re.match(r'^/(?:[a-z]{2}/)?game/([^/]+)$',path)
        if not match:return None
        path='/en/game/'+match[1]
    elif host=='store.epicgames.com':
        match=re.match(r'^/(?:[^/]+/)?p/([^/]+)$',path)
        if not match:return None
        path='/en-US/p/'+match[1]
    query=[(k,v) for k,v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith('utm_') and k not in ['ref','referrer','affiliate','aff','snr']]
    return urllib.parse.urlunsplit((p.scheme,host,path,urllib.parse.urlencode(query),''))

def normalized_links(links):
    out={}
    for src in links:
        url=canonical_listing(src['url'])
        if not url:continue
        item={**src,'url':url}
        host=urllib.parse.urlsplit(url).hostname
        if host in ['moddb.com','www.moddb.com','indiedb.com','www.indiedb.com']:item['kind']='project'
        key=((host or '').removeprefix('www.'),urllib.parse.urlsplit(url).path,urllib.parse.urlsplit(url).query)
        if key in out:out[key]={**out[key],**item}
        else:out[key]=item
    return list(out.values())
