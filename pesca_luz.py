"""Material-aware palette animation on the original, unchanged pixel clusters."""
import math
from datetime import datetime
from dataclasses import dataclass
from collections import deque
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter

FRAME_COUNT=96


@dataclass(frozen=True)
class LightFrame:
    background: QImage
    foreground: QImage
    night: float
    daylight: float
    position: float
    label: str


def weights(position):
    # Local civil clock, without network/geolocation. Distinct noon palette.
    stops=tuple((hour/24,kind) for hour,kind in (
        (0,'night'),(5,'night'),(6,'dawn'),(8,'day'),(10,'day'),
        (12,'noon'),(14,'noon'),(16,'day'),(17.5,'dusk'),
        (18.5,'dusk'),(20,'night'),(24,'night')))
    for (lo,a),(hi,b) in zip(stops,stops[1:]):
        if lo<=position<=hi:
            t=(position-lo)/(hi-lo)
            t=t*t*(3-2*t)
            return a,b,t
    return 'night','night',0


def local_position(moment=None):
    moment=datetime.now() if moment is None else moment
    return (moment.hour*3600+moment.minute*60+moment.second+moment.microsecond/1e6)/86400


def phase_label(position):
    hour=position*24
    return ('AMANHECER' if 5<=hour<8 else 'MEIO-DIA' if 11<=hour<14
            else 'DIA' if 8<=hour<17 else 'ENTARDECER' if 17<=hour<20 else 'NOITE')


def palette_rgb(rgb,material,kind):
    r,g,b=rgb
    lum=(r*.25+g*.65+b*.1)/255
    if kind=='dusk':return rgb
    if material=='sky':
        ramps={'day':((65,126,174),(105,91,72)),
               'noon':((75,139,189),(102,101,65)),
               'dawn':((107,82,132),(121,98,69)),
               'night':((8,13,35),(28,34,44))}
        base,span=ramps[kind]
        out=tuple(base[i]+span[i]*lum for i in range(3))
    elif kind=='night':
        if material=='water':out=(r*.28+6,g*.45+10,b*.52+22)
        elif material=='reflection':out=(r*.31+13,g*.39+18,b*.50+31)
        else:out=(r*.29+4,g*.36+6,b*.45+r*.035+15)
    elif kind=='dawn':
        out=(r*.83+16,g*.79+12,b*.95+17)
    elif kind=='noon':
        if material=='water':out=(r*.88+13,g*1.17+12,b*1.12+14)
        elif material=='reflection':out=(r*.87+24,g+24,b*1.15+26)
        else:out=(r*1.08+12,g*1.15+13,b*1.01+8)
    elif material=='water':out=(r*.85+8,g*1.12+8,b*1.08+12)
    elif material=='reflection':out=(r*.85+20,g*.96+20,b*1.14+26)
    elif g>r*1.07 and g>b*.95:out=(r*1.02+9,g*1.13+10,b*.91+8)
    else:out=(r*1.08+6,g*1.10+8,b*1.04+7)
    return tuple(max(0,min(255,round(c))) for c in out)


class Lighting:
    def __init__(self,background,foreground):
        w,h=background.width(),background.height()
        source=background.convertToFormat(QImage.Format_RGBA8888)
        rgba=bytes(source.constBits())
        # Connected warm sky pixels. Warm cabin/wood pixels do not share its LUT.
        sky=set();queue=deque()
        def sky_color(x,y):
            i=(y*w+x)*4;r,g,b=rgba[i:i+3]
            return y<62 and r>145 and g>95 and b>85 and r>g*1.06
        for x in range(w):
            if sky_color(x,0):sky.add(x);queue.append((x,0))
        while queue:
            x,y=queue.popleft()
            for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                idx=yy*w+xx
                if 0<=xx<w and 0<=yy<h and idx not in sky and sky_color(xx,yy):
                    sky.add(idx);queue.append((xx,yy))
        materials=[]
        for y in range(h):
            for x in range(w):
                i=(y*w+x)*4;r,g,b=rgba[i:i+3]
                material='land'
                if y*w+x in sky:material='sky'
                elif y>63 and r<g*.97 and b>g*.65:material='water'
                elif y>63 and 170<x<225 and r>g*1.05 and g>85:material='reflection'
                materials.append(material)
        plates={}
        lookup={}
        for kind in ('night','dawn','day','noon','dusk'):
            data=bytearray(rgba)
            for index,material in enumerate(materials):
                i=index*4;rgb=tuple(rgba[i:i+3]);key=(rgb,material,kind)
                if key not in lookup:lookup[key]=palette_rgb(rgb,material,kind)
                data[i:i+3]=bytes(lookup[key])
            plates[kind]=QImage(bytes(data),w,h,w*4,QImage.Format_RGBA8888).copy()
        self.frames=[]
        for index in range(FRAME_COUNT):
            position=index/FRAME_COUNT
            a,b,t=weights(position)
            img=plates[a].copy()
            if a!=b:
                p=QPainter(img);p.setOpacity(t);p.drawImage(0,0,plates[b]);p.end()
            front=QImage(w,h,QImage.Format_ARGB32_Premultiplied);front.fill(Qt.transparent)
            p=QPainter(front);p.drawImage(0,0,img)
            p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            p.drawImage(0,0,foreground);p.end()
            # Foreground PNG's alpha owns the overlap, not its sunset RGB.
            night=(1-t if a=='night' else .18*(1-t) if a=='dusk' else 0)+(t if b=='night' else .18*t if b=='dusk' else 0)
            daylight=(1-t if a in ('day','noon') else 0)+(t if b in ('day','noon') else 0)
            label=phase_label(position)
            self.frames.append(LightFrame(img,front,night,daylight,position,label))
        self.frames=tuple(self.frames)

    def at(self,moment=None):
        """Read the device's local clock on every render, including clock changes.

        An explicit datetime is only used by isolated previews/QA. Scene animation
        time and save timestamps never drive this clock. Interpolate cached plates
        without per-pixel Python work or an ever-growing cache.
        """
        position=local_position(moment)
        index=position*FRAME_COUNT
        lo=int(index)%FRAME_COUNT;hi=(lo+1)%FRAME_COUNT;t=index-int(index)
        a,b=self.frames[lo],self.frames[hi]
        if t==0:
            return a
        def blend(first,second):
            img=first.copy();p=QPainter(img)
            # Plates share the original binary coverage. SourceOver interpolates
            # colour and preserves those exact opaque/transparent pixel edges.
            p.setOpacity(t);p.drawImage(0,0,second);p.end()
            return img
        return LightFrame(blend(a.background,b.background),blend(a.foreground,b.foreground),
                          a.night*(1-t)+b.night*t,a.daylight*(1-t)+b.daylight*t,
                          position,phase_label(position))

    @staticmethod
    def actors(img,frame):
        # SourceAtop changes the palette but preserves each sprite's exact alpha.
        p=QPainter(img);p.setCompositionMode(QPainter.CompositionMode_SourceAtop)
        if frame.night:
            p.fillRect(img.rect(),QColor(20,32,61,round(frame.night*132)))
        if frame.daylight:
            p.fillRect(img.rect(),QColor(220,245,218,round(frame.daylight*25)))
        p.end()

    @staticmethod
    def emissive(p,f,dy,frame):
        n=frame.night
        if n<.12:return
        p.save()
        # Small stepped light pools, never a soft radial gradient.
        for x,y,w,h,alpha in ((150,97+dy,13,10,24),(153,98+dy,8,7,42),
                               (44,54,13,9,30),(47,55,8,6,44)):
            p.fillRect(x,y,w,h,QColor(238,160,76,round(alpha*n)))
        for x in (49,53):
            p.fillRect(x,56,2,3,QColor('#d5995c'))
            p.fillRect(x,56,1,2,QColor('#f5d28a'))
        p.fillRect(155,98+dy,5,4,QColor('#bd864e'))
        p.fillRect(156,98+dy,3,3,QColor('#f4c87a'))
        p.fillRect(157,98+dy,1,2,QColor('#fff1bb' if int(f*7)%3 else '#ffda94'))
        if n>.5:
            for i,(x,y) in enumerate(((25,94),(65,87),(222,113),(32,130),(244,97),(74,76))):
                if math.sin(f*1.7+i)>0:
                    p.fillRect(x+round(math.sin(f+i)*2),y+round(math.cos(f*.7+i)),1,1,QColor('#e6dba1'))
        p.restore()
