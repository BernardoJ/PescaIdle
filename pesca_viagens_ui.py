"""Travel, scheduled absence and progressively revealed regional collection."""
import copy
from datetime import datetime
from PySide6.QtCore import Qt, QTimer, QDateTime, QSize
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (QApplication,QDialog,QVBoxLayout,QHBoxLayout,QLabel,QListWidget,
    QListWidgetItem,QPushButton,QComboBox,QCheckBox,QDateTimeEdit,QDoubleSpinBox)
from pesca_catalogo import ESPECIES,LOCAIS,OCORRENCIAS,eligible
from pesca_tempo import LABELS,snapshot
from pesca_offline import schedule,cancel
from pesca_especies_visual import species_image
from pesca_plataforma import mobile


class Page(QDialog):
    def __init__(self,game,title):
        super().__init__(game);self.game=game;self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowStaysOnTopHint,True);self.resize(650,540)
        self.layout=QVBoxLayout(self);self.layout.setContentsMargins(18,18,18,18)
        heading=QLabel(title);heading.setProperty('heading',True);self.layout.addWidget(heading)
    def close_button(self):
        button=QPushButton('Voltar à pescaria');button.clicked.connect(self.accept);self.layout.addWidget(button)


class ColecaoDialog(Page):
    def __init__(self,game):
        super().__init__(game,'Enciclopédia')
        row=QVBoxLayout() if mobile() else QHBoxLayout();self.local=QComboBox();self.period=QComboBox();self.ordem=QComboBox()
        self.local.addItem('Todos os locais',None)
        for id_,m in LOCAIS.items():self.local.addItem(m['nome'],id_)
        self.period.addItem('Todos os períodos',None)
        for id_,name in LABELS.items():self.period.addItem(name,id_)
        self.ordem.addItem('Ordem alfabética','alpha');self.ordem.addItem('Quantidade registrada','count')
        for widget in (self.local,self.period,self.ordem):row.addWidget(widget)
        self.layout.addLayout(row)
        flags=QVBoxLayout() if mobile() else QHBoxLayout();self.agora=QCheckBox('Disponível agora');self.pistas=QCheckBox('Mostrar pistas de desconhecidas')
        flags.addWidget(self.agora);flags.addWidget(self.pistas);self.layout.addLayout(flags)
        self.summary=QLabel();self.layout.addWidget(self.summary)
        body=QVBoxLayout() if mobile() else QHBoxLayout();self.lista=QListWidget();self.lista.setIconSize(QSize(54,36))
        if mobile():self.lista.setMinimumHeight(200)
        self.detail=QLabel();self.detail.setWordWrap(True);self.detail.setTextFormat(Qt.PlainText)
        self.detail.setAlignment(Qt.AlignTop);self.detail.setProperty('panel',True)
        self.detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        body.addWidget(self.lista,1);body.addWidget(self.detail,1);self.layout.addLayout(body,1)
        for w in (self.local,self.period,self.ordem):w.currentIndexChanged.connect(self.refresh)
        for w in (self.agora,self.pistas):w.toggled.connect(self.refresh)
        self.lista.currentItemChanged.connect(self.show_detail)
        self.close_button();self._signature=None
        self.timer=QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(750)
        self.finished.connect(self.timer.stop);self.refresh()

    def poll(self):
        s=self.game.estado;sig=(tuple(s['inventario_por_id'].items()),snapshot(self.game._wall())['periodo_id'],s['local_atual_id'])
        if sig!=self._signature:self._signature=sig;self.refresh()

    def refresh(self,*_):
        current=self.lista.currentItem();selected=current.data(Qt.UserRole) if current else None
        scroll=self.lista.verticalScrollBar().value();inv=self.game.estado['inventario_por_id']
        map_id=self.local.currentData();period_id=self.period.currentData()
        now=snapshot(self.game._wall())['periodo_id'];actual=self.game.estado['local_atual_id']
        visible=[]
        for id_,s in ESPECIES.items():
            count=inv.get(id_,0)
            if count==0 and not self.pistas.isChecked():continue
            occurrences=[o for o in OCORRENCIAS if o['species_id']==id_]
            if map_id:occurrences=[o for o in occurrences if o['map_id']==map_id]
            if period_id:occurrences=[o for o in occurrences if period_id in o['periods']]
            if self.agora.isChecked():occurrences=[o for o in occurrences if now in o['periods'] and o['map_id']==(map_id or actual)]
            if occurrences:visible.append(id_)
        visible.sort(key=lambda id_:((0 if inv.get(id_,0) else 1),
            (-inv.get(id_,0) if self.ordem.currentData()=='count' else ESPECIES[id_]['nome'].casefold()) if inv.get(id_,0) else list(ESPECIES).index(id_)))
        self.lista.blockSignals(True);self.lista.clear();row=0
        for id_ in visible:
            s=ESPECIES[id_];count=inv.get(id_,0)
            item=QListWidgetItem(f"{s['nome']} · {count}" if count else 'Espécie desconhecida · pista')
            item.setData(Qt.UserRole,id_);item.setIcon(QIcon(QPixmap.fromImage(species_image(id_,count==0))))
            self.lista.addItem(item)
            if id_==selected:row=self.lista.count()-1
        if visible:self.lista.setCurrentRow(row)
        self.lista.blockSignals(False);self.lista.verticalScrollBar().setValue(scroll)
        scope=[o['species_id'] for o in OCORRENCIAS if not map_id or o['map_id']==map_id]
        scope=set(scope);global_known=sum(inv.get(id_,0)>0 for id_ in scope)
        regional=self.game.estado['registros_regionais'].get(map_id or actual,{})
        self.summary.setText(f"Coleção global: {global_known}/{len(scope)} · Registros neste local: {sum(regional.values())}\nValor: 1 registro · Raridade: 5 · Curiosidade: 10")
        self.show_detail()

    def show_detail(self,*_):
        item=self.lista.currentItem()
        if item is None:self.detail.setText('Pesque para descobrir espécies. Ative as pistas para explorar a coleção.');return
        id_=item.data(Qt.UserRole);s=ESPECIES[id_];n=self.game.estado['inventario_por_id'].get(id_,0)
        occurrences=[o for o in OCORRENCIAS if o['species_id']==id_]
        places='\n'.join(LOCAIS[o['map_id']]['nome']+': '+', '.join(LABELS[p] for p in o['periods']) for o in occurrences)
        if n==0:
            self.detail.setText('Espécie desconhecida\n\nPista de encontro:\n'+places+'\n\nRegistre um encontro para revelar sua identidade.');return
        local=self.local.currentData() or self.game.estado['local_atual_id']
        regional=self.game.estado['registros_regionais'].get(local,{}).get(id_,0)
        legacy=self.game.estado['legado_sem_contexto'].get(id_,0)
        text=f"{s['nome']}\n{s['cientifico']}\n\nValor: {self.game.fmt_currency(s['valor'])} moedas\n"
        text+=f"Raridade: {s['raridade']}\n" if n>=5 else f'Raridade: faltam {5-n} registros\n'
        text+='\n'+s['curiosidade'] if n>=10 else f'\nCuriosidade: faltam {10-n} registros'
        text+=f'\n\nGlobal: {n} · Aqui: {regional}\nAntigos sem local/horário: {legacy}\n\n{places}'
        verified=s.get('verification',{})
        if n>=10 and verified.get('url'):text+='\n\nFonte: '+verified['url']
        if n>=10 and verified.get('status')=='legado_preservado':text+='\n\nInformação preservada do catálogo anterior.'
        self.detail.setText(text)


class ViajarDialog(Page):
    def __init__(self,game):
        super().__init__(game,'Viajar')
        self.lista=QListWidget()
        for id_,m in LOCAIS.items():
            unlocked=id_ in game.estado['locais_desbloqueados']
            item=QListWidgetItem(m['nome']+(' · disponível' if unlocked else f" · barco Nv {m['nivel_barco']}"))
            item.setData(Qt.UserRole,id_);self.lista.addItem(item)
        self.layout.addWidget(self.lista)
        self.preview=QLabel();self.preview.setAlignment(Qt.AlignCenter);self.layout.addWidget(self.preview)
        self.detail=QLabel();self.detail.setWordWrap(True);self.layout.addWidget(self.detail)
        self.button=QPushButton('Viajar gratuitamente');self.button.clicked.connect(self.go);self.layout.addWidget(self.button)
        self.close_button();self.lista.currentItemChanged.connect(self.refresh);self.lista.setCurrentRow(0)

    def refresh(self,*_):
        item=self.lista.currentItem()
        if not item:return
        id_=item.data(Qt.UserRole);m=LOCAIS[id_];s=self.game.estado
        unlocked=id_ in s['locais_desbloqueados'];self.button.setEnabled(unlocked)
        img,_=self.game._render.render(self.game,map_id=id_)
        width=min(512,QApplication.primaryScreen().availableGeometry().width()-52) if mobile() else 512
        self.preview.setPixmap(QPixmap.fromImage(img.scaled(width,round(width*144/256),Qt.KeepAspectRatio,Qt.FastTransformation)))
        ids={o['species_id'] for o in OCORRENCIAS if o['map_id']==id_}
        known=sum(s['inventario_por_id'].get(x,0)>0 for x in ids)
        regional=sum(s['registros_regionais'].get(id_,{}).get(x,0)>0 for x in ids)
        self.detail.setText(f"{m['nome']} · coleção global {known}/{len(ids)} · regional {regional}/{len(ids)}\n{m['descricao']}\n"+
            ('Desbloqueio permanente. Viagem grátis; fisgadas em andamento terminam no local de origem.' if unlocked else f"Desbloqueia ao atingir barco Nv {m['nivel_barco']}."))

    def go(self):
        if self.game.viajar(self.lista.currentItem().data(Qt.UserRole)):self.accept()


class ExpedicaoDialog(Page):
    def __init__(self,game):
        super().__init__(game,'Expedição offline')
        note=QLabel('A expedição substitui o progresso offline desta ausência.\nFeche o jogo antes do início. Não acorda o computador. Retornar encerra a janela, sem pagar tempo futuro.')
        note.setWordWrap(True);self.layout.addWidget(note)
        self.local=QComboBox()
        for id_ in game.estado['locais_desbloqueados']:self.local.addItem(LOCAIS[id_]['nome'],id_)
        self.layout.addWidget(self.local)
        self.start=QDateTimeEdit(QDateTime.fromSecsSinceEpoch(int(game._wall()+3600)));self.start.setCalendarPopup(True)
        self.start.setDisplayFormat('dd/MM/yyyy HH:mm');self.layout.addWidget(self.start)
        self.hours=QDoubleSpinBox();self.hours.setRange(.25,4);self.hours.setSingleStep(.25);self.hours.setValue(1)
        self.hours.setSuffix(' horas');self.layout.addWidget(self.hours)
        self.status=QLabel();self.status.setWordWrap(True);self.layout.addWidget(self.status)
        button=QPushButton('Agendar');button.clicked.connect(self.plan);self.layout.addWidget(button)
        cancel_button=QPushButton('Cancelar agendamento');cancel_button.clicked.connect(self.cancel_plan);self.layout.addWidget(cancel_button)
        self.close_button();self.refresh()

    def refresh(self):
        plan=self.game.estado.get('expedicao')
        self.status.setText('Nenhuma expedição agendada.' if not plan else
            f"{LOCAIS[plan['map_id']]['nome']} · {plan['status']}\n{datetime.fromtimestamp(plan['inicio_utc']):%d/%m %H:%M} · {plan['duracao']/3600:g} h")
        if plan:
            labels=list(dict.fromkeys(snapshot(plan['inicio_utc']+second)['rotulo'] for second in range(0,int(plan['duracao']),60)))
            self.status.setText(self.status.text()+'\nPeríodos: '+', '.join(labels))

    def plan(self):
        self.game.tick();candidate=copy.deepcopy(self.game.estado)
        try:schedule(candidate,self.local.currentData(),self.start.dateTime().toSecsSinceEpoch(),self.hours.value()*3600,self.game._wall())
        except ValueError as exc:self.status.setText(str(exc));return
        if self.game._commit(candidate):self.refresh()

    def cancel_plan(self):
        candidate=copy.deepcopy(self.game.estado);cancel(candidate)
        if self.game._commit(candidate):self.refresh()
