"""Sprite sampling and registration; coordinates in source-image top-left pixels."""
import math
from PIL import Image

ALPHA_CUTOFFS = {
    'FiveBakedV80': .4, 'SevenSpecialV80': .4, 'VictoryFinaleV1': .4,
    'IngotSpecialFXV1': .035, 'YarnObstacleV3': .2,
    'ThirdGroup': .2, 'FourthGroup': .2,
}

def sample_rect(image, rect, *, pivot=(.5,.5), scale=(1,1)):
    x,y,w,h=rect
    assert w>0 and h>0 and x>=-.01 and y>=-.01
    assert x+w<=image.width+.01 and y+h<=image.height+.01, (rect,image.size)
    result=image.convert('RGBA').transform(
        (max(1,round(w)),max(1,round(h))), Image.Transform.EXTENT,
        (x,y,x+w,y+h), Image.Resampling.BILINEAR,
    )
    result.info['sprite']={'rect':list(rect),'sourceSize':list(image.size),'pivot':list(pivot),'scale':list(scale)}
    return result

def register_frames(frames, family, padding=4):
    """Preserve a shared Unity origin, per-frame pivot and body-reference scale."""
    cutoff=ALPHA_CUTOFFS.get(family,0)
    prepared=[];bounds=[];geometry=[]
    for frame in frames:
        meta=frame.info.get('sprite',{'rect':[0,0,*frame.size],'sourceSize':list(frame.size),'pivot':[.5,.5],'scale':[1,1]})
        im=frame.convert('RGBA')
        if cutoff:
            table=[round(max(0,min(1,(a/255-cutoff)/(1-cutoff)))*255) for a in range(256)]
            im.putalpha(im.getchannel('A').point(table))
        sx,sy=meta['scale'];size=(max(1,round(im.width*sx)),max(1,round(im.height*sy)))
        if im.size!=size:im=im.resize(size,Image.Resampling.BICUBIC)
        px,py=meta['pivot'];left=-px*im.width;top=-(1-py)*im.height
        bounds.append((left,top,left+im.width,top+im.height));prepared.append(im)
        geometry.append(dict(meta,alphaCutoff=cutoff,renderSize=list(im.size)))
    left=math.floor(min(b[0] for b in bounds))-padding;top=math.floor(min(b[1] for b in bounds))-padding
    right=math.ceil(max(b[2] for b in bounds))+padding;bottom=math.ceil(max(b[3] for b in bounds))+padding
    size=(right-left,bottom-top);normalized=[]
    for im,box,meta in zip(prepared,bounds,geometry):
        pos=(round(box[0]-left),round(box[1]-top))
        assert pos[0]>=padding and pos[1]>=padding
        assert pos[0]+im.width<=size[0]-padding and pos[1]+im.height<=size[1]-padding
        canvas=Image.new('RGBA',size);canvas.paste(im,pos)
        meta['offset']=list(pos);normalized.append(canvas)
    return normalized,geometry,[-left,-top]
