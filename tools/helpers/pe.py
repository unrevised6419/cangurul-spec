import struct,sys
import os; EXE=os.environ.get('EXE','Cangourou.exe')
d=open(EXE,'rb').read()
pe=struct.unpack_from('<I',d,0x3c)[0]
ns=struct.unpack_from('<H',d,pe+6)[0]; osz=struct.unpack_from('<H',d,pe+20)[0]
base=struct.unpack_from('<I',d,pe+24+28)[0]
secs=[]
o=pe+24+osz
for i in range(ns):
    n=d[o:o+8].rstrip(b'\0').decode(); vs,va,rs,ro=struct.unpack_from('<IIII',d,o+8); secs.append((n,base+va,vs,ro,rs)); o+=40
def off(v):
    for n,va,vs,ro,rs in secs:
        if va<=v<va+max(vs,rs): return ro+v-va
def rd(v,n): o=off(v); return d[o:o+n]
def u32(v): return struct.unpack('<I',rd(v,4))[0]
def lstr(v):
    o=off(v)
    if o is None: return None
    rc,ln=struct.unpack_from('<iI',d,o-8)
    if rc==-1 and ln<5000: return d[o:o+ln].decode('cp1250')
    return None
