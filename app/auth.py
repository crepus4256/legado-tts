import os,hmac
from pathlib import Path
from fastapi import HTTPException,Request
KEY_FILE=Path('/data/access_key')
def access_key():
    try:
        value=KEY_FILE.read_text().strip()
        if value:return value
    except Exception:pass
    return os.environ.get('TTS_'+'ACCESS_KEY','')
def supplied(request:Request):
    value=request.headers.get('X-TTS-Key','')
    if not value:
        header=request.headers.get('Authorization','')
        if header.lower().startswith('bearer '):value=header[7:]
    return value or request.query_params.get('key','')
def require(request:Request):
    expected=access_key();actual=supplied(request)
    if not expected or not hmac.compare_digest(actual,expected):raise HTTPException(401,'invalid access key')
def set_key(value):
    value=(value or '').strip()
    if len(value)<12:raise ValueError('密钥至少需要12个字符')
    if len(value)>128:raise ValueError('密钥不能超过128个字符')
    KEY_FILE.parent.mkdir(parents=True,exist_ok=True)
    tmp=KEY_FILE.with_suffix('.tmp');tmp.write_text(value);os.chmod(tmp,0o600);tmp.replace(KEY_FILE)
