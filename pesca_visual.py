"""Original pixel art for Pesca Idle. All scene coordinates are logical pixels.

Static plates are local PNGs; sprites are constructed once in a bounded LRU.
No antialiasing, gradients, network, or floating point sprite transforms.
"""
import math
import json
import sys
from collections import OrderedDict
from pathlib import Path
from pesca_ambiente import Environment
from pesca_luz import Lighting
from pesca_equipamentos import rod, bait
from pesca_regional_visual import RegionalEnvironment
from pesca_especies_visual import species_image
from pesca_catalogo import INICIAL
from datetime import datetime
from pesca_efeitos import extra

from PySide6.QtCore import Qt, QPoint, QRect, QRectF
from PySide6.QtGui import QColor, QImage, QPainter, QPolygon, QPen

WIDTH, HEIGHT, SCALE = 256, 144, 2
BOAT_X, DECK_Y = 82, 105
BOAT_Y = 96
CHARACTER_X, CHARACTER_Y = 105, 69
BENCH_Y = CHARACTER_Y + 34  # Directly below the lowest rear-thigh pixel.
HAND_X, HAND_Y = CHARACTER_X + 30, CHARACTER_Y + 25
HEADBAND_X, HEADBAND_Y = 14, 22
# Attachment pixels in each cropped atlas sprite, rather than its bounding box.
# Brims/headbands share the hairline; enclosing helmets use their forehead seam.
HAT_ANCHORS = {
    'chapeu_palha': (12, 10), 'chapeu_bone': (10, 10),
    'chapeu_gorro': (8, 14), 'chapeu_quepe': (11, 11),
    'chapeu_pirata': (12, 11), 'chapeu_cartola': (10, 13),
    'chapeu_coroa': (10, 13), 'chapeu_pikachu': (10, 16),
    'chapeu_ninja': (10, 7), 'chapeu_samurai': (11, 9),
    'chapeu_cowboy': (12, 11), 'chapeu_mago': (12, 18),
    'chapeu_astronauta': (11, 10), 'chapeu_folhas': (11, 11),
    'chapeu_marinheiro': (11, 12), 'chapeu_raposa': (11, 9),
    'chapeu_corais': (11, 14),
}
PET_X, PET_Y = 83, DECK_Y - 23
FLOAT_X, WATER_Y = 193, 111
INK = '#202b3f'
GOLD = '#e6b96b'
CREAM = '#ffe5af'
PALETTE = {
    'sky': ('#555678', '#676583', '#877a91', '#aa8d98', '#caa39c', '#e1b59c', '#f1cba5'),
    'water': ('#5d9291', '#4f898a', '#407f85', '#34747d', '#2b6574', '#285968', '#254c60'),
    'leaf': ('#233f47', '#28534e', '#3d6b55', '#60805b', '#91a16a', '#b7b47a'),
    'rock': ('#364954', '#58646a', '#81877f', '#a9a593', '#d1bba0'),
}


def resource_path(name):
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'assets' / name


def integer_viewport(device_ratio, scale=SCALE):
    """Choose whole physical pixels even at fractional Windows DPI scales."""
    physical_scale=max(1,math.floor(scale*device_ratio+.5))
    return QRectF(0,0,WIDTH*physical_scale/device_ratio,
                  HEIGHT*physical_scale/device_ratio),physical_scale


def rect(p, x, y, w, h, color):
    p.fillRect(int(x), int(y), int(w), int(h), QColor(color))


def poly(p, points, color):
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    p.drawPolygon(QPolygon([QPoint(int(x), int(y)) for x, y in points]))


def line(p, a, b, color, width=1):
    p.setPen(QPen(QColor(color), width, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))
    p.drawLine(QPoint(*map(int, a)), QPoint(*map(int, b)))


def blank(w=WIDTH, h=HEIGHT):
    img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    return img


def cluster(p, x, y, w, h, color):
    """Stepped foliage mass with large coherent pixel groups."""
    poly(p, [(x, y+h//3), (x+2, y+h//3), (x+2, y+2), (x+w//3, y+2),
             (x+w//3, y), (x+2*w//3, y), (x+2*w//3, y+2), (x+w-2, y+2),
             (x+w-2, y+h//3), (x+w, y+h//3), (x+w, y+2*h//3),
             (x+w-3, y+2*h//3), (x+w-3, y+h-1), (x+w//2, y+h-1),
             (x+w//2, y+h+1), (x+3, y+h+1), (x+3, y+2*h//3), (x, y+2*h//3)], color)


def tint(rgb, target, fraction):
    a,b=QColor(*rgb[:3]),QColor(target)
    return QColor(int(a.red()*(1-fraction)+b.red()*fraction),
                  int(a.green()*(1-fraction)+b.green()*fraction),
                  int(a.blue()*(1-fraction)+b.blue()*fraction))


def stamp(p, grade, palette, x, y, shade=False):
    for j,row in enumerate(grade):
        for i,c in enumerate(row):
            if c in palette:
                color=QColor(*palette[c])
                if shade:
                    above=j==0 or i>=len(grade[j-1]) or grade[j-1][i] not in palette
                    below=j==len(grade)-1 or i>=len(grade[j+1]) or grade[j+1][i] not in palette
                    if above and i>=len(row)//3:
                        color=tint(palette[c], '#ffe1a6', .25)
                    elif below or i<len(row)//3:
                        color=tint(palette[c], '#263a4c', .3)
                    if below and color.lightness()>80:
                        rect(p,x+i,y+j+1,1,1,'#273648')
                rect(p,x+i,y+j,1,1,color)


class SceneRenderer:
    CACHE_LIMIT=192

    def __init__(self, clothes, hats, flags, pets, floats, boat_colors):
        self.clothes,self.hats,self.flags,self.pets,self.floats=clothes,hats,flags,pets,floats
        self.boat_colors=boat_colors
        self.cache=OrderedDict()
        self.background=QImage(str(resource_path('enseada.png')))
        self.foreground=QImage(str(resource_path('margem.png')))
        self.boat_master=QImage(str(resource_path('barco.png')))
        self.character_master=QImage(str(resource_path('pescador.png')))
        self.cosmetics={}
        manifest=json.loads(resource_path('cosmeticos.json').read_text(encoding='utf-8'))
        for category,ids in manifest.items():
            atlas=QImage(str(resource_path(category+'.png')))
            if atlas.width()!=96 or atlas.height()!=32*((len(ids)+2)//3):
                raise RuntimeError(f'Atlas {category}.png ausente ou inválido.')
            for i,id_ in enumerate(ids):
                tile=atlas.copy((i%3)*32,(i//3)*32,32,32)
                xs,ys=[],[]
                for yy in range(32):
                    for xx in range(32):
                        if tile.pixelColor(xx,yy).alpha():
                            xs.append(xx); ys.append(yy)
                if not xs:
                    raise RuntimeError(f'Sprite {id_} vazio no atlas.')
                self.cosmetics[id_]=tile.copy(min(xs),min(ys),max(xs)-min(xs)+1,max(ys)-min(ys)+1)
        if self.background.size().width()!=WIDTH or self.background.height()!=HEIGHT:
            raise RuntimeError('Asset assets/enseada.png ausente ou inválido.')
        if self.foreground.width()!=WIDTH or self.foreground.height()!=HEIGHT:
            raise RuntimeError('Asset assets/margem.png ausente ou inválido.')
        if self.boat_master.size().width()!=84 or self.character_master.width()!=32:
            raise RuntimeError('Sprites barco.png / pescador.png ausentes ou inválidos.')
        self.environment=Environment(self.background)
        self.lighting=Lighting(self.background,self.foreground)
        self.map_cache=OrderedDict([(INICIAL,(self.background,self.foreground,self.environment,self.lighting))])
        self.map_manifest=json.loads(resource_path('mapas/manifesto.json').read_text(encoding='utf-8'))

    def select_map(self,map_id):
        if map_id not in self.map_cache:
            if map_id==INICIAL:
                background=QImage(str(resource_path('enseada.png')))
                foreground=QImage(str(resource_path('margem.png')))
                materials=None;environment=Environment(background)
            else:
                root=resource_path('mapas');background=QImage(str(root/(map_id+'.png')))
                foreground=QImage(str(root/(map_id+'-margem.png')))
                materials=QImage(str(root/(map_id+'-materiais.png')))
                if background.width()!=WIDTH or background.height()!=HEIGHT or materials.isNull():
                    raise RuntimeError('Cenário incompleto: '+map_id)
                environment=RegionalEnvironment(map_id,root,self.map_manifest[map_id])
            self.map_cache[map_id]=(background,foreground,environment,Lighting(background,foreground,materials))
            if len(self.map_cache)>2:self.map_cache.popitem(last=False)
        self.map_cache.move_to_end(map_id)
        self.background,self.foreground,self.environment,self.lighting=self.map_cache[map_id]

    def cached(self, key, builder):
        if key not in self.cache:
            self.cache[key]=builder()
            if len(self.cache)>self.CACHE_LIMIT:
                self.cache.popitem(last=False)
        self.cache.move_to_end(key)
        return self.cache[key]

    def boat(self, level):
        img=self.boat_master.copy()
        # Hue changes preserve the artist's original luminance / plank shading.
        if level:
            target=self.boat_colors[min(level,len(self.boat_colors)-1)]
            for yy in range(13,img.height()):
                for xx in range(img.width()):
                    c=img.pixelColor(xx,yy)
                    if c.alpha() and c.red()>c.blue()*1.25:
                        lum=(c.red()*.3+c.green()*.6+c.blue()*.1)/125
                        ramp=tint(target,'#253147',max(0,1-lum))
                        if lum>1:
                            ramp=tint(target,'#ffe0a0',min(.65,(lum-1)*.65))
                        img.setPixelColor(xx,yy,ramp)
        p=QPainter(img)
        if level>=6:
            rect(p,12,17,2,2,'#f4d48d')
            rect(p,69,16,2,2,'#f4d48d')
        if level>=9:
            poly(p,[(45,17),(47,19),(45,21),(43,19)],'#ffe4a0')
        p.end()
        return img

    def boat_front(self, level):
        rear=self.cached(('boat',level),lambda:self.boat(level))
        front=blank(84,28)
        for x in range(84):
            rail=13-round(11*((x-40)/44)**2) if x>=40 else 13-round(6*((40-x)/40)**2)
            for y in range(max(0,rail),28):
                front.setPixelColor(x,y,rear.pixelColor(x,y))
        return front

    def character(self, clothes, hat, pose):
        img=self.character_master.copy()
        outfit=self.clothes.get(clothes,self.clothes['roupa_vermelha'])
        pal=outfit['pal']
        target=pal.get('c',(196,89,69))
        if clothes!='roupa_vermelha':
            for yy in range(16,33):
                for xx in range(img.width()):
                    c=img.pixelColor(xx,yy)
                    if c.alpha() and c.red()>c.green()*1.7 and c.red()>c.blue()*1.3:
                        lum=c.red()/175
                        color=tint(target,'#252840',max(0,1-lum))
                        if lum>1:
                            color=tint(target,'#ffe0b0',min(.48,(lum-1)*.55))
                        if clothes=='roupa_listrada' and yy%3==0:
                            color=tint(pal.get('w',(231,219,184)),'#3d485a',.25)
                        img.setPixelColor(xx,yy,color)
        # Forward forearm is a separate rigid pixel piece, with a shoulder bridge.
        arm=img.copy(20,21,12,8)
        if pose in (1,2):
            for yy in range(21,29):
                for xx in range(20,32):
                    img.setPixelColor(xx,yy,QColor(Qt.transparent))
        p=QPainter(img)
        if pose in (1,2):
            lift=2 if pose==1 else 4
            p.drawImage(20,21-lift,arm)
            line(p,(20,23-lift),(19,24),'#df9b65',2)
        # Redrawn facial clusters restore expression at actual native resolution.
        rect(p,16,12,2,1,'#34283a')
        rect(p,16,13,1,1,'#fbebc5')
        rect(p,17,13,1,2,'#3a344a')
        rect(p,18,16,2,1,'#c58962')
        rect(p,19,15,1,1,'#ffe0a2')
        if pose==3:
            rect(p,16,12,2,2,'#dc9a68')
            rect(p,16,13,2,1,'#74504d')
        if pose==2:
            rect(p,18,17,2,1,'#fff1c7')
        for overlay in outfit.get('overlay',[]):
            stamp(p,overlay,pal,6,20,True)
        p.end()
        # A seated pose folds the shins into the cockpit, above its front rail.
        compact=blank(32,39)
        p=QPainter(compact)
        p.setRenderHint(QPainter.SmoothPixmapTransform,False)
        p.drawImage(0,0,img.copy(0,0,32,29))
        p.drawImage(QRect(0,29,32,10),img,QRect(0,29,32,15))
        # Both soles rest on the same interior floor rather than hanging in air.
        rect(p,24,36,6,2,'#6e422f')
        rect(p,24,38,7,1,'#af7b49')
        rect(p,25,37,4,1,'#c49660')
        p.end()
        # Headroom accommodates the tallest existing hats without clipping.
        img=blank(32,56)
        p=QPainter(img)
        p.drawImage(0,16,compact)
        if hat in self.cosmetics:
            sprite=self.cosmetics[hat]
            anchor_x,anchor_y=HAT_ANCHORS[hat]
            p.drawImage(HEADBAND_X-anchor_x,HEADBAND_Y-anchor_y,sprite)
            if hat=='chapeu_ninja':
                rect(p,17,28,2,1,'#ddc099')
                rect(p,18,28,1,1,'#fff0cb')
            elif hat in ('chapeu_raposa','chapeu_samurai'):
                # The dark interior lies behind the face; the top rim/ears/horns
                # remain foreground, instead of painting a flat plate over it.
                p.drawImage(13,26,compact.copy(13,10,8,9))
                line(p,(12,25),(20,25),'#965c43' if hat=='chapeu_raposa' else '#b4b6bb')
        p.end()
        return img


    def flag(self, id_, frame):
        img=blank(22,42)
        p=QPainter(img)
        line(p,(2,3),(2,40),'#4a4842',2)
        line(p,(2,2),(2,39),'#bb9567')
        rect(p,1,1,3,2,'#f0ce85')
        grade,pal=self.flags[id_]
        for j in range(12):
            row=grade[min(len(grade)-1,j*len(grade)//12)]
            for i in range(18):
                c=row[min(len(row)-1,i*len(row)//18)]
                if c in pal:
                    dy=round(math.sin(frame*math.pi/2-i*.35)) if i>1 else 0
                    fold=(i+frame*2)%9
                    color=tint(pal[c],'#2d4450',.27) if fold>5 or j==11 else tint(pal[c],'#ffe2af',.18) if fold<2 or j==0 else QColor(*pal[c])
                    rect(p,4+i,5+j+dy,1,1,color)
        p.end()
        return img

    def catalog_sprite(self, table, id_):
        img=blank(24,24)
        p=QPainter(img)
        if id_ in self.cosmetics:
            sprite=self.cosmetics[id_]
            p.drawImage((24-sprite.width())//2,24-sprite.height(),sprite)
        elif id_ in table:
            grade,pal=table[id_]
            stamp(p,grade,pal,(24-len(grade[0]))//2,24-len(grade),True)
        p.end()
        return img

    @staticmethod
    def pet_frame(seconds):
        phase=seconds%7
        return 1 if 1.5<=phase<3 else 2 if 3<=phase<3.3 else 3 if 5<=phase<6 else 0

    def pet(self,id_,frame):
        """Four pixel poses per pet, with an unchanged floor/feet anchor."""
        sprite=self.cosmetics[id_]
        w,h=sprite.width(),sprite.height();x=(24-w)//2;y=24-h
        img=blank(24,24);p=QPainter(img)
        p.setRenderHint(QPainter.SmoothPixmapTransform,False)
        if frame==1:
            # A one-pixel exhale compresses the body; the two foot rows stay put.
            p.drawImage(QRect(x,y+1,w,h-3),sprite,QRect(0,0,w,h-2))
        else:
            p.drawImage(x,y,sprite.copy(0,0,w,h-2))
        p.drawImage(x,22,sprite.copy(0,h-2,w,2))
        if frame==2:
            # Close the dark eye clusters with their own nearby fur/skin colour.
            eyes={
                'boneco_pato':((10,3),),'boneco_gato':((10,5),),
                'boneco_caranguejo':((5,3),(10,3)),'boneco_pinguim':((9,5),),
                'boneco_agumon':((10,4),),'boneco_robot':((6,5),),
                'boneco_slime':((10,6),),'boneco_tartaruga':((12,5),),
                'boneco_axolote':((6,5),(10,5)),'boneco_baleia':((11,6),),
                'boneco_fantasma':((8,5),),'boneco_polvo':((9,4),),
                'boneco_capivara':((11,4),),'boneco_raposa':((11,5),)}
            for ex,ey in eyes[id_]:
                color=sprite.pixelColor(min(w-1,ex),min(h-1,ey+2))
                if not color.alpha():color=QColor('#8892a0')
                rect(p,x+ex,y+ey,2,1,color)
        if frame==3:
            # Ears/fins/claws and tails move independently of the planted body.
            if id_ in ('boneco_gato','boneco_raposa','boneco_pato','boneco_baleia','boneco_agumon'):
                tail=sprite.copy(0,h//2,4,h-h//2-2)
                p.setCompositionMode(QPainter.CompositionMode_Clear)
                p.fillRect(x,y+h//2,4,h-h//2-2,Qt.transparent)
                p.setCompositionMode(QPainter.CompositionMode_SourceOver)
                p.drawImage(x,y+h//2-1,tail)
            else:
                top=sprite.copy(2,0,w-4,4)
                p.setCompositionMode(QPainter.CompositionMode_Clear)
                p.fillRect(x+2,y,w-4,4,Qt.transparent)
                p.setCompositionMode(QPainter.CompositionMode_SourceOver)
                p.drawImage(x+3,y,top)
        p.end();return img

    def item_image(self, slot, id_):
        """Inventory thumbnails share the exact equipped art, built on demand."""
        if id_ in self.cosmetics:
            return self.cosmetics[id_]
        if slot=='roupa':
            return self.cached(('person',id_,'chapeu_nenhum',0),
                               lambda:self.character(id_,'chapeu_nenhum',0)).copy(4,32,23,13)
        if slot=='bandeira' and id_ in self.flags:
            return self.cached(('flag',id_,0),lambda:self.flag(id_,0)).copy(4,3,18,15)
        if slot=='acessorio' and id_!='acessorio_nenhum':
            img=blank(96,80)
            p=QPainter(img)
            p.translate(-181,-26) if id_=='teia_aracnidea' else p.translate(-80,-50)
            self.accessory_effects(p,id_,.3,0,True)
            self.accessories(p,id_,.3,0,True)
            self.accessories(p,id_,.3,0,False)
            self.accessory_effects(p,id_,.3,0,False)
            p.end()
            xs,ys=[],[]
            for y in range(img.height()):
                for x in range(img.width()):
                    if img.pixelColor(x,y).alpha():
                        xs.append(x); ys.append(y)
            return img.copy(min(xs),min(ys),max(xs)-min(xs)+1,max(ys)-min(ys)+1)
        return blank(16,16)

    def accessories(self,p,id_,f,dy,behind=False,hand=None):
        x,y=118,90+dy
        if id_=='acessorio_nenhum':
            return
        wings=id_ in ('asas_fenix','asas_boreais')
        if behind!=wings:
            return
        warm='#ffd153' if id_=='asas_fenix' else '#56ffcd'
        if wings:
            for side in (-1,1):
                yy=y+round(math.sin(f*1.3))
                pts=[(x,yy),(x+side*9,yy-11),(x+side*23,yy-23),(x+side*19,yy-9),
                     (x+side*14,yy-1),(x+side*7,yy+3)]
                poly(p,pts,'#e96338' if id_=='asas_fenix' else '#687fe0')
                for k in range(4):
                    line(p,(x+side*(4+k*3),yy-k*2),(x+side*(19-k*2),yy-18+k*4),warm)
            return
        if id_ in ('sabre_energia','cajado_tempestade','martelo_pesado'):
            hand=hand or (HAND_X,HAND_Y+dy)
            tip=(148,69+dy)
            if id_=='martelo_pesado':tip=(hand[0]+5,hand[1]-11)
            line(p,hand,tip,'#453e46',3)
            line(p,hand,tip,'#c09b68')
            if id_=='martelo_pesado':
                p.save();p.translate(tip[0]-148,tip[1]-(69+dy))
                poly(p,[(142,65+dy),(151,68+dy),(152,73+dy),(143,71+dy)],'#43495b')
                line(p,(143,66+dy),(150,68+dy),'#c2ced0',2)
                if math.sin(f*.9)>.85:
                    rect(p,146,67+dy,2,1,'#e0c694')
                    rect(p,147,66+dy,1,3,'#e0c694')
                p.restore()
            elif id_=='sabre_energia':
                line(p,(138,88+dy),tip,'#367d99',5)
                line(p,(138,88+dy),tip,'#85d9dc',3)
                line(p,(138,88+dy),tip,'#e9ffff')
            else:
                cluster(p,144,64+dy,7,7,'#659ac2')
                rect(p,146,65+dy,3,3,'#d9f7f0')
        elif id_=='teia_aracnidea':
            anchor=(213,42)
            for xx,yy in ((185,44),(196,67),(218,69)):
                line(p,anchor,(xx,yy),'#b7c6c5')
            for offset in (6,12,18):
                line(p,(213-offset,43),(207-offset//2,43+offset),'#91b0b3')
                line(p,(207-offset//2,43+offset),(216,43+offset),'#91b0b3')
        elif id_ in ('orbe_dragon','broche_lunar','chama_yokai'):
            xx=x+23+round(3*math.sin(f*.8)); yy=y-15+round(2*math.cos(f*.8))
            if id_=='broche_lunar':
                poly(p,[(xx,yy-5),(xx-4,yy-2),(xx-4,yy+3),(xx,yy+5),(xx+4,yy+3),
                        (xx,yy+2),(xx-1,yy-1)],'#f1faff')
                line(p,(xx-3,yy-2),(xx-3,yy+2),'#c2dbef')
            else:
                color='#b58aca' if id_=='chama_yokai' else '#e69e55'
                cluster(p,xx-4,yy-4,8,7,color)
                rect(p,xx-2,yy-3,3,2,'#ffe4a5')
                if id_=='orbe_dragon':
                    poly(p,[(xx,yy-3),(xx+1,yy-1),(xx+3,yy-1),(xx+1,yy+1),
                            (xx+2,yy+3),(xx,yy+2),(xx-2,yy+3),(xx-1,yy+1),
                            (xx-3,yy-1),(xx-1,yy-1)],'#b64029')
                if id_=='chama_yokai':
                    poly(p,[(xx-3,yy),(xx,yy-9),(xx+1,yy-3),(xx+4,yy)],color)
        elif id_=='estrelas_orbitais':
            for i in range(5):
                a=f*.35+i*math.tau/5
                xx=x+round(22*math.cos(a)); yy=y+round(23*math.sin(a))
                rect(p,xx-1,yy,3,1,'#f7d99b')
                rect(p,xx,yy-1,1,3,'#f7d99b')

    @staticmethod
    def lightning_active(seconds):
        phase=seconds%3.2
        return phase<.55 or .72<=phase<.92

    def accessory_effects(self,p,id_,f,dy,behind=False,hand=None):
        """Emissive pixel effects stay readable in daylight and after night tinting.

        Rear halos sit behind the actors; front arcs and impact sparks wrap around
        them. These phases never consume the fishing RNG or modify the save.
        """
        x,y=CHARACTER_X+14,CHARACTER_Y+19+dy
        hx,hy=hand or (HAND_X,HAND_Y+dy)
        extra(p,id_,f,dy,behind,hand)
        auras={
            'anel_verde_esmeralda':('#12683e','#42f579','#e2ffc0'),
            'aura_cyber':('#26506f','#51e7ff','#e1fcff'),
            'escudo_bolhas':('#356c92','#8be8ff','#f0ffff'),
        }
        if id_ in auras:
            dark,color,bright=auras[id_]
            pulse=round(math.sin(f*2.1))
            rx,ry=22+pulse,25+pulse
            points=[(x+round(rx*math.cos(i*math.tau/32)),
                     y+round(ry*math.sin(i*math.tau/32))) for i in range(33)]
            if behind:
                if id_=='escudo_bolhas':
                    poly(p,points,QColor(90,202,244,32))
                for i in range(32):
                    if id_=='aura_cyber' and i%4==3:
                        continue
                    line(p,points[i],points[i+1],dark,3)
                    line(p,points[i],points[i+1],color)
                    if (i-int(f*5))%8<2:
                        line(p,points[i],points[i+1],bright)
                for i in range(4):
                    angle=f*.55+i*math.tau/4
                    xx=x+round((rx+3)*math.cos(angle))
                    yy=y+round((ry+3)*math.sin(angle))
                    poly(p,[(xx,yy-2),(xx+2,yy),(xx,yy+2),(xx-2,yy)],dark)
                    rect(p,xx-1,yy,3,1,bright)
                    rect(p,xx,yy-1,1,3,color)
                if id_=='aura_cyber':
                    for side in (-1,1):
                        xx=x+side*(rx+4)
                        line(p,(xx,y-9),(xx,y+8),color)
                        line(p,(xx,y-9),(xx-side*4,y-9),bright)
                        rect(p,xx-1,y+7,3,3,bright)
            else:
                # Only the lower, foreground arc crosses the hull, not the face.
                for i in range(2,15):
                    if id_=='aura_cyber' and i%4==3:
                        continue
                    line(p,points[i],points[i+1],dark,3)
                    line(p,points[i],points[i+1],color)
                    if (i-int(f*5))%8<2:
                        line(p,points[i],points[i+1],bright)
                if id_=='anel_verde_esmeralda':
                    poly(p,[(hx,hy-3),(hx+3,hy),(hx,hy+3),(hx-3,hy)],dark)
                    rect(p,hx-2,hy-1,4,3,color)
                    rect(p,hx,hy-1,1,2,bright)
                    for i in range(3):
                        yy=y-10-(int(f*7)+i*8)%27
                        xx=x-18+i*17+round(2*math.sin(f+i))
                        rect(p,xx,yy,2,2,color)
                        rect(p,xx,yy-1,1,1,bright)
                elif id_=='aura_cyber':
                    for i in range(3):
                        xx=x-14+i*14
                        yy=y+19-(int(f*8)+i*7)%35
                        line(p,(xx,yy),(xx,yy+4),color)
                        rect(p,xx-1,yy,3,2,bright)
                else:
                    for i in range(3):
                        xx=x-17+i*16+round(2*math.sin(f+i))
                        yy=y+16-(int(f*5)+i*13)%45
                        p.setPen(QPen(QColor(color),1));p.setBrush(Qt.NoBrush)
                        p.drawEllipse(xx-2,yy-2,5,5)
                        rect(p,xx-1,yy-2,2,1,bright)
            return
        if id_=='martelo_pesado':
            active=self.lightning_active(f)
            end_x=176+((int(f//3.2)%3)-1)*4
            if behind and active:
                wobble=int(f*18)%2
                points=[(end_x-3,10),(end_x-8,26),(end_x,37),
                        (end_x-7,51),(end_x+2,64),(end_x-6,79),
                        (end_x+3,92),(end_x,113)]
                points=[(xx+wobble,yy) for xx,yy in points]
                for start,end in zip(points,points[1:]):
                    line(p,start,end,'#24456d',5)
                    line(p,start,end,'#5fcfff',3)
                    line(p,start,end,'#eeffff')
                for branch in (((end_x-7,51),(end_x-18,57),(end_x-14,70)),
                               ((end_x+2,64),(end_x+13,71),(end_x+9,83))):
                    for start,end in zip(branch,branch[1:]):
                        line(p,start,end,'#5fcfff',3)
                        line(p,start,end,'#eeffff')
            elif not behind:
                # The held hammer also has a permanent rune and a pulsing charge.
                p.save();p.translate(hx+5-148,hy-11-(69+dy))
                rect(p,146,67+dy,3,1,'#b8efff')
                rect(p,147,66+dy,1,3,'#efffff')
                if active:
                    line(p,(143,64+dy),(139,69+dy),'#83dfff')
                    line(p,(151,68+dy),(154,73+dy),'#efffff')
                p.restore()
                if active:
                    width=5+int((f%3.2)*10)
                    line(p,(end_x-width,115),(end_x+width,115),'#7fdcff')
                    for side in (-1,1):
                        line(p,(end_x+side*3,113),(end_x+side*8,107),'#eeffff')
                        rect(p,end_x+side*11,110,2,2,'#70cfff')
        elif id_=='chama_yokai' and not behind:
            xx=x+22+round(3*math.sin(f*.8));yy=y-13+round(2*math.cos(f*.8))
            poly(p,[(xx-5,yy+3),(xx-5,yy-2),(xx-2,yy-6),(xx,yy-11),
                    (xx+2,yy-5),(xx+5,yy-2),(xx+5,yy+3),(xx,yy+6)],'#633d98')
            poly(p,[(xx-3,yy+2),(xx-2,yy-4),(xx,yy-8),
                    (xx+1,yy-2),(xx+3,yy+2),(xx,yy+4)],'#db99ff')
            rect(p,xx-1,yy-2,2,5,'#fff0ff')
            for i in range(3):
                rect(p,xx-7+i*6,yy-9-(int(f*7)+i*4)%10,1,2,'#e5bdff')

    def render(self, game, map_id=None):
        map_id=map_id or game.estado['local_atual_id']
        self.select_map(map_id)
        f=game.fase
        dy=round(1.5*math.sin(f*1.4)+.5*math.sin(f*.65))
        result=getattr(game,'_last_result',None)
        observing=bool(result and result['categoria']=='especial')
        pose=1 if game.fisgando>0 else 2 if game.capturando>0 and not observing else 0
        sprite_pose=3 if pose==0 and int(f*3)%17==16 else pose
        breath=0  # The pelvis and boots stay anchored to the seat during idle.
        hand=(HAND_X,HAND_Y+dy+breath-(2 if pose==1 else 4 if pose==2 else 0))
        moment=getattr(game,'_preview_clock',None)
        if moment is None and hasattr(game,'_clock_snapshot'):
            moment=datetime.fromisoformat(game._clock_snapshot['local_iso'])
        lighting=self.lighting.at(moment)
        self.current_light=lighting
        img=lighting.background.copy()
        p=QPainter(img)
        self.environment.sky(p,f,lighting.night,lighting.position)
        self.environment.reflections(p,f,lighting.night,lighting.position)
        p.end()
        actors=blank()
        p=QPainter(actors)
        p.setRenderHint(QPainter.Antialiasing,False)
        self.environment.water(p,f)
        # Sparse traveling glints. Positions follow perspective, not a tiled grid.
        p.save();p.setClipRegion(self.environment.water_clip)
        for k in range(34):
            yy=72+(k*17)%66
            xx=(k*47+int(f*(2+(yy-70)//20)))%256
            if 80<xx<168 and 98<yy<122:
                continue
            color=('#92b4a7','#6b9e99','#51848b')[k%3]
            rect(p,xx,yy,2+(k*7)%9,1,color)
            if k%5==0:
                rect(p,xx+3,yy+2,3,1,'#386d79')
        p.restore()
        # Underwater hull reflection / displacement appears before the boat.
        sx=round(2*math.sin(f*.9));sy=round(dy*.5)
        poly(p,[(84+sx,118+sy),(100+sx,122+sy),(143+sx,123+sy),
                (160+sx,118+sy),(154+sx,126+sy),(110+sx,128+sy),(88+sx,122+sy)],'#284b58')
        for yy,w in ((120,63),(123,45),(127,29)):
            shift=round(2*math.sin(f*2+yy));stretch=round(2*math.sin(f*1.4+yy))
            rect(p,91+(63-w)//2+sx+shift,yy+sy,w+stretch,1,'#426c70')
        band=game.equipado('bandeira')
        if band in self.flags:
            p.drawImage(87,DECK_Y-38+dy,self.cached(('flag',band,int(f*4)%4),lambda:self.flag(band,int(f*4)%4)))
        p.drawImage(BOAT_X,BOAT_Y+dy,self.cached(('boat',game.estado['barco']),lambda:self.boat(game.estado['barco'])))
        # The seat and pelvis use the same anchor; fore-hull occludes the boots.
        poly(p,[(104,BENCH_Y+dy),(122,BENCH_Y+dy),(128,BENCH_Y+4+dy),
                (109,BENCH_Y+4+dy)],'#a87549')
        line(p,(104,BENCH_Y+dy),(123,BENCH_Y+dy),'#ebc084')
        rect(p,107,BENCH_Y+1+dy,16,2,'#705039')
        rect(p,107,BENCH_Y+3+dy,2,4,'#514132')
        rect(p,123,BENCH_Y+3+dy,2,4,'#514132')
        # Contact shadows touch thighs and soles; they never float independently.
        rect(p,108,BENCH_Y+dy,11,1,'#3c2e31')
        rect(p,120,CHARACTER_Y+39+dy,8,1,'#172831')
        rect(p,129,CHARACTER_Y+39+dy,8,1,'#172831')
        self.accessories(p,game.equipado('acessorio'),f,dy,True,hand)
        ch,hat=game.equipado('roupa'),game.equipado('chapeu')
        p.drawImage(CHARACTER_X,CHARACTER_Y-16+dy,self.cached(('person',ch,hat,sprite_pose),lambda:self.character(ch,hat,sprite_pose)))
        p.drawImage(BOAT_X,BOAT_Y+dy,self.cached(('front',game.estado['barco']),lambda:self.boat_front(game.estado['barco'])))
        # Coiled rope, fishing basket and a physical lantern on the bow.
        for xx,yy,w in ((144,103,8),(145,101,6),(146,100,4)):
            rect(p,xx,yy+dy,w,1,'#cfb589')
        rect(p,92,99+dy,8,5,'#796848')
        rect(p,93,98+dy,6,1,'#ceae77')
        for xx in (94,97):
            line(p,(xx,99+dy),(xx,103+dy),'#b89866')
        # Lantern flicker uses two pixel ramps, never soft bloom.
        rect(p,154,96+dy,7,8,INK)
        rect(p,156,94+dy,3,2,'#ab9a7d')
        rect(p,155,98+dy,5,4,'#bd864e')
        rect(p,156,98+dy,3,3,'#f4c87a')
        rect(p,157,98+dy,1,2,'#ffedba' if int(f*7)%3 else '#ffda94')
        rect(p,155,104+dy,6,1,'#e7bd76')
        # Mascots sit on the stern ledge, in front of the rail/post and basket.
        # Keep their shared foot anchor while letting the whole body remain visible.
        pet=game.equipado('boneco')
        if pet in self.pets:
            frame=self.pet_frame(f)
            rect(p,PET_X+6,DECK_Y+1+dy,12,1,'#423834')
            p.drawImage(PET_X,PET_Y+dy,self.cached(('pet',pet,frame),lambda:self.pet(pet,frame)))
        for k in range(6):
            yy=124+k*3; w=max(2,9-k)
            rect(p,157-w//2+round(math.sin(f*3+k)),yy,w,1,'#b7a17a' if k<3 else '#748d7c')
        # Waterline overlap is restricted to the lowest edge of the hull.
        for xx,w,yy in ((90,8,118),(104,18,124),(128,14,124),(151,7,117)):
            rect(p,xx,yy+dy,w,1,'#94b1a1')
            rect(p,xx+3,yy+1+dy,w-2,1,'#457f83')
        tip=(190,67+dy) if pose==0 else (174,53+dy) if pose==1 else (167,49+dy)
        rod(p,hand,tip,game.estado['vara'],f,pose)
        fy=FLOAT_X
        by=WATER_Y+round(math.sin(f*2))
        if game.fisgando>0:
            by+=round(2*abs(math.sin(f*17)))
        # A taut line during the strike, sagging angular line at rest.
        joint=(191,88) if pose==0 else (186,78)
        line(p,tip,joint,'#b4c2b6')
        line(p,joint,(fy,by-3),'#b4c2b6')
        for offset,w in ((3,14),(5,8)):
            rect(p,fy-w//2,by+offset,w,1,'#86aea1' if offset==3 else '#376976')
        float_id=game.equipado('boia')
        sprite=self.cached(('float',float_id),lambda:self.catalog_sprite(self.floats,float_id))
        p.drawImage(fy-12,by-21,sprite)
        bait(p,fy,by,f)
        if game.fisgando>0 or game.capturando>0:
            for i in range(7):
                a=i*math.pi/6
                d=4+(int(f*12)+i)%7
                xx=fy+round(math.cos(a)*d)
                yy=by-round(math.sin(a)*d*.7)
                rect(p,xx,yy,1,2,'#d0e2c5')
        if game.fisgando>0:
            rect(p,141,64+dy,2,7,'#ffe7a0')
            rect(p,141,73+dy,2,2,'#ffe7a0')
        result=getattr(game,'_last_result',None)
        if game.capturando>0 and result and result['categoria']=='peixe':
            t=1-game.capturando/1.2
            xx=193-round(t*43); yy=108-round(math.sin(t*math.pi)*31)
            p.drawImage(xx-12,yy-8,species_image(result['species_id']).scaled(24,16,Qt.IgnoreAspectRatio,Qt.FastTransformation))
        elif game.capturando>0 and result and result['categoria']=='especial':
            # Observations and samples stay at the surface, detached from the hook.
            p.drawImage(182,101,species_image(result['species_id']).scaled(64,42,Qt.IgnoreAspectRatio,Qt.FastTransformation))
            line(p,(205,137),(229,137),'#b7ddcd')
        self.accessories(p,game.equipado('acessorio'),f,dy,False,hand)
        p.end()
        self.lighting.actors(actors,lighting)
        p=QPainter(img)
        self.accessory_effects(p,game.equipado('acessorio'),f,dy,True,hand)
        p.drawImage(0,0,actors)
        self.accessory_effects(p,game.equipado('acessorio'),f,dy,False,hand)
        p.drawImage(0,0,lighting.foreground)
        foliage=blank();fp=QPainter(foliage)
        self.environment.foreground(fp,f)
        self.environment.events(fp,f,lighting.night)
        fp.end();self.lighting.actors(foliage,lighting);p.drawImage(0,0,foliage)
        if map_id==INICIAL:self.lighting.emissive(p,f,dy,lighting)
        else:self.environment.emissive(p,f,dy,lighting)
        # Animated flower tips match the foreground's warm/cool pixel ramps.
        for xx,yy in (((17,123),(244,119)) if map_id==INICIAL else ()):
            rect(p,xx+round(math.sin(f*.8+xx)),yy,1,1,'#e6c895')
        # Tiny moths and fireflies in the near bank, below the UI.
        for i,(xx,yy) in enumerate(((33,91),(73,68),(230,104)) if map_id==INICIAL else ()):
            if lighting.night>.6 and math.sin(f*1.2+i)>-.2:
                xx+=round(2*math.sin(f*.7+i)); yy+=round(2*math.cos(f+i))
                rect(p,xx,yy,1,1,'#f6d493')
                if math.sin(f*1.2+i)>.75:
                    rect(p,xx-1,yy,3,1,'#d6c88b')
        p.end()
        return img,dy
