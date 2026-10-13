import re,sys
from pe import *
src=open(sys.argv[1]).read()
def rep(m):
    v=int(m.group(2),16)
    s=lstr(v)
    if s is None and m.group(1).startswith('PTR'):
        try:
            p=u32(v); s=lstr(p)
        except Exception: s=None
    if s is None: return m.group(0)
    return m.group(0)+'/*"'+s.replace('\r','\\r').replace('\n','\\n')+'"*/'
out=re.sub(r'(&?DAT_|PTR_[A-Za-z_]*?_?|s_[^ ]*?_)([0-9a-f]{8})',rep,src)
# also raw hex constants 0x4xxxxx
def rep2(m):
    v=int(m.group(1),16)
    if 0x401000<=v<0x467000:
        s=lstr(v)
        if s: return m.group(0)+'/*"'+s.replace('\r','\\r').replace('\n','\\n')+'"*/'
    return m.group(0)
out=re.sub(r'0x(4[0-6][0-9a-f]{4})\b',rep2,out)
open(sys.argv[2],'w').write(out)
