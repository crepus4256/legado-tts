import json, os, threading, time
PATH='/data/regions.json'; lock=threading.Lock()
def _load():
    try: return json.load(open(PATH))
    except Exception: return {}
def ordered(configured):
    stats=_load(); now=time.time()
    def score(r):
        s=stats.get(r,{})
        penalty=min(s.get('failures',0),10)*2 + (20 if now-s.get('last_success',0)>86400 else 0)
        return s.get('avg_latency',9)+penalty
    known=[r for r in configured if stats.get(r,{}).get('successes',0)>0]
    unknown=[r for r in configured if r not in known]
    return sorted(known,key=score)+unknown
def record(region,ok,elapsed,error=''):
    with lock:
        data=_load(); s=data.setdefault(region,{'successes':0,'failures':0,'avg_latency':0,'last_success':0,'last_error':''})
        if ok:
            n=s['successes']; s['successes']=n+1; s['avg_latency']=round((s['avg_latency']*n+elapsed)/(n+1),4); s['last_success']=time.time(); s['failures']=max(0,s['failures']-1)
        else: s['failures']+=1; s['last_error']=str(error)[:160]
        os.makedirs('/data',exist_ok=True); tmp=PATH+'.tmp'; json.dump(data,open(tmp,'w'),indent=2); os.replace(tmp,PATH)
def stats(): return _load()
