import json, os, threading, time

PATH='/data/regions.json'
STALE_SECONDS=86400
lock=threading.Lock()

def _load():
    try:
        with open(PATH,encoding='utf-8') as stream:data=json.load(stream)
        return data if isinstance(data,dict) else {}
    except Exception:return {}

def _normalise(value):
    value=value if isinstance(value,dict) else {}
    last_error=str(value.get('last_error','') or '')[:160]
    if 'last_failure' not in value and value.get('last_success') and not value.get('consecutive_failures'):
        last_error=''
    return {
        'successes':max(0,int(value.get('successes',0) or 0)),
        'failures':max(0,int(value.get('failures',0) or 0)),
        'consecutive_failures':max(0,int(value.get('consecutive_failures',0) or 0)),
        'avg_latency':max(0,float(value.get('avg_latency',0) or 0)),
        'last_latency':max(0,float(value.get('last_latency',0) or 0)),
        'last_attempt':max(0,float(value.get('last_attempt',0) or 0)),
        'last_success':max(0,float(value.get('last_success',0) or 0)),
        'last_failure':max(0,float(value.get('last_failure',0) or 0)),
        'last_error':last_error,
    }

def _state(stats,now):
    if not stats['last_attempt'] and not stats['successes'] and not stats['failures']:return 'untested'
    if stats['consecutive_failures']>=3:return 'unavailable'
    if stats['consecutive_failures']>0:return 'degraded'
    if not stats['last_success']:return 'unavailable'
    if now-stats['last_success']>STALE_SECONDS:return 'stale'
    return 'healthy'

def ordered(configured):
    data=_load();now=time.time();positions={region:index for index,region in enumerate(configured)}
    def score(region):
        stats=_normalise(data.get(region));state=_state(stats,now)
        penalty={'healthy':0,'degraded':20,'stale':40,'unavailable':80,'untested':10}[state]
        return penalty+(stats['avg_latency'] or 9),positions[region]
    return sorted(configured,key=score)

def record(region,ok,elapsed,error=''):
    with lock:
        data=_load();stats=_normalise(data.get(region));now=time.time()
        stats['last_attempt']=now;stats['last_latency']=round(max(0,elapsed),4)
        if ok:
            count=stats['successes'];stats['successes']=count+1
            stats['avg_latency']=round((stats['avg_latency']*count+elapsed)/(count+1),4)
            stats['last_success']=now;stats['consecutive_failures']=0
            stats['last_failure']=0;stats['last_error']=''
        else:
            stats['failures']+=1;stats['consecutive_failures']+=1
            stats['last_failure']=now;stats['last_error']=str(error)[:160]
        data[region]=stats
        os.makedirs(os.path.dirname(PATH),exist_ok=True);tmp=PATH+'.tmp'
        with open(tmp,'w',encoding='utf-8') as stream:json.dump(data,stream,indent=2)
        os.replace(tmp,PATH)

def status(configured):
    data=_load();now=time.time();enabled_set=set(configured)
    def item(region):
        stats=_normalise(data.get(region));return {'id':region,'state':_state(stats,now),**stats}
    return {
        'enabled':[item(region) for region in configured],
        'disabled':[item(region) for region in sorted(data) if region not in enabled_set],
    }
