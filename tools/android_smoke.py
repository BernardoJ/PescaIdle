"""On-device checks, included only in the disposable Android QA package."""
import copy,json,os,traceback
from pathlib import Path
from PySide6.QtCore import QTimer,Qt,QEvent
from PySide6.QtWidgets import QWidget
from PySide6.QtTest import QTest


def schedule(app,game,lifecycle):
    QTimer.singleShot(1800,lambda:run(app,game,lifecycle))


def run(app,g,lifecycle):
    out=Path(os.environ['PESCA_IDLE_QA_DIR']).resolve();checks=[]
    report={'passed':False,'checks':checks,'platform':app.platformName(),
            'profile':os.environ['PESCA_IDLE_SAVE_PATH'],'window':[g.width(),g.height()],
            'ratio':g.devicePixelRatioF()}
    try:
        from pesca_catalogo import LOCAIS,ESPECIES,desbloquear
        from pesca_idle import LojaDialog,ESTADO_PADRAO
        from pesca_viagens_ui import ColecaoDialog,ViajarDialog,ExpedicaoDialog
        from pesca_plataforma import fit_dialog
        from pesca_moedas import set_balance,balance,cents
        from pesca_pescaria import FishingEngine
        from pesca_save import SaveStore
        from pesca_loja import CAT,SLOTS,sold_items
        from pesca_conquistas import grant,RECOMPENSA_LIVRO
        assert app.platformName()=='android'
        assert out.name.startswith('qa-') and out/'save.json'==g._store.path
        checks.append('Android Qt and disposable private profile')
        g.relogio.stop();g.timer_save.stop();g.pausado=True
        state=copy.deepcopy(g.estado);state['barco']=10;state['vara']=10;state['pausado']=True
        set_balance(state,100000);desbloquear(state);assert g._commit(state)
        assert g.rect_icone.width()>=44 and g.scene_rect.left()>=0
        g.repaint();QTest.qWait(150);g.grab().save(str(out/'game.png'))
        for map_id in LOCAIS:
            image,_=g._render.render(g,map_id=map_id)
            assert not image.isNull();assert image.save(str(out/(map_id+'.png')))
        checks.append('8 packaged map assets rendered')
        shop=fit_dialog(LojaDialog(g));shop.show();QTest.qWait(150)
        slot='chapeu';shop.categoria.setCurrentIndex(1+list(SLOTS).index(slot))
        first=next(x for x in sold_items() if x[1]==slot)
        for row in range(shop.listas[slot].count()):
            if shop.listas[slot].item(row).data(Qt.UserRole)==first[0]:shop.listas[slot].setCurrentRow(row);break
        before=balance(g.estado);shop.btn.click();app.processEvents()
        assert g.estado['equipados'][slot]==first[0] and balance(g.estado)==before-cents(first[3])
        assert shop.lbl_moedas.text()==f'Suas moedas: {g.fmt_currency(g.estado["moedas"])}'
        QTest.qWait(150)
        shop.grab().save(str(out/'shop.png'));shop.accept()
        assert not shop.timer.isActive();shop.deleteLater()
        checks.append('touch-sized shop purchase and preview lifecycle')
        for cls,name in ((ColecaoDialog,'collection'),(ViajarDialog,'travel'),(ExpedicaoDialog,'expedition')):
            dlg=fit_dialog(cls(g));dlg.show();QTest.qWait(150)
            assert dlg.width()<=g.width() and dlg.height()<=g.height()
            scroll=dlg.findChild(__import__('PySide6.QtWidgets',fromlist=['QScrollArea']).QScrollArea)
            assert scroll.widget().width()<=scroll.viewport().width()
            dlg.grab().save(str(out/(name+'.png')));dlg.accept();dlg.deleteLater()
        app.sendPostedEvents(None,QEvent.DeferredDelete)
        checks.append('collection travel expedition scrollable dialogs')
        engine=FishingEngine(g.estado);candidate=engine.advance(60,g._wall()-60,g.estado['contexto_fuso'])
        assert engine.events and g._commit(candidate)
        counts=copy.deepcopy(g.estado['inventario_por_id'])
        assert sum(counts.values())>0
        assert g.viajar('rio_das_vitorias')
        checks.append('fishing reward and unlocked travel')
        state=copy.deepcopy(g.estado);state['cosmeticos']+=list(x[0] for x in sold_items() if x[0] not in state['cosmeticos'])
        grant(state,tuple(CAT.values()));assert 'fashionista' in state['conquistas']
        assert RECOMPENSA_LIVRO not in state['cosmeticos'];assert g._commit(state)
        checks.append('Fashionista excludes encyclopedia reward')
        assert g.salvar();g._store.close()
        with SaveStore(out/'save.json') as store:
            loaded=store.load(ESTADO_PADRAO,g._wall())
            assert loaded['moedas_centavos']==g.estado['moedas_centavos']
            assert loaded['inventario_por_id']==counts
        g._store=SaveStore(out/'save.json');g._store.load(ESTADO_PADRAO,g._wall())
        checks.append('atomic save reload and profile lock release')
        clock={'now':g._wall(),'mono':g._monotonic()}
        g._wall=lambda:clock['now'];g._monotonic=lambda:clock['mono']
        g.pausado=False;g.estado['pausado']=False;lifecycle.changed(Qt.ApplicationSuspended)
        clock['now']+=120;clock['mono']+=120;lifecycle.changed(Qt.ApplicationActive)
        assert g._last_offline['paid_seconds']==120
        once=copy.deepcopy(g.estado);lifecycle.changed(Qt.ApplicationActive);assert g.estado==once
        g.alternar_pausa();before=copy.deepcopy(g.estado['inventario_por_id'])
        lifecycle.changed(Qt.ApplicationSuspended);clock['now']+=60;clock['mono']+=60;lifecycle.changed(Qt.ApplicationActive)
        assert g.pausado and g.estado['inventario_por_id']==before
        checks.append('historical resume once and intentional pause')
        assert g.salvar();assert len(ESPECIES)==88
        report['passed']=True
    except Exception:
        report['error']=traceback.format_exc()
    (out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PESCA_QA_RESULT='+json.dumps(report),flush=True)
