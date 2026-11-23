"""Validate catalog references, image geometry, durations and original SHA256."""
from pathlib import Path
from PIL import Image
import hashlib,json,math

root=Path(__file__).resolve().parents[1]
catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
originals={}
ids=set()
for a in catalog['animations']:
    assert a['id'] not in ids,a['id']
    ids.add(a['id'])
    assert len(a['durations'])==a['count'] and all(t>=0 and math.isfinite(t) for t in a['durations']) and sum(a['durations'])>0,a['id']
    with Image.open(root/a['sheet']) as im:
        assert im.size==(a['columns']*a['width'],math.ceil(a['count']/a['columns'])*a['height']),a['id']
        im.verify()
    with Image.open(root/a['thumb']) as im:im.verify()
    for src in a['originals']:originals[src['file']]=src['sha256']
for file,digest in originals.items():
    assert hashlib.sha256((root/file).read_bytes()).hexdigest()==digest,file
assert sum(a['count'] for a in catalog['animations'])==catalog['stats']['frames']
assert len(catalog['animations'])==catalog['stats']['animations']
report={'result':'passed','animations':len(ids),'frames':catalog['stats']['frames'],'verifiedOriginals':len(originals),'checks':['Unique animation IDs','Nonnegative authored frame durations and positive clip duration','Atlas frame geometry','Decodable preview assets','Original file SHA256','Statistics match catalog']}
(root/'verification').mkdir(exist_ok=True)
(root/'verification/assets.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
