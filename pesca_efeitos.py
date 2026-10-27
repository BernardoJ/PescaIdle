"""Emitted pixel light and cosmetic animation, independent of fishing RNG."""
import math
from PySide6.QtCore import Qt,QPoint
from PySide6.QtGui import QColor,QPolygon,QPen


def storm_window(seconds):
    block=int(seconds//31);code=(block*1103515245+12345)&0x7fffffff
    start=12+code%10;length=4+(code//31)%4
    return start<=seconds%31<start+length


def extra(p,id_,f,dy,behind,hand):
    def rect(x,y,w,h,c):p.fillRect(round(x),round(y),w,h,QColor(c))
    def poly(points,c):
        p.setPen(Qt.NoPen);p.setBrush(QColor(c));p.drawPolygon(QPolygon([QPoint(round(x),round(y)) for x,y in points]))
    def line(a,b,c,width=1):p.setPen(QPen(QColor(c),width));p.drawLine(QPoint(round(a[0]),round(a[1])),QPoint(round(b[0]),round(b[1])))
    def glow(x,y,rx,ry,color):
        for add,alpha in ((5,12),(3,22),(1,35)):
            c=QColor(color);c.setAlpha(alpha);p.setPen(Qt.NoPen);p.setBrush(c)
            p.drawEllipse(round(x-rx-add),round(y-ry-add),2*(rx+add)+1,2*(ry+add)+1)
    x,y=119,88+dy;hx,hy=hand or (135,94+dy)
    xx=141+round(3*math.sin(f*.8));yy=75+dy+round(2*math.cos(f*.8))
    if id_=='sabre_energia' and behind:
        for width,alpha in ((11,16),(9,22),(7,35)):
            line((138,88+dy),(148,69+dy),QColor(101,224,255,alpha),width)
    elif id_=='broche_lunar' and behind:glow(xx,yy,6,7,'#d8ecff')
    elif id_=='chama_yokai' and behind:glow(xx,yy-2,7,10,'#b779ed')
    elif id_=='cajado_tempestade' and storm_window(f):
        if behind:
            for i in range(4):
                cx=93+i*27;cy=18+(i%2)*4
                poly([(cx-16,cy+6),(cx-11,cy),(cx-2,cy),(cx+2,cy-5),(cx+12,cy-3),(cx+17,cy+3),(cx+21,cy+7)],'#445978')
                line((cx-8,cy+1),(cx+10,cy+1),'#7b91ac',2)
        else:
            for i in range(30):
                rx=85+(i*23+int(f*8))%135;ry=35+(i*13+int(f*27))%84
                line((rx,ry),(rx-2,ry+4),QColor(173,203,233,110))
            glow(148,68+dy,4,4,'#75c9fa')
    elif id_=='teia_aracnidea' and not behind:
        anchors=((213,42,26),(171,30,17),(232,94,19))
        for cx,cy,r in anchors:
            points=[(cx+round(r*math.cos(i*math.tau/6)),cy+round(r*math.sin(i*math.tau/6))) for i in range(6)]
            for point in points:line((cx,cy),point,QColor(209,239,244,155))
            for radius in (.33,.66,1):
                inner=[(cx+round((xx-cx)*radius),cy+round((yy-cy)*radius)) for xx,yy in points]
                for a,b in zip(inner,inner[1:]+inner[:1]):line(a,b,QColor(204,235,240,140))
        dot=round((math.sin(f*.8)+1)*9)
        rect(211,46+dot,2,2,'#f0fcff')
    elif id_=='orbe_dragon':
        if behind:glow(xx,yy,6,6,'#ffb44b')
        else:
            # Winding body with independent orbit and head direction.
            cx=119+round(32*math.cos(f*.55));cy=58+dy+round(15*math.sin(f*.55))
            body=[(cx-i*2,cy+round(3*math.sin(f*3-i*.55))) for i in range(15)]
            for a,b in zip(body,body[1:]):line(a,b,'#244f35',5);line(a,b,'#51bd64',3)
            for i in range(1,13,3):rect(body[i][0],body[i][1]-2,1,1,'#f0c775')
            poly([(cx-4,cy-3),(cx+3,cy-4),(cx+7,cy-1),(cx+6,cy+3),(cx-2,cy+3)],'#73d778')
            rect(cx+4,cy-2,1,1,'#202c3a');rect(cx+5,cy+1,3,1,'#eecb83')
            line((cx,cy-3),(cx-2,cy-7),'#ebd6ac');line((cx+3,cy-4),(cx+3,cy-8),'#ebd6ac')
            line((cx+7,cy+1),(cx+11,cy-1),'#f1ddb0');line((cx+6,cy+2),(cx+11,cy+4),'#f1ddb0')
            for i in (4,9):
                bx,by=body[i];line((bx,by),(bx-1,by+5),'#80dc7f');line((bx-1,by+5),(bx+2,by+5),'#f3d392')
    elif id_=='estrelas_orbitais':
        glow(x,y,22,25,'#657cff') if behind else None
        p.setBrush(Qt.NoBrush)
        for axis in (-1,1):
            points=[(x+round(26*math.cos(i*.2+f*.25)),y+round(17*math.sin(i*.2+f*.25)+axis*8*math.cos(i*.2+f*.25))) for i in range(33)]
            for i,(a,b) in enumerate(zip(points,points[1:])):
                if (a[1]<y)==behind:line(a,b,'#6889ca' if i%3 else '#c2ddff')
        for i in range(7):
            angle=f*.5+i*math.tau/7;sx=x+round(26*math.cos(angle));sy=y+round(25*math.sin(angle))
            if (sy<y)==behind:
                glow(sx,sy,1,1,'#a1b9ff');rect(sx-1,sy,3,1,'#fff7ce');rect(sx,sy-1,1,3,'#cce7ff')
    elif id_=='enciclopedia_viva':
        bx=148+round(3*math.sin(f*.8));by=77+dy+round(2*math.cos(f*1.2))
        if behind:glow(bx,by,9,7,'#c1fff0')
        else:
            poly([(bx-10,by-7),(bx-2,by-6),(bx,by-4),(bx+3,by-6),(bx+11,by-7),(bx+11,by+6),(bx+2,by+7),(bx,by+5),(bx-3,by+7),(bx-10,by+6)],'#446874')
            poly([(bx-8,by-5),(bx-2,by-4),(bx,by-2),(bx,by+4),(bx-3,by+5),(bx-8,by+3)],'#eaffd5')
            poly([(bx+1,by-2),(bx+3,by-4),(bx+9,by-5),(bx+9,by+3),(bx+2,by+5)],'#fff4c9')
            for i in range(3):line((bx-7,by-2+i*2),(bx-3,by-1+i*2),'#6ead99');line((bx+3,by-1+i*2),(bx+7,by-2+i*2),'#b7ae72')
            rect(bx,by-2,1,6,'#86c7b5')
            for i in range(4):rect(bx-12+i*7,by-10-(int(f*6)+i*3)%8,1,2,'#d2fff0')
