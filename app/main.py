import asyncio,json,time,shutil
from urllib.parse import parse_qs
from fastapi import FastAPI,Request,Query,HTTPException
from fastapi.responses import Response,HTMLResponse,JSONResponse
from . import auth,config_store,voices,regions,audio_cache,synthesizer,text_codec
app=FastAPI(title='Legado TTS Manager',docs_url=None,redoc_url=None)
def speed_rate(v):
    try:n=float(v)
    except:return '+0%'
    p=round((n-6.5)*20) if n<=10 else round((n-20)*2.5)
    return f'{max(-50,min(70,p)):+d}%'
def clean_metric(v,default,suffix):
    v=(v or default).strip()
    if len(v)>12 or not v.endswith(suffix):return default
    try:n=float(v[:-len(suffix)])
    except:return default
    if suffix=='%' and not -50 <= n <= 200:return default
    if suffix=='Hz' and not -100 <= n <= 100:return default
    return v
def params(values,cfg):
    is_preview=values('preview','') in ('1','true','yes')
    accept_client_speed=cfg.get('follow_legado_speed',True) or is_preview
    speed=values('speed',values('spd','')) if accept_client_speed else ''
    incoming_rate=values('rate','') if accept_client_speed else ''
    return {'voice':values('voice',cfg['default_voice']),'rate':clean_metric(incoming_rate or (speed_rate(speed) if speed else cfg['default_rate']),cfg['default_rate'],'%'),'pitch':clean_metric(values('pitch',cfg['default_pitch']),cfg['default_pitch'],'Hz'),'volume':clean_metric(values('volume',cfg['default_volume']),cfg['default_volume'],'%'),'style':values('style',cfg.get('default_style','')),'role':values('role',cfg.get('default_role',''))}
async def serve(request,text,values,form_encoded=False):
    auth.require(request);text=text_codec.decode_text(text,form_encoded)
    if not text:raise HTTPException(400,'empty text')
    if len(text)>5000:raise HTTPException(413,'text too long')
    cfg=config_store.load(); p=params(values,cfg); started=time.monotonic()
    data,source,hit=await synthesizer.synthesize(text,p,cfg)
    print(json.dumps({'event':'tts','source':source,'voice':p['voice'],'seconds':round(time.monotonic()-started,3),'bytes':len(data),'cache':hit},ensure_ascii=False),flush=True)
    return Response(data,media_type='audio/mp3',headers={'Content-Length':str(len(data)),'Cache-Control':'no-cache, no-store','Accept-Ranges':'bytes','X-TTS-Source':source,'X-TTS-Cache':'HIT' if hit else 'MISS','X-TTS-Rate':p['rate'],'X-TTS-Speed-Mode':'legado' if cfg.get('follow_legado_speed',True) else 'server'})
@app.get('/health')
def health():return {'status':'ok','defaultVoice':config_store.load()['default_voice']}
@app.get('/tts')
async def get_tts(request:Request,text:str=Query(...)):
    return await serve(request,text,lambda n,d='':request.query_params.get(n,d))
@app.post('/tts')
async def post_tts(request:Request):
    body=parse_qs((await request.body()).decode(errors='replace'),keep_blank_values=True);q=request.query_params
    def val(n,d=''):return q.get(n) if q.get(n) is not None else (body.get(n,[d])[0])
    return await serve(request,val('tex',val('text','')),val,True)
@app.get('/voices')
def list_voices(request:Request,locale:str='',q:str=''):
    auth.require(request);cfg=config_store.load();return {'voices':voices.public(locale,q,cfg['voices_ttl_hours'])}
@app.get('/status')
def status(request:Request):
    auth.require(request);cfg=config_store.load()
    return {'config':cfg,'regions':regions.status(cfg['regions']),'cache':audio_cache.status()}
@app.post('/admin/config')
async def admin_config(request:Request):
    auth.require(request);body=await request.json()
    try:return config_store.save(body)
    except ValueError as exc:raise HTTPException(400,str(exc))
@app.post('/admin/voices/refresh')
def refresh_voices(request:Request):
    auth.require(request);voices.refresh(True);return {'ok':True,'count':len(voices.all_voices())}
@app.post('/admin/regions/benchmark')
async def benchmark_regions(request:Request):
    auth.require(request);cfg=config_store.load()
    try:return {'regions':await asyncio.to_thread(synthesizer.benchmark_regions,cfg,True)}
    except Exception as exc:raise HTTPException(502,'region benchmark failed: '+str(exc))
@app.post('/admin/cache/clear')
def clear_cache(request:Request):
    auth.require(request);shutil.rmtree('/cache',ignore_errors=True);return {'ok':True}
@app.post('/admin/key')
async def change_key(request:Request):
    auth.require(request)
    body=await request.json()
    try:auth.set_key(body.get('new_key',''))
    except ValueError as exc:raise HTTPException(400,str(exc))
    return {'ok':True}

@app.get('/admin',response_class=HTMLResponse)
def admin():
    return HTMLResponse(open('/srv/app/admin.html',encoding='utf-8').read())
