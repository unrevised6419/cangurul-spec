import struct,sys
from pe import *
exec(open('rsrc.py').read().split('for p,v,s in out')[0])
class R:
    def __init__(s,b): s.b=b; s.p=0
    def u8(s): v=s.b[s.p]; s.p+=1; return v
    def n(s,k,f): v=struct.unpack_from(f,s.b,s.p)[0]; s.p+=k; return v
    def ss(s): l=s.u8(); v=s.b[s.p:s.p+l]; s.p+=l; return v.decode('cp1250')
def val(r,t=None):
    t=r.u8()
    if t==0: return None
    if t==1:
        L=[]
        while r.b[r.p]!=0: L.append(val(r))
        r.p+=1; return L
    if t==2: return r.n(1,'<b')
    if t==3: return r.n(2,'<h')
    if t==4: return r.n(4,'<i')
    if t==5: r.p+=10; return 'ext'
    if t in (6,7): return r.ss()
    if t==9: return True
    if t==8: return False
    if t==10:
        l=r.n(4,'<I'); b=r.b[r.p:r.p+l]; r.p+=l; return ('BIN',l,b)
    if t==11:
        L=[]
        while True:
            x=r.ss()
            if not x: break
            L.append(x)
        return set(L)
    if t==12: l=r.n(4,'<I'); v=r.b[r.p:r.p+l].decode('cp1250'); r.p+=l; return v
    if t==13: return None
    if t==14:
        L=[]
        while r.b[r.p]!=0:
            item=[]
            while r.b[r.p]!=0:
                k=r.ss(); item.append((k,val(r)))
            r.p+=1; L.append(item)
        r.p+=1; return L
    if t==15: r.p+=4; return 'single'
    if t==16: r.p+=8; return 'curr'
    if t==17: r.p+=8; return 'date'
    if t==18: l=r.n(4,'<I'); v=r.b[r.p:r.p+2*l].decode('utf-16le'); r.p+=2*l; return v
    if t==19: return r.n(8,'<q')
    if t==20: l=r.n(4,'<I'); v=r.b[r.p:r.p+l].decode('utf-8'); r.p+=l; return v
    raise Exception('type %d at %d'%(t,r.p))
def comp(r,ind,outf):
    f=r.b[r.p]
    if f&0xf0==0xf0:
        fl=r.u8()
        if fl&2: r.ss() if False else val(r)
    cls=r.ss(); nm=r.ss()
    outf.write('  '*ind+'object %s: %s\n'%(nm,cls))
    while r.b[r.p]!=0:
        k=r.ss(); v=val(r)
        if isinstance(v,tuple): v='<BIN %d>'%v[1] if not k.endswith('Lines.Strings') else v
        outf.write('  '*ind+'  %s = %r\n'%(k,v))
    r.p+=1
    while r.b[r.p]!=0: comp(r,ind+1,outf)
    r.p+=1
for p,v,s in out:
    if p[0]==10 and isinstance(p[1],str) and p[1].startswith('T'):
        b=rd(v,s); assert b[:4]==b'TPF0'
        r=R(b); r.p=4
        with open('dfm_%s.txt'%p[1],'w') as f: comp(r,0,f)
        open('raw_%s.bin'%p[1],'wb').write(b)
