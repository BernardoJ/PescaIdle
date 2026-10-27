"""Original pixel decoration artwork; backgrounds are cached, fish draw on top."""
import math
from functools import lru_cache
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QImage, QPainter, QColor, QPolygon
from pesca_aquario_decor import CAT, SLOTS

def poly(p,points,color):
    p.setPen(Qt.NoPen);p.setBrush(QColor(color))
    p.drawPolygon(QPolygon([QPoint(x,y) for x,y in points]))

def line(p,points,color):
    p.setPen(QColor(color));p.drawPolyline(QPolygon([QPoint(x,y) for x,y in points]))

@lru_cache(maxsize=64)
def aquarium_background(selection=None):
    chosen=dict(zip(SLOTS,selection or [None]*len(SLOTS)))
    style={slot:CAT[id_]['style'] if id_ in CAT and CAT[id_]['slot']==slot else None for slot,id_ in chosen.items()}
    image=QImage(256,128,QImage.Format_ARGB32_Premultiplied)
    image.fill(QColor('#263749'));p=QPainter(image)
    def box(x,y,w,h,color):p.fillRect(x,y,w,h,QColor(color))
    for y in range(0,128,16):
        box(0,y,256,1,'#32465a')
        for x in range((y//16%2)*16,256,32):box(x,y,1,16,'#32465a')
    box(7,8,242,108,'#101e2b')
    frame={
        None:('#ba9860','#f0d39b','#69513c','#a9c8bf'),
        'madeira':('#9b724b','#dec48f','#6f5139','#a9c8bf'),
        'cobre':('#b57554','#e6b982','#6e5549','#a9c8bf'),
        'marmore':('#688eac','#c8dfdf','#374f75','#b6d9e1')
    }[style['moldura']]
    for inset,color in zip((0,1,3,5),frame):
        p.setPen(QColor(color));p.setBrush(Qt.NoBrush)
        p.drawRect(8+inset,9+inset,239-2*inset,104-2*inset)
    for y in range(16,106):
        depth=(y-16)/90
        box(15,y,226,1,QColor(int(29-depth*13),int(91-depth*47),int(108-depth*48)).name())
    light={
        None:('#d2af76','#f5dca0',[(162,217,199,16)]*3),
        'ambar':('#bb8452','#ffdd90',[(255,203,112,23)]*3),
        'safira':('#91b3cb','#d8f1fa',[(114,190,250,24)]*3),
        'aurora':('#8975aa','#d3e8ed',[(107,244,188,26),(201,148,250,25),(103,205,243,25)])
    }[style['luz']]
    for i,x in enumerate((42,114,191)):
        p.setPen(Qt.NoPen);p.setBrush(QColor(*light[2][i]))
        p.drawPolygon(QPolygon([QPoint(x,16),QPoint(x+8,16),QPoint(x+33,105),QPoint(x-14,105)]))
        box(x-6,5,22,4,light[0]);box(x-2,10,14,2,light[1])
        if style['luz']:
            box(x-7,4,24,1,light[1]);box(x+1,7,8,1,frame[2])

    p.save();p.setClipRect(16,16,224,90)
    if style['fundo']=='pedras':
        for x,y,w,h in ((62,59,28,43),(91,45,36,57),(139,64,31,38),(172,51,22,51)):
            poly(p,[(x,y+9),(x+9,y),(x+w-4,y+5),(x+w,y+h),(x-4,y+h)],'#28525d')
            line(p,[(x+9,y+2),(x+13,y+22),(x+7,y+34)],'#386573')
    elif style['fundo']=='algas':
        for x,height in ((65,42),(87,61),(114,33),(144,51),(174,62),(200,40)):
            pts=[(x+round(5*math.sin(y*.13)),103-y) for y in range(height)]
            line(p,pts,'#2b6463')
            for y in range(10,height,9):
                poly(p,[(x+round(5*math.sin(y*.13)),103-y),(x-9,100-y),(x-3,96-y)],'#326966')
    elif style['fundo']=='ruinas':
        for x in (74,112,163):
            box(x,53,9,50,'#335e69');box(x-2,50,13,4,'#46727a')
            box(x+2,57,1,40,'#49747a');box(x-2,98,13,4,'#2b4e5e')
        poly(p,[(72,52),(86,40),(156,40),(174,52),(169,55),(154,46),(89,46),(78,55)],'#3c6973')
        line(p,[(95,42),(101,45),(98,50)],'#254c5e')
    gravel={None:('#aa9d78','#6d7b70'),'cascalho':('#aa9470','#73654f'),
        'areia':('#d7c9a0','#a39a79'),'jade':('#6b9b89','#3f6e67')}[style['substrato']]
    box(15,102,226,6,gravel[0])
    for i in range(38):box(17+i*6,103+i%3,2,1,gravel[1])
    if style['substrato']=='jade':
        for i in range(22):
            x=19+i*10;box(x,103+i%3,4,2,'#87b8a1');box(x+1,103+i%3,2,1,'#b4d5b3')
    elif style['substrato']=='areia':
        for x in (47,96,153,213):line(p,[(x,104),(x+2,102),(x+4,104)],'#ece0ba')
    if style['plantas'] is None:
        for x,height in ((27,28),(37,18),(220,33),(230,22)):
            for y in range(height):
                box(x+round(2*math.sin(y*.4)),103-y,2,2,'#507e70')
                if y%6==0:box(x-3,103-y,5,2,'#729e7a')
    else:
        for x,height in ((25,38),(37,25),(220,44),(231,29)):
            line(p,[(x,103),(x-1,103-height//2),(x+2,103-height)],'#538675')
            for y in range(7,height,7):
                yy=103-y
                if style['plantas']=='elodeas':
                    poly(p,[(x,yy),(x-7,yy-4),(x-5,yy+1),(x,yy+2),(x+6,yy-2),(x+5,yy+3)],'#6caa83')
                elif style['plantas']=='samambaias':
                    poly(p,[(x,yy+3),(x-9,yy-5),(x-7,yy-8),(x-2,yy-3),(x+2,yy-9),(x+6,yy-7),(x+5,yy-2)],'#75a886')
                else:
                    p.setPen(Qt.NoPen);p.setBrush(QColor('#83b697'));p.drawEllipse(x-7,yy-3,10,5)
            if style['plantas']=='lotus':
                yy=103-height
                poly(p,[(x-6,yy+2),(x-6,yy-2),(x-2,yy),(x+1,yy-5),(x+4,yy),(x+8,yy-1),(x+5,yy+3)],'#d7a4b4')
                box(x,yy,3,2,'#f3d99b')
    if style['ornamento'] is None:
        for x,width in ((43,18),(185,23)):
            box(x,99,width,5,'#566d70');box(x+3,95,width-6,5,'#77948c');box(x+5,95,width-9,1,'#9bb0a0')
    elif style['ornamento']=='conchas':
        for x,y,size in ((43,100,7),(54,99,5),(185,98,10),(201,101,6)):
            poly(p,[(x,y),(x+1,y-size//2),(x+size//2,y-size//2-2),(x+size-1,y-size//2),(x+size,y),(x+size//2,y+2)],'#d9c9b3')
            for dx in (2,4,6):line(p,[(x+size//2,y+1),(x+dx,y-size//2)],'#a9978c')
    elif style['ornamento']=='bau':
        box(184,91,28,13,'#634f43');box(185,89,26,6,'#a27c52')
        box(184,94,28,2,'#d0ac65');box(187,90,2,14,'#d3b576');box(207,90,2,14,'#d3b576')
        box(197,94,3,4,'#ecd292');box(198,95,1,2,'#5a5843')
        for x in (176,180,215):box(x,102,3,1,'#d7be7b')
    elif style['ornamento']=='coral':
        for x,h in ((181,18),(186,25),(207,22),(213,14)):
            box(x,103-h,3,h,'#b27e8b')
            for y in range(103-h+4,103,6):
                line(p,[(x,y),(x-4,y-3),(x-4,y-6)],'#d5a0a2')
                line(p,[(x+2,y+2),(x+6,y-2),(x+6,y-5)],'#d5a0a2')
        line(p,[(186,80),(192,75),(202,75),(208,82)],'#d9aaa8')
        line(p,[(187,82),(193,78),(200,78),(206,83)],'#ba8b99')
    p.restore()
    box(8,115,240,4,frame[0]);box(12,119,232,9,'#514333')
    if style['base'] is None:
        for x in (20,76,132,188):box(x,120,47,2,'#776042')
    elif style['base']=='carvalho':
        box(12,119,232,9,'#805b3b')
        for x in (19,74,129,184):
            box(x,120,47,5,'#aa8252');line(p,[(x+4,123),(x+20,121),(x+39,124)],'#715236')
    elif style['base']=='navegador':
        box(12,119,232,9,'#483f3c');box(13,126,230,1,'#b69364')
        for x in (26,81,136,191):
            for i,color in enumerate(('#789992','#b99072','#6a879f','#c9b187')):
                box(x+i*5,120,4,6,color)
            box(x+31,121,7,5,'#d7ba78');box(x+34,120,1,7,'#405869')
    else:
        box(12,119,232,9,'#2b435b');box(14,120,228,1,'#f0d08a');box(14,126,228,1,'#b39258')
        for x in (20,70,120,170,225):poly(p,[(x,123),(x+3,121),(x+6,123),(x+3,125)],'#dec080')
    if style['moldura']=='madeira':
        for y in (11,112):line(p,[(17,y),(39,y+1),(57,y),(70,y+1)],'#b79769')
    elif style['moldura']=='cobre':
        for x in (11,244):
            for y in (13,58,110):box(x,y,2,2,'#e7c095')
        box(11,40,2,7,'#6f9988');box(244,89,2,6,'#6f9988')
    elif style['moldura']=='marmore':
        for x in (10,243):line(p,[(x,20),(x+2,33),(x,46),(x+2,57)],'#9dbbc9')
    p.end();return image
