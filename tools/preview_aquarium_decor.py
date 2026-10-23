"""Render only: synthetic fixtures and price arithmetic, never personal saves or fishing."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    from tools.aquarium_preview import isolate,synthetic_state
    output=isolate(args.out)
    from PySide6.QtCore import Qt,QRectF
    from PySide6.QtGui import QImage,QPainter,QColor,QFont
    from PySide6.QtWidgets import QApplication,QWidget,QScrollArea
    from pesca_ui import configure_app
    from pesca_idle import (ESTADO_PADRAO,LojaDialog,SceneRenderer,ROUPAS,HATS,BANDEIRAS,
                            BONECOS,BOIAS,CORES_BARCO)
    from pesca_aquario_decor import CAT,CATALOGO,SLOTS,empty_decoration
    from pesca_aquario_decor_ui import DecorationDialog
    from pesca_museu_ui import AquariumView,MuseuDialog
    from pesca_catalogo import ESPECIES,probabilities
    from pesca_tempo import LABELS
    from pesca_moedas import reward
    from pesca_loja import sold_items
    app=QApplication([]);app.setQuitOnLastWindowClosed(False);configure_app(app)
    class Host(QWidget):
        def __init__(self):
            super().__init__();self.estado=copy.deepcopy(ESTADO_PADRAO)
            self.estado.update(synthetic_state())
            self.estado.update(moedas=20000,moedas_centavos=2000000)
            self.previa={};self._save_error=None
            self._render=SceneRenderer(ROUPAS,HATS,BANDEIRAS,BONECOS,BOIAS,CORES_BARCO)
        def _commit(self,state):self.estado=copy.deepcopy(state);return True  # Interactive preview memory only.
        def tick(self):pass
        def atualizar_tooltip(self):pass
        def custo_peca(self,tipo):return 30+20*self.estado[tipo]
        def pecas_necessarias(self,tipo):return 2+self.estado[tipo]
        def comprar_peca(self,tipo):pass
    host=Host()
    store=LojaDialog(host);store.setWindowTitle('PRÉVIA SINTÉTICA - Loja de decorações')
    store.setAttribute(Qt.WA_DontShowOnScreen,True)
    store.abas.setCurrentWidget(store.decoracoes);store.resize(980,680)
    store.show();app.processEvents();store.decoracoes.aquarium.timer.stop();store.decoracoes.aquarium.phase=0
    store.grab().save(str(output/'loja.png'));store.close()
    fixture=host.estado
    fixture['museu']['decoracao']=empty_decoration()
    fixture['museu']['decoracao']['compradas']=list(CAT)
    # Three illustrative combinations, not rewards from a simulated game.
    presets={
        'jardim':['aquario_substrato_areia','aquario_plantas_lotus','aquario_fundo_pedras',
                  'aquario_ornamento_conchas','aquario_moldura_madeira','aquario_base_carvalho','aquario_luz_ambar'],
        'ruinas':['aquario_substrato_jade','aquario_plantas_samambaias','aquario_fundo_ruinas',
                  'aquario_ornamento_bau','aquario_moldura_cobre','aquario_base_navegador','aquario_luz_safira'],
        'coral':['aquario_substrato_jade','aquario_plantas_elodeas','aquario_fundo_algas',
                 'aquario_ornamento_coral','aquario_moldura_marmore','aquario_base_real','aquario_luz_aurora']}
    view=AquariumView(lambda:fixture,ESPECIES)
    for name,items in presets.items():
        fixture['museu']['decoracao']['equipadas']=dict(zip(SLOTS,items))
        view.render_image(0,2).save(str(output/(name+'.png')))
    fixture['museu']['decoracao']['equipadas']=dict(zip(SLOTS,presets['ruinas']))
    editor=DecorationDialog(host);editor.setAttribute(Qt.WA_DontShowOnScreen,True);editor.show();app.processEvents()
    editor.panel.aquarium.timer.stop();editor.panel.preview_requested=False;editor.panel.update_selection()
    for w,h in ((800,650),(320,568)):
        editor.resize(w,h)
        for _ in range(4):app.processEvents()
        editor.panel.aquarium.timer.stop();editor.panel.aquarium.phase=0
        print(dict(dialog=(editor.width(),editor.height()),panel=(editor.panel.width(),editor.panel.height()),
            min_panel=(editor.panel.minimumSizeHint().width(),editor.panel.minimumSizeHint().height()),
            direction=editor.panel.body.direction().name,filter_width=editor.panel.slot.width(),
            action_min=editor.panel.action.minimumSizeHint().width(),clear_min=editor.panel.clear.minimumSizeHint().width()))
        editor.grab().save(str(output/('decorar-'+str(w)+'.png')))
        if w==320:
            scroll=editor.findChild(QScrollArea)
            scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
            for _ in range(3):app.processEvents()
            editor.grab().save(str(output/'decorar-320-base.png'))
    editor.close()
    museum=MuseuDialog(host);museum.setAttribute(Qt.WA_DontShowOnScreen,True)
    museum.resize(640,700);museum.show();app.processEvents();museum.aquario.timer.stop();museum.aquario.phase=0
    museum.grab().save(str(output/'museu.png'));museum.close()
    # A labelled catalogue sheet of all 21 implemented styles.
    sheet=QImage(1100,1410,QImage.Format_ARGB32_Premultiplied);sheet.fill(QColor('#192e3a'));p=QPainter(sheet)
    p.setPen(QColor('#e6ecd9'));p.setFont(QFont('Segoe UI',15,QFont.Bold));p.drawText(24,29,'Decorações do aquário | coleção inicial e preços propostos')
    for n,item in enumerate(CATALOGO):
        x=18+(n%3)*364;y=48+(n//3)*192
        p.fillRect(x,y,350,180,QColor('#234854'))
        fixture['museu']['decoracao']['equipadas']={slot:item['id'] if slot==item['slot'] else None for slot in SLOTS}
        p.drawImage(QRectF(x+47,y+6,256,128),view.render_image(0,1))
        p.setPen(QColor('#e6ecd9'));p.setFont(QFont('Segoe UI',11,QFont.Bold));p.drawText(x+12,y+153,item['nome'])
        p.setFont(QFont('Segoe UI',9));p.drawText(x+12,y+172,str(item['price'])+' moedas · '+SLOTS[item['slot']]['nome'])
    p.end();sheet.save(str(output/'catalogo.png'));view.close();host.close()
    # Frozen-context expected values, NOT a progression or offline simulation.
    contexts=[]
    for rod,boat in ((0,0),(3,3),(10,10)):
        values=[]
        for period in LABELS:
            probs=probabilities('enseada_do_poente',period,rod)
            average=sum(prob*reward(ESPECIES[id_]['valor'],boat)/100 for id_,prob in probs.items() if id_ in ESPECIES)
            values.append(dict(period=period,coins_per_cast=average,reference_coins_per_hour=3600*average/(15/(1+.15*rod)+1.5)))
        contexts.append(dict(rod=rod,boat=boat,periods=values))
    old=sold_items()
    data=dict(reference_sha='9d5d7831752b79f5578007bb51b255329c15cfd0',catalogue=list(CATALOGO),
        current_shop=dict(count=len(old),minimum=min(x[3] for x in old),maximum=max(x[3] for x in old)),
        equipment=dict(first_level_total=60,complete_one_equipment=sum((2+n)*(30+20*n) for n in range(10))),
        decoration_total=sum(x['price'] for x in CATALOGO),contexts=contexts,
        method='Analytical mean using real probabilities/reward and fixed map/period/equipment. No fishing, purchases, save or progression simulation.',
        capture_scope='Actual Qt widgets, synthetic in-memory discovery/balance/owned fixtures. No automated interaction tests or persistence tests.')
    (output/'precos.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({**{k:data[k] for k in ('current_shop','equipment','decoration_total')},
        'save_created':Path(os.environ['PESCA_IDLE_SAVE_PATH']).exists()}))
    return 0

if __name__=='__main__':raise SystemExit(main())
