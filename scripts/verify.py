"""Validate catalog references, image geometry, durations and original SHA256."""
from pathlib import Path
from PIL import Image,ImageStat
import hashlib,json,math

root=Path(__file__).resolve().parents[1]
catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
policy=json.loads((root/'runtime-policy.json').read_text(encoding='utf-8'))
assert catalog['audit']['version']==policy['version']
originals={}
ids=set()
for a in catalog['animations']:
    assert a['id'] not in ids,a['id']
    ids.add(a['id'])
    assert a['status']=='现用动画' and not a['aliases'] and a['family'] in policy['families']
    assert all(src['source'] in policy['resourcePaths'] for src in a['originals'])
    assert len(a['durations'])==a['count'] and all(t>=0 and math.isfinite(t) for t in a['durations']) and sum(a['durations'])>0,a['id']
    with Image.open(root/a['sheet']) as im:
        assert im.size==(a['columns']*a['width'],math.ceil(a['count']/a['columns'])*a['height']),a['id']
        im.verify()
    assert len(a['frameGeometry'])==a['count'] and a['previewVersion']==3
    with Image.open(root/a['sheet']) as sheet:
        alpha=sheet.getchannel('A')
        for i,g in enumerate(a['frameGeometry']):
            x,y,w,h=g['rect'];sw,sh=g['sourceSize'];assert x>=-.01 and y>=-.01 and x+w<=sw+.01 and y+h<=sh+.01
            ox,oy=g['offset'];rw,rh=g['renderSize'];px,py=g['pivot']
            assert abs(ox+px*rw-a['origin'][0])<=.51 and abs(oy+(1-py)*rh-a['origin'][1])<=.51
            assert ox>=4 and oy>=4 and ox+rw<=a['width']-4 and oy+rh<=a['height']-4
            fx=i%a['columns']*a['width'];fy=i//a['columns']*a['height'];cell=alpha.crop((fx,fy,fx+a['width'],fy+a['height']))
            k=max(2,min(8,rw//20,rh//20));corners=[]
            for cx,cy in [(fx+ox+1,fy+oy+1),(fx+ox+rw-k-1,fy+oy+1),(fx+ox+1,fy+oy+rh-k-1),(fx+ox+rw-k-1,fy+oy+rh-k-1)]:
                corners.append(ImageStat.Stat(alpha.crop((cx,cy,cx+k,cy+k))).median[0])
            assert sorted(corners)[1]==0,('Rectangular alpha matte',a['name'],i,corners)
            assert cell.crop((0,0,a['width'],3)).getbbox() is None
            assert cell.crop((0,a['height']-3,a['width'],a['height'])).getbbox() is None
            assert cell.crop((0,0,3,a['height'])).getbbox() is None
            assert cell.crop((a['width']-3,0,a['width'],a['height'])).getbbox() is None
    with Image.open(root/a['thumb']) as im:im.verify()
    for src in a['originals']:originals[src['file']]=src['sha256']
for file,digest in originals.items():
    assert hashlib.sha256((root/file).read_bytes()).hexdigest()==digest,file
used={a[k] for a in catalog['animations'] for k in ['sheet','thumb']}|set(originals)
actual={p.relative_to(root).as_posix() for p in (root/'assets').rglob('*') if p.is_file()}
assert used==actual,'Orphaned or missing generated assets'
assert {src['source'] for a in catalog['animations'] for src in a['originals']}==set(policy['resourcePaths'])
assert sum(a['count'] for a in catalog['animations'])==catalog['stats']['frames']
assert len(catalog['animations'])==catalog['stats']['animations']
report={'result':'passed','animations':len(ids),'frames':catalog['stats']['frames'],'verifiedOriginals':len(originals),'checks':['Unique animation IDs','Nonnegative authored frame durations and positive clip duration','Atlas frame geometry','Decodable preview assets','Original file SHA256','Statistics match catalog','Runtime resource allowlist','No historical aliases or orphaned asset files','906 source rectangles and shared pivots','Transparent atlas-cell guards: no neighboring-cell bleed','No persistent rectangular corner matte in any of 906 frames']}
(root/'verification').mkdir(exist_ok=True)
(root/'verification/assets.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
