import hashlib, json, os, time
ROOT='/cache'
def key(params): return hashlib.sha256(json.dumps(params,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def get(k,ttl_days):
    p=f'{ROOT}/{k}.mp3'
    try:
        if time.time()-os.path.getmtime(p)<=ttl_days*86400: return open(p,'rb').read()
        os.unlink(p)
    except Exception: pass
    return None
def put(k,data):
    os.makedirs(ROOT,exist_ok=True); p=f'{ROOT}/{k}.mp3'; tmp=p+'.tmp'; open(tmp,'wb').write(data); os.replace(tmp,p)
def cleanup(ttl_days,max_mb):
    os.makedirs(ROOT,exist_ok=True); now=time.time(); files=[]
    for n in os.listdir(ROOT):
        if not n.endswith('.mp3'): continue
        p=f'{ROOT}/{n}'
        try:
            st=os.stat(p)
            if now-st.st_mtime>ttl_days*86400: os.unlink(p)
            else: files.append((st.st_mtime,st.st_size,p))
        except Exception: pass
    total=sum(x[1] for x in files); limit=max_mb*1024*1024
    for _,size,p in sorted(files):
        if total<=limit: break
        try: os.unlink(p); total-=size
        except Exception: pass
    return {'files':len([x for x in files if os.path.exists(x[2])]),'bytes':max(total,0)}
def status():
    os.makedirs(ROOT,exist_ok=True); fs=[f'{ROOT}/{n}' for n in os.listdir(ROOT) if n.endswith('.mp3')]; return {'files':len(fs),'bytes':sum(os.path.getsize(p) for p in fs if os.path.exists(p))}
