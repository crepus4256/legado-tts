from urllib.parse import unquote


def decode_text(value,form_encoded=False):
    value=value or ''
    if form_encoded:
        value=value.replace('+',' ')
    for _ in range(2):
        decoded=unquote(value)
        if decoded==value:break
        value=decoded
    return value.strip()
