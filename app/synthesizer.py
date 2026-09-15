import asyncio,html,os,tempfile,time
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import edge_tts
from . import token_manager,regions,voices,audio_cache

def _ssml(text,voice,rate,pitch,volume,style,role,meta):
    body=f'<prosody rate="{html.escape(rate)}" pitch="{html.escape(pitch)}" volume="{html.escape(volume)}">{html.escape(text)}</prosody>'
    styles=meta.get('StyleList',[]) if meta else []; roles=meta.get('RolePlayList',[]) if meta else []
    if style and style in styles:
        role_attr=f' role="{html.escape(role)}"' if role and role in roles else ''
        body=f'<mstts:express-as style="{html.escape(style)}"{role_attr}>{body}</mstts:express-as>'
    return f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN"><voice name="{html.escape(voice)}">{body}</voice></speak>'.encode()
def azure(text,voice,rate,pitch,volume,style,role,cfg):
    meta=voices.find(voice,cfg['voices_ttl_hours'])
    if not meta: raise ValueError('voice not found')
    payload=_ssml(text,voice,rate,pitch,volume,style,role,meta); errors=[]
    for refresh in (False,True):
        token=token_manager.get(force=refresh)
        for region in regions.ordered(cfg['regions']):
            started=time.monotonic(); url=f'https://{region}.tts.speech.microsoft.com/cognitiveservices/v1'
            try:
                req=Request(url,data=payload,method='POST',headers={'Authorization':token,'Content-Type':'application/ssml+xml','X-Microsoft-OutputFormat':'audio-24khz-48kbitrate-mono-mp3','User-Agent':'okhttp/4.5.0'})
                with urlopen(req,timeout=25) as r:data=r.read()
                if len(data)<1000:raise RuntimeError('empty audio')
                regions.record(region,True,time.monotonic()-started); return data,region
            except HTTPError as e:
                regions.record(region,False,time.monotonic()-started,'HTTP '+str(e.code)); errors.append(region+':'+str(e.code))
                if e.code==401:token_manager.invalidate()
            except Exception as e:
                regions.record(region,False,time.monotonic()-started,type(e).__name__); errors.append(region+':'+type(e).__name__)
    raise RuntimeError(','.join(errors))
async def edge(text,rate,pitch,volume,voice):
    fd,path=tempfile.mkstemp(suffix='.mp3');os.close(fd)
    try:await edge_tts.Communicate(text,voice,rate=rate,pitch=pitch,volume=volume).save(path);return open(path,'rb').read()
    finally:
        if os.path.exists(path):os.unlink(path)
async def synthesize(text,params,cfg):
    cache_key=audio_cache.key({'text':text,**params}); cached=audio_cache.get(cache_key,cfg['cache_ttl_days']) if cfg['cache_enabled'] else None
    if cached:return cached,'cache',True
    try:data,source=await asyncio.to_thread(azure,text,params['voice'],params['rate'],params['pitch'],params['volume'],params['style'],params['role'],cfg)
    except Exception:data=await edge(text,params['rate'],params['pitch'],params['volume'],cfg['edge_fallback_voice']);source='edge-fallback'
    if cfg['cache_enabled']:audio_cache.put(cache_key,data);audio_cache.cleanup(cfg['cache_ttl_days'],cfg['cache_max_mb'])
    return data,source,False
