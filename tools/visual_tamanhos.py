"""Qt visual fixtures and injected input events; not Android/physical input."""
from pathlib import Path
import os,sys,json,hashlib,copy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.verificar_tamanhos import QA,fresh,add,NOW
os.environ['QT_QPA_PLATFORM']='windows'
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QImage,QPainter,QColor,QFont
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from pesca_idle import JogoPesca,ESTADO_PADRAO
from pesca_museu_ui import MuseuDialog,AquariumView
from pesca_viagens_ui import ColecaoDialog
from pesca_plataforma import fit_dialog
from pesca_ui import configure_app
from pesca_especies_visual import species_image
import pesca_tamanhos as sizes
from pesca_tamanho_visual import scale_for

APP=QApplication.instance() or QApplication([]);configure_app(APP)
OUT=QA/'visual';OUT.mkdir(exist_ok=True)
def digest(img):return hashlib.sha256(bytes(img.constBits())).hexdigest()
def mm_event(s,sid,mm):
    e=add(s,sid,.5)
    e['measurement']=dict(mm=mm,band=sizes.band(mm,sizes.rule_snapshot(sid)),rule=sizes.rule_snapshot(sid))
    # Replace only this synthetic fixture's records, not a captured player's state.
    item=copy.deepcopy(e['measurement']);item.update(event_id=e['id'],utc=NOW,map_id='enseada_do_poente',periodo_id='dia')
    s['medidas_peixes']['records'][sid]={'n':1,'menor':copy.deepcopy(item),'maior':copy.deepcopy(item)}
    s['medidas_peixes']['quantity']=sum(r['n'] for r in s['medidas_peixes']['records'].values())
    return e

def game(name,mobile=False):
    os.environ['PESCA_IDLE_MOBILE']='1' if mobile else '0'
    configure_app(APP)
    import pesca_idle
    pesca_idle.SAVE_PATH=QA/(name+'.json')
    g=JogoPesca(wall_clock=lambda:NOW,monotonic_clock=lambda:0)
    g.setAttribute(Qt.WA_DontShowOnScreen,True);g.pausado=True
    g.estado=fresh(9);g.estado['pausado']=True;g.fase=2
    g.show();APP.processEvents()
    return g

g=game('visual-desktop')
checks={};bounds=0
cached={sid:digest(species_image(sid)) for sid in sizes.RULES}
for sid in sizes.RULES:
    rule=sizes.rule_snapshot(sid)
    contact=QImage(1536,640,QImage.Format_ARGB32_Premultiplied);contact.fill(QColor('#172b3b'))
    painter=QPainter(contact);painter.setFont(QFont('Segoe UI',11));painter.setPen(QColor('#eef0de'))
    scales=[]
    for i,(label,key) in enumerate((('Pequeno','min_mm'),('Típico','typical_mm'),('Grande','max_mm'))):
        g.estado=fresh(9);g.estado['pausado']=True
        event=mm_event(g.estado,sid,rule[key]);g.estado['museu']['aquario']=[sid,None,None]
        view=AquariumView(lambda:g.estado,__import__('pesca_catalogo').ESPECIES)
        aq=view.render_image(4)
        g._last_result=event;g.capturando=.6;g.fisgando=0
        g.popup=[g._describe(event)[0],'#ffe3ac',4]
        scene,_=g._render.render(g)
        painter.drawText(i*512+12,24,label+' · '+sizes.fmt(rule[key])+' · design provisório')
        painter.drawImage(QRectF(i*512,42,512,288),scene)
        painter.drawImage(QRectF(i*512,362,512,256),aq)
        scales.append(scale_for(event['measurement'],sid))
        view.deleteLater()
    painter.end();contact.save(str(OUT/('variacao-'+sid+'.png')))
    assert scales==sorted(scales);checks[sid]={'scales':scales,'range_mm':[rule['min_mm'],rule['max_mm']]}

# Three simultaneous species, with real record selection in each occupied slot.
g.estado=fresh(9);g.estado['pausado']=True
for sid in ('lambari','tilapia_do_nilo','carpa_comum'):
    add(g.estado,sid,0);add(g.estado,sid,1)
g.estado['museu']['aquario']=['lambari','tilapia_do_nilo','carpa_comum']
assert g._commit(copy.deepcopy(g.estado))
d=MuseuDialog(g);d.setAttribute(Qt.WA_DontShowOnScreen,True);d.resize(640,700);d.show();APP.processEvents()
for phase in (i/10 for i in range(600)):
    for sid,x,y,reverse in d.aquario.fish_positions(phase):
        slot=g.estado['museu']['aquario'].index(sid);sc=scale_for(sizes.exhibit(g.estado,slot),sid)
        assert 16<=x-18*sc and x+18*sc<=240
        assert 16<=y-12*sc and y+12*sc<=106
        bounds+=1
d.grab().save(str(OUT/'museu-desktop-topo.png'))
d.specimen_selectors[0].setFocus();QTest.keyClick(d.specimen_selectors[0],Qt.Key_End);APP.processEvents()
assert g.estado['museu']['exemplares'][0]=='menor'
selected=sizes.exhibit(g.estado,0)
assert selected['mm']==g.estado['medidas_peixes']['records']['lambari']['menor']['mm']
d.aquario.render_image(3).scaled(768,384,Qt.KeepAspectRatio,Qt.FastTransformation).save(str(OUT/'aquario-misto.png'))
animation=QImage(1536,256,QImage.Format_ARGB32_Premultiplied);animation.fill(QColor('#172b3b'))
ap=QPainter(animation)
frames=[]
for i,t in enumerate((0,10,20)):
    frame=d.aquario.render_image(t);frames.append(digest(frame));ap.drawImage(QRectF(i*512,0,512,256),frame)
ap.end();animation.save(str(OUT/'aquario-animacao.png'));assert len(set(frames))==3
d.scroll.verticalScrollBar().setValue(d.scroll.verticalScrollBar().maximum());APP.processEvents()
d.grab().save(str(OUT/'museu-desktop-rodape.png'))
QTest.mouseClick(d.remove_buttons[2],Qt.LeftButton);APP.processEvents()
assert g.estado['museu']['aquario'][2] is None
assert not d.specimen_selectors[2].isEnabled()
legacy=copy.deepcopy(g.estado);legacy['inventario_por_id']['pacu']=10;legacy['total_pescados']+=10
assert g._commit(legacy);d._signature=None;d.refresh()
d.selectors[2].setCurrentIndex(d.selectors[2].findData('pacu'));APP.processEvents()
assert sizes.exhibit(g.estado,2) is None and not d.specimen_selectors[2].isEnabled()
assert 'Sem exemplar medido' in d.details[2].text()
d.scroll.verticalScrollBar().setValue(d.scroll.verticalScrollBar().maximum());APP.processEvents()
d.grab().save(str(OUT/'museu-legado-sem-medida.png'))
checks['qt_input']={'key_end_selected_smaller':True,'mouse_click_removed_slot':True,
                    'kind':'QTest-injected events, not direct callback calls or physical OS input'}
d.accept();d.deleteLater();APP.processEvents()

add(g.estado,'lambari',.5)
e=ColecaoDialog(g);e.setAttribute(Qt.WA_DontShowOnScreen,True);e.show();APP.processEvents()
e.local.setCurrentIndex(e.local.findData('enseada_do_poente'));APP.processEvents()
row=next(i for i in range(e.lista.count()) if e.lista.item(i).data(Qt.UserRole)=='lambari')
e.lista.setCurrentRow(row);APP.processEvents()
assert 'Menor:' in e.detail.text() and 'Maior:' in e.detail.text()
e.period.setCurrentIndex(e.period.findData('noite'));e.agora.setChecked(True);APP.processEvents()
from pesca_catalogo import OCORRENCIAS
from pesca_tempo import snapshot
now=snapshot(g._wall())['periodo_id']
for i in range(e.lista.count()):
    sid=e.lista.item(i).data(Qt.UserRole)
    assert any(o['species_id']==sid and o['map_id']=='enseada_do_poente' and 'noite' in o['periods'] and now in o['periods'] for o in OCORRENCIAS)
e.period.setCurrentIndex(0);e.agora.setChecked(False);e.ordem.setCurrentIndex(1);APP.processEvents()
counts=[g.estado['inventario_por_id'][e.lista.item(i).data(Qt.UserRole)] for i in range(e.lista.count())]
assert counts==sorted(counts,reverse=True)
e.ordem.setCurrentIndex(0);APP.processEvents()
e.lista.setCurrentRow(next(i for i in range(e.lista.count()) if e.lista.item(i).data(Qt.UserRole)=='lambari'))
checks['filters']={'local_period_now_valid':True,'count_order_valid':True,'kind':'programmatic widget selections'}
e.grab().save(str(OUT/'enciclopedia-desktop.png'));e.accept();e.deleteLater()
g._last_result=add(g.estado,'lambari',.98);g.capturando=.6;g.popup=[g._describe(g._last_result)[0],'#ffe3ac',4]
g.grab().save(str(OUT/'captura-desktop.png'));g.close();APP.processEvents()

for width,height in ((320,568),(360,800)):
    m=game('visual-mobile-'+str(width),True)
    for sid in ('lambari','tilapia_do_nilo','carpa_comum'):
        add(m.estado,sid,0);add(m.estado,sid,1)
    m.estado['museu']['aquario']=['lambari','tilapia_do_nilo','carpa_comum'];m.salvar()
    m.resize(width,height)
    md=MuseuDialog(m);md.setAttribute(Qt.WA_DontShowOnScreen,True);md.resize(width,height);md.show();APP.processEvents()
    md.grab().save(str(OUT/f'museu-mobile-{width}-topo.png'))
    md.scroll.verticalScrollBar().setValue(md.scroll.verticalScrollBar().maximum());APP.processEvents()
    md.grab().save(str(OUT/f'museu-mobile-{width}-rodape.png'))
    assert md.back.geometry().bottom()<=md.scroll.widget().height()
    if width==320:
        preserved=copy.deepcopy(m.estado)
        for sid in sizes.RULES:
            rule=sizes.rule_snapshot(sid)
            panels=QImage(960,568,QImage.Format_ARGB32_Premultiplied);panels.fill(QColor('#172b3b'))
            p=QPainter(panels)
            for column,key in enumerate(('min_mm','typical_mm','max_mm')):
                m.estado=fresh(9);m.estado['pausado']=True
                mm_event(m.estado,sid,rule[key]);m.estado['museu']['aquario']=[sid,None,None]
                md._signature=None;md.refresh()
                for _ in range(3):md.scroll.verticalScrollBar().setValue(0);APP.processEvents()
                p.drawPixmap(column*320,0,md.grab())
            p.end();panels.save(str(OUT/f'variacao-mobile-{sid}.png'))
        m.estado=preserved;md._signature=None;md.refresh()
    md.accept();md.deleteLater();APP.processEvents()
    enc=fit_dialog(ColecaoDialog(m));enc.setAttribute(Qt.WA_DontShowOnScreen,True);enc.resize(width,height);enc.show();APP.processEvents()
    enc.lista.setCurrentRow(next(i for i in range(enc.lista.count()) if enc.lista.item(i).data(Qt.UserRole)=='lambari'))
    APP.processEvents();enc.grab().save(str(OUT/f'enciclopedia-mobile-{width}.png'))
    assert 'Recordes pessoais' in enc.detail.text()
    from PySide6.QtWidgets import QScrollArea
    outer=next(s for s in enc.findChildren(QScrollArea) if s.widget() is not enc.detail)
    for _ in range(4):
        outer.verticalScrollBar().setValue(outer.verticalScrollBar().maximum());APP.processEvents()
    enc.grab().save(str(OUT/f'enciclopedia-mobile-{width}-rodape.png'))
    enc.accept();enc.deleteLater();APP.processEvents()
    if width==320:
        for sid in sizes.RULES:
            rule=sizes.rule_snapshot(sid)
            shots=QImage(960,568,QImage.Format_ARGB32_Premultiplied);shots.fill(QColor('#172b3b'))
            p=QPainter(shots);sprite_regions=[]
            for column,key in enumerate(('min_mm','typical_mm','max_mm')):
                m.estado=fresh(9);m.estado['pausado']=True
                event=mm_event(m.estado,sid,rule[key]);m._last_result=event;m.capturando=.6
                m.popup=[m._describe(event)[0],'#ffe3ac',4]
                m.repaint();APP.processEvents();shot=m.grab();p.drawPixmap(column*320,0,shot)
                area=m.scene_rect
                cx=round(area.x()+171*area.width()/256);cy=round(area.y()+77*area.height()/144)
                sprite_regions.append(digest(shot.toImage().copy(cx-16,cy-12,32,24)))
            p.end();shots.save(str(OUT/f'captura-mobile-{sid}.png'))
            assert len(set(sprite_regions))==3,'Mobile capture sprite did not change: '+sid
        checks['mobile_capture_sprite_regions_distinct']=True
    m.close();APP.processEvents()

for sid in cached:assert cached[sid]==digest(species_image(sid))
checks.update(geometry_checks=bounds,cache_original_unchanged=True,native_qt_platform=APP.platformName(),
              android_native_test=False,viewport_mobile_only=True,frames_checked=600)
(QA/'visual-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False))
