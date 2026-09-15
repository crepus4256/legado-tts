import json,os,threading
PATH='/data/config.json'
DEFAULTS={'default_voice':'zh-CN-XiaoxiaoMultilingualNeural','edge_fallback_voice':'zh-CN-XiaoxiaoNeural','regions':['eastus','westus','eastasia','southeastasia','westeurope','northeurope'],'default_rate':'+0%','follow_legado_speed':True,'default_pitch':'+0Hz','default_volume':'+0%','default_style':'','default_role':'','cache_enabled':True,'cache_ttl_days':14,'cache_max_mb':1024,'voices_ttl_hours':24}
_lock=threading.Lock()
def load():
    data=dict(DEFAULTS)
    try:data.update(json.load(open(PATH)))
    except Exception:pass
    return data
def save(changes):
    with _lock:
        data=load()
        for k,v in changes.items():
            if k in DEFAULTS:data[k]=v
        os.makedirs('/data',exist_ok=True);tmp=PATH+'.tmp';json.dump(data,open(tmp,'w'),ensure_ascii=False,indent=2);os.replace(tmp,PATH);return data
