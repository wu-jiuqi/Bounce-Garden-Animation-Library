"""Rebuild the standalone gallery from a BounceBusters checkout. Python 3 + Pillow."""
from pathlib import Path
from PIL import Image
import argparse, collections, hashlib, json, math, re, shutil

OUT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--project', type=Path, default=OUT.parent)
args = parser.parse_args()
ROOT = args.project.resolve()
ART = ROOT/'ArtSource'
RES = ROOT/'BounceGarden/BounceGarden/Assets/Resources/Art'
items, signatures, consumed = [], {}, set()
audit = {'excluded': [], 'scanRoots': ['ArtSource', 'BounceGarden/BounceGarden/Assets/Resources/Art'], 'policy': 'Exclude platform mirrors, screenshots, recordings, static cosmetics and non-animation UI. Keep distinct historical artwork; deduplicate identical decoded frame sequences.'}
for directory in ['assets/originals','assets/previews','metadata']:
    (OUT/directory).mkdir(parents=True, exist_ok=True)

def store(p):
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    target = OUT/'assets/originals'/(digest+p.suffix.lower())
    if not target.exists(): shutil.copyfile(p,target)
    return {'file': target.relative_to(OUT).as_posix(), 'source': p.relative_to(ROOT).as_posix(), 'sha256': digest}

def add(name, group, frames, sources, fps=None, durations=None, status='历史素材', evidence='', note=''):
    if len(frames)<2:return
    frames = [im.convert('RGBA') for im in frames]
    h = hashlib.sha256()
    for im in frames: h.update(str(im.size).encode()); h.update(im.tobytes())
    sig=h.hexdigest()
    origin={'name':name,'group':group,'status':status,'sources':[p.relative_to(ROOT).as_posix() for p in sources], 'evidence':evidence}
    if sig in signatures:
        signatures[sig]['aliases'].append(origin)
        known={x['source'] for x in signatures[sig]['originals']}
        signatures[sig]['originals'].extend(store(p) for p in dict.fromkeys(sources) if p.relative_to(ROOT).as_posix() not in known)
        return
    uid=sig[:20]
    # One common canvas preserves frame registration. No per-frame auto-cropping.
    w=max(im.width for im in frames); hh=max(im.height for im in frames)
    cols=min(8,len(frames)); rows=math.ceil(len(frames)/cols)
    sheet=Image.new('RGBA',(w*cols,hh*rows))
    for i,im in enumerate(frames): sheet.paste(im,((i%cols)*w+(w-im.width)//2,(i//cols)*hh+(hh-im.height)//2))
    sheet.save(OUT/f'assets/previews/{uid}.webp',lossless=True,method=3)
    thumb=frames[0].copy();thumb.thumbnail((240,240));thumb.save(OUT/f'assets/previews/{uid}-thumb.webp',lossless=True)
    originals=[store(p) for p in dict.fromkeys(sources)]
    timing='原始时长' if durations else '原始帧率' if fps else '预览帧率'
    durations=durations if durations and len(durations)==len(frames) else [1000/(fps or 12)]*len(frames)
    item=dict(id=uid,name=name,group=group,status=status,count=len(frames),width=w,height=hh,columns=cols,
              sheet=f'assets/previews/{uid}.webp',thumb=f'assets/previews/{uid}-thumb.webp',durations=durations,
              timing=timing,fps=fps or 12,originals=originals,evidence=evidence,note=note,aliases=[])
    items.append(item);signatures[sig]=item

def grid(p,cols=4,rows=4,indices=None):
    with Image.open(p) as image:
        w,h=image.size
        return [image.crop((round(i%cols*w/cols),round(i//cols*h/rows),round((i%cols+1)*w/cols),round((i//cols+1)*h/rows))) for i in (indices if indices is not None else range(cols*rows))]

def runtime(p,name=None,cols=4,rows=4,indices=None,fps=None,durations=None,code='',note=''):
    add(name or p.stem,p.parent.name,grid(p,cols,rows,indices),[p],fps,durations,'运行资源',code,note)

# Explicit runtime slicing rules, checked against the Unity readers.
for folder,code,fps in [('SevenSpecialV80','SevenSpecialArt.cs',16/.76),('IngotSpecialFXV1','IngotSpecialFx.cs',16/.76),('VictoryFinaleV1','VictoryBombArt.cs',None)]:
    for p in sorted((RES/folder).glob('*.png')):runtime(p,code=code,fps=fps)
for p in sorted((RES/'FiveBakedV80').glob('ordinary-*.png')):runtime(p,code='SevenSpecialArt.BakedFrames',note='16 张原画帧；游戏可能按不同阶段选取播放。')
for p in sorted((RES/'FiveBakedV80').glob('*-five-colors.png')):
    for color in range(5):
        # Unity repeats the five phases into a sixteen-frame sequence.
        ids=[color+5*phase for phase in [0]*4+[1]*3+[2]*3+[3]*3+[4]*3]
        runtime(p,p.stem+f' / 颜色 {color+1}',5,5,ids,code='SevenSpecialArt.BakedFrames',note='按游戏逻辑将五阶段映射为16帧；前7帧的独立方砖贴图未叠加。')
runtime(RES/'Jelly/blue_jelly_pop.png','蓝色果冻消除',fps=25,code='JellyBrickArt.cs')
for folder,ds in [('VictoryCatV23',[300,100,100,180,80,80,80,120,100,80,80,80,100,100,140,200]),('FailureCatV26',[280,140,140,180,140,140,120,120,100,100,100,100,120,140,160,240])]:
    runtime(RES/folder/'cat-atlas.png','胜利猫咪' if folder.startswith('Victory') else '失败猫咪',durations=ds,code=folder+' Animation.cs')
d=json.loads((RES/'YarnV19/launcher_manifest.json').read_text(encoding='utf-8-sig'))
runtime(RES/'YarnV19/cat_fixed_pivot_atlas.png','猫咪发射',durations=d['frame_durations_ms'],code='YarnArt.cs')
for p in (RES/'StreakBoostersV62').glob('*.png'):
    if 'trail' in p.stem:continue
    runtime(p,p.stem+' / 球体循环',indices=range(4,8),fps=12,code='StreakBallArt.cs')
    runtime(p,p.stem+' / 碰撞',indices=range(8,16),fps=16,code='StreakImpactPool.cs')
for folder,filename,bottom in [('YarnObstacleV3','animation-layout.json',True),('ThirdGroup','layout.json',False),('FourthGroup','layout.json',False)]:
    layout=RES/folder/filename
    data=json.loads(layout.read_text(encoding='utf-8-sig'))
    for clip in data['clips']:
        if len(clip['frames'])<2:continue
        # These are state alternatives rather than a temporal animation.
        if clip['key'] in ['states','ingot']:continue
        p=RES/folder/(clip['key']+'.png'); image=Image.open(p);sw=clip['sourceWidth'];sh=clip['sourceHeight']
        frames=[]
        for f in clip['frames']:
            x,y,w,h=[f[k] for k in ['x','y','w','h']]
            if bottom:y=sh-y-h
            frames.append(image.crop((round(x*image.width/sw),round(y*image.height/sh),round((x+w)*image.width/sw),round((y+h)*image.height/sh))))
        fps=25 if clip['key']=='yarn-unravel' else 16/.68 if 'layer-loss' in clip['key'] else 20 if folder=='FourthGroup' else 12 if clip['key']=='shimmer' else 24 if clip['key']=='ring' else None
        add(clip['key'],folder,frames,[p],fps=fps,status='运行资源',evidence=layout.relative_to(ROOT).as_posix(),note='按项目裁切元数据读取；状态与连续动作合在同一图集时可逐帧检查。')
# Packed victory effect rectangles are top-left pixels, not a uniform grid.
layout=RES/'VictoryV23/atlases.json'
data=json.loads(layout.read_text(encoding='utf-8-sig'))
groups=collections.defaultdict(list)
for entry in data['sprites']:
    m=re.match(r'(.+?)[_-](\d+)$',entry['name'])
    if m:groups[m[1]].append((int(m[2]),entry))
for key,es in groups.items():
    fs=[];ps=[]
    for _,e in sorted(es):
        p=RES/'VictoryV23'/(e['texture']+'.png');im=Image.open(p);x,y,w,h=e['rect'];fs.append(im.crop((x,y,x+w,y+h)));ps.append(p)
    add(key,'VictoryV23',fs,ps,status='运行资源',evidence=layout.relative_to(ROOT).as_posix())

# Current failure screen packed clips.
layout=RES/'FailureV25/atlases.json'
entries=json.loads(layout.read_text(encoding='utf-8-sig'))['sprites']
for prefix in ['background','title']:
    fs=[];ps=[]
    for e in entries:
        if not e['name'].startswith(prefix+'_'):continue
        p=RES/'FailureV25'/(e['texture']+'.png');im=Image.open(p)
        sw,sh=(2560,3840) if e['texture']=='background' else (2048,256)
        x,y,w,h=e['rect'];fs.append(im.crop((round(x*im.width/sw),round(y*im.height/sh),round((x+w)*im.width/sw),round((y+h)*im.height/sh))));ps.append(p)
    add(prefix,'FailureV25',fs,ps,status='运行资源',evidence=layout.relative_to(ROOT).as_posix())

# Historical registered yarn revisions have no exported PNG frames.
for layout in sorted(ART.glob('YarnObstacle-v*/animation-layout.json')):
    for clip in json.loads(layout.read_text(encoding='utf-8-sig'))['clips']:
        if len(clip['frames'])<2:continue
        p=layout.parent/(clip['key']+'.png')
        if not p.exists():continue
        image=Image.open(p);sw=clip['sourceWidth'];sh=clip['sourceHeight'];fs=[]
        for f in clip['frames']:
            x,y,w,h=[f[k] for k in ['x','y','w','h']];y=sh-y-h
            fs.append(image.crop((round(x*image.width/sw),round(y*image.height/sh),round((x+w)*image.width/sw),round((y+h)*image.height/sh))))
        add(clip['key'],layout.parent.name,fs,[p],evidence=layout.relative_to(ROOT).as_posix())
p=ART/'LoadingPreview-v1/cat-walk-sheet.png'
add('猫咪行走','LoadingPreview-v1',grid(p,4,2),[p],evidence='ArtSource/LoadingPreview-v1/build_preview.py')

# Read explicit file-based sequences from all historical art manifests.
def walk(obj, manifest, key='', parent=None):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k in ['frames','frameFiles'] and isinstance(v,list) and len(v)>1:
                files=[x if isinstance(x,str) else x.get('file','') if isinstance(x,dict) else '' for x in v]
                if all(isinstance(x,str) and x.lower().endswith('.png') for x in files):
                    paths=[manifest.parent/x for x in files]
                    if all(p.is_file() for p in paths):
                        # Mixed rows in a sheet are split by numbered filename below.
                        stems={re.sub(r'[-_]\d+$','',p.stem) for p in paths}
                        if len(stems)==1 and next(iter(stems)) not in ['loot_icons','power_cube_pairs']:
                            ds=obj.get('durationsMs') or obj.get('preview_durations_ms')
                            if isinstance(v[0],dict) and all('duration_ms' in x for x in v):ds=[x['duration_ms'] for x in v]
                            add(obj.get('name') or obj.get('key') or next(iter(stems))+' '+key,manifest.relative_to(ART).parts[0],[Image.open(p).copy() for p in paths],paths,obj.get('fps') or obj.get('recommended_fps'),ds,evidence=manifest.relative_to(ROOT).as_posix())
                            consumed.update(p.resolve() for p in paths)
            walk(v,manifest,key+'/'+k,obj)
    elif isinstance(obj,list):
        for i,x in enumerate(obj):walk(x,manifest,key+'/'+str(i),parent)

for manifest in sorted(ART.rglob('*.json')):
    if not any(s in manifest.name for s in ['manifest','layout']):continue
    try:walk(json.loads(manifest.read_text(encoding='utf-8-sig')),manifest)
    except (ValueError,KeyError,TypeError):continue

# Numbered exported frame folders cover older art pipelines with no manifest.
groups=collections.defaultdict(list)
for p in sorted(ART.rglob('*.png')):
    rel=p.relative_to(ART);parts=[s.lower() for s in rel.parts]
    if p.resolve() in consumed:continue
    if any(s in '/'.join(parts) for s in ['evidence','introductions','inputframes','cosmetics','catcosmetics','source/']):continue
    if not any(s in ['frames','assets'] for s in parts[:-1]):continue
    m=re.match(r'(.+?)[_-](\d+)$',p.stem)
    if m and m[1] not in ['loot_icons','power_cube_pairs']:groups[(p.parent,m[1])].append((int(m[2]),p))
for (directory,name),entries in groups.items():
    if len(entries)<2:continue
    paths=[p for _,p in sorted(entries)]
    # Skip collections of distinct icons, levels and rendered rigs.
    if len({Image.open(p).size for p in paths})>1 and 'frame' not in directory.name.lower():continue
    add(name,directory.relative_to(ART).parts[0],[Image.open(p).copy() for p in paths],paths,note='按文件编号排序；没有可靠时长元数据时使用12fps预览。')

# Copy small metadata used to trace the extraction; source artwork stays byte-exact.
for p in [*ART.rglob('*manifest.json'),*ART.rglob('*layout.json'),*RES.rglob('*layout*.json')]:
    rel=p.relative_to(ROOT);target=OUT/'metadata'/rel
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
priority={'VictoryCatV23':0,'FailureCatV26':1,'YarnV19':2,'Jelly':3,'SevenSpecialV80':4,'YarnObstacleV3':5,'ThirdGroup':6,'IngotSpecialFXV1':7}
items.sort(key=lambda a:(a['status']!='运行资源',priority.get(a['group'],20),a['group'],a['name']))
catalog={'title':'喵弹拆箱 · 序列帧动画库','animations':items,'stats':{'animations':len(items),'frames':sum(a['count'] for a in items),'runtime':sum(a['status']=='运行资源' for a in items),'groups':len(set(a['group'] for a in items))},'audit':audit}
(OUT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'catalog.js').write_text('window.ANIMATION_CATALOG='+json.dumps(catalog,ensure_ascii=False)+';',encoding='utf-8')
print(json.dumps(catalog['stats'],ensure_ascii=False))
