"""Qt mobile presentation and lifecycle, isolated desktop preview (not Android)."""
import copy,json,os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
with tempfile.TemporaryDirectory(prefix='pesca-mobile-') as tmp:
    os.environ['PESCA_IDLE_SAVE_PATH']=str(Path(tmp)/'save.json');os.environ['PESCA_IDLE_MOBILE']='1'
    os.environ['APPDATA']=str(Path(tmp)/'appdata');os.environ['LOCALAPPDATA']=str(Path(tmp)/'localappdata')
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtCore import Qt,QEvent
    from PySide6.QtWidgets import QApplication,QWidget
    from pesca_ui import configure_app,InfoDialog
    from pesca_idle import JogoPesca,LojaDialog
    from pesca_viagens_ui import ColecaoDialog,ViajarDialog,ExpedicaoDialog
    from pesca_plataforma import fit_dialog
    from pesca_android import MobileLifecycle
    app=QApplication([]);configure_app(app);g=JogoPesca();g.show()
    out=Path(os.environ.get('PESCA_IDLE_QA_DIR',tmp));out.mkdir(parents=True,exist_ok=True)
    checks=[]
    for name,w,h in [('portrait',360,800),('landscape',800,360)]:
        g.resize(w,h);app.processEvents();g.grab().save(str(out/(name+'.png')))
        assert g.rect_icone.width()>=44
        assert g.scene_rect.left()>=0 and g.scene_rect.top()>=0
        assert g.scene_rect.right()<=g.width()+.01 and g.scene_rect.bottom()<=g.height()+.01
        checks.append('viewport '+name)
        for cls,title in [(LojaDialog,'shop'),(ColecaoDialog,'collection'),(ViajarDialog,'travel'),(ExpedicaoDialog,'expedition')]:
            d=fit_dialog(cls(g));d.resize(w,h);d.show();app.processEvents();d.grab().save(str(out/(name+'-'+title+'.png')))
            assert d.width()==w and d.height()==h
            d.accept()
            if hasattr(d,'timer'):assert not d.timer.isActive()
            d.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);checks.append(title+' '+name)
    clock={'now':g._wall(),'mono':g._monotonic()};g._wall=lambda:clock['now'];g._monotonic=lambda:clock['mono']
    lifecycle=MobileLifecycle(app,g);g.tick();before=copy.deepcopy(g.estado)
    lifecycle.changed(Qt.ApplicationSuspended);assert not g.relogio.isActive()
    clock['now']+=120;clock['mono']+=120;lifecycle.changed(Qt.ApplicationActive)
    assert g.relogio.isActive() and g._last_offline['paid_seconds']==120
    once=copy.deepcopy(g.estado);lifecycle.changed(Qt.ApplicationActive);assert g.estado==once
    g.alternar_pausa();paused=copy.deepcopy(g.estado['inventario_por_id'])
    lifecycle.changed(Qt.ApplicationSuspended);clock['now']+=120;clock['mono']+=120;lifecycle.changed(Qt.ApplicationActive)
    assert g.estado['inventario_por_id']==paused and g.pausado
    checks.extend(['suspend saves','resume offline once','intentional pause preserved'])
    g.close();assert g._store.lock is None
    (out/'mobile.json').write_text(json.dumps({'checks':checks,'profile_isolated':True,'backend':'Qt offscreen on desktop; Android installation is a separate test'},indent=2),encoding='utf-8')
    print('Mobile preview/lifecycle passed:',len(checks))
