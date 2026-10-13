"""Extract every application image and sound from a Delphi PE: RT_BITMAP, RT_ICON (main icon)
and bitmaps embedded in DFM form resources (TBitmap Picture/Glyph data).
Usage: python3 extract_images.py <exe> <outdir>
Stock VCL bitmaps (BB*) and cursors are skipped."""
import struct, sys, os, re
exe, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
d = open(exe, 'rb').read()
pe = struct.unpack_from('<I', d, 0x3c)[0]; ns = struct.unpack_from('<H', d, pe+6)[0]; osz = struct.unpack_from('<H', d, pe+20)[0]
secs = []
o = pe+24+osz
for i in range(ns):
    vs, va, rs, ra = struct.unpack_from('<IIII', d, o+8); secs.append((va, vs, ra, rs)); o += 40
rsrc_rva = struct.unpack_from('<I', d, pe+24+96+8*2)[0]
def off(rva):
    for va, vs, ra, rs in secs:
        if va <= rva < va+max(vs, rs): return rva-va+ra
base = off(rsrc_rva)
def name(e):
    if e & 0x80000000:
        p = base+(e & 0x7fffffff); n = struct.unpack_from('<H', d, p)[0]; return d[p+2:p+2+2*n].decode('utf-16le')
    return e
def walk(p, depth, path, res):
    nn, ni = struct.unpack_from('<HH', d, p+12)
    for k in range(nn+ni):
        e, t = struct.unpack_from('<II', d, p+16+8*k)
        if t & 0x80000000: walk(base+(t & 0x7fffffff), depth+1, path+[name(e)], res)
        else:
            rva, sz = struct.unpack_from('<II', d, base+t); res.append((path+[name(e)], off(rva), sz))
res = []; walk(base, 0, [], res)
def save_dib(fn, dib):
    hs = struct.unpack_from('<I', dib, 0)[0]; bc = struct.unpack_from('<H', dib, 14)[0]
    clr = struct.unpack_from('<I', dib, 32)[0] or ((1 << bc) if bc <= 8 else 0)
    open(fn, 'wb').write(b'BM'+struct.pack('<IHHI', 14+len(dib), 0, 0, 14+hs+4*clr)+dib)
class R:
    def __init__(s, b): s.b, s.p = b, 4
    def u8(s): v = s.b[s.p]; s.p += 1; return v
    def ss(s): n = s.u8(); v = s.b[s.p:s.p+n].decode('cp1250'); s.p += n; return v
    def u32(s): v = struct.unpack_from('<I', s.b, s.p)[0]; s.p += 4; return v
def skip(r, t):
    if t == 1:
        while r.b[r.p] != 0: skip(r, r.u8())
        r.p += 1
    elif t in (2,): r.p += 1
    elif t == 3: r.p += 2
    elif t in (4, 15): r.p += 4
    elif t == 5: r.p += 10
    elif t in (6, 7): r.ss()
    elif t in (10, 12, 20): n = r.u32(); r.p += n
    elif t == 11:
        while r.ss(): pass
    elif t == 14:
        while r.b[r.p] != 0:
            if r.b[r.p] in (2, 3, 4): skip(r, r.u8())
            skip(r, 1)
        r.p += 1
    elif t in (16, 17, 19): r.p += 8
    elif t == 18: n = r.u32(); r.p += 2*n
def obj(r, form, owner_cb):
    if r.b[r.p] & 0xf0 == 0xf0:
        f = r.u8()
        if f & 2: skip(r, r.u8())
    r.ss(); oname = r.ss()
    while r.b[r.p] != 0:
        prop = r.ss(); t = r.u8()
        if t == 10 and prop == 'Bitmap':          # TImageList: "IL" stream with image + mask BMPs
            n = r.u32(); blob = r.b[r.p:r.p+n]; r.p += n; k = 0; j = 0
            while (j := blob.find(b'BM', j)) != -1:
                sz2 = struct.unpack_from('<I', blob, j+2)[0]
                if 60 < sz2 <= len(blob)-j and blob[j+14:j+18] == b'\x28\0\0\0':
                    owner_cb(form, oname, f'imagelist{k}', b'\x00\x00\x00\x00'+blob[j:j+sz2]); k += 1; j += sz2
                else: j += 2
        elif t == 10 and prop.endswith(('Glyph.Data', 'Picture.Data', 'Bitmap.Data')):
            n = r.u32(); owner_cb(form, oname, prop, r.b[r.p:r.p+n]); r.p += n
        else: skip(r, t)
    r.p += 1
    while r.b[r.p] != 0: obj(r, form, owner_cb)
    r.p += 1
def save_dfm(form, oname, prop, data):
    if data[:1] == b'\x07' or data[1:8] == b'TBitmap':
        n = data[0]; cls = data[1:1+n].decode(); body = data[1+n:]
        if cls == 'TBitmap': body = body[4:]
    elif data[4:6] == b'BM': cls, body = 'Glyph', data[4:]   # Glyph.Data: dword size + BMP
    else: cls, body = 'raw', data
    w, h = struct.unpack_from('<ii', body, 18) if body[:2] == b'BM' else (0, 0)
    ext = 'bmp' if body[:2] == b'BM' else ('ico' if cls == 'TIcon' else 'bin')
    fn = f'{out}/{form.lower()}_{oname}_{prop.split(".")[0].lower()}.{ext}'
    open(fn, 'wb').write(body); print('DFM', form, oname, prop, cls, f'{w}x{h}')
def dfm_images(form, b):
    obj(R(b), form, save_dfm)
SHORT = re.compile(rb'([\x01-\x3f])([A-Za-z_][A-Za-z0-9_]*)')
for path, p, sz in res:
    typ, nm = path[0], path[1]
    b = d[p:p+sz]
    if typ == 2 and isinstance(nm, str) and not nm.startswith('BB'):
        save_dib(f'{out}/{nm.lower()}.bmp', b); print('RT_BITMAP', nm)
    elif typ == 3:
        open(f'{out}/icon_{nm}.ico', 'wb').write(struct.pack('<HHHBBBBHHII', 0, 1, 1, b[4], b[8]//2, 0, 0, 1, struct.unpack_from('<H', b, 14)[0], sz, 22)+b)
        print('RT_ICON', nm)
    elif typ == 10 and isinstance(nm, str) and b[:4] == b'TPF0':
        dfm_images(nm, b)

# sounds: every RIFF/WAVE chunk anywhere in the file
k = 0; j = 0
while (j := d.find(b'RIFF', j)) != -1:
    n = struct.unpack_from('<I', d, j+4)[0]
    if d[j+8:j+12] == b'WAVE' and n < len(d):
        open(f'{out}/sound_{k}.wav', 'wb').write(d[j:j+8+n]); print('WAV', k, n+8, 'bytes at file offset', hex(j)); k += 1; j += 8+n
    else: j += 4
