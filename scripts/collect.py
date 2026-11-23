"""Rebuild the standalone gallery from a BounceBusters checkout. Python 3 + Pillow."""
from pathlib import Path
from PIL import Image
import argparse, collections, hashlib, json, math, re, shutil

OUT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--project', type=Path, default=OUT.parent)
args = parser.parse_args()
ROOT = args.project.resolve()
RES = ROOT/'BounceGarden/BounceGarden/Assets/Resources/Art'
items, signatures, consumed = [], {}, set()
audit = {'version': '0.4.0', 'campaignLevels': 45, 'scanRoots': ['BounceGarden/BounceGarden/Assets/Resources/Art'], 'policy': 'Explicit runtime readers only. Never scan ArtSource, historical frame folders, or unrelated metadata.'}
for directory in ['assets/originals','assets/previews','metadata']:
    (OUT/directory).mkdir(parents=True, exist_ok=True)

def store(p):
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    target = OUT/'assets/originals'/(digest+p.suffix.lower())
    if not target.exists(): shutil.copyfile(p,target)
    return {'file': target.relative_to(OUT).as_posix(), 'source': p.relative_to(ROOT).as_posix(), 'sha256': digest}

def add(name, group, frames, sources, fps=None, durations=None, status='现用动画', evidence='', note=''):
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
    if not (OUT/f'assets/previews/{uid}.webp').exists():sheet.save(OUT/f'assets/previews/{uid}.webp',lossless=True,method=3)
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
    for p in sorted((RES/folder).glob('*.png')):runtime(p,code=code,fps=fps or 20)
for p in sorted((RES/'FiveBakedV80').glob('ordinary-*.png')):runtime(p,fps=25,code='SevenSpecialArt.cs',note='16 张原画帧；游戏可能按不同阶段选取播放。')
for p in sorted((RES/'FiveBakedV80').glob('*-five-colors.png')):
    for color in range(5):
        # SevenSpecialFx plays only frame indices 7 through 15.
        ids=[color+5*phase for phase in [2]*3+[3]*3+[4]*3]
        runtime(p,p.stem+f' / 颜色 {color+1}',5,5,ids,fps=9/.66,code='SevenSpecialArt.cs',note='只播放 SevenSpecialFx 实际使用的第7–15帧，共9帧／0.66秒；不展示已被方砖替换的旧待机阶段。')
runtime(RES/'Jelly/blue_jelly_pop.png','蓝色果冻消除',fps=25,code='JellyBrickArt.cs')
for folder,ds in [('VictoryCatV23',[300,100,100,180,80,80,80,120,100,80,80,80,100,100,140,200]),('FailureCatV26',[280,140,140,180,140,140,120,120,100,100,100,100,120,140,160,240])]:
    runtime(RES/folder/'cat-atlas.png','胜利猫咪' if folder.startswith('Victory') else '失败猫咪',durations=ds,code='VictoryCatAnimation.cs' if folder.startswith('Victory') else 'FailureCatAnimation.cs')
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
        if clip['key'] in ['states','ingot','shimmer']:continue
        p=RES/folder/(clip['key']+'.png'); image=Image.open(p);sw=clip['sourceWidth'];sh=clip['sourceHeight']
        frames=[]
        for f in clip['frames']:
            x,y,w,h=[f[k] for k in ['x','y','w','h']]
            if bottom:y=sh-y-h
            frames.append(image.crop((round(x*image.width/sw),round(y*image.height/sh),round((x+w)*image.width/sw),round((y+h)*image.height/sh))))
        fps=25 if clip['key']=='yarn-unravel' else 16/.68 if 'layer-loss' in clip['key'] else 20 if folder=='FourthGroup' else 12 if clip['key']=='shimmer' else 24 if clip['key']=='ring' else None
        if clip['key']=='cat':frames=frames[3:];fps=20
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
    add(key,'VictoryV23',fs,ps,fps=8 if key=='halo' else 12,status='运行资源',evidence=layout.relative_to(ROOT).as_posix())

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
    add(prefix,'FailureV25',fs,ps,fps=24,status='运行资源',evidence=layout.relative_to(ROOT).as_posix())

# Only metadata consumed by the retained animation readers belongs in this library.
for rel in ['YarnV19/launcher_manifest.json','YarnObstacleV3/animation-layout.json','ThirdGroup/layout.json','FourthGroup/layout.json','VictoryV23/atlases.json','FailureV25/atlases.json']:
    p=RES/rel;target=OUT/'metadata'/p.relative_to(ROOT)
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
groups={'VictoryCatV23':'猫咪角色','FailureCatV26':'猫咪角色','YarnV19':'猫咪角色','ThirdGroup':'招财猫与元宝','Jelly':'普通果冻','FiveBakedV80':'果冻与特殊砖','SevenSpecialV80':'特殊砖组合','IngotSpecialFXV1':'元宝技能','YarnObstacleV3':'毛线机关','StreakBoostersV62':'强化球','FourthGroup':'铜钱机关','VictoryV23':'通关与失败','VictoryFinaleV1':'通关与失败','FailureV25':'通关与失败'}
labels={'combo-bands':'条带组合','combo-bomb':'双炸弹组合','combo-cross':'十字组合','combo-merge':'技能合并','flower-vortex':'五色花漩涡','yarn-layer-loss':'二级毛线脱层','yarn-layer-loss-l3':'三级毛线脱层','yarn-unravel':'毛线完全解开','cat':'招财猫挥爪','ring':'元宝光环','burst':'通关爆发','halo':'通关光晕','background':'失败云朵循环','single-burst':'单色结算爆炸','bomb-3-colors':'三色结算爆炸','bomb-4-colors':'四色结算爆炸','bomb-5-colors':'五色结算爆炸'}
kind_names={'bomb':'炸弹','cross':'十字激光','flower':'五色花','horizontal':'横向激光','vertical':'纵向激光','ordinary':'普通果冻'}
colors={'pink':'粉红','yellow':'明黄','mint':'薄荷绿','blue':'天蓝','lilac':'丁香紫'}
for item in items:
    family=item['group'];name=item['name'];item['family']=family;item['group']=groups[family]
    if family=='FiveBakedV80':
        kind=name.split('-')[0]
        if kind=='ordinary':item['name']=colors[name.split('-')[1]]+'果冻消除'
        else:item['name']=list(colors.values())[int(name.rsplit(' ',1)[1])-1]+kind_names[kind]+'施放'
    elif family=='IngotSpecialFXV1':item['name']='元宝'+{'bomb':'爆炸','flower':'五色花','laser':'激光','merge':'合并'}[name]
    elif family=='StreakBoostersV62':
        kind=name.split(' / ')[0];item['name']={'bomb':'炸弹球','pierce':'穿透球','super':'超级球'}[kind]+' / '+name.split(' / ')[1]
    elif name=='burst' and family=='FourthGroup':item['name']='铜钱破碎'
    else:item['name']=labels.get(name,name)
    item['status']='现用动画';item['aliases']=[]
    if family=='ThirdGroup' and name=='cat':item['note']='当前招财猫挥爪动作：源图第3–15帧，20fps；初始与蓄力状态不是独立动画。'
priority={'猫咪角色':0,'普通果冻':1,'果冻与特殊砖':2,'特殊砖组合':3,'毛线机关':4,'招财猫与元宝':5,'元宝技能':6,'强化球':7,'铜钱机关':8,'通关与失败':9}
items.sort(key=lambda a:(priority[a['group']],a['name']))
policy=json.loads((OUT/'runtime-policy.json').read_text(encoding='utf-8'))
assert {s['source'] for a in items for s in a['originals']}==set(policy['resourcePaths']),'Runtime resource allowlist changed; review before publishing.'
catalog={'title':'喵弹拆箱 · 现用动画库','animations':items,'stats':{'animations':len(items),'frames':sum(a['count'] for a in items),'runtime':len(items),'groups':len(set(a['group'] for a in items))},'audit':audit}
(OUT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'catalog.js').write_text('window.ANIMATION_CATALOG='+json.dumps(catalog,ensure_ascii=False)+';',encoding='utf-8')
used={a[k] for a in items for k in ['sheet','thumb']}|{s['file'] for a in items for s in a['originals']}
for folder in ['assets/originals','assets/previews']:
    base=(OUT/folder).resolve()
    for p in base.iterdir():
        if p.is_file() and p.relative_to(OUT).as_posix() not in used:
            assert p.resolve().is_relative_to(base);p.unlink()
metadata_roots={(OUT/'metadata'/RES.relative_to(ROOT)/rel).resolve() for rel in ['YarnV19/launcher_manifest.json','YarnObstacleV3/animation-layout.json','ThirdGroup/layout.json','FourthGroup/layout.json','VictoryV23/atlases.json','FailureV25/atlases.json']}
for p in (OUT/'metadata').rglob('*'):
    if p.is_file() and p.resolve() not in metadata_roots:p.unlink()
for p in sorted((OUT/'metadata').rglob('*'),key=lambda p:len(p.parts),reverse=True):
    if p.is_dir() and not any(p.iterdir()):p.rmdir()
print(json.dumps(catalog['stats'],ensure_ascii=False))
