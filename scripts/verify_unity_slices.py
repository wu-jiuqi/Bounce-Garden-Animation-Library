"""Compare all exported web frames with independently exported Unity Sprite values."""
from pathlib import Path
import collections,json,sys

root=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]) if len(sys.argv)>1 else root.parent/'Builds/AnimationCleanup/unity-slices.json'
actual=json.loads(source.read_text(encoding='utf-8-sig'))['frames']
catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
groups=collections.defaultdict(list)
for item in actual:groups[item['family'],item['texture']].append(item)
max_rect=max_pivot=0;checks=0
for animation in catalog['animations']:
    key=animation['family'],Path(animation['originals'][0]['source']).stem
    for frame in animation['frameGeometry']:
        sw,sh=frame['sourceSize'];expected=[v/s for v,s in zip(frame['rect'],[sw,sh,sw,sh])]
        candidates=groups[key]
        assert candidates,('Missing Unity frame',key)
        i=min(range(len(candidates)),key=lambda i:sum(abs(a-b) for a,b in zip(candidates[i]['rect'],expected)))
        unity=candidates.pop(i)
        rect_error=max(abs(a-b)*s for a,b,s in zip(unity['rect'],expected,[sw,sh,sw,sh]))
        pivot_error=max(abs(a-b)*s for a,b,s in zip(unity['pivot'],frame['pivot'],frame['renderSize']))
        assert rect_error<.01,(key,rect_error,unity['rect'],expected)
        assert pivot_error<=1.01,(key,pivot_error,unity['pivot'],frame['pivot'])
        max_rect=max(max_rect,rect_error);max_pivot=max(max_pivot,pivot_error);checks+=1
assert checks==906 and not any(groups.values())
report={'result':'passed','comparedFrames':checks,'maxSourceRectErrorPixels':max_rect,'maxPivotErrorPixels':max_pivot,'method':'Actual Unity Sprite.rect and Sprite.pivot compared to each web frame; no web exporter logic used in the engine dump.'}
(root/'verification/unity-slice-parity.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
