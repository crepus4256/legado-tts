import json,os,threading
PATH='/data/config.json'
DEFAULTS={'default_voice':'zh-CN-XiaoxiaoMultilingualNeural','edge_fallback_voice':'zh-CN-XiaoxiaoNeural','regions':['eastus','westus','eastasia','southeastasia','westeurope','northeurope'],'default_rate':'+0%','follow_legado_speed':True,'default_pitch':'+0Hz','default_volume':'+0%','default_style':'','default_role':'','cache_enabled':True,'cache_ttl_days':14,'cache_max_mb':1024,'voices_ttl_hours':24}
REGIONS=set(DEFAULTS['regions'])
_lock=threading.Lock()
def _string(value,name,allow_empty=False):
    if not isinstance(value,str) or (not allow_empty and not value.strip()) or len(value)>128:raise ValueError(f'{name} is invalid')
    return value.strip()
def _metric(value,name,suffix,low,high):
    if not isinstance(value,str) or not value.endswith(suffix):raise ValueError(f'{name} is invalid')
    try:number=float(value[:-len(suffix)])
    except ValueError:raise ValueError(f'{name} is invalid')
    if not low<=number<=high:raise ValueError(f'{name} is out of range')
    return value
def _integer(value,name,low,high):
    if isinstance(value,bool) or not isinstance(value,int) or not low<=value<=high:raise ValueError(f'{name} is out of range')
    return value
def _validate(name,value):
    if name in ('default_voice','edge_fallback_voice'):return _string(value,name)
    if name in ('default_style','default_role'):return _string(value,name,True)
    if name=='default_rate':return _metric(value,name,'%',-50,200)
    if name=='default_pitch':return _metric(value,name,'Hz',-100,100)
    if name=='default_volume':return _metric(value,name,'%',-50,200)
    if name in ('follow_legado_speed','cache_enabled'):
        if not isinstance(value,bool):raise ValueError(f'{name} must be a boolean')
        return value
    if name=='regions':
        if not isinstance(value,list) or not value or len(value)>len(REGIONS) or any(not isinstance(v,str) or v not in REGIONS for v in value) or len(set(value))!=len(value):raise ValueError('regions is invalid')
        return value
    if name=='cache_ttl_days':return _integer(value,name,1,365)
    if name=='cache_max_mb':return _integer(value,name,16,102400)
    if name=='voices_ttl_hours':return _integer(value,name,1,720)
    return value
def load():
    data=dict(DEFAULTS)
    try:
        with open(PATH,encoding='utf-8') as stream:saved=json.load(stream)
        if isinstance(saved,dict):
            for k,v in saved.items():
                if k in DEFAULTS:
                    try:data[k]=_validate(k,v)
                    except ValueError:pass
    except Exception:pass
    return data
def save(changes):
    if not isinstance(changes,dict):raise ValueError('config must be a JSON object')
    with _lock:
        data=load()
        for k,v in changes.items():
            if k in DEFAULTS:data[k]=_validate(k,v)
        os.makedirs(os.path.dirname(PATH),exist_ok=True);tmp=PATH+'.tmp'
        with open(tmp,'w',encoding='utf-8') as stream:json.dump(data,stream,ensure_ascii=False,indent=2)
        os.replace(tmp,PATH);return data
