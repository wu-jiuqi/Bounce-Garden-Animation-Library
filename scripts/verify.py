"""Validate catalog references, image geometry, durations and original SHA256."""
from pathlib import Path
from PIL import Image
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
report={'result':'passed','animations':len(ids),'frames':catalog['stats']['frames'],'verifiedOriginals':len(originals),'checks':['Unique animation IDs','Nonnegative authored frame durations and positive clip duration','Atlas frame geometry','Decodable preview assets','Original file SHA256','Statistics match catalog','Runtime resource allowlist','No historical aliases or orphaned asset files']}
(root/'verification').mkdir(exist_ok=True)
(root/'verification/assets.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
