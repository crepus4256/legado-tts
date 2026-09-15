import json,os,time
from urllib.request import urlopen
URL='https://cnb.cool/mingwuyan/yinpin/-/git/raw/main/voices.json'; PATH='/data/voices.json'
def refresh(force=False,ttl_hours=24):
    if not force and os.path.exists(PATH) and time.time()-os.path.getmtime(PATH)<ttl_hours*3600:return
    data=urlopen(URL,timeout=20).read(); voices=json.loads(data)
    os.makedirs('/data',exist_ok=True); tmp=PATH+'.tmp'; open(tmp,'wb').write(data); os.replace(tmp,PATH)
def all_voices(ttl_hours=24):
    try: refresh(False,ttl_hours)
    except Exception:
        if not os.path.exists(PATH): raise
    return json.load(open(PATH,encoding='utf-8'))
def find(voice_id,ttl_hours=24):
    for v in all_voices(ttl_hours):
        if v.get('ShortName')==voice_id:return v
    return None
def public(locale='',query='',ttl_hours=24):
    out=[]; q=query.lower()
    for v in all_voices(ttl_hours):
        if locale and v.get('Locale')!=locale:continue
        blob=' '.join(str(v.get(k,'')) for k in ('ShortName','LocalName','DisplayName')).lower()
        if q and q not in blob:continue
        out.append({'id':v.get('ShortName'),'name':v.get('LocalName') or v.get('DisplayName'),'locale':v.get('Locale'),'gender':v.get('Gender'),'status':v.get('Status'),'styles':v.get('StyleList',[]),'roles':v.get('RolePlayList',[])})
    return out
