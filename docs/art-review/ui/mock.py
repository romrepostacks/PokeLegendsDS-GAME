from PIL import Image, ImageDraw, ImageFont
import random
SM=ImageFont.load_default_imagefont()           # crisp 6x11 bitmap
BIG=ImageFont.truetype('/usr/share/fonts/opentype/unifont/unifont_jp.otf',16)
girl=None   # 4 frames 64x64: down,left,right,up
hair=Image.open('/tmp/r10/hair-shapes.png').convert('RGBA')
H=hair.resize((hair.width//3,hair.height//3),Image.NEAREST)
H=key(H) if False else H  # cells 40x58
def hair_tile(i):  # girl front view of shape i
    r=2+i//4; c=(i%4)*3
    return key(H.crop((c*40,r*58,c*40+40,r*58+38)))
NAMES=['Short','Crop','Spiky','Shaggy','Wavy','Ponytail','Bob','Braids']
TABS=['Body','Hair','Hat','Top','Scarf','Legs','Shoes','Skin','Eyes']
SW=[(236,233,230),(250,226,160),(232,190,90),(200,140,60),(150,90,50),(95,60,40),(60,40,30),(30,25,25),(170,170,175),(230,120,60),(200,60,60),(230,120,170),(150,90,200),(70,110,220),(60,170,170),(90,170,90)]
def icon(d,x,y,k,col):
    # tiny 12x12 glyphs
    if k==0: d.ellipse((x+3,y,x+8,y+5),fill=col); d.rectangle((x+2,y+6,x+9,y+11),fill=col)
    elif k==1: d.pieslice((x,y,x+11,y+12),180,360,fill=col); d.rectangle((x,y+6,x+2,y+11),fill=col); d.rectangle((x+9,y+6,x+11,y+11),fill=col)
    elif k==2: d.pieslice((x+1,y+2,x+10,y+14),180,360,fill=col); d.rectangle((x,y+7,x+11,y+9),fill=col); d.ellipse((x+4,y,x+7,y+3),fill=col)
    elif k==3: d.polygon([(x,y+3),(x+3,y),(x+8,y),(x+11,y+3),(x+9,y+5),(x+9,y+11),(x+2,y+11),(x+2,y+5)],fill=col)
    elif k==4: d.rectangle((x,y+2,x+11,y+5),fill=col); d.rectangle((x+7,y+5,x+10,y+11),fill=col)
    elif k==5: d.polygon([(x+1,y),(x+10,y),(x+11,y+11),(x+7,y+11),(x+6,y+4),(x+5,y+4),(x+4,y+11),(x,y+11)],fill=col)
    elif k==6: d.rectangle((x+2,y+1,x+6,y+8),fill=col); d.rectangle((x+2,y+7,x+11,y+11),fill=col)
    elif k==7: d.ellipse((x+1,y+1,x+10,y+10),fill=col)
    elif k==8: d.ellipse((x,y+3,x+11,y+9),fill=col); d.ellipse((x+4,y+4,x+7,y+8),fill=(0,0,0,0) if False else None,outline=None)
def txt(d,xy,s,f,col,anchor='la'):
    l,t,r,b=d.textbbox((0,0),s,font=f); w,h=r-l,b-t
    x,y=xy
    if anchor[0]=='m': x-=w//2
    elif anchor[0]=='r': x-=w
    if anchor[1]=='m': y-=h//2
    d.text((x-l,y-t),s,font=f,fill=col)
def key(im):
    im=im.convert('RGBA'); bg=im.getpixel((0,0)); px=im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x,y][:3]==bg[:3]: px[x,y]=(0,0,0,0)
    return im

def top_screen(T):
    im=Image.new('RGB',(256,192),T['sky0']); d=ImageDraw.Draw(im)
    for y in range(192):  # sky gradient
        t=y/191; c=tuple(int(T['sky0'][i]*(1-t)+T['sky1'][i]*t) for i in range(3)); d.line((0,y,255,y),fill=c)
    # distant hills / snow ground
    d.polygon([(0,120),(50,100),(110,116),(170,96),(256,112),(256,192),(0,192)],fill=T['hill'])
    d.rectangle((0,140,255,191),fill=T['snow'])
    random.seed(3)
    for _ in range(60): x,y=random.randrange(256),random.randrange(140); d.point((x,y),fill=T['flake'])
    # platform + shadow
    d.ellipse((88,150,168,166),fill=T['pad']); d.ellipse((96,152,160,163),fill=T['pad2'])
    ch=key(Image.open('/tmp/r9/girl-idle.png').crop((0,0,64,64))).resize((128,128),Image.NEAREST); im.paste(ch,(64,32),ch)
    # name plate
    d.rounded_rectangle((6,6,120,24),4,fill=T['plate'],outline=T['line'])
    txt(d,(63,15),'TRAINER',BIG,T['ptext'],'mm')
    d.rounded_rectangle((176,6,250,24),4,fill=T['plate'],outline=T['line'])
    txt(d,(213,15),'Girl',SM,T['ptext'],'mm')
    # facing arrows
    for x,s in ((24,'<'),(232,'>')): d.rounded_rectangle((x-9,88,x+9,106),4,fill=T['plate'],outline=T['line']); txt(d,(x,97),s,SM,T['ptext'],'mm')
    txt(d,(128,178),'L / R  turn     Y  walk',SM,T['hint'],'mm')
    return im

def bottom_screen(T,sel=4,tab=1,swsel=3):
    im=Image.new('RGB',(256,192),T['bg']); d=ImageDraw.Draw(im)
    if T.get('paper'):
        random.seed(9)
        for _ in range(500): x,y=random.randrange(256),random.randrange(192); d.point((x,y),fill=T['grain'])
    # tab ribbon
    tw=28
    for i,n in enumerate(TABS):
        x=2+i*tw; on=i==tab
        box=(x,2,x+tw-2,24 if on else 22)
        d.rounded_rectangle(box,4,fill=T['tabon'] if on else T['taboff'],outline=T['line'])
        icon(d,x+7,6,i,T['icon_on'] if on else T['icon_off'])
    d.line((0,24,255,24),fill=T['line'])
    # section title
    d.rounded_rectangle((4,28,252,44),4,fill=T['panel'],outline=T['line'])
    txt(d,(10,36),'HAIR',BIG,T['accent'],'lm'); txt(d,(56,36),'Style 5 of 8',SM,T['text'],'lm')
    txt(d,(246,36),NAMES[sel],SM,T['text'],'rm')
    # option grid 4x2
    for k in range(8):
        cx,cy=k%4,k//4; x=6+cx*62; y=48+cy*48
        on=k==sel
        d.rounded_rectangle((x,y,x+58,y+44),5,fill=T['tileon'] if on else T['tile'],outline=T['accent'] if on else T['line'],width=2 if on else 1)
        t=hair_tile(k); im.paste(t,(x+9,y+3),t)
        if on: d.rectangle((x+2,y+34,x+56,y+42),fill=T['accent']); txt(d,(x+29,y+38),NAMES[k],SM,T['onacc'],'mm')
    # swatches
    d.rounded_rectangle((4,146,252,166),4,fill=T['panel'],outline=T['line'])
    txt(d,(10,156),'<',SM,T['text'],'lm'); txt(d,(246,156),'>',SM,T['text'],'rm')
    for i,c in enumerate(SW[:14]):
        x=18+i*16; d.rectangle((x,150,x+12,162),fill=c,outline=T['line'])
        if i==swsel: d.rectangle((x-2,148,x+14,164),outline=T['accent'],width=2)
    # buttons
    for (x0,x1,lab,key,prim) in ((4,80,'Random','X',0),(86,162,'Back','B',0),(168,252,'Confirm','START',1)):
        d.rounded_rectangle((x0,170,x1,189),5,fill=T['btnp'] if prim else T['btn'],outline=T['line'])
        d.rounded_rectangle((x0+3,173,x0+3+6*len(key)+4,186),3,fill=T['key'])
        txt(d,(x0+5+3*len(key)+0,180),key,SM,T['keytext'],'mm')
        txt(d,((x0+6*len(key)+9+x1)//2,180),lab,SM,T['btext_p'] if prim else T['btext'],'mm')
    return im

THEMES={
'frost':dict(sky0=(22,44,78),sky1=(70,120,170),hill=(150,180,210),snow=(220,234,246),flake=(255,255,255),pad=(120,170,210),pad2=(170,210,236),
  plate=(16,34,60),line=(110,200,240),ptext=(232,246,255),hint=(30,50,80),
  bg=(14,30,54),panel=(22,48,80),tabon=(40,90,140),taboff=(20,40,66),icon_on=(255,216,90),icon_off=(120,170,210),
  accent=(255,216,90),text=(220,238,255),tile=(24,52,86),tileon=(36,84,128),onacc=(20,30,50),
  btn=(24,52,86),btnp=(255,216,90),btext=(220,238,255),btext_p=(20,30,50),key=(110,200,240),keytext=(14,30,54)),
'classic':dict(sky0=(170,215,240),sky1=(225,240,250),hill=(200,215,230),snow=(245,248,252),flake=(255,255,255),pad=(200,60,60),pad2=(235,110,100),
  plate=(255,255,255),line=(40,48,68),ptext=(40,48,68),hint=(60,70,90),
  bg=(232,236,242),panel=(255,255,255),tabon=(214,68,60),taboff=(205,212,224),icon_on=(255,255,255),icon_off=(80,90,110),
  accent=(214,68,60),text=(40,48,68),tile=(246,248,252),tileon=(255,236,232),onacc=(255,255,255),
  btn=(255,255,255),btnp=(214,68,60),btext=(40,48,68),btext_p=(255,255,255),key=(40,48,68),keytext=(255,255,255)),
'notebook':dict(sky0=(200,215,225),sky1=(235,230,215),hill=(190,200,200),snow=(245,242,232),flake=(255,255,255),pad=(160,120,80),pad2=(200,160,110),
  plate=(246,238,219),line=(90,70,50),ptext=(59,45,31),hint=(90,70,50),paper=1,grain=(222,208,180),
  bg=(233,220,192),panel=(246,238,219),tabon=(196,73,47),taboff=(214,196,160),icon_on=(255,244,226),icon_off=(110,85,60),
  accent=(196,73,47),text=(59,45,31),tile=(246,238,219),tileon=(255,232,214),onacc=(255,244,226),
  btn=(246,238,219),btnp=(46,110,100),btext=(59,45,31),btext_p=(255,244,226),key=(90,70,50),keytext=(246,238,219)),
}
for name,T in THEMES.items():
    top=top_screen(T); bot=bottom_screen(T)
    ds=Image.new('RGB',(256+16,192*2+24),(30,30,36)); ds.paste(top,(8,8)); ds.paste(bot,(8,192+16))
    ds.resize((ds.width*3,ds.height*3),Image.NEAREST).save(f'{name}.png')
print('ok')
