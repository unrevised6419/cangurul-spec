from pe import *
import struct
rs=[s for s in secs if s[0]=='.rsrc'][0]; rva0=rs[1]
def dirent(v,lvl,path,out):
    o=off(v); nn,ni=struct.unpack_from('<HH',d,o+12)
    for i in range(nn+ni):
        nm,ofs=struct.unpack_from('<II',d,o+16+8*i)
        if nm&0x80000000:
            p=off(rva0+(nm&0x7fffffff)); l=struct.unpack_from('<H',d,p)[0]; name=d[p+2:p+2+2*l].decode('utf-16le')
        else: name=nm
        if ofs&0x80000000: dirent(rva0+(ofs&0x7fffffff),lvl+1,path+[name],out)
        else:
            e=off(rva0+ofs); drva,sz=struct.unpack_from('<II',d,e); out.append((path+[name],base+drva,sz))
out=[]; dirent(rva0,0,[],out)
for p,v,s in out: print(p,hex(v),s)
