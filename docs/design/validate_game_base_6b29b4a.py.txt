"""Integration/visual QA. All state is in TemporaryDirectory, including autosave.

Run: .venv/Scripts/python tools/validate_game.py
The optional baseline is obtained from the immutable original Git revision.
"""
import copy
import json
import os
import random
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from PySide6.QtCore import Qt, QPoint, QPointF, QTimer, QRect
from PySide6.QtGui import QImage, QPainter, QColor, QFont, QMouseEvent
from PySide6.QtWidgets import QApplication, QMenu
import pesca_idle as game
from pesca_ui import configure_app, InfoDialog
import pesca_luz
from pesca_equipamentos import rod, bait

app=QApplication([])
configure_app(app)
out=Path(os.environ.get('PESCA_IDLE_QA_DIR',str(root/'docs'/'visual')))
out.mkdir(parents=True,exist_ok=True)
checks=[]


def check(name,condition):
    assert condition,name
    checks.append(name)


def capture(widget,name):
    widget.setAttribute(Qt.WA_DontShowOnScreen,True)
    widget.show()
    app.processEvents()
    check('PNG '+name,widget.grab().save(str(out/name)))


with tempfile.TemporaryDirectory(prefix='pesca-qa-') as tmp:
    game.SAVE_PATH=Path(tmp)/'save.json'
    old=copy.deepcopy(game.ESTADO_PADRAO)
    old.update(moedas=12345.75,vara=3,barco=4,total_pescados=12,
               inventario={'Lambari':12},ultimo_salvo=time.time())
    old['equipados'].pop('acessorio')
    old['cosmeticos'].append('chapeu_bone')
    game.SAVE_PATH.write_text(json.dumps(old),encoding='utf-8')
    window=game.JogoPesca()
    window.relogio.stop()
    window.timer_save.stop()
    window.fase=2.0
    # Deterministic screenshots; production still reads the local device clock.
    window._preview_clock=datetime(2026,10,6,18)
    ratio=window.devicePixelRatioF()
    check('Integer physical scene scale',abs(window.scene_rect.width()*ratio/game.ART_W-window.physical_scale)<.0001)
    # Environmental layers must visibly animate without consuming gameplay RNG.
    def ambient_layer(name,phase):
        img=QImage(game.ART_W,game.ART_H,QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        p=QPainter(img)
        getattr(window._render.environment,name)(p,phase)
        p.end()
        return img
    for layer in ('sky','water','foreground'):
        check('Animated environment: '+layer,ambient_layer(layer,0)!=ambient_layer(layer,1.4))
    check('Sky animation behind tree silhouettes',window._render.environment.sky_clip.contains(QPoint(160,13))
          and not window._render.environment.sky_clip.contains(QPoint(12,20)))
    check('Underwater animation excludes banks',window._render.environment.water_clip.contains(QPoint(120,112))
          and not window._render.environment.water_clip.contains(QPoint(12,20)))
    meteor=ambient_layer('sky',8.4)
    check('Meteor visible in night sky',meteor.pixelColor(163,12)==QColor('#fff9dc'))
    renderer=window._render
    lighting=renderer.lighting
    for hour,label in ((0,'NOITE'),(6,'AMANHECER'),(9,'DIA'),(12,'MEIO-DIA'),(18,'ENTARDECER'),(22,'NOITE')):
        moment=datetime(2026,10,6,hour)
        with patch.object(pesca_luz,'datetime') as clock:
            clock.now.return_value=moment
            check('Local device clock '+label,lighting.at().label==label)
            check('Clock position '+str(hour),lighting.at().position==hour/24)
    check('Distinct noon palette',lighting.at(datetime(2026,10,6,12)).background!=lighting.at(datetime(2026,10,6,9)).background)
    check('Bounded light plates',len(lighting.frames)==pesca_luz.FRAME_COUNT==96)
    first=lighting.at(datetime(2026,10,6,5,15,0))
    next_=lighting.at(datetime(2026,10,6,5,15,30))
    check('Clock interpolates cached colours',next_.position>first.position and next_.night!=first.night)
    for hour in (0,6,12,18):
        light=lighting.at(datetime(2026,10,6,hour,17,28))
        check('Foreground alpha preserved '+str(hour),all(abs(light.foreground.pixelColor(x,y).alpha()-renderer.foreground.pixelColor(x,y).alpha())<=1
              for x,y in ((0,0),(12,20),(10,142),(245,132),(125,80))))
    window.fase=0;fixed,_=window.desenhar_cena();fixed_light=renderer.current_light
    window.fase=123;window.desenhar_cena()
    check('Animation phase cannot change time of day',renderer.current_light.position==fixed_light.position)
    window._preview_clock=None;state_before=copy.deepcopy(window.estado)
    with patch.object(pesca_luz,'datetime') as clock:
        clock.now.return_value=datetime(2026,10,6,12)
        window.desenhar_cena();day_label=renderer.current_light.label
        clock.now.return_value=datetime(2026,10,6,22)
        window.desenhar_cena();night_label=renderer.current_light.label
    check('Running renderer follows device clock changes',day_label=='MEIO-DIA' and night_label=='NOITE')
    check('Civil clock leaves saved progress unchanged',window.estado==state_before)
    window._preview_clock=datetime(2026,10,6,18)
    def event_layer(phase,night,sky=False):
        img=QImage(256,144,QImage.Format_ARGB32_Premultiplied);img.fill(Qt.transparent)
        p=QPainter(img)
        if sky:renderer.environment.sky(p,phase,night,0 if night else .5)
        else:renderer.environment.events(p,phase,night)
        p.end();return img
    day_events=event_layer(0,0);night_events=event_layer(0,1)
    check('Day butterflies',day_events.pixelColor(34,108).alpha()>0)
    check('Night owl exclusive',night_events.pixelColor(68,72).alpha()>0 and day_events.pixelColor(68,72).alpha()==0)
    check('Butterflies absent at night',night_events.pixelColor(34,108).alpha()==0)
    check('Meteor absent by day',event_layer(8.4,0,True).pixelColor(163,12)!=QColor('#fff9dc'))
    for pet_id in renderer.pets:
        if pet_id not in renderer.cosmetics:continue
        poses=[renderer.pet(pet_id,i) for i in range(4)]
        check('Pet breathing '+pet_id,poses[0]!=poses[1])
        check('Pet blinking '+pet_id,poses[0]!=poses[2])
        check('Pet tail/fin/ear '+pet_id,poses[0]!=poses[3])
        check('Pet planted feet '+pet_id,all(img.copy(0,22,24,2)==poses[0].copy(0,22,24,2) for img in poses))
    for flag_id in renderer.flags:
        check('Animated cloth '+flag_id,renderer.flag(flag_id,0)!=renderer.flag(flag_id,1))
    pet_sheet=QImage(576,112*len(renderer.pets),QImage.Format_ARGB32)
    pet_sheet.fill(QColor('#1c2b3b'));p=QPainter(pet_sheet);p.setFont(QFont('Segoe UI',9))
    for row,pet_id in enumerate(renderer.pets):
        for frame in range(4):
            p.drawImage(QRect(frame*144,row*112,96,96),renderer.pet(pet_id,frame))
        p.setPen(QColor('#ffe3ac'));p.drawText(8,row*112+109,game.CAT[pet_id][2])
    p.end();pet_sheet.save(str(out/'mascotes-quadros.png'))
    rods=[]
    for level in range(11):
        img=QImage(256,144,QImage.Format_ARGB32_Premultiplied);img.fill(Qt.transparent)
        p=QPainter(img);rod(p,(135,94),(190,67),level,0,0);p.end();rods.append(img)
    check('Eleven visibly distinct rod tiers',all(a!=b for i,a in enumerate(rods) for b in rods[i+1:]))
    def bait_image(phase):
        img=QImage(256,144,QImage.Format_ARGB32_Premultiplied);img.fill(Qt.transparent)
        p=QPainter(img);bait(p,193,111,phase);p.end();return img
    check('Animated underwater bait',bait_image(0)!=bait_image(1))
    window.fase=2
    rng_state=random.getstate()
    window.desenhar_cena()
    check('Renderer preserves gameplay RNG',random.getstate()==rng_state)
    check('Legacy save inventory/economy',window.estado['inventario']=={'Lambari':12}
          and window.estado['moedas']==12345.75 and window.estado['vara']==3)
    check('Legacy default slot migration',window.estado['equipados']['acessorio']=='acessorio_nenhum')
    window.estado=copy.deepcopy(game.ESTADO_PADRAO)
    # Every light phase is inspected as an actual rendered scene.
    light_sheet=QImage(1536,624,QImage.Format_ARGB32)
    light_sheet.fill(QColor('#1c2b3b'));p=QPainter(light_sheet);p.setFont(QFont('Segoe UI',9))
    for i,hour in enumerate((0,6,9,12,18,22)):
        window._preview_clock=datetime(2026,10,6,hour)
        window.fase=8.4 if hour in (0,22) else 2
        scene,_=window.desenhar_cena()
        x,y=i%3*512,i//3*312;p.drawImage(QRect(x,y,512,288),scene)
        p.setPen(QColor('#ffe3ac'));p.drawText(x+12,y+306,f'{hour:02d}:00 · {renderer.current_light.label}')
        scene.scaled(512,288,Qt.IgnoreAspectRatio,Qt.FastTransformation).save(str(out/f'horario-{hour:02d}.png'))
    p.end();check('Six local lighting phases rendered',light_sheet.save(str(out/'ciclo-horarios.png')))
    window._preview_clock=datetime(2026,10,6,18);window.fase=2
    capture(window,'depois.png')
    window.fisgando=1.0
    capture(window,'fisgada.png')
    window.fisgando=0
    window.capturando=.65
    window.mostrar_popup('Cavalinho-do-mar-pigmeu  +123.456,75 moedas','#ffe3ac')
    capture(window,'captura.png')
    # Longest achievement and currency must fit the wrapped notification region.
    window.mostrar_popup('Conquista desbloqueada: Temos que vestir todos!','#ffe3ac')
    capture(window,'conquista.png')
    window.popup=None
    window.capturando=0
    # Every catalog ID is rendered; all hull levels and finite flag frames.
    for slot in game.SLOTS:
        items=[it for it in game.CATALOGO if it[1]==slot]
        cellw,cellh=512,312
        sheet=QImage(cellw*3,cellh*((len(items)+2)//3),QImage.Format_ARGB32)
        sheet.fill(QColor('#1c2b3b'))
        p=QPainter(sheet)
        p.setFont(QFont('Segoe UI',9))
        for i,(id_,_,name,_) in enumerate(items):
            window.previa={slot:id_}
            window.fase=2+i*.3
            scene,_=window.desenhar_cena()
            x,y=(i%3)*cellw,(i//3)*cellh
            p.drawImage(QRect(x,y,512,288),scene)
            p.setPen(QColor('#ffe3ac'))
            p.drawText(QRect(x+8,y+288,496,24),Qt.AlignVCenter,name)
        p.end()
        check('Catalog rendered: '+slot,sheet.save(str(out/('catalogo-'+slot+'.png'))))
    window.previa={}
    for hour in (0,6,12,18):
        window._preview_clock=datetime(2026,10,6,hour)
        rendered=[]
        for id_,slot,_,_ in game.CATALOGO:
            window.previa={slot:id_}
            scene,_=window.desenhar_cena()
            rendered.append(not scene.isNull() and scene.width()==256 and scene.height()==144)
        check('All 91 cosmetics at local hour '+str(hour),all(rendered))
    window.previa={};window._preview_clock=datetime(2026,10,6,18)
    sheet=QImage(1536,312*4,QImage.Format_ARGB32)
    sheet.fill(QColor('#1c2b3b'))
    p=QPainter(sheet)
    p.setFont(QFont('Segoe UI',9))
    for level in range(11):
        window.estado['barco']=level
        scene,_=window.desenhar_cena()
        x,y=level%3*512,level//3*312
        p.drawImage(QRect(x,y,512,288),scene)
        p.setPen(QColor('#ffe3ac'))
        p.drawText(x+12,y+306,f'Barco nível {level}')
    p.end()
    sheet.save(str(out/'barcos.png'))
    sheet.fill(QColor('#1c2b3b'));p=QPainter(sheet)
    p.setFont(QFont('Segoe UI',9))
    for level in range(11):
        window.estado['vara']=level;window.estado['barco']=0
        scene,_=window.desenhar_cena();x,y=level%3*512,level//3*312
        p.drawImage(QRect(x,y,512,288),scene);p.setPen(QColor('#ffe3ac'))
        p.drawText(x+12,y+306,f'Vara nível {level}')
    p.end();sheet.save(str(out/'varas.png'))
    window.estado=copy.deepcopy(game.ESTADO_PADRAO)
    window.estado['moedas']=50000
    shop=game.LojaDialog(window)
    check('Integer physical preview scale',abs(shop.preview_scene.scene_rect.width()*ratio/game.ART_W-shop.preview_scene.physical_scale)<.0001)
    check('Catalog count',sum(li.count() for li in shop.listas.values())==len(game.CATALOGO))
    shop.abas.setCurrentIndex(1)
    target=next(i for i in range(shop.listas['chapeu'].count())
                if shop.listas['chapeu'].item(i).data(Qt.UserRole)=='chapeu_bone')
    shop.listas['chapeu'].setCurrentRow(target)
    check('Preview isolated',window.previa=={'chapeu':'chapeu_bone'} and
          window.estado['equipados']['chapeu']=='chapeu_palha')
    before=window.estado['moedas']
    shop.acao()
    check('Buy and equip',window.estado['moedas']==before-150 and
          'chapeu_bone' in window.estado['cosmeticos'] and
          window.estado['equipados']['chapeu']=='chapeu_bone')
    shop.acao()
    check('Owned item no duplicate debit',window.estado['moedas']==before-150)
    capture(shop,'loja.png')
    window.estado['moedas']=1000000
    for slot_index,slot in enumerate(game.SLOTS,1):
        shop.abas.setCurrentIndex(slot_index)
        for row in range(shop.listas[slot].count()):
            shop.listas[slot].setCurrentRow(row)
            item=shop.listas[slot].item(row).data(Qt.UserRole)
            equipped_before=window.estado['equipados'][slot]
            check('Preview '+item,window.previa.get(slot)==item and window.estado['equipados'][slot]==equipped_before)
            expected=0 if item in window.estado['cosmeticos'] else game.CAT[item][3]
            balance=window.estado['moedas']
            shop.acao()
            check('Equip '+item,window.estado['equipados'][slot]==item and
                  window.estado['moedas']==balance-expected)
    shop.accept()
    check('Preview cleared on closing',window.previa=={})
    encyclopedia=game.EnciclopediaDialog(window)
    capture(encyclopedia,'enciclopedia-vazia.png')
    check('Empty encyclopedia',encyclopedia.lista.count()==0)
    window.estado['inventario']={'Cavalinho-do-mar-pigmeu':10,'Lambari':1,'Vaquita':5}
    encyclopedia.atualizar_progresso()
    capture(encyclopedia,'enciclopedia.png')
    check('Discovery entries',encyclopedia.lista.count()==3)
    check('Revealed curiosity','Camufla-se' in encyclopedia.detalhes.text())
    encyclopedia.ordenacao.setCurrentIndex(1)
    check('Quantity ordering',encyclopedia.lista.item(0).data(Qt.UserRole)=='Cavalinho-do-mar-pigmeu')
    encyclopedia.accept()
    # Actual modal flows, including an inventory long enough to require scrolling.
    window.estado['inventario']={entry['nome']:123456 for entry in game.LOOT if entry['tipo']=='peixe'}
    info_snapshots=[]
    def close_info():
        for widget in app.topLevelWidgets():
            if isinstance(widget,InfoDialog):
                widget.grab().save(str(out/('conquistas-painel.png' if widget.windowTitle()=='Conquistas' else 'status-painel.png')))
                info_snapshots.append((widget.windowTitle(),widget.page.text(),widget.scroll.verticalScrollBar().maximum(),widget.height()))
                widget.accept()
    QTimer.singleShot(20,close_info);window.mostrar_status()
    check('Complete inventory fits scrollable RPG panel',info_snapshots[-1][2]>0 and info_snapshots[-1][3]<=app.primaryScreen().availableGeometry().height())
    check('Long inventory text preserved','123456' in info_snapshots[-1][1] and 'Vaquita' in info_snapshots[-1][1])
    QTimer.singleShot(20,close_info);window.mostrar_conquistas()
    check('Achievement RPG dialog',info_snapshots[-1][0]=='Conquistas' and bool(info_snapshots[-1][1]))
    # Parts and reward mechanics, with deterministic controlled catches.
    window.estado=copy.deepcopy(game.ESTADO_PADRAO)
    window.estado['moedas']=1000
    window.comprar_peca('vara');window.comprar_peca('vara')
    check('Upgrade parts/cost preserved',window.estado['vara']==1 and
          window.estado['pecas_vara']==0 and window.estado['moedas']==940)
    window.estado['barco']=3
    with patch.object(game.random,'choices',return_value=[next(i for i in game.LOOT if i['nome']=='Vaquita')]):
        result=window.sortear()
    check('Reward / inventory / achievements',window.estado['moedas']==8940 and
          window.estado['inventario']['Vaquita']==1 and result['tipo']=='peixe')
    window.salvar()
    reloaded=window.carregar()
    check('Save roundtrip',reloaded==window.estado)
    window.estado['ultimo_salvo']=time.time()-100000
    random.seed(1729)
    summary=window.simular_offline()
    check('Offline limit and catches','limite de 4h' in summary and window.estado['total_pescados']>100)
    # Compare full economy / random probabilities / offline simulation against baseline.
    import types
    source=subprocess.run(['git','show','b4ef8c7:pesca_idle.py'],cwd=root,capture_output=True,check=True).stdout.decode('utf-8')
    original=types.ModuleType('pesca_original')
    exec(compile(source,'baseline.py','exec'),original.__dict__)
    original.SAVE_PATH=Path(tmp)/'original.json'
    baseline=original.JogoPesca()
    baseline.relogio.stop();baseline.timer_save.stop()
    for level in (0,3,10):
        state=copy.deepcopy(game.ESTADO_PADRAO)
        state.update(vara=level,barco=level,ultimo_salvo=time.time()-7200)
        baseline.estado=copy.deepcopy(state);window.estado=copy.deepcopy(state)
        with patch.object(time,'time',return_value=200000):
            baseline.estado['ultimo_salvo']=190000
            window.estado['ultimo_salvo']=190000
            random.seed(1234);a=baseline.simular_offline()
            random.seed(1234);b=window.simular_offline()
        check(f'Original offline/probabilities identical level {level}',
              a==b and baseline.estado==window.estado)
    # Pause holds the fish timer and capture animation, while scenery keeps moving.
    window.pausado=True
    window.espera=10;window.fisgando=.8;window.capturando=.5
    window.ultimo_tick=time.monotonic()-.2
    window.tick()
    check('Pause preserves fishing state',window.espera==10 and window.fisgando==.8 and window.capturando==.5)
    window.alternar_pausa()
    check('Resume',not window.pausado)
    window.fisgando=.01;window.ultimo_tick=time.monotonic()-.1
    with patch.object(game.random,'choices',return_value=[game.LOOT[-1]]):
        window.tick()
    check('Strike completes to capture',window.fisgando<=0 and window.capturando==1.2 and window.popup)
    window.fase=2.0;window.popup=None;window.capturando=0;window.fisgando=0
    # Direct Qt event dispatch exercises frameless dragging with global positions.
    window.move(100,100)
    def mouse(kind,local,global_pos,button,buttons):
        app.sendEvent(window,QMouseEvent(kind,QPointF(*local),QPointF(*global_pos),button,buttons,Qt.NoModifier))
    mouse(QMouseEvent.MouseButtonPress,(30,50),(130,150),Qt.LeftButton,Qt.LeftButton)
    mouse(QMouseEvent.MouseMove,(30,50),(180,190),Qt.NoButton,Qt.LeftButton)
    mouse(QMouseEvent.MouseButtonRelease,(30,50),(180,190),Qt.LeftButton,Qt.NoButton)
    check('Window drag',window.pos()==QPoint(150,140) and not window._arrastando)
    check('Always on top / frameless',bool(window.windowFlags() & Qt.WindowStaysOnTopHint)
          and bool(window.windowFlags() & Qt.FramelessWindowHint))
    window.posicionar()
    geo=app.primaryScreen().availableGeometry()
    check('Bottom-right initial placement',window.x()==geo.right()+1-window.width()
          and window.y()==geo.bottom()+1-window.height())
    menu_items=[]
    def close_menu():
        for widget in app.topLevelWidgets():
            if isinstance(widget,QMenu):
                widget.grab().save(str(out/'menu.png'))
                menu_items.extend(a.text() for a in widget.actions())
                widget.close()
    QTimer.singleShot(20,close_menu)
    window.abrir_menu()
    check('Menu actions',all(x in menu_items for x in ('Loja','Enciclopédia','Conquistas','Pausar','Sair')))
    # Stress cache using all outfit combinations, no frame-key growth.
    for dress in game.ROUPAS:
        for hat in game.HATS:
            window.previa={'roupa':dress,'chapeu':hat}
            window.desenhar_cena()
    for n in range(100):
        window.fase=n*.066;window.desenhar_cena()
    check('Cache bounded',len(window._render.cache)<=window._render.CACHE_LIMIT)
    window.previa={};window.estado=copy.deepcopy(game.ESTADO_PADRAO)
    window._preview_clock=datetime(2026,10,6,18,17,28)
    start=time.perf_counter()
    for i in range(120):
        window.fase=i/15;window.desenhar_cena()
    ms=(time.perf_counter()-start)*1000/120
    window._preview_clock=datetime(2026,10,6,18)
    window.fase=2
    capture(window,'depois.png')
    before=QImage(str(root/'docs'/'visual'/'antes.png'))
    native_scene,_=window.desenhar_cena()
    native_scene.copy(98,54,48,70).scaled(288,420,Qt.IgnoreAspectRatio,Qt.FastTransformation).save(str(out/'encaixe-personagem.png'))
    environment_sheet=QImage(1536,624,QImage.Format_ARGB32)
    environment_sheet.fill(QColor('#1c2b3b'))
    p=QPainter(environment_sheet);p.setFont(QFont('Segoe UI',9))
    for i,phase in enumerate((0,1.4,4,8.2,8.6,9.1)):
        window.fase=phase;scene,_=window.desenhar_cena()
        x,y=i%3*512,i//3*312
        p.drawImage(QRect(x,y,512,288),scene)
        p.setPen(QColor('#ffe3ac'));p.drawText(x+8,y+305,f'Ambiente • {phase:.1f} s')
    p.end();environment_sheet.save(str(out/'ambiente-quadros.png'))
    after=QImage(str(out/'depois.png'))
    beforew,beforeh=before.width()*window.physical_scale,before.height()*window.physical_scale
    after_x=beforew+56
    comparison=QImage(beforew+after.width()+56,max(beforeh,after.height())+44,QImage.Format_ARGB32)
    comparison.fill(QColor('#1c2b3b'))
    p=QPainter(comparison)
    p.setFont(QFont('Segoe UI',11));p.setPen(QColor('#ffe3ac'))
    p.drawText(12,24,f'ANTES • 120×68 (ampliação inteira {window.physical_scale*2}×)')
    p.drawText(after_x,24,f'DEPOIS • 256×144 (ampliação inteira {window.physical_scale}×)')
    p.drawImage(QRect(28,38+(after.height()-beforeh)//2,beforew,beforeh),before)
    p.drawImage(after_x,38,after)
    p.end();comparison.save(str(out/'comparacao.png'))
    baseline.close();window.close()
    check('Close saves',game.SAVE_PATH.exists() and not window.relogio.isActive())
    report={'checks':checks,'count':len(checks),'catalog_items':len(game.CATALOGO),
            'average_scene_ms':round(ms,2),'cache_limit':window._render.CACHE_LIMIT,
            'qt_scale_factor':os.getenv('QT_SCALE_FACTOR','1'), 'save_isolated':True}
    report.update(device_pixel_ratio=ratio,physical_scale=window.physical_scale)
    report.update(clock_source='device_local',light_plates=96,animated_pets=14,animated_flags=13,
                  lighting_hours=[0,6,9,12,18,22])
    (out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
