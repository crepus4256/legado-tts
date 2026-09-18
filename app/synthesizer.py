import asyncio,html,os,tempfile,threading,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import edge_tts
from . import token_manager,regions,voices,audio_cache

_benchmark_lock=threading.Lock()

def _ssml(text,voice,rate,pitch,volume,style,role,meta):
    body=f'<prosody rate="{html.escape(rate)}" pitch="{html.escape(pitch)}" volume="{html.escape(volume)}">{html.escape(text)}</prosody>'
    styles=meta.get('StyleList',[]) if meta else []; roles=meta.get('RolePlayList',[]) if meta else []
    if style and style in styles:
        role_attr=f' role="{html.escape(role)}"' if role and role in roles else ''
        body=f'<mstts:express-as style="{html.escape(style)}"{role_attr}>{body}</mstts:express-as>'
    return f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN"><voice name="{html.escape(voice)}">{body}</voice></speak>'.encode()

def _request(region,payload,token,timeout):
    url=f'https://{region}.tts.speech.microsoft.com/cognitiveservices/v1'
    req=Request(url,data=payload,method='POST',headers={'Authorization':token,'Content-Type':'application/ssml+xml','X-Microsoft-OutputFormat':'audio-24khz-48kbitrate-mono-mp3','User-Agent':'okhttp/4.5.0'})
    with urlopen(req,timeout=timeout) as response:data=response.read()
    if len(data)<1000:raise RuntimeError('empty audio')
    return data

def benchmark_regions(cfg,force=False):
    with _benchmark_lock:
        configured=cfg['regions']
        if not force and not regions.needs_benchmark(configured):return regions.status(configured)
        meta=voices.find(cfg['default_voice'],cfg['voices_ttl_hours'])
        if not meta:raise ValueError('voice not found')
        payload=_ssml('区域测速',cfg['default_voice'],'+0%','+0Hz','+0%','','',meta)
        token=token_manager.get(force=True)
        def probe(region):
            started=time.monotonic()
            try:
                _request(region,payload,token,10)
                elapsed=time.monotonic()-started;regions.record(region,True,elapsed,benchmark=True)
                return region,True,''
            except HTTPError as exc:
                if exc.code==401:
                    error='HTTP 401';regions.record(region,False,time.monotonic()-started,error,benchmark=True)
                    return region,False,'authentication:401'
                error='HTTP '+str(exc.code);regions.record(region,False,time.monotonic()-started,error,benchmark=True)
                return region,False,error
            except Exception as exc:
                error=type(exc).__name__;regions.record(region,False,time.monotonic()-started,error,benchmark=True)
                return region,False,error
        with ThreadPoolExecutor(max_workers=len(configured)) as executor:
            results=dict((region,(ok,error)) for region,ok,error in (future.result() for future in as_completed([executor.submit(probe,region) for region in configured])))
        if any(error=='authentication:401' for ok,error in results.values()):token_manager.invalidate()
        return regions.status(configured)

def azure(text,voice,rate,pitch,volume,style,role,cfg):
    meta=voices.find(voice,cfg['voices_ttl_hours'])
    if not meta: raise ValueError('voice not found')
    if regions.needs_benchmark(cfg['regions']):benchmark_regions(cfg)
    payload=_ssml(text,voice,rate,pitch,volume,style,role,meta); errors=[]
    for refresh in (False,True):
        token=token_manager.get(force=refresh)
        for region in regions.ordered(cfg['regions']):
            started=time.monotonic()
            try:
                data=_request(region,payload,token,25)
                regions.record(region,True,time.monotonic()-started); return data,region
            except HTTPError as e:
                if e.code==401:
                    regions.record(region,False,time.monotonic()-started,'HTTP 401')
                    token_manager.invalidate();errors.append('authentication:401');break
                regions.record(region,False,time.monotonic()-started,'HTTP '+str(e.code));errors.append(region+':'+str(e.code))
            except Exception as e:
                regions.record(region,False,time.monotonic()-started,type(e).__name__); errors.append(region+':'+type(e).__name__)
    raise RuntimeError(','.join(errors))
async def edge(text,rate,pitch,volume,voice):
    fd,path=tempfile.mkstemp(suffix='.mp3');os.close(fd)
    try:
        await edge_tts.Communicate(text,voice,rate=rate,pitch=pitch,volume=volume).save(path)
        with open(path,'rb') as stream:return stream.read()
    finally:
        if os.path.exists(path):os.unlink(path)
async def synthesize(text,params,cfg):
    cache_key=audio_cache.key({'text':text,**params}); cached=audio_cache.get(cache_key,cfg['cache_ttl_days']) if cfg['cache_enabled'] else None
    if cached:return cached,'cache',True
    try:data,source=await asyncio.to_thread(azure,text,params['voice'],params['rate'],params['pitch'],params['volume'],params['style'],params['role'],cfg)
    except Exception:data=await edge(text,params['rate'],params['pitch'],params['volume'],cfg['edge_fallback_voice']);source='edge-fallback'
    if cfg['cache_enabled']:audio_cache.put(cache_key,data);audio_cache.cleanup(cfg['cache_ttl_days'],cfg['cache_max_mb'])
    return data,source,False
