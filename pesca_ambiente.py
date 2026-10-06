"""Bounded, deterministic pixel animation; never consumes gameplay randomness."""
import math
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QImage, QPainter, QColor, QPolygon, QBitmap, QRegion


def pixel(p,x,y,w,h,color):
    p.fillRect(round(x),round(y),w,h,QColor(color))


def shape(p,points,color):
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    p.drawPolygon(QPolygon([QPoint(round(x),round(y)) for x,y in points]))


def image(w,h):
    img=QImage(w,h,QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    return img


def celestial_progress(position,night=False):
    # Sun: 06:00..18:00; moon: 18:00..06:00. Both have continuous arcs.
    start=.75 if night else .25
    return min(1,((position-start)%1)/.5)


class Environment:
    def __init__(self,background):
        # Clip birds/clouds behind the existing mountain/tree silhouettes.
        sky=QImage(background.size(),QImage.Format_Mono)
        water=QImage(background.size(),QImage.Format_Mono)
        # QBitmap regions include BLACK bits; QImage's default Mono table is
        # reversed, so define white=empty / black=visible explicitly.
        for mask in (sky,water):
            mask.setColor(0,QColor('white').rgba())
            mask.setColor(1,QColor('black').rgba())
        sky.fill(0); water.fill(0)
        for y in range(background.height()):
            for x in range(background.width()):
                c=background.pixelColor(x,y)
                if y<37 and c.red()>145 and c.green()>105 and c.red()>c.green()*1.06:
                    sky.setPixel(x,y,1)
                if 79<y<142 and 68<x<221 and c.red()<c.green()*.97 and c.blue()>75:
                    water.setPixel(x,y,1)
        self.sky_clip=QRegion(QBitmap.fromImage(sky))
        self.water_clip=QRegion(QBitmap.fromImage(water))
        self.cloud=self.make_cloud()
        self.clouds=[]
        for n in range(8):
            cloud=self.cloud.copy();p=QPainter(cloud)
            p.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            p.fillRect(cloud.rect(),QColor(21,34,64,round(n/7*200)))
            p.end();self.clouds.append(cloud)
        self.clouds=tuple(self.clouds)
        self.ferns=tuple(self.make_fern(frame) for frame in (-1,0,1,0))
        self.boughs=tuple(self.make_bough(frame) for frame in (-1,0,1,0))

    @staticmethod
    def make_cloud():
        img=image(46,9);p=QPainter(img)
        shape(p,[(0,7),(6,5),(14,5),(18,2),(24,2),(27,0),(32,0),(35,3),
                 (41,3),(46,6),(39,8),(12,8)],'#d8a399')
        shape(p,[(7,5),(17,4),(22,2),(29,2),(32,1),(35,4),(41,4),
                 (44,6),(34,6),(25,5),(17,6)],'#f4c49d')
        pixel(p,21,2,6,1,'#ffdbac');pixel(p,31,3,4,1,'#ffdbac')
        p.end();return img

    @staticmethod
    def make_fern(sway):
        img=image(30,28);p=QPainter(img)
        # Fixed root, flexible top. Stepped fronds alternate around the stem.
        for y in range(7,28):
            x=14+round(sway*(28-y)/12)
            pixel(p,x,y,1,1,'#99a274' if y<19 else '#55664b')
        for side in (-1,1):
            for k in range(4):
                y=12+k*4; x=14+round(sway*(28-y)/12)
                tip=x+side*(6-k)
                shape(p,[(x,y+2),(tip,y-3),(tip+side*3,y-4),
                         (tip+side*2,y),(x+side*2,y+3)],'#355a4e')
                pixel(p,tip,y-3,3 if side>0 else 2,1,'#89976a')
                pixel(p,x+side*3,y,2,1,'#5f8058')
        pixel(p,13+sway*2,6,2,3,'#b1ad70')
        p.end();return img

    @staticmethod
    def make_bough(sway):
        img=image(29,24);p=QPainter(img)
        for i in range(19):
            pixel(p,3+i,2+i//2,1,1,'#554f41')
        for x,y in ((6,5),(11,7),(15,10),(21,12)):
            xx=x+sway;yy=y+abs(sway)
            shape(p,[(xx-2,yy),(xx+2,yy-1),(xx+5,yy+3),(xx+4,yy+7),
                     (xx+2,yy+5),(xx-2,yy+4)],'#31554e')
            pixel(p,xx+1,yy,3,1,'#9c9c66')
            pixel(p,xx+2,yy+2,2,2,'#64825a')
        p.end();return img

    def sky(self,p,f,night=1,position=0):
        p.save();p.setClipRegion(self.sky_clip)
        # Slow drift, with the wrap happening beyond the visible sky.
        for x,y in ((round(98+(f*.7)%186),11),(round(214-(f*.35)%210),25)):
            p.drawImage(x,y,self.clouds[0])
            p.setOpacity(night);p.drawImage(x,y,self.clouds[-1]);p.setOpacity(1)
        x=round(-18+((f+36)%75)*4)
        for i in range(3 if night<.55 else 0):
            xx=x-i*9; yy=19+round(3*math.sin(f*.28))+i*3
            flap=int(f*5+i)%4
            pixel(p,xx,yy,2,1,'#465b6e')
            for side in (-1,1):
                for k in range(1,4):
                    wing_y=yy-(k//2+1) if flap==0 else yy+k//2 if flap==2 else yy
                    pixel(p,xx+side*k,wing_y,1,1,'#556777')
        # Rare, gentle meteor. Stars appear gradually during twilight.
        p.setOpacity(max(0,min(1,(night-.22)/.78)))
        stars=((107,14),(125,6),(139,25),(151,10),(166,22),(181,6),(196,17),
               (215,8),(232,29),(117,32),(158,31),(205,30),(223,20))
        for i,(xx,yy) in enumerate(stars):
            pulse=math.sin(f*1.1+i*1.7)
            pixel(p,xx,yy,1,1,'#dfdbbe' if pulse<.5 else '#ffedc6')
            if pulse>.92 and i%3==0:
                pixel(p,xx-1,yy,3,1,'#aaafbd');pixel(p,xx,yy-1,1,3,'#aaafbd')
                pixel(p,xx,yy,1,1,'#fff6ce')
        if night>.25:
            moon_progress=celestial_progress(position,True)
            xx=round(108+125*min(1,moon_progress));yy=round(33-26*math.sin(min(1,moon_progress)*math.pi))
            p.setOpacity(min(1,night*1.2))
            shape(p,[(xx-2,yy-5),(xx+2,yy-5),(xx+5,yy-2),(xx+5,yy+2),
                     (xx+2,yy+5),(xx-2,yy+5),(xx-4,yy+2),(xx-4,yy-2)],'#d6e1d1')
            shape(p,[(xx+1,yy-5),(xx+4,yy-2),(xx+3,yy+2),(xx,yy+3),
                     (xx-2,yy+2),(xx-2,yy-1)],'#889db3')
            pixel(p,xx-2,yy-3,2,2,'#f0edcf')
        elif .25<position<.75:
            progress=celestial_progress(position)
            xx=round(110+120*progress);yy=round(32-24*math.sin(progress*math.pi))
            p.setOpacity(.7)
            shape(p,[(xx-3,yy-4),(xx+3,yy-4),(xx+5,yy-1),(xx+5,yy+2),
                     (xx+2,yy+5),(xx-2,yy+5),(xx-5,yy+2),(xx-5,yy-1)],'#ffd9a3')
            pixel(p,xx-2,yy-3,4,4,'#fff0c1')
        p.setOpacity(1)
        meteor=(f-8)%83
        if night>.65 and meteor<1.3:
            xx=round(147+meteor*41);yy=round(6+meteor*18)
            for i,color in enumerate(('#fff1c3','#edd49f','#c7a393','#a78491')):
                pixel(p,xx-i*3,yy-i,3,1,color)
            pixel(p,xx,yy-1,1,3,'#fff9dc')
        p.restore()

    def reflections(self,p,f,night,position):
        if night<.25:return
        progress=celestial_progress(position,True)
        xx=round(108+125*progress)
        p.save();p.setClipRegion(self.water_clip);p.setOpacity(.48*night)
        for i in range(13):
            yy=76+i*4;w=2+i//2
            offset=round(2*math.sin(f*1.4+i*1.8))
            pixel(p,xx-w//2+offset,yy,w,1,'#bac9c0' if i<5 else '#779daf')
        p.restore()

    def events(self,p,f,night):
        if night<.28:
            # Day: butterflies visit the two flowering banks with slow wingbeats.
            for i,(x,y) in enumerate(((34,105),(233,103))):
                if (f+i*11)%37>13:continue
                xx=x+round(5*math.sin(f*.8+i));yy=y+round(3*math.cos(f*.6+i))
                wing=1 if int(f*3)%2 else 2
                pixel(p,xx-wing-1,yy-1,wing,2,'#deb986' if i==0 else '#bcabd4')
                pixel(p,xx+1,yy-1,wing,2,'#f4d9a2' if i==0 else '#dcd2dd')
                pixel(p,xx,yy,1,2,'#6b625c')
        elif night>.75:
            # Night: a sleepy owl rests on a fixed branch; no alarming effects.
            xx,yy=68,72
            shape(p,[(xx-3,yy-4),(xx-2,yy-6),(xx,yy-4),(xx+2,yy-6),
                     (xx+4,yy-3),(xx+3,yy+3),(xx-2,yy+3),(xx-4,yy-1)],'#9a8069')
            pixel(p,xx-2,yy-3,2,2,'#e1c4a0');pixel(p,xx+1,yy-3,2,2,'#e1c4a0')
            blink=int(f*2)%23==22
            for eye in (-1,2):pixel(p,xx+eye,yy-2,1,1,'#654b42' if blink else '#313b4c')
            pixel(p,xx,yy,1,1,'#dbac74')
            pixel(p,xx-2,yy+3,5,1,'#66513c')

    def water(self,p,f):
        p.save();p.setClipRegion(self.water_clip)
        p.setOpacity(.38)
        for i in range(4):
            x=round(76+((f*(3+i*.5)+i*38)%139))
            y=92+i*12+round(2*math.sin(f*.5+i))
            # A quiet, flattened silhouette under the surface, with a tail beat.
            shape(p,[(x-6,y),(x-3,y-2),(x+3,y-1),(x+5,y),
                     (x+2,y+2),(x-3,y+1)],'#193f51')
            tail=round(math.sin(f*5+i))
            shape(p,[(x-5,y),(x-9,y-2+tail),(x-9,y+2+tail)],'#214b5c')
        p.restore()

    def foreground(self,p,f):
        phase=int(f*1.6)%4
        p.drawImage(14,116,self.ferns[phase])
        p.drawImage(230,115,self.ferns[(phase+1)%4])
        p.drawImage(42,26,self.boughs[phase])
