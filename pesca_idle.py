"""
Pesca Idle - v0.4  (pixel art HD-2D)
Novidades:
  - Visual em pixel art com iluminação estilo HD-2D (brilho da lanterna, reflexos,
    bokeh, vaga-lumes e juncos desfocados em primeiro plano).
  - Menu acessado pelo ícone do baú no canto superior direito (sem botão direito).
  - "Loja" única: upgrades de vara e barco + acessórios cosméticos.

Requisitos:  pip install PySide6
Executar:    python pesca_idle.py        (ou pythonw pesca_idle.py)
"""
import sys
import os
import json
import math
import random
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QRect, QPoint, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QImage, QRadialGradient, QLinearGradient, QBrush, qRgba,
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QMenu, QMessageBox, QDialog, QVBoxLayout,
    QLabel, QTabWidget, QListWidget, QListWidgetItem, QPushButton,
)

# ----------------------------------------------------------------------------
# Configurações (mexa à vontade)
# ----------------------------------------------------------------------------
INTERVALO_PESCA = (10, 20)     # segundos entre uma pesca e outra (vara nível 0)
NIVEL_MAX = 10
LIMITE_OFFLINE = 4 * 3600      # máximo de segundos de progresso offline (4 horas)
SAVE_PATH = Path(os.getenv("APPDATA", str(Path.home()))) / "PescaIdle" / "save.json"

# Tabela de capturas. O peso é relativo: maior peso significa encontro mais
# frequente. Fauna protegida e organismos microscópicos são tratados como
# encontros abstratos do jogo, não como orientação de pesca real.
LOOT = [
    {"nome": "Bota velha", "tipo": "lixo", "valor": 0, "peso": 8},
    # Espécies raras, endêmicas, ameaçadas ou de observação excepcional.
    {"nome": "Tubarão-lagarto", "cientifico": "Chlamydoselachus anguineus", "tipo": "peixe", "valor": 250, "peso": 0.18},
    {"nome": "Vaquita", "cientifico": "Phocoena sinus", "tipo": "peixe", "valor": 5000, "peso": 0.04},
    {"nome": "Celacanto-comorense", "cientifico": "Latimeria chalumnae", "tipo": "peixe", "valor": 2000, "peso": 0.08},
    {"nome": "Peixe-mão-vermelho", "cientifico": "Thymichthys politus", "tipo": "peixe", "valor": 5000, "peso": 0.025},
    {"nome": "Cavalinho-do-mar-pigmeu", "cientifico": "Hippocampus bargibanti", "tipo": "peixe", "valor": 120, "peso": 0.35},
    {"nome": "Lula-magnapinna", "cientifico": "Magnapinna spp.", "tipo": "peixe", "valor": 1800, "peso": 0.05},
    {"nome": "Tubarão-boca-grande", "cientifico": "Megachasma pelagios", "tipo": "peixe", "valor": 800, "peso": 0.10},
    {"nome": "Peixe-ogro", "cientifico": "Anoplogaster cornuta", "tipo": "peixe", "valor": 80, "peso": 0.5},
    {"nome": "Narval", "cientifico": "Monodon monoceros", "tipo": "peixe", "valor": 700, "peso": 0.12},
    {"nome": "Baleia-azul", "cientifico": "Balaenoptera musculus", "tipo": "peixe", "valor": 1000, "peso": 0.10},
    # Fauna de ocorrência moderada a alta, com capturabilidade reduzida.
    {"nome": "Tubarão-branco", "cientifico": "Carcharodon carcharias", "tipo": "peixe", "valor": 250, "peso": 0.20},
    {"nome": "Manta-gigante", "cientifico": "Mobula birostris", "tipo": "peixe", "valor": 180, "peso": 0.30},
    {"nome": "Peixe-lua", "cientifico": "Mola mola", "tipo": "peixe", "valor": 80, "peso": 0.60},
    {"nome": "Garoupa-verdadeira", "cientifico": "Epinephelus marginatus", "tipo": "peixe", "valor": 35, "peso": 1.0},
    {"nome": "Tartaruga-verde", "cientifico": "Chelonia mydas", "tipo": "peixe", "valor": 500, "peso": 0.08},
    {"nome": "Mero-preto", "cientifico": "Epinephelus itajara", "tipo": "peixe", "valor": 90, "peso": 0.40},
    {"nome": "Orca", "cientifico": "Orcinus orca", "tipo": "peixe", "valor": 650, "peso": 0.10},
    {"nome": "Peixe-papagaio-azul", "cientifico": "Scarus coeruleus", "tipo": "peixe", "valor": 8, "peso": 2.0},
    {"nome": "Polvo-comum", "cientifico": "Octopus vulgaris", "tipo": "peixe", "valor": 5, "peso": 2.5},
    {"nome": "Linguado-comum", "cientifico": "Solea solea", "tipo": "peixe", "valor": 4, "peso": 2.0},
    {"nome": "Golfinho-nariz-de-garrafa", "cientifico": "Tursiops truncatus", "tipo": "peixe", "valor": 150, "peso": 0.20},
    {"nome": "Barracuda-grande", "cientifico": "Sphyraena barracuda", "tipo": "peixe", "valor": 10, "peso": 1.7},
    {"nome": "Atum-azul", "cientifico": "Thunnus thynnus", "tipo": "peixe", "valor": 100, "peso": 0.20},
    {"nome": "Peixe-palhaço", "cientifico": "Amphiprion ocellaris", "tipo": "peixe", "valor": 2, "peso": 3.0},
    {"nome": "Lagosta-americana", "cientifico": "Homarus americanus", "tipo": "peixe", "valor": 3, "peso": 2.4},
    {"nome": "Água-viva-juba-de-leão", "cientifico": "Cyanea capillata", "tipo": "peixe", "valor": 1, "peso": 1.0},
    {"nome": "Lula-de-humboldt", "cientifico": "Dosidicus gigas", "tipo": "peixe", "valor": 2, "peso": 1.8},
    {"nome": "Salmão-rosa", "cientifico": "Oncorhynchus gorbuscha", "tipo": "peixe", "valor": 1.5, "peso": 3.0},
    {"nome": "Bacalhau-do-atlântico", "cientifico": "Gadus morhua", "tipo": "peixe", "valor": 2, "peso": 0.8},
    {"nome": "Cavala", "cientifico": "Scomber scombrus", "tipo": "peixe", "valor": 1, "peso": 4.5},
    # Cardumes, espécies de alta biomassa e organismos planctônicos.
    {"nome": "Sardinha-do-pacífico", "cientifico": "Sardinops sagax", "tipo": "peixe", "valor": 0.5, "peso": 7},
    {"nome": "Anchoveta-peruana", "cientifico": "Engraulis ringens", "tipo": "peixe", "valor": 0.25, "peso": 12},
    {"nome": "Arenque-atlântico", "cientifico": "Clupea harengus", "tipo": "peixe", "valor": 0.25, "peso": 9},
    {"nome": "Polaca-do-alasca", "cientifico": "Gadus chalcogrammus", "tipo": "peixe", "valor": 0.3, "peso": 10},
    {"nome": "Camarão-cinza", "cientifico": "Crangon crangon", "tipo": "peixe", "valor": 0.2, "peso": 9},
    {"nome": "Mexilhão-azul", "cientifico": "Mytilus edulis", "tipo": "peixe", "valor": 0.1, "peso": 10},
    {"nome": "Caranguejo-falso", "cientifico": "Munida gregaria", "tipo": "peixe", "valor": 0.15, "peso": 7},
    {"nome": "Calano", "cientifico": "Calanus finmarchicus", "tipo": "peixe", "valor": 0.1, "peso": 10},
    {"nome": "Salpa-antártica", "cientifico": "Salpa thompsoni", "tipo": "peixe", "valor": 0.1, "peso": 8},
    {"nome": "Peixe-lanterna-glaciar", "cientifico": "Benthosema glaciale", "tipo": "peixe", "valor": 0.1, "peso": 9},
    {"nome": "Peixe-lanterna-de-müller", "cientifico": "Maurolicus muelleri", "tipo": "peixe", "valor": 0.1, "peso": 10},
    {"nome": "Krill-do-pacífico", "cientifico": "Euphausia pacifica", "tipo": "peixe", "valor": 0.1, "peso": 9},
    {"nome": "Krill-antártico", "cientifico": "Euphausia superba", "tipo": "peixe", "valor": 0.1, "peso": 12},
    {"nome": "Copépode-comum", "cientifico": "Acartia tonsa", "tipo": "peixe", "valor": 0.1, "peso": 12},
    {"nome": "Peixe-lanterna-comum", "cientifico": "Symbolophorus barnardi", "tipo": "peixe", "valor": 0.1, "peso": 7},
    # Espécies extras comuns em pescarias tropicais e de água doce.
    {"nome": "Lambari", "cientifico": "Astyanax lacustris", "tipo": "peixe", "valor": 0.1, "peso": 8},
    {"nome": "Tilápia-do-nilo", "cientifico": "Oreochromis niloticus", "tipo": "peixe", "valor": 0.2, "peso": 4},
    {"nome": "Tambaqui", "cientifico": "Colossoma macropomum", "tipo": "peixe", "valor": 0.8, "peso": 1.5},
    {"nome": "Pacu", "cientifico": "Piaractus mesopotamicus", "tipo": "peixe", "valor": 0.5, "peso": 1.5},
]

# Cor do casco do barco por nível
CORES_BARCO = [
    (150, 95, 55), (170, 110, 60), (120, 130, 140), (90, 150, 190),
    (200, 170, 70), (210, 90, 90), (140, 90, 190), (60, 170, 130),
    (230, 140, 50), (240, 220, 120), (250, 250, 250),
]

# ----------------------------------------------------------------------------
# Loja de cosméticos: (id, slot, nome, preço em moedas)
# Os itens são apenas visuais e não alteram nada na pescaria.
# ----------------------------------------------------------------------------
SLOTS = {
    "chapeu": "Chapéus",
    "roupa": "Roupas",
    "bandeira": "Bandeiras",
    "boia": "Boias",
    "boneco": "Bonecos",
}

CATALOGO = [
    ("chapeu_palha",    "chapeu",   "Chapéu de palha",    0),
    ("chapeu_nenhum",   "chapeu",   "Sem chapéu",         0),
    ("chapeu_bone",     "chapeu",   "Boné azul",          150),
    ("chapeu_gorro",    "chapeu",   "Gorro de lã",        200),
    ("chapeu_quepe",    "chapeu",   "Quepe de capitão",   500),
    ("chapeu_pirata",   "chapeu",   "Chapéu de pirata",   800),
    ("chapeu_cartola",  "chapeu",   "Cartola",            1200),
    ("chapeu_coroa",    "chapeu",   "Coroa dourada",      5000),
    ("chapeu_pikachu",  "chapeu",   "Gorro do Pikachu",   9999),

    ("roupa_vermelha",  "roupa",    "Camisa vermelha",    0),
    ("roupa_azul",      "roupa",    "Camisa azul",        100),
    ("roupa_verde",     "roupa",    "Colete verde",       250),
    ("roupa_listrada",  "roupa",    "Camisa listrada",    400),
    ("roupa_capa",      "roupa",    "Capa de chuva",      700),
    ("roupa_capitao",   "roupa",    "Casaco de capitão",  1500),
    ("roupa_gala",      "roupa",    "Traje de gala",      3000),

    ("bandeira_nenhum",   "bandeira", "Sem bandeira",       0),
    ("bandeira_vermelha", "bandeira", "Bandeirinha vermelha", 100),
    ("bandeira_brasil",   "bandeira", "Bandeira do Brasil", 300),
    ("bandeira_arco",     "bandeira", "Bandeira arco-íris", 500),
    ("bandeira_pirata",   "bandeira", "Bandeira pirata",    1000),

    ("boia_vermelha",   "boia",     "Boia vermelha",      0),
    ("boia_amarela",    "boia",     "Boia amarela",       100),
    ("boia_listrada",   "boia",     "Boia listrada",      250),
    ("boia_coracao",    "boia",     "Boia coração",       600),
    ("boia_estrela",    "boia",     "Boia estrela",       1500),

    ("boneco_nenhum",     "boneco", "Sem boneco",         0),
    ("boneco_pato",       "boneco", "Patinho de borracha", 300),
    ("boneco_caranguejo", "boneco", "Caranguejo",         700),
    ("boneco_gato",       "boneco", "Gatinho",            1500),
    ("boneco_pinguim",    "boneco", "Pinguim",            3000),
    ("boneco_agumon",     "boneco", "Agumon",             9999),
]
CAT = {c[0]: c for c in CATALOGO}

ESTADO_PADRAO = {
    "moedas": 0,
    "vara": 0,
    "barco": 0,
    "pecas_vara": 0,
    "pecas_barco": 0,
    "total_pescados": 0,
    "inventario": {},
    "conquistas": [],
    "ultimo_salvo": 0,
    "cosmeticos": [
        "chapeu_palha", "chapeu_nenhum", "roupa_vermelha",
        "bandeira_nenhum", "boia_vermelha", "boneco_nenhum",
    ],
    "equipados": {
        "chapeu": "chapeu_palha",
        "roupa": "roupa_vermelha",
        "bandeira": "bandeira_nenhum",
        "boia": "boia_vermelha",
        "boneco": "boneco_nenhum",
    },
}


def fmt_tempo(seg):
    m = int(seg // 60)
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}min" if h else f"{m}min"


def fmt_moedas(valor):
    """Mostra até duas casas decimais usando separadores pt-BR."""
    valor = round(float(valor), 2)
    if valor.is_integer():
        return f"{int(valor):,}".replace(",", ".")
    texto = f"{valor:,.2f}".rstrip("0").rstrip(".")
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


# ============================================================================
# SPRITES (pixel art)
# A cena é desenhada em 120x68 "pixels de arte" e ampliada 2x (sem suavização).
# ============================================================================
ART_W, ART_H = 120, 68
ESCALA = 2
AGUA_Y = 52                      # linha d'água
CASCO_X, CASCO_Y = 12, 46        # canto esquerdo e topo (convés) do casco
MASTRO_X, MASTRO_TOPO = 15, 22
BONECO_X = 18
LANT_X, LANT_Y = 54, 40          # canto da lanterna (5x6)
ROD_ORIGEM = (46, 38)
ROD_PONTA = (100, 20)
BOIA_X = 100
COR_CONTORNO = (36, 28, 48)
COR_LUZ = (255, 198, 120)


def misturar(c1, c2, k):
    return tuple(int(a + (b - a) * k) for a, b in zip(c1[:3], c2[:3]))


def clarear(c, k):
    return misturar(c, (255, 255, 255), k)


def escurecer(c, k):
    return misturar(c, (0, 0, 0), k)


class Camada:
    """Buffer esparso de pixels de arte: {(x, y): (r, g, b[, a])}."""

    def __init__(self):
        self.px = {}

    def ponto(self, x, y, cor):
        self.px[(x, y)] = cor

    def sprite(self, grade, pal, x0, y0):
        for j, linha in enumerate(grade):
            for i, ch in enumerate(linha):
                cor = pal.get(ch)
                if cor is not None:
                    self.px[(x0 + i, y0 + j)] = cor

    def luz_borda(self, cor=COR_LUZ, k=0.38):
        """Luz quente vinda da direita (lanterna): clareia a borda direita."""
        for q in [q for q in self.px if (q[0] + 1, q[1]) not in self.px]:
            c = self.px[q]
            self.px[q] = misturar(c, cor, k) + tuple(c[3:])

    def contorno(self, cor=COR_CONTORNO):
        novos = {}
        for (x, y) in self.px:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in self.px:
                    novos[q] = cor
        self.px.update(novos)

    def para_qimage(self):
        """Retorna (QImage recortada, ox, oy) onde (ox, oy) é a posição do canto."""
        if not self.px:
            img = QImage(1, 1, QImage.Format_ARGB32)
            img.fill(0)
            return img, 0, 0
        xs = [q[0] for q in self.px]
        ys = [q[1] for q in self.px]
        x0, y0 = min(xs), min(ys)
        img = QImage(max(xs) - x0 + 1, max(ys) - y0 + 1, QImage.Format_ARGB32)
        img.fill(0)
        for (x, y), c in self.px.items():
            a = c[3] if len(c) > 3 else 255
            img.setPixel(x - x0, y - y0, qRgba(c[0], c[1], c[2], a))
        return img, x0, y0


# ------------------------------------------------------------------ casco
def montar_casco(nivel):
    cor = CORES_BARCO[min(nivel, len(CORES_BARCO) - 1)]
    claro, escuro = clarear(cor, 0.30), escurecer(cor, 0.35)
    larg, alt = 50, 10
    cam = Camada()
    for x in range(larg):
        t = (x + 0.5) / larg
        s = math.sin(math.pi * t)
        fundo = int(round((alt - 1) - (1 - s) ** 1.2 * alt * 0.9))
        topo = 0
        if t > 0.9:
            topo = -min(3, int((t - 0.9) * 40))
        elif t < 0.05:
            topo = -1
        for yy in range(topo, fundo + 1):
            if yy <= 0:
                c = claro
            elif yy == fundo or yy % 3 == 2:
                c = escuro
            else:
                c = cor
            cam.ponto(CASCO_X + x, CASCO_Y + yy, c)
    cam.luz_borda()
    cam.contorno()
    return cam


# ------------------------------------------------------------- personagem
CABECA = [
    ".HHHHH.",
    "HHHHHHH",
    "HHsssss",
    "Hssssks",
    ".ssssss",
    ".sssdsS",
    "..SSSS.",
]
PAL_CABECA = {
    "H": (112, 66, 38), "s": (246, 205, 160), "S": (214, 160, 118),
    "k": (40, 30, 45), "d": (238, 150, 140),
}

TORSO = [
    ".cccccc.",
    "Cccccccc",
    "Cccccccc",
    "Cccccccc",
    "CCcccccc",
    "CCcccccc",
    "CCCccccc",
    "CCCccccc",
    "CCCCcccc",
    "CCCCCCCC",
]

ARM = [
    "cc......",
    ".ccss...",
    "..ssSs..",
    "....sSs.",
]

LEGS = [
    "pppppppp.......",
    "pppppppppppp...",
    "ppppppppppppbbb",
    "PPPPPPPPPPPPbbb",
]
PAL_LEGS = {"p": (70, 90, 150), "P": (48, 62, 112), "b": (92, 60, 40)}


def _ov(*linhas):
    return list(linhas)


ROUPAS = {
    "roupa_vermelha": {"pal": {"c": (214, 66, 58), "C": (158, 44, 48)}},
    "roupa_azul": {"pal": {"c": (66, 110, 214), "C": (44, 76, 160)}},
    "roupa_verde": {
        "pal": {"c": (72, 160, 92), "C": (48, 112, 68), "w": (240, 240, 245)},
        "overlay": [_ov("........", "...ww...", "...ww...", "...ww...", "...ww...",
                        "...ww...", "...ww...", "...ww...", "........", "........")],
    },
    "roupa_listrada": {
        "pal": {"c": (240, 240, 245), "C": (186, 186, 204), "b": (40, 70, 160)},
        "overlay": [_ov("........", ".bbbbbbb", "........", ".bbbbbbb", "........",
                        ".bbbbbbb", "........", ".bbbbbbb", "........", "........")],
    },
    "roupa_capa": {
        "pal": {"c": (246, 206, 44), "C": (200, 150, 24), "d": (190, 130, 20)},
        "overlay": [_ov(".dddddd.", "....d...", "....d...", "....d...", "....d...",
                        "....d...", "....d...", "....d...", "........", "........")],
    },
    "roupa_capitao": {
        "pal": {"c": (36, 58, 124), "C": (22, 36, 84), "g": (244, 204, 70)},
        "overlay": [_ov("........", "g......g", "..g..g..", "........", "..g..g..",
                        "........", "..g..g..", "........", "........", "........")],
    },
    "roupa_gala": {
        "pal": {"c": (40, 40, 48), "C": (24, 24, 30), "w": (245, 245, 250),
                "r": (214, 50, 56)},
        "overlay": [_ov("........", "..wrrw..", "...ww...", "...ww...", "...w....",
                        "........", "........", "........", "........", "........")],
    },
}

# Chapéus: a última linha fica em y=27 e o centro em x=35 (cabeça em x=32..38)
HATS = {
    "chapeu_palha": (
        ["....yyyyy....", "...yyyyyyy...", "...rrrrrrr...", ".yyyyyyyyyyy.", "YYYYYYYYYYYYY"],
        {"y": (240, 200, 90), "Y": (205, 160, 60), "r": (200, 60, 50)}),
    "chapeu_bone": (
        ["..bbbbbb...", ".bbbbbbbb..", "bbbbbbbbbVV", "BBBBBBBBB.."],
        {"b": (60, 110, 220), "B": (40, 76, 170), "V": (36, 60, 130)}),
    "chapeu_gorro": (
        ["...ww...", "..wwww..", ".pppppp.", "pppppppp", "pppppppp", "wwwwwwww"],
        {"p": (212, 70, 100), "w": (245, 245, 250)}),
    "chapeu_quepe": (
        ["..wwwwwww..", ".wwwwwwwww.", "wwwwwgwwwww", "bbbbbbbbbbb", ".vvvvvvvvvv"],
        {"w": (245, 245, 250), "g": (240, 200, 60), "b": (30, 50, 110), "v": (20, 30, 70)}),
    "chapeu_pirata": (
        [".....kkk.....", "...kkkkkkk...", "..kkkkwkkkk..", ".kkkkwwwkkkk.",
         "kgggggggggggk", ".kkk.....kkk."],
        {"k": (46, 40, 58), "w": (240, 240, 245), "g": (220, 170, 50)}),
    "chapeu_cartola": (
        ["..kkkkkkK..", "..kkkkkkK..", "..kkkkkkK..", "..kkkkkkK..",
         "..rrrrrrr..", "..kkkkkkK..", "kkkkkkkkkkk"],
        {"k": (30, 26, 40), "K": (66, 60, 82), "r": (200, 50, 60)}),
    "chapeu_coroa": (
        ["g.g.g.g.g", "ggggggggg", "gggrgrggg", "GGGGGGGGG"],
        {"g": (250, 205, 60), "G": (200, 150, 30), "r": (220, 50, 70)}),
    "chapeu_pikachu": (
        [".kk.....kk.", ".kk.....kk.", ".yy.....yy.", ".yyy...yyy.", "..yyyyyyy..",
         ".yyyyyyyyy.", "yyyyyyyyyyy", "ryyyyyyyyyr", "YYYYYYYYYYY"],
        {"y": (252, 218, 50), "Y": (226, 180, 30), "k": (34, 28, 32), "r": (232, 70, 60)}),
}


def montar_personagem(roupa_id, chapeu_id):
    cam = Camada()
    cam.sprite(LEGS, PAL_LEGS, 32, 42)
    roupa = ROUPAS.get(roupa_id, ROUPAS["roupa_vermelha"])
    pal = dict(roupa["pal"])
    cam.sprite(TORSO, pal, 32, 32)
    for ov in roupa.get("overlay", []):
        cam.sprite(ov, pal, 32, 32)
    pal_braco = dict(pal)
    pal_braco.update({"s": (246, 205, 160), "S": (214, 160, 118)})
    cam.sprite(ARM, pal_braco, 40, 35)
    cam.sprite(CABECA, PAL_CABECA, 32, 25)
    chapeu = HATS.get(chapeu_id)
    if chapeu:
        grade, pal_h = chapeu
        cam.sprite(grade, pal_h, 35 - len(grade[0]) // 2, 28 - len(grade))
    cam.luz_borda()
    cam.contorno()
    return cam


# --------------------------------------------------------------- bandeiras
_ARCO = ["rrrrrrrrrrrr", "oooooooooooo", "yyyyyyyyyyyy", "gggggggggggg",
         "bbbbbbbbbbbb", "vvvvvvvvvvvv"]
BANDEIRAS = {
    "bandeira_vermelha": (
        ["rrr.........", "rrrrrr......", "rrrrrrrrr...", "rrrrrrrrrrrr",
         "rrrrrrrrr...", "rrrrrr......", "rrr........."],
        {"r": (220, 50, 56)}),
    "bandeira_pirata": (
        ["kkkkkkkkkkkk", "kkkkwwwwkkkk", "kkkwwwwwwkkk", "kkkwkwwkwkkk",
         "kkkwwwwwwkkk", "kkkkwkwkkkkk", "kkkkkkkkkkkk"],
        {"k": (30, 28, 38), "w": (240, 240, 245)}),
    "bandeira_arco": (
        _ARCO,
        {"r": (230, 50, 56), "o": (250, 150, 40), "y": (250, 222, 50),
         "g": (70, 180, 80), "b": (60, 120, 220), "v": (140, 80, 190)}),
    "bandeira_brasil": (
        ["gggggggggggg", "gggggyyggggg", "gggyyyyyyggg", "ggyyybbyyygg",
         "gyyybbbbyyyg", "ggyyybbyyygg", "gggyyyyyyggg", "gggggyyggggg",
         "gggggggggggg"],
        {"g": (40, 150, 70), "y": (250, 215, 40), "b": (40, 70, 170)}),
}


def montar_bandeira(id_, fase):
    cam = Camada()
    for y in range(MASTRO_TOPO, CASCO_Y + 1):
        cam.ponto(MASTRO_X, y, (110, 76, 40))
    cam.ponto(MASTRO_X, MASTRO_TOPO - 1, (244, 204, 70))
    grade, pal = BANDEIRAS[id_]
    for c in range(len(grade[0])):
        amp = 0 if c < 2 else 1
        desl = int(round(math.sin(fase * math.pi / 2 - c * 0.55))) * amp
        for r, linha in enumerate(grade):
            cor = pal.get(linha[c])
            if cor is not None:
                cam.ponto(MASTRO_X + 1 + c, MASTRO_TOPO + r + desl, cor)
    cam.luz_borda()
    cam.contorno()
    return cam


# ----------------------------------------------------------------- bonecos
BONECOS = {
    "boneco_pato": (
        [".......yyy..", "......yyyyyo", "......yykyoo", ".......yyy..",
         "yy..yyyyyy..", "yyyyyyyyyyy.", ".yyyyyyyyyy.", ".YyyyyyyyyY.",
         "..YYYYYYYY.."],
        {"y": (252, 220, 56), "Y": (222, 176, 34), "o": (240, 132, 32), "k": (34, 28, 32)}),
    "boneco_gato": (
        [".g......g.", ".gg....gg.", ".gggggggg.", ".ggkggkgg.", ".ggggpggg.",
         "..gggggg..", ".gggggggg.", "gggggggggg", "gGgggggGgg", "gGGggggGGg",
         ".gwg..gwg."],
        {"g": (156, 156, 172), "G": (116, 116, 134), "k": (30, 24, 34),
         "p": (238, 140, 150), "w": (236, 236, 244)}),
    "boneco_caranguejo": (
        ["rr.......rr", "rrr.w.w.rrr", ".rr.k.k.rr.", "..rrrrrrr..",
         ".rrrrrrrrr.", "..RRRRRRR..", ".r.r...r.r."],
        {"r": (216, 66, 52), "R": (160, 42, 42), "w": (245, 245, 250), "k": (30, 24, 34)}),
    "boneco_pinguim": (
        ["..kkkk..", ".kkkkkk.", ".kkwkwk.", ".kkkkkoo", "kkkwwwkk", "kkwwwwwk",
         "kkwwwwwk", "kkwwwwwk", ".kkwwwk.", ".kkkkkk.", "..oo.oo."],
        {"k": (44, 44, 66), "w": (240, 240, 245), "o": (240, 150, 40)}),
    "boneco_agumon": (
        ["...oooooo...", "..oooooooo..", ".oooooooooo.", ".oowgoowgoo.",
         ".oowgoowgoo.", ".oooooooooo.", ".ooowwwwooo.", "..oooooooo..",
         "..ooccccoo..", "..occccccoo.", "..occccccoo.", "..oooooooo..",
         "..ww....ww.."],
        {"o": (250, 140, 30), "c": (255, 226, 150), "w": (245, 245, 250),
         "g": (40, 170, 90)}),
}


def montar_boneco(id_):
    cam = Camada()
    grade, pal = BONECOS[id_]
    cam.sprite(grade, pal, BONECO_X, CASCO_Y - len(grade))
    cam.luz_borda()
    cam.contorno()
    return cam


# ------------------------------------------------------------------- boias
BOIAS = {
    "boia_vermelha": (
        ["..w..", ".rrr.", "rrrrr", "rrrrr", "wwwww", ".www."],
        {"r": (230, 50, 56), "w": (246, 246, 250)}),
    "boia_amarela": (
        ["..w..", ".yyy.", "yyyyy", "yyyyy", "wwwww", ".www."],
        {"y": (250, 210, 44), "w": (246, 246, 250)}),
    "boia_listrada": (
        ["..w..", ".rrr.", "wwwww", "rrrrr", "wwwww", ".rrr."],
        {"r": (230, 50, 56), "w": (246, 246, 250)}),
    "boia_coracao": (
        [".pp.pp.", "ppppppp", "ppppppp", ".ppppp.", "..ppp..", "...p..."],
        {"p": (240, 90, 150)}),
    "boia_estrela": (
        ["...y...", "...y...", "yyyyyyy", ".yyyyy.", "..yyy..", ".yy.yy.", ".y...y."],
        {"y": (250, 204, 44)}),
}


def montar_boia(id_):
    grade, pal = BOIAS.get(id_, BOIAS["boia_vermelha"])
    cam = Camada()
    cam.sprite(grade, pal, -(len(grade[0]) // 2), -(len(grade) // 2))
    cam.contorno()
    return cam


# --------------------------------------------------- lanterna, ícone e juncos
def montar_lanterna():
    cam = Camada()
    grade = ["..m..", ".mmm.", "kgggk", "kgwgk", "kgggk", "mmmmm"]
    pal = {"m": (120, 108, 120), "k": (60, 44, 36), "g": (255, 214, 120),
           "w": (255, 247, 205)}
    cam.sprite(grade, pal, LANT_X, LANT_Y)
    cam.contorno()
    return cam


def montar_bau(hover):
    cam = Camada()
    grade = [".kkkkkkkk.", "kbbbbbbbbk", "kBBBBBBBBk", "kkkkggkkkk",
             "kbbbggbbbk", "kbbbbbbbbk", "kBBBBBBBBk", ".kkkkkkkk."]
    madeira = (206, 140, 76) if hover else (176, 112, 56)
    pal = {"k": (36, 26, 30), "b": madeira, "B": escurecer(madeira, 0.25),
           "g": (255, 220, 90) if hover else (250, 206, 70)}
    cam.sprite(grade, pal, 0, 0)
    return cam


def montar_juncos(larg, alt, caules):
    cam = Camada()
    for x, altura, incl in caules:
        for i in range(altura):
            xx = x + int(incl * i / max(altura, 1))
            cor = (74, 150, 96) if i % 4 == 0 else (30, 84, 62)
            cam.ponto(xx, alt - 1 - i, cor)
        if altura > 7:
            xt = x + int(incl)
            for j in range(3):
                cam.ponto(xt, alt - altura - j, (120, 76, 44))
    return cam


JUNCOS_ESQ = [(1, 9, 2), (3, 6, 1), (5, 10, 3), (7, 5, 1), (9, 8, -1), (11, 4, 0)]
JUNCOS_DIR = [(1, 7, 1), (3, 10, -2), (5, 5, 0), (7, 8, -1)]

# Brilhos fixos na água e pontos de luz (coordenadas em pixels de arte / tela)
FAISCAS = [(10, 56), (30, 60), (48, 57), (70, 61), (88, 56), (104, 64), (80, 58), (22, 64)]
BOKEH = [(28, 30, 9), (176, 26, 12), (150, 96, 7), (60, 100, 6)]
VAGALUMES = [(70, 46), (160, 58), (24, 78)]

# ============================================================================
# === JOGO (Qt) ==============================================================
# ============================================================================


class LojaDialog(QDialog):
    def __init__(self, jogo):
        super().__init__(None, Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.jogo = jogo
        self.setWindowTitle("Loja")
        self.setFixedSize(470, 440)

        lay = QVBoxLayout(self)
        self.lbl_moedas = QLabel()
        self.lbl_moedas.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_moedas)

        self.abas = QTabWidget()

        # --- aba Equipamento (upgrades de vara e barco)
        self.tab_equip = QWidget()
        le = QVBoxLayout(self.tab_equip)
        self.equip = {}
        info = (
            ("vara", "Vara de pesca",
             "Pesca mais rápido e aumenta a chance de peixes raros.",
             "Comprar peça de vara"),
            ("barco", "Barco", "Aumenta o valor das moedas de cada peixe.",
             "Comprar tábua de barco"),
        )
        for tipo, titulo, desc, botao in info:
            lbl = QLabel()
            lbl.setWordWrap(True)
            btn = QPushButton()
            btn.clicked.connect(lambda _=False, t=tipo: self.comprar(t))
            le.addWidget(lbl)
            le.addWidget(btn)
            le.addSpacing(14)
            self.equip[tipo] = (lbl, btn, titulo, desc, botao)
        le.addStretch(1)
        self.abas.addTab(self.tab_equip, "Equipamento")

        # --- abas de cosméticos
        self.listas = {}
        for slot, titulo in SLOTS.items():
            lista = QListWidget()
            lista.currentItemChanged.connect(self.ao_selecionar)
            self.listas[slot] = lista
            self.abas.addTab(lista, titulo)
        self.abas.currentChanged.connect(self.ao_selecionar)
        lay.addWidget(self.abas)

        self.dica = QLabel("Selecione um item para experimentá-lo no barco. "
                           "Os acessórios são apenas visuais.")
        self.dica.setWordWrap(True)
        lay.addWidget(self.dica)

        self.btn = QPushButton("Comprar")
        self.btn.clicked.connect(self.acao)
        lay.addWidget(self.btn)

        self.preencher()
        self.atualizar_moedas()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_moedas)
        self.timer.start(500)

        geo = QApplication.primaryScreen().availableGeometry()
        x = max(geo.x(), jogo.x() - self.width() - 10)
        y = geo.y() + geo.height() - self.height() - 10
        self.move(x, y)
        self.finished.connect(self.ao_fechar)

    # ---- equipamento
    def comprar(self, tipo):
        self.jogo.comprar_peca(tipo)
        self.atualizar_moedas()

    def atualizar_equipamento(self):
        e = self.jogo.estado
        for tipo, (lbl, btn, titulo, desc, botao) in self.equip.items():
            nivel = e[tipo]
            if nivel >= NIVEL_MAX:
                lbl.setText(f"<b>{titulo}</b> — Nv {nivel} (máximo)<br>{desc}")
                btn.setText("Nível máximo")
                btn.setEnabled(False)
            else:
                custo = self.jogo.custo_peca(tipo)
                lbl.setText(
                    f'<b>{titulo}</b> — Nv {nivel}  '
                    f'(peças {e["pecas_" + tipo]}/{self.jogo.pecas_necessarias(tipo)})'
                    f'<br>{desc}')
                btn.setText(f"{botao} ({custo} moedas)")
                btn.setEnabled(e["moedas"] >= custo)

    # ---- cosméticos
    def slot_atual(self):
        idx = self.abas.currentIndex()
        return None if idx == 0 else list(SLOTS)[idx - 1]

    def id_atual(self):
        slot = self.slot_atual()
        if slot is None:
            return None
        item = self.listas[slot].currentItem()
        return item.data(Qt.UserRole) if item else None

    def preencher(self):
        e = self.jogo.estado
        for slot, lista in self.listas.items():
            atual = lista.currentRow()
            lista.blockSignals(True)
            lista.clear()
            linha_equipada = 0
            for id_, s, nome, preco in CATALOGO:
                if s != slot:
                    continue
                if e["equipados"][slot] == id_:
                    status = "✔ equipado"
                    linha_equipada = lista.count()
                elif id_ in e["cosmeticos"]:
                    status = "comprado"
                else:
                    status = f"{preco} moedas"
                it = QListWidgetItem(f"{nome}  —  {status}")
                it.setData(Qt.UserRole, id_)
                lista.addItem(it)
            lista.setCurrentRow(atual if atual >= 0 else linha_equipada)
            lista.blockSignals(False)
        self.ao_selecionar()

    def ao_selecionar(self, *_):
        self.jogo.previa = {}
        id_ = self.id_atual()
        if id_:
            self.jogo.previa[self.slot_atual()] = id_
        self.atualizar_botao()
        self.jogo.update()

    def atualizar_botao(self):
        e = self.jogo.estado
        slot = self.slot_atual()
        cosmetico = slot is not None
        self.btn.setVisible(cosmetico)
        self.dica.setVisible(cosmetico)
        id_ = self.id_atual()
        if not id_:
            self.btn.setEnabled(False)
            return
        if e["equipados"][slot] == id_:
            self.btn.setText("Equipado")
            self.btn.setEnabled(False)
        elif id_ in e["cosmeticos"]:
            self.btn.setText("Equipar")
            self.btn.setEnabled(True)
        else:
            preco = CAT[id_][3]
            self.btn.setText(f"Comprar e equipar ({preco} moedas)")
            self.btn.setEnabled(e["moedas"] >= preco)

    def atualizar_moedas(self):
        self.lbl_moedas.setText(
            f'Suas moedas: {fmt_moedas(self.jogo.estado["moedas"])}')
        self.atualizar_equipamento()
        self.atualizar_botao()

    def acao(self):
        e = self.jogo.estado
        id_ = self.id_atual()
        if not id_:
            return
        slot = self.slot_atual()
        if id_ not in e["cosmeticos"]:
            preco = CAT[id_][3]
            if e["moedas"] < preco:
                return
            e["moedas"] -= preco
            e["cosmeticos"].append(id_)
            self.jogo.verificar_conquistas()
        e["equipados"][slot] = id_
        self.jogo.salvar()
        self.jogo.atualizar_tooltip()
        self.preencher()
        self.atualizar_moedas()

    def ao_fechar(self, *_):
        self.jogo.previa = {}
        self.jogo.update()


class JogoPesca(QWidget):
    W, H = ART_W * ESCALA, ART_H * ESCALA
    DURACAO_POPUP = 3.5
    ICONE_X, ICONE_Y = 216, 6

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setFixedSize(self.W, self.H)

        self.estado = self.carregar()
        self.previa = {}             # itens em teste na loja (não comprados)
        self.fase = 0.0
        self.pausado = False
        self.fisgando = 0.0
        self.popup = None            # [texto, cor, tempo_restante]
        self.hover = False
        self._cache = {}
        self.rect_icone = QRect(self.ICONE_X - 5, self.ICONE_Y - 4, 30, 26)
        self.fonte = QFont("Consolas", 9, QFont.Bold)
        self.fonte.setStyleStrategy(QFont.NoAntialias)

        # Progresso offline: calculado antes de começar a pescar
        resumo = self.simular_offline()
        self.verificar_conquistas()
        self.salvar()
        self.espera = self.nova_espera()
        self.ultimo_tick = time.monotonic()

        self.posicionar()
        self.atualizar_tooltip()

        self.relogio = QTimer(self)
        self.relogio.timeout.connect(self.tick)
        self.relogio.start(66)       # ~15 fps (visual pixel art, leve na CPU)

        self.timer_pos = QTimer(self)
        self.timer_pos.timeout.connect(self.posicionar)
        self.timer_pos.start(5000)

        self.timer_save = QTimer(self)
        self.timer_save.timeout.connect(self.salvar)
        self.timer_save.start(30000)

        if resumo:
            QTimer.singleShot(800, lambda: self.caixa("Pesca Idle", resumo))

    # ------------------------------------------------------------------ save
    def carregar(self):
        estado = json.loads(json.dumps(ESTADO_PADRAO))
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                estado.update(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        for slot, padrao in ESTADO_PADRAO["equipados"].items():
            estado["equipados"].setdefault(slot, padrao)
        for id_ in ESTADO_PADRAO["cosmeticos"]:
            if id_ not in estado["cosmeticos"]:
                estado["cosmeticos"].append(id_)
        estado.setdefault("conquistas", [])
        return estado

    def salvar(self):
        self.estado["ultimo_salvo"] = time.time()
        try:
            SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.estado, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ------------------------------------------------------------- posição
    def posicionar(self):
        geo = QApplication.primaryScreen().availableGeometry()
        x = geo.x() + geo.width() - self.width()
        y = geo.y() + geo.height() - self.height()
        self.move(x, y)
        self.raise_()

    # ---------------------------------------------------------- lógica do jogo
    def nova_espera(self):
        lo, hi = INTERVALO_PESCA
        base = random.uniform(lo, hi)
        return base / (1 + 0.15 * self.estado["vara"])

    def tick(self):
        agora = time.monotonic()
        dt = min(agora - self.ultimo_tick, 0.5)
        self.ultimo_tick = agora
        self.fase += dt

        if not self.pausado:
            if self.fisgando > 0:
                self.fisgando -= dt
                if self.fisgando <= 0:
                    r = self.sortear()
                    self.mostrar_popup(r["texto"], r["cor"])
                    self.salvar()
                    self.atualizar_tooltip()
                    self.espera = self.nova_espera()
            else:
                self.espera -= dt
                if self.espera <= 0:
                    self.fisgando = 1.5

        if self.popup:
            self.popup[2] -= dt
            if self.popup[2] <= 0:
                self.popup = None

        self.update()

    def mostrar_popup(self, texto, cor="#ffffff"):
        self.popup = [texto, cor, self.DURACAO_POPUP]

    def pecas_necessarias(self, tipo):
        return 2 + self.estado[tipo]

    def aplicar_upgrade(self, tipo):
        """Troca peças acumuladas por níveis. Retorna True se subiu de nível."""
        e = self.estado
        subiu = False
        while (e["pecas_" + tipo] >= self.pecas_necessarias(tipo)
               and e[tipo] < NIVEL_MAX):
            e["pecas_" + tipo] -= self.pecas_necessarias(tipo)
            e[tipo] += 1
            subiu = True
        if subiu:
            self.verificar_conquistas()
        return subiu

    def sortear(self):
        """Faz uma pescaria, aplica o resultado no estado e descreve o que houve."""
        e = self.estado
        pesos = []
        for item in LOOT:
            p = item["peso"]
            if item["valor"] >= 25:          # vara melhor => mais chance de raros
                p *= 1 + 0.15 * e["vara"]
            pesos.append(p)
        item = random.choices(LOOT, weights=pesos)[0]

        tipo = item["tipo"]
        r = {"tipo": tipo, "texto": "", "cor": "#ffffff"}
        if tipo == "peixe":
            ganho = round(item["valor"] * (1 + 0.2 * e["barco"]), 2)
            e["moedas"] += ganho
            e["total_pescados"] += 1
            e["inventario"][item["nome"]] = e["inventario"].get(item["nome"], 0) + 1
            self.verificar_conquistas()
            r["texto"] = f'{item["nome"]}  +{fmt_moedas(ganho)} moedas'
            r["cor"] = "#ffd54f" if item["valor"] >= 25 else "#ffffff"
        elif tipo == "lixo":
            r["texto"] = f'{item["nome"]}... nada de útil'
            r["cor"] = "#b0b0b0"
        return r

    def simular_offline(self):
        """Simula as pescarias do tempo em que o jogo ficou fechado (máx. 4h).
        Retorna o texto do resumo, ou None se não houver o que mostrar."""
        e = self.estado
        ultimo = e.get("ultimo_salvo", 0)
        if not ultimo:
            return None
        ausente = time.time() - ultimo
        if ausente < 60:
            return None
        tempo = min(ausente, LIMITE_OFFLINE)

        vara0, barco0, moedas0 = e["vara"], e["barco"], e["moedas"]
        pescas = 0
        t = self.nova_espera() + 1.5
        while t <= tempo:
            self.sortear()
            pescas += 1
            t += self.nova_espera() + 1.5

        linhas = ["Bem-vindo de volta!", ""]
        contado = f"Tempo contado: {fmt_tempo(tempo)}"
        if ausente > LIMITE_OFFLINE:
            contado += f" (limite de {fmt_tempo(LIMITE_OFFLINE)})"
        linhas.append(contado)
        linhas.append(f"Pescarias: {pescas}")
        linhas.append(f'Moedas ganhas: +{fmt_moedas(e["moedas"] - moedas0)}')
        if e["vara"] > vara0:
            linhas.append(f'Vara: Nv {vara0} → Nv {e["vara"]}')
        if e["barco"] > barco0:
            linhas.append(f'Barco: Nv {barco0} → Nv {e["barco"]}')
        return "\n".join(linhas)

    def custo_peca(self, tipo):
        return 30 + 20 * self.estado[tipo]

    def comprar_peca(self, tipo):
        e = self.estado
        nome = "Vara" if tipo == "vara" else "Barco"
        if e[tipo] >= NIVEL_MAX:
            self.mostrar_popup(f"{nome} já está no nível máximo", "#80d8ff")
            return
        custo = self.custo_peca(tipo)
        if e["moedas"] < custo:
            self.mostrar_popup("Moedas insuficientes", "#ff8080")
            return
        e["moedas"] -= custo
        e["pecas_" + tipo] += 1
        if self.aplicar_upgrade(tipo):
            self.mostrar_popup(f"{nome} melhorada! Nv {e[tipo]}", "#80ff80")
        else:
            self.mostrar_popup(
                f'Peça comprada ({e["pecas_" + tipo]}/{self.pecas_necessarias(tipo)})',
                "#80d8ff")
        self.salvar()
        self.atualizar_tooltip()

    def atualizar_tooltip(self):
        e = self.estado
        self.setToolTip(
            f'Moedas: {fmt_moedas(e["moedas"])}  |  Vara Nv {e["vara"]}  |  Barco Nv {e["barco"]}'
        )

    def verificar_conquistas(self):
        e = self.estado
        definicoes = [
            ("vestir_todos", "Temos que vestir todos!", "Compre o Gorro do Pikachu na loja.", "chapeu_pikachu" in e["cosmeticos"]),
            ("criatura_digital", "Criatura Digital.", "Compre o Boneco Agumon na loja.", "boneco_agumon" in e["cosmeticos"]),
            ("rei_pesca", "Rei da pesca.", "Registre todas as espécies aquáticas pelo menos uma vez.", all(e["inventario"].get(i["nome"], 0) > 0 for i in LOOT if i["tipo"] == "peixe")),
            ("mestre_vara", "Mestre da vara.", "Coloque a vara de pesca no nível máximo.", e["vara"] >= NIVEL_MAX),
            ("mestre_barco", "Mestre do barco.", "Coloque o barco de pesca no nível máximo.", e["barco"] >= NIVEL_MAX),
            ("rei_piratas", "Rei dos piratas?", "Compre todos os itens de pirata na loja.", all(i[0] in e["cosmeticos"] for i in CATALOGO if "pirata" in i[0])),
        ]
        novos = []
        for id_, titulo, descricao, concluiu in definicoes:
            if concluiu and id_ not in e["conquistas"]:
                e["conquistas"].append(id_)
                novos.append(titulo)
        if novos:
            self.salvar()
            self.mostrar_popup(f"Conquista desbloqueada: {novos[0]}", "#ffe27a")

    def mostrar_conquistas(self):
        self.verificar_conquistas()
        e = self.estado
        definicoes = [
            ("vestir_todos", "Temos que vestir todos!", "Compre o Gorro do Pikachu na loja."),
            ("criatura_digital", "Criatura Digital.", "Compre o Boneco Agumon na loja."),
            ("rei_pesca", "Rei da pesca.", "Registre todas as espécies aquáticas pelo menos uma vez."),
            ("mestre_vara", "Mestre da vara.", "Coloque a vara de pesca no nível máximo."),
            ("mestre_barco", "Mestre do barco.", "Coloque o barco de pesca no nível máximo."),
            ("rei_piratas", "Rei dos piratas?", "Compre todos os itens de pirata na loja."),
        ]
        linhas = [f'{"🏆" if id_ in e["conquistas"] else "○"} {titulo}\n   {descricao}' for id_, titulo, descricao in definicoes]
        self.caixa("Achievements", "\n\n".join(linhas))

    def equipado(self, slot):
        return self.previa.get(slot, self.estado["equipados"][slot])

    # ---------------------------------------------------------- menu (ícone)
    def mouseMoveEvent(self, ev):
        sobre = self.rect_icone.contains(ev.position().toPoint())
        if sobre != self.hover:
            self.hover = sobre
            self.update()
        self.setToolTip("Menu" if sobre else self._texto_tooltip())

    def leaveEvent(self, ev):
        if self.hover:
            self.hover = False
            self.update()

    def mousePressEvent(self, ev):
        if (ev.button() == Qt.LeftButton
                and self.rect_icone.contains(ev.position().toPoint())):
            self.abrir_menu()

    def _texto_tooltip(self):
        e = self.estado
        return (f'Moedas: {fmt_moedas(e["moedas"])}  |  Vara Nv {e["vara"]}  |  '
                f'Barco Nv {e["barco"]}')

    def abrir_menu(self):
        m = QMenu(self)
        m.addAction("Loja", self.abrir_loja)
        m.addAction("Status e inventário", self.mostrar_status)
        m.addAction("Achievements", self.mostrar_conquistas)
        m.addSeparator()
        m.addAction("Retomar" if self.pausado else "Pausar", self.alternar_pausa)
        m.addAction("Sair", self.sair)
        m.exec(self.mapToGlobal(QPoint(self.rect_icone.left(), self.rect_icone.bottom())))

    def alternar_pausa(self):
        self.pausado = not self.pausado

    def abrir_loja(self):
        dlg = LojaDialog(self)
        dlg.exec()
        self.previa = {}
        self.update()

    def caixa(self, titulo, texto):
        m = QMessageBox(None)
        m.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        m.setWindowTitle(titulo)
        m.setText(texto)
        m.setIcon(QMessageBox.Information)
        m.exec()

    def mostrar_status(self):
        e = self.estado
        inv = "\n".join(f"  {n}: {q}" for n, q in sorted(e["inventario"].items())) or "  (vazio)"
        texto = (
            f'Moedas: {fmt_moedas(e["moedas"])}\n'
            f'Vara: Nv {e["vara"]}  (peças {e["pecas_vara"]}/{self.pecas_necessarias("vara")})\n'
            f'Barco: Nv {e["barco"]}  (tábuas {e["pecas_barco"]}/{self.pecas_necessarias("barco")})\n'
            f'Total pescado: {e["total_pescados"]}\n\n'
            f'Espécies registradas:\n{inv}'
        )
        self.caixa("Pesca Idle", texto)

    def sair(self):
        self.salvar()
        QApplication.quit()

    # --------------------------------------------------------------- desenho
    def sprite(self, chave, construtor):
        if chave not in self._cache:
            self._cache[chave] = construtor().para_qimage()
        return self._cache[chave]

    @staticmethod
    def blit(sp, spr, x=0, y=0):
        img, ox, oy = spr
        sp.drawImage(x + ox, y + oy, img)

    def desenhar_cena(self):
        """Desenha a cena em pixels de arte (120x68) e devolve a QImage."""
        f = self.fase
        e = self.estado
        dy = int(round(0.5 + 0.5 * math.sin(f * 1.4)))   # balanço do barco (0 ou 1)

        cena = QImage(ART_W, ART_H, QImage.Format_ARGB32_Premultiplied)
        cena.fill(Qt.transparent)
        sp = QPainter(cena)

        # Céu de entardecer e silhuetas distantes para dar profundidade HD-2D.
        ceu = QLinearGradient(0, 0, 0, AGUA_Y)
        ceu.setColorAt(0.0, QColor(27, 32, 67, 238))
        ceu.setColorAt(0.55, QColor(81, 63, 99, 226))
        ceu.setColorAt(1.0, QColor(220, 132, 103, 214))
        sp.fillRect(0, 0, ART_W, AGUA_Y, QBrush(ceu))
        sp.setPen(Qt.NoPen)
        sp.setBrush(QColor(37, 49, 76, 230))
        sp.drawEllipse(-24, 27, 82, 33)
        sp.drawEllipse(24, 31, 75, 27)
        sp.setBrush(QColor(48, 55, 82, 220))
        sp.drawEllipse(73, 29, 72, 31)
        sp.drawEllipse(104, 33, 56, 25)

        # barco e tudo que está nele
        self.blit(sp, self.sprite(("casco", e["barco"]),
                                  lambda: montar_casco(e["barco"])), 0, dy)
        band = self.equipado("bandeira")
        if band in BANDEIRAS:
            fase = int(f * 3) % 4
            self.blit(sp, self.sprite(("bandeira", band, fase),
                                      lambda: montar_bandeira(band, fase)), 0, dy)
        bon = self.equipado("boneco")
        if bon in BONECOS:
            self.blit(sp, self.sprite(("boneco", bon), lambda: montar_boneco(bon)), 0, dy)
        self.blit(sp, self.sprite("lanterna", montar_lanterna), 0, dy)
        roupa, chapeu = self.equipado("roupa"), self.equipado("chapeu")
        self.blit(sp, self.sprite(("pers", roupa, chapeu),
                                  lambda: montar_personagem(roupa, chapeu)), 0, dy)

        # vara, linha e boia
        tremor = int(round(1.5 * math.sin(f * 20))) if self.fisgando > 0 else 0
        ponta_y = ROD_PONTA[1] + tremor + dy
        sp.setPen(QPen(QColor(122, 84, 44), 1))
        sp.drawLine(ROD_ORIGEM[0], ROD_ORIGEM[1] + dy, ROD_PONTA[0], ponta_y)
        mergulho = int(3 * abs(math.sin(f * 14))) if self.fisgando > 0 else 0
        boia_y = AGUA_Y + int(round(math.sin(f * 2 + 1))) + mergulho
        sp.setPen(QPen(QColor(235, 235, 240, 190), 1))
        sp.drawLine(BOIA_X, ponta_y, BOIA_X, boia_y - 3)
        boia = self.equipado("boia")
        self.blit(sp, self.sprite(("boia", boia), lambda: montar_boia(boia)), BOIA_X, boia_y)

        # água (camadas translúcidas por cima do casco e da boia)
        topos = [AGUA_Y + int(round(math.sin(x * 0.45 + f * 2.0))) for x in range(ART_W)]
        cor_agua = QColor(58, 140, 214, 205)
        for x, topo in enumerate(topos):
            sp.fillRect(x, topo, 1, ART_H - topo, cor_agua)
        sp.fillRect(0, 58, ART_W, 5, QColor(28, 92, 170, 95))
        sp.fillRect(0, 63, ART_W, 5, QColor(18, 56, 124, 120))
        crista = QColor(170, 225, 255, 230)
        for x, topo in enumerate(topos):
            sp.fillRect(x, topo, 1, 1, crista)

        # reflexo da lanterna na água
        for i, yy in enumerate(range(AGUA_Y + 3, AGUA_Y + 15, 2)):
            desl = int(round(1.3 * math.sin(yy * 0.8 + f * 3)))
            larg = max(1, 5 - i // 2)
            sp.fillRect(LANT_X + 2 - larg // 2 + desl, yy + dy, larg, 1,
                        QColor(255, 204, 120, max(30, 150 - i * 20)))

        # faíscas na água
        for k, (sx, sy) in enumerate(FAISCAS):
            ph = (f * 0.7 + k * 0.31) % 1.0
            if ph < 0.35:
                sp.fillRect(sx, sy, 1, 1, QColor(255, 255, 255, 210))
                if 0.1 < ph < 0.25:
                    sp.fillRect(sx - 1, sy, 1, 1, QColor(255, 255, 255, 110))
                    sp.fillRect(sx + 1, sy, 1, 1, QColor(255, 255, 255, 110))
        sp.end()
        return cena, dy

    def paintEvent(self, _):
        f = self.fase
        cena, dy = self.desenhar_cena()

        p = QPainter(self)
        p.drawImage(QRect(0, 0, self.W, self.H), cena)   # ampliação sem suavização
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)

        # brilho (bloom) quente da lanterna, com leve tremulação
        flick = 0.82 + 0.18 * math.sin(f * 6.3) * math.sin(f * 2.7 + 1)
        cx, cy = (LANT_X + 2.5) * ESCALA, (LANT_Y + 3) * ESCALA + dy * ESCALA
        g = QRadialGradient(QPointF(cx, cy), 40)
        g.setColorAt(0.0, QColor(255, 205, 120, int(95 * flick)))
        g.setColorAt(0.35, QColor(255, 170, 80, int(40 * flick)))
        g.setColorAt(1.0, QColor(255, 140, 50, 0))
        p.setCompositionMode(QPainter.CompositionMode_Plus)
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), 40, 40)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # bokeh: discos de luz fora de foco
        for k, (bx, by, r) in enumerate(BOKEH):
            x = bx + 5 * math.sin(f * 0.3 + k * 1.7)
            y = by + 3 * math.cos(f * 0.25 + k * 2.3)
            p.setBrush(QColor(255, 232, 190, 22))
            p.setPen(QPen(QColor(255, 244, 214, 44), 1))
            p.drawEllipse(QPointF(x, y), r, r)
        p.setPen(Qt.NoPen)

        # vaga-lumes
        for k, (bx, by) in enumerate(VAGALUMES):
            x = bx + 7 * math.sin(f * 0.6 + k * 2.1)
            y = by + 4 * math.sin(f * 0.8 + k * 1.3)
            a = 0.5 + 0.5 * math.sin(f * 2.2 + k * 1.7)
            gv = QRadialGradient(QPointF(x, y), 8)
            gv.setColorAt(0.0, QColor(255, 244, 160, int(120 * a)))
            gv.setColorAt(1.0, QColor(255, 244, 160, 0))
            p.setBrush(QBrush(gv))
            p.drawEllipse(QPointF(x, y), 8, 8)
            p.fillRect(int(x) // 2 * 2, int(y) // 2 * 2, 2, 2,
                       QColor(255, 246, 180, int(200 * a) + 40))

        # juncos desfocados em primeiro plano (profundidade de campo)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        p.setOpacity(0.85)
        esq, ox, oy = self.sprite("juncos_esq", lambda: montar_juncos(14, 12, JUNCOS_ESQ))
        p.drawImage(QRect(ox * 3, self.H - 12 * 3 + oy * 3, esq.width() * 3, esq.height() * 3), esq)
        dire, ox, oy = self.sprite("juncos_dir", lambda: montar_juncos(10, 11, JUNCOS_DIR))
        p.drawImage(QRect(self.W - 10 * 3 + ox * 3, self.H - 11 * 3 + oy * 3,
                          dire.width() * 3, dire.height() * 3), dire)
        p.setOpacity(1.0)
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)

        # popup do que foi pescado
        if self.popup:
            texto, cor, restante = self.popup
            prog = 1 - restante / self.DURACAO_POPUP
            y = int(30 - 16 * prog)
            alpha = 255 if restante > 0.8 else int(255 * restante / 0.8)
            p.setFont(self.fonte)
            largura = p.fontMetrics().horizontalAdvance(texto) + 16
            x = (self.W - largura) // 2
            p.setBrush(QColor(20, 16, 34, int(alpha * 0.82)))
            p.setPen(QPen(QColor(255, 255, 255, int(alpha * 0.35)), 1))
            p.drawRect(x, y - 12, largura, 22)
            p.setPen(QColor(0, 0, 0, int(alpha * 0.7)))
            p.drawText(x + 1, y - 12 + 1, largura, 22, Qt.AlignCenter, texto)
            c = QColor(cor)
            c.setAlpha(alpha)
            p.setPen(c)
            p.drawText(x, y - 12, largura, 22, Qt.AlignCenter, texto)
            p.setPen(Qt.NoPen)

        # botão de menu hambúrguer
        if self.hover:
            gi = QRadialGradient(QPointF(self.ICONE_X + 10, self.ICONE_Y + 8), 24)
            gi.setColorAt(0.0, QColor(255, 220, 140, 120))
            gi.setColorAt(1.0, QColor(255, 220, 140, 0))
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            p.setBrush(QBrush(gi))
            p.drawEllipse(QPointF(self.ICONE_X + 10, self.ICONE_Y + 8), 24, 24)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.setPen(QPen(QColor(24, 28, 44, 225), 2))
        p.setBrush(QColor(245, 232, 202, 235) if self.hover else QColor(28, 42, 66, 220))
        p.drawRoundedRect(self.ICONE_X, self.ICONE_Y, 22, 20, 4, 4)
        p.setPen(QPen(QColor(35, 43, 55) if self.hover else QColor(245, 232, 202), 2))
        for yy in (self.ICONE_Y + 5, self.ICONE_Y + 10, self.ICONE_Y + 15):
            p.drawLine(self.ICONE_X + 5, yy, self.ICONE_X + 17, yy)
        p.end()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    jogo = JogoPesca()
    jogo.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
