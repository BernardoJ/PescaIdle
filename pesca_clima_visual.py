"""Original pixel weather, masked by region and independent of gameplay RNG."""
import math
from functools import lru_cache
from PySide6.QtCore import Qt,QPoint
from PySide6.QtGui import QColor,QImage,QPainter,QPolygon,QPen


@lru_cache(maxsize=5)
def weather_image(weather):
    image=QImage(32,32,QImage.Format_ARGB32_Premultiplied);image.fill(Qt.transparent)
    p=QPainter(image);p.setRenderHint(QPainter.Antialiasing,False)
    def rect(x,y,w,h,color):p.fillRect(x,y,w,h,QColor(color))
    if weather in ('sol_forte','ameno'):
        for x,y,w,h in [(14,2,3,4),(14,23,3,4),(3,13,4,3),(24,13,4,3),(5,5,3,3),(23,5,3,3),(5,23,3,3),(23,23,3,3)]:rect(x,y,w,h,'#e7b952')
        rect(9,8,13,15,'#d4933c');rect(7,10,17,11,'#f4c762');rect(10,10,11,10,'#ffe9a3')
    if weather in ('chuva','neve','ventania','ameno'):
        y=6 if weather!='ameno' else 17
        rect(6,y+5,21,9,'#4d667d');rect(10,y+1,12,14,'#86a0ae');rect(4,y+7,24,6,'#9fb7bf');rect(8,y+5,18,6,'#cfddd8')
        if weather=='chuva':
            for x in (8,15,22):rect(x,22,2,6,'#78b8e5');rect(x-1,25,1,3,'#b0dcf3')
        elif weather=='neve':
            for x,y in ((8,24),(17,26),(25,23)):
                rect(x-2,y,5,1,'#d5f0ff');rect(x,y-2,1,5,'#f3fbff')
        elif weather=='ventania':
            rect(3,22,22,2,'#c1e3db');rect(9,26,20,2,'#82bdb9');rect(24,20,3,3,'#e4f2dd')
    p.end();return image


class WeatherEffects:
    @staticmethod
    def background(p,environment,f,weather,light):
        if weather in ('ameno','legado'):return
        p.save();p.setClipRegion(environment.sky_clip)
        tint={'chuva':QColor(28,50,79,64),'sol_forte':QColor(255,189,80,round(28*(1-light.night)+7)),
              'neve':QColor(139,177,205,42),'ventania':QColor(101,127,141,28)}[weather]
        p.fillRect(0,0,256,144,tint)
        if weather in ('chuva','neve','ventania'):
            speed=5 if weather=='ventania' else 2
            for i in range(7):
                x=(i*47+int(f*speed))%325-35;y=10+(i*11)%42
                p.setOpacity(.85 if weather=='chuva' else .55)
                # Reuse the authored stepped cloud silhouette and bounded cache.
                p.drawImage(x,y,environment.clouds[6 if weather=='chuva' else 3 if weather=='neve' else 4])
            p.setOpacity(1)
        if weather=='sol_forte' and light.night<.3:
            for i in range(6):
                x=151+i*18;p.setPen(QPen(QColor(255,227,157,25),3));p.drawLine(x,0,x-26,64)
        p.restore()

    @staticmethod
    def foreground(p,environment,f,weather,light,map_id):
        if weather in ('ameno','legado'):return
        p.save()
        if weather=='chuva':
            p.setPen(QPen(QColor(173,207,232,125),1))
            for i in range(52):
                x=(i*41-int(f*17))%264;y=(i*29+int(f*62))%150-5
                if not (103<x<146 and 48<y<108):p.drawLine(x,y,x-2,y+5)
            p.save();p.setClipRegion(environment.water_clip)
            for i in range(25):
                x=(i*43+17)%256;y=76+(i*17)%64;phase=(int(f*7)+i)%5
                if phase<3:
                    p.setPen(QColor(159,198,211,145));p.drawLine(x-phase,y,x+phase,y)
                    if phase==2:p.drawPoint(x,y+1)
            p.restore()
        elif weather=='sol_forte':
            p.save();p.setClipRegion(environment.water_clip)
            p.fillRect(0,0,256,144,QColor(246,177,78,round(13*(1-light.night)+4)))
            if light.night<.4:
                for i in range(18):
                    x=(i*43+int(f*3))%256;y=76+(i*19)%63
                    c=QColor(255,232,153,round(75+35*math.sin(f+i)))
                    p.fillRect(x,y,4+(i%4),1,c)
                    if i%3==0:p.fillRect(x+2,y-1,1,3,c)
            p.restore()
        elif weather=='neve':
            if map_id=='mar_das_auroras':
                for i in range(38):
                    x=(i*43+int(5*math.sin(f*.7+i)))%256;y=(i*31+int(f*(6+i%4)))%150-3
                    if 103<x<146 and 48<y<108:continue
                    p.fillRect(x,y,2 if i%3 else 1,1,QColor(217,237,247,185))
                    if i%5==0:p.fillRect(x,y-1,1,3,QColor(235,248,255,135))
            else:
                p.save();p.setClipRegion(environment.water_clip)
                for i in range(5):
                    x=(i*69+int(f*2))%330-50;y=75+i*9
                    p.fillRect(x,y,60,2,QColor(188,211,222,24));p.fillRect(x+10,y+2,44,2,QColor(188,211,222,16))
                p.restore()
        elif weather=='ventania':
            for i in range(11):
                x=(i*47+int(f*(55+i%3*10)))%310-25;y=15+(i*17)%101
                if 90<x<151 and 48<y<109:continue
                p.fillRect(x,y,9+i%9,1,QColor(191,215,208,95))
            p.save();p.setClipRegion(environment.water_clip)
            for i in range(16):
                x=(i*37+int(f*12))%280-10;y=76+(i*13)%62
                p.fillRect(x,y,10+i%7,1,QColor(180,213,210,125));p.fillRect(x+2,y+1,5,1,QColor(143,185,192,90))
            p.restore()
        p.restore()
