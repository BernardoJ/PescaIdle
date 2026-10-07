"""Location-owned masks and pixel effects. No lake props on offshore maps."""
import math
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QColor, QBitmap, QRegion, QPen
from pesca_ambiente import Environment, pixel, shape


def region(path):
    source=QImage(str(path)); mask=QImage(source.size(),QImage.Format_Mono)
    mask.setColor(0,QColor('white').rgba());mask.setColor(1,QColor('black').rgba());mask.fill(0)
    for y in range(source.height()):
        for x in range(source.width()):
            c=source.pixelColor(x,y)
            if c.alpha()>128 and c.red()>128:mask.setPixel(x,y,1)
    return QRegion(QBitmap.fromImage(mask))


class RegionalEnvironment(Environment):
    def __init__(self,map_id,assets,manifest):
        self.map_id=map_id;self.manifest=manifest
        self.sky_clip=region(assets/(map_id+'-ceu.png'))
        self.water_clip=region(assets/(map_id+'-agua.png'))
        cloud=self.make_cloud(); self.clouds=[]
        for n in range(8):
            img=cloud.copy()
            from PySide6.QtGui import QPainter
            p=QPainter(img);p.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            p.fillRect(img.rect(),QColor(21,34,64,round(n/7*200)));p.end();self.clouds.append(img)

    def sky(self,p,f,night=1,position=0):
        super().sky(p,f,night,position)
        if self.map_id=='mar_das_auroras' and night>.55:
            p.save();p.setClipRegion(self.sky_clip)
            for i in range(55):
                x=30+i*4;y=18+round(8*math.sin(i*.14+f*.12))
                color=QColor(100,242,189,round((night-.5)*90))
                p.fillRect(x,y,3,14+round(5*math.sin(i*.27)),color)
                p.fillRect(x,y+5,2,5,QColor(168,143,246,round(night*45)))
            p.restore()

    def foreground(self,p,f):
        # Production masks already contain the distinct shore geometry.
        pass

    def events(self,p,f,night):
        if self.map_id in ('rio_das_vitorias','mangue_das_raizes') and night>.35:
            for i in range(8):
                if math.sin(f*.8+i)>.4:
                    pixel(p,18+(i*37)%226+round(math.sin(f+i)*3),68+(i*13)%55,1,1,'#deed95')
        if self.map_id=='fossa_das_lanternas':
            p.save();p.setClipRegion(self.water_clip)
            for i in range(9):
                x=45+(i*27+int(f*2))%210;y=88+(i*11)%48
                pixel(p,x,y,1,1,'#6adccf' if i%2 else '#a7b6fa')
            p.restore()

    def water(self,p,f):
        p.save();p.setClipRegion(self.water_clip)
        if self.map_id=='recife_das_cores':
            for i in range(8):
                x=30+(int(f*4)+i*28)%240;y=97+(i*7)%37
                shape(p,[(x-3,y),(x,y-2),(x+4,y),(x,y+2)],'#51aeb6' if i%2 else '#d4b770')
        elif self.map_id in ('mar_dos_ventos','mar_das_auroras'):
            for i in range(8):
                x=(i*43+int(f*4))%256;y=75+(i*13)%62
                pixel(p,x,y,10+i%7,1,'#a3c7ca');pixel(p,x+3,y-1,5,1,'#d1dad5')
        else:
            for i in range(6):
                x=(i*47+int(f*3))%256;y=76+(i*11)%57
                pixel(p,x,y,7+i%5,1,'#91b4b1')
        p.restore()

    def emissive(self,p,f,dy,frame):
        # Common boat lantern plus explicitly authored shore/observatory lamps.
        if frame.night<.12:return
        for x,y in [*self.manifest['lights'],(157,100+dy)]:
            p.fillRect(x-3,y-2,7,5,QColor(244,194,109,round(frame.night*35)))
            pixel(p,x,y,2,2,'#ffe4a3')
