import base64,gzip,hashlib,hmac,json,threading,time,uuid
from datetime import datetime,timezone
from email.utils import format_datetime
from urllib.parse import quote_plus
from urllib.request import Request,urlopen
URL='https://dev.microsofttranslator.com/apps/endpoint?api-version=1.0'
KEY='oik6PdDdMnOXemTbwvMn9de/h9lFnfBa'+'CWbGMMZqqoSaQaqUOqjVGm5NqsmjcBI1'+'x+sS9ugjB55HEJWRiFXYFw=='
_lock=threading.Lock(); _cache={'token':'','created':0}
def invalidate(): _cache.update(token='',created=0)
def get(force=False):
    with _lock:
        now=time.time()
        if not force and _cache['token'] and now-_cache['created']<480:return _cache['token']
        date=format_datetime(datetime.now(timezone.utc),usegmt=True).lower().replace('gmt','')+'GMT'; uid=uuid.uuid4().hex
        raw=('MSTranslatorAndroidApp'+quote_plus(URL.split('://',1)[1])+date+uid).lower().encode()
        sig=base64.b64encode(hmac.new(base64.b64decode(KEY),raw,hashlib.sha256).digest()).decode()
        headers={'Accept-Language':'zh-Hans','X-ClientVersion':'4.0.530a 5fe1dc6c','X-UserId':'0f04d16a175c411e','X-HomeGeographicRegion':'zh-Hans-CN','X-ClientTraceId':str(uuid.uuid4()),'X-MT-Signature':'MSTranslatorAndroidApp::'+sig+'::'+date+'::'+uid,'User-Agent':'okhttp/4.5.0','Content-Type':'application/json; charset=utf-8','Content-Length':'0','Accept-Encoding':'gzip'}
        with urlopen(Request(URL,data=b'',headers=headers,method='POST'),timeout=15) as r:
            body=r.read(); body=gzip.decompress(body) if r.headers.get('Content-Encoding')=='gzip' else body
        token=json.loads(body).get('t','')
        if not token: raise RuntimeError('Microsoft token missing')
        _cache.update(token=token,created=now); return token
