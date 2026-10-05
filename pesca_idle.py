"""
Pesca Idle - v0.8  (pixel art 16-bit de aventura)
Novidades:
  - Cenário, sprites e interface com paleta viva de RPGs 16-bit, serras em pixels,
    mar turquesa e céu de fim de tarde em faixas de cor.
  - Janela sem moldura arrastável; abre no canto inferior direito como antes.
  - Menu hambúrguer no canto superior direito e janela que pode ser arrastada.
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

from PySide6.QtCore import Qt, QTimer, QRect, QRectF, QPoint, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QImage, QRadialGradient,
    QBrush, QPainterPath, qRgba,
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QMenu, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QListWidget, QListWidgetItem, QPushButton, QComboBox,
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

CURIOSIDADES = {
    "Tubarão-lagarto": "Seu corpo alongado e as seis fendas branquiais lembram fósseis de antigos tubarões.",
    "Vaquita": "Vive somente no norte do Golfo da Califórnia. É uma pequena toninha e costuma evitar barcos.",
    "Celacanto-comorense": "Suas nadadeiras lobadas se movem alternadamente, como membros durante um nado lento.",
    "Peixe-mão-vermelho": "Usa as nadadeiras peitorais parecidas com mãos para caminhar pelo fundo do mar.",
    "Cavalinho-do-mar-pigmeu": "Camufla-se em corais gorgônias; sua coloração pode combinar com o coral que o abriga.",
    "Lula-magnapinna": "Seus braços e tentáculos muito longos criam uma silhueta incomum nas filmagens de águas profundas.",
    "Tubarão-boca-grande": "É um tubarão filtrador: nada com a boca aberta para capturar pequenos organismos.",
    "Peixe-ogro": "Seus dentes grandes ajudam a capturar presas num ambiente profundo onde alimento é escasso.",
    "Narval": "A famosa “presa” é, na verdade, um dente que pode crescer vários metros para fora da mandíbula.",
    "Baleia-azul": "É o maior animal conhecido; alimenta-se principalmente de krill, filtrado com placas de barbas.",
    "Tubarão-branco": "Seu dorso escuro e ventre claro ajudam a camuflá-lo quando visto de cima ou de baixo.",
    "Manta-gigante": "Apesar do tamanho, alimenta-se filtrando zooplâncton da água.",
    "Peixe-lua": "Seu corpo alto e achatado termina numa estrutura curta no lugar de uma cauda típica.",
    "Garoupa-verdadeira": "Como várias garoupas, pode mudar de sexo ao longo da vida; em geral, fêmeas tornam-se machos.",
    "Tartaruga-verde": "Adultos comem principalmente algas e capim-marinho; o nome vem da gordura esverdeada, não do casco.",
    "Mero-preto": "Juvenis costumam usar manguezais e estuários como abrigo antes de viverem em recifes e naufrágios.",
    "Orca": "É o maior membro da família dos golfinhos, e diferentes grupos têm vocalizações e hábitos próprios.",
    "Peixe-papagaio-azul": "Seu bico raspa algas da superfície dos recifes; peixes-papagaio também ajudam a produzir areia.",
    "Polvo-comum": "Tem três corações e sangue azulado, adaptados à circulação de oxigênio no corpo e nas brânquias.",
    "Linguado-comum": "Quando adulto, repousa de lado no fundo e mantém os dois olhos voltados para cima.",
    "Golfinho-nariz-de-garrafa": "Produz assobios característicos que ajudam indivíduos a reconhecer e localizar uns aos outros.",
    "Barracuda-grande": "Seus dentes afiados e corpo hidrodinâmico favorecem ataques rápidos contra peixes menores.",
    "Atum-azul": "É altamente migratório e pode cruzar grandes trechos do Atlântico durante suas viagens.",
    "Peixe-palhaço": "Vive entre os tentáculos de anêmonas; uma camada de muco ajuda a evitar suas ferroadas.",
    "Lagosta-americana": "Usa suas antenas para explorar o ambiente e detectar sinais químicos na água.",
    "Água-viva-juba-de-leão": "Seus tentáculos finos ficam suspensos sob o sino e capturam pequenas presas à deriva.",
    "Lula-de-humboldt": "Muda rapidamente de cor com células pigmentares, usando padrões para sinalizar a outras lulas.",
    "Salmão-rosa": "Seu ciclo de vida costuma durar dois anos; muitos adultos retornam juntos aos rios para desovar.",
    "Bacalhau-do-atlântico": "Uma fêmea pode liberar milhões de ovos, embora apenas uma pequena parte chegue à fase adulta.",
    "Cavala": "Forma cardumes velozes e costuma migrar conforme a temperatura e a disponibilidade de alimento.",
    "Sardinha-do-pacífico": "Seus grandes cardumes podem se deslocar e mudar de tamanho conforme as condições do oceano.",
    "Anchoveta-peruana": "A corrente fria e rica em nutrientes de Humboldt sustenta uma das maiores pescarias de uma única espécie.",
    "Arenque-atlântico": "Seus ovos pegajosos aderem a algas, pedras e outras superfícies submersas.",
    "Polaca-do-alasca": "Vive em cardumes no Pacífico Norte e sustenta uma das maiores pescarias comerciais do mundo.",
    "Camarão-cinza": "Pode variar a coloração e se enterrar na areia, o que ajuda a escapar de predadores.",
    "Mexilhão-azul": "Prende-se a rochas e outras superfícies com fios resistentes chamados bissos.",
    "Caranguejo-falso": "Apesar do nome, é um crustáceo aparentado às lagostas e pode formar enormes concentrações.",
    "Calano": "Este copépode acumula reservas de energia e é alimento importante para peixes e baleias em mares frios.",
    "Salpa-antártica": "Pode formar longas cadeias de indivíduos clonados que filtram partículas da água.",
    "Peixe-lanterna-glaciar": "Faz parte do grupo de peixes que sobe à superfície à noite para se alimentar e desce de dia.",
    "Peixe-lanterna-de-müller": "Pequeno e mesopelágico, ajuda a transferir energia do plâncton para predadores maiores.",
    "Krill-do-pacífico": "Forma enxames e é uma fonte essencial de alimento para peixes, aves e mamíferos marinhos.",
    "Krill-antártico": "Esses pequenos crustáceos vivem em grandes enxames e são a base alimentar de muitos animais antárticos.",
    "Copépode-comum": "É minúsculo, mas serve de alimento a larvas de peixes e participa da base das cadeias marinhas.",
    "Peixe-lanterna-comum": "Os fotóforos do corpo produzem luz e ajudam a quebrar sua silhueta na penumbra oceânica.",
    "Lambari": "O nome reúne pequenos peixes de água doce; muitos vivem em cardumes e são importantes para predadores locais.",
    "Tilápia-do-nilo": "A fêmea protege ovos e filhotes na boca, comportamento conhecido como incubação bucal.",
    "Tambaqui": "Seus dentes fortes conseguem triturar frutos e sementes que caem na água durante a cheia.",
    "Pacu": "Seus dentes achatados lembram os humanos e ajudam a quebrar sementes e frutos duros.",
}

# Paleta viva de aventura em 16-bit; cada nível do barco ganha uma cor própria.
CORES_BARCO = [
    (177, 91, 53), (207, 126, 61), (93, 129, 153), (53, 138, 191),
    (222, 174, 68), (210, 77, 73), (148, 89, 190), (54, 165, 131),
    (236, 128, 48), (250, 209, 96), (250, 238, 194),
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
    "acessorio": "Acessórios",
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
    ("chapeu_ninja",    "chapeu",   "Touca ninja",        1800),
    ("chapeu_samurai",  "chapeu",   "Elmo de samurai",    2600),
    ("chapeu_cowboy",   "chapeu",   "Chapéu de xerife",    950),
    ("chapeu_mago",     "chapeu",   "Chapéu de arquimago", 3200),
    ("chapeu_astronauta", "chapeu", "Capacete espacial",   4100),
    ("chapeu_folhas",   "chapeu",   "Coroa de folhas",     750),
    ("chapeu_marinheiro", "chapeu", "Boina de marinheiro", 650),
    ("chapeu_raposa",   "chapeu",   "Capuz de raposa",    2100),
    ("chapeu_corais",   "chapeu",   "Coroa de corais",    2900),

    ("roupa_vermelha",  "roupa",    "Camisa vermelha",    0),
    ("roupa_azul",      "roupa",    "Camisa azul",        100),
    ("roupa_verde",     "roupa",    "Colete verde",       250),
    ("roupa_listrada",  "roupa",    "Camisa listrada",    400),
    ("roupa_capa",      "roupa",    "Capa de chuva",      700),
    ("roupa_capitao",   "roupa",    "Casaco de capitão",  1500),
    ("roupa_gala",      "roupa",    "Traje de gala",      3000),
    ("roupa_ninja",     "roupa",    "Traje de ninja",     2200),
    ("roupa_astral",    "roupa",    "Manto estelar",      3500),
    ("roupa_mergulhador", "roupa",  "Traje de mergulho",   2800),
    ("roupa_fenix",     "roupa",    "Manto da fênix",      5200),
    ("roupa_cyber",     "roupa",    "Jaqueta cyberpunk",  4600),
    ("roupa_mago",      "roupa",    "Túnica de arquimago", 3900),
    ("roupa_marinheiro", "roupa",   "Uniforme de convés",  850),
    ("roupa_aurora",    "roupa",    "Manto da aurora",    4800),
    ("roupa_abisso",    "roupa",    "Armadura abissal",   6800),

    ("bandeira_nenhum",   "bandeira", "Sem bandeira",       0),
    ("bandeira_vermelha", "bandeira", "Bandeirinha vermelha", 100),
    ("bandeira_brasil",   "bandeira", "Bandeira do Brasil", 300),
    ("bandeira_arco",     "bandeira", "Bandeira arco-íris", 500),
    ("bandeira_pirata",   "bandeira", "Bandeira pirata",    1000),
    ("bandeira_dragao",   "bandeira", "Bandeira do dragão", 1300),
    ("bandeira_nebulosa", "bandeira", "Bandeira nebulosa",  1700),
    ("bandeira_sol",      "bandeira", "Bandeira do sol nascente", 1400),
    ("bandeira_kraken",   "bandeira", "Bandeira do kraken", 2100),
    ("bandeira_galaxia",  "bandeira", "Bandeira galáctica", 2400),
    ("bandeira_folhas",   "bandeira", "Bandeira da floresta", 950),
    ("bandeira_sakura", "bandeira", "Bandeira de sakura",  1150),
    ("bandeira_tempestade", "bandeira", "Bandeira da tempestade", 1850),
    ("bandeira_compasso", "bandeira", "Bandeira do explorador", 2750),

    ("boia_vermelha",   "boia",     "Boia vermelha",      0),
    ("boia_amarela",    "boia",     "Boia amarela",       100),
    ("boia_listrada",   "boia",     "Boia listrada",      250),
    ("boia_coracao",    "boia",     "Boia coração",       600),
    ("boia_estrela",    "boia",     "Boia estrela",       1500),
    ("boia_planeta",    "boia",     "Boia planeta",       2200),
    ("boia_bolha",      "boia",     "Boia de bolha",      1200),
    ("boia_donut",      "boia",     "Boia de rosquinha",   900),
    ("boia_abacaxi",    "boia",     "Boia de abacaxi",    1300),
    ("boia_kraken",     "boia",     "Boia do kraken",     2400),
    ("boia_foguete",    "boia",     "Boia foguete",       1800),
    ("boia_lotus",      "boia",     "Boia de lótus",       700),
    ("boia_limao",      "boia",     "Boia de limão",       1050),
    ("boia_perola",     "boia",     "Boia pérola lunar",   2800),

    ("boneco_nenhum",     "boneco", "Sem boneco",         0),
    ("boneco_pato",       "boneco", "Patinho de borracha", 300),
    ("boneco_caranguejo", "boneco", "Caranguejo",         700),
    ("boneco_gato",       "boneco", "Gatinho",            1500),
    ("boneco_pinguim",    "boneco", "Pinguim",            3000),
    ("boneco_agumon",     "boneco", "Agumon",             9999),
    ("boneco_robot",      "boneco", "Robô explorador",    6000),
    ("boneco_slime",      "boneco", "Mascote gelatinoso", 4500),
    ("boneco_raposa",     "boneco", "Raposa mística",     3800),
    ("boneco_polvo",      "boneco", "Polvo de pelúcia",   2600),
    ("boneco_capivara",   "boneco", "Capivara aventureira", 3300),
    ("boneco_fantasma",   "boneco", "Fantasma camarada",  2200),
    ("boneco_tartaruga", "boneco", "Tartaruguinha",       1800),
    ("boneco_axolote",   "boneco", "Axolote sorridente",  2700),
    ("boneco_baleia",    "boneco", "Baleia viajante",     4100),

    ("acessorio_nenhum", "acessorio", "Sem acessório",          0),
    ("anel_verde_esmeralda", "acessorio", "Anel Verde-Esmeralda", 12000),
    ("martelo_pesado", "acessorio", "Martelo Pesado",            15000),
    ("teia_aracnidea", "acessorio", "Lançador de Teia",           10500),
    ("orbe_dragon", "acessorio", "Orbe do Dragão",                14000),
    ("broche_lunar", "acessorio", "Broche Lunar",                 11500),
    ("sabre_energia", "acessorio", "Sabre de Energia",             16000),
    ("asas_fenix", "acessorio", "Asas da Fênix",                    22000),
    ("aura_cyber", "acessorio", "Aura Cyberpunk",                   18500),
    ("estrelas_orbitais", "acessorio", "Constelação Orbital",       20000),
    ("chama_yokai", "acessorio", "Chamas de Yokai",                 23500),
    ("cajado_tempestade", "acessorio", "Cajado da Tempestade",       17000),
    ("escudo_bolhas", "acessorio", "Escudo de Bolhas",               19000),
    ("asas_boreais", "acessorio", "Asas Boreais",                     25000),
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
        "acessorio_nenhum",
    ],
    "equipados": {
        "chapeu": "chapeu_palha",
        "roupa": "roupa_vermelha",
        "bandeira": "bandeira_nenhum",
        "boia": "boia_vermelha",
        "boneco": "boneco_nenhum",
        "acessorio": "acessorio_nenhum",
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


def raridade_da_especie(item):
    """Converte o peso relativo de encontro em uma faixa para a enciclopédia."""
    peso = item["peso"]
    if peso >= 8:
        return "Comum"
    if peso >= 3:
        return "Incomum"
    if peso >= 1:
        return "Raro"
    if peso >= 0.1:
        return "Muito raro"
    return "Lendário"


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
COR_CONTORNO = (35, 31, 68)
COR_LUZ = (255, 218, 133)


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
    "roupa_ninja": {
        "pal": {"c": (54, 48, 76), "C": (28, 26, 42), "r": (190, 42, 62)},
        "overlay": [_ov("........", "........", "..rrrr..", "...rr...", "...rr...",
                        "...rr...", "...rr...", "........", "........", "........")],
    },
    "roupa_astral": {
        "pal": {"c": (66, 62, 160), "C": (38, 36, 108), "g": (255, 224, 110)},
        "overlay": [_ov("........", ".g......", "........", "......g.",
                        "...g....", "........", ".g......", "........", ".....g..", "........")],
    },
    "roupa_mergulhador": {
        "pal": {"c": (36, 142, 166), "C": (22, 76, 108), "w": (220, 245, 245)},
        "overlay": [_ov("........", "..wwww..", "..w..w..", "........", "..ww....",
                        "........", "........", "........", "........", "........")],
    },
    "roupa_fenix": {
        "pal": {"c": (192, 55, 34), "C": (104, 38, 45), "g": (255, 190, 50)},
        "overlay": [_ov("........", ".g....g.", "..g..g..", "...gg...", "........",
                        "..g..g..", ".g....g.", "........", "........", "........")],
    },
    "roupa_cyber": {
        "pal": {"c": (38, 42, 68), "C": (22, 24, 40), "p": (246, 56, 176), "b": (40, 220, 246)},
        "overlay": [_ov("........", ".pp..bb.", "........", "..b..p..", "........",
                        ".pp..bb.", "........", "........", "........", "........")],
    },
    "roupa_mago": {
        "pal": {"c": (102, 58, 150), "C": (52, 36, 98), "g": (255, 220, 92)},
        "overlay": [_ov("........", "...g....", "........", ".g......", "........",
                        "......g.", "........", "...g....", "........", "........")],
    },
    "roupa_marinheiro": {
        "pal": {"c": (42, 94, 156), "C": (24, 54, 104), "w": (240, 240, 245), "g": (240, 194, 72)},
        "overlay": [_ov("........", ".ww..ww.", "..wwww..", "...gg...", "........",
                        "..wwww..", "........", "........", "........", "........")],
    },
    "roupa_aurora": {
        "pal": {"c": (64, 102, 142), "C": (38, 58, 112), "p": (190, 110, 220), "g": (100, 238, 210)},
        "overlay": [_ov("........", ".p....g.", "..p..g..", "...pg...", "...pg...",
                        "..g..p..", ".g....p.", "........", "........", "........")],
    },
    "roupa_abisso": {
        "pal": {"c": (34, 62, 94), "C": (18, 34, 62), "b": (42, 212, 220), "g": (238, 188, 74)},
        "overlay": [_ov("........", ".b....b.", "..bbbb..", "...gg...", "...bb...",
                        "...bb...", "........", ".b....b.", "........", "........")],
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
    "chapeu_ninja": (
        ["...kkkkk...", "..kkkkkkk..", ".kkkkkkkkk.", "kkkkkkkkkkk",
         "kkkkkkkkkkk", "kkkkkkkkkkk", "kkkkkkkkkkk", "kkkkkkkkkkk",
         "kkk....kkkk", "kkk....kkkk", "kkkkkkkkkkk", "kkkkkkkkkkk",
         ".kkkkkkkkk.", "..kkkkkkk..", "...kkkkk..."],
        {"k": (20, 20, 30), "K": (38, 39, 52)}),
    "chapeu_samurai": (
        ["..y...........y..", "..yy.........yy..", ".yy...........yy.",
         ".y.............y.", "..yy.........yy..", "...yyyyyyyyyyy...",
         "..ygggggggggggy..", ".ggggrrrrrgggggg.", "ggggggggggggggggg",
         ".kkkkkkkkkkkkkkk."],
        {"y": (255, 221, 112), "g": (220, 166, 55), "r": (154, 42, 52),
         "k": (33, 32, 42)}),
    "chapeu_cowboy": (
        [".....ggg.....", "...ggggggg...", ".ggggggggggg.", "..kkkkkkkkk..",
         "...kkkkkkk..."],
        {"g": (178, 112, 54), "k": (80, 49, 34)}),
    "chapeu_mago": (
        ["......p......", ".....ppp.....", "....ppppp....", "...ppppppp...",
         "..ppppppppp..", ".pppppgppppp.", "ppppppppppppp", "...ggggggg..."],
        {"p": (92, 54, 156), "g": (255, 218, 82)}),
    "chapeu_astronauta": (
        ["...wwwwwww...", ".wwwwwwwwwww.", "wwwwwwwwwwwww", "wwbbbbbbbbbww",
         "wwbbbbbbbbbww", "wwwwwwwwwwwww", ".wwwwwwwwwww.", "..wwwwwwwww..",
         "...ggggggg..."],
        {"w": (220, 230, 239), "b": (52, 152, 205), "g": (205, 166, 78)}),
    "chapeu_folhas": (
        ["..gg..gg..", ".gggggggg.", "gggggggggg", ".gggggggg.", "..gggggg.."],
        {"g": (70, 154, 74)}),
    "chapeu_marinheiro": (
        ["...wwwwww...", "..wwwwwwww..", ".bbbbbbbbbb.", "bbbbbbbbbbbb",
         "..gggggggg.."],
        {"w": (242, 243, 247), "b": (38, 66, 128), "g": (242, 196, 70)}),
    "chapeu_raposa": (
        ["y........y", "yy......yy", ".yy....yy.", "..yyyyyy..", ".yywwwwyy.",
         "yywwwwwwyy", ".yyyyyyyy."],
        {"y": (222, 112, 43), "w": (245, 232, 208)}),
    "chapeu_corais": (
        ["..rr.g..bb..", ".rrrgg..bbb.", ".rrrrgggbbb.", ".rrrrrrrrrr.",
         "rrrrrrrrrrrr"],
        {"r": (236, 108, 120), "g": (255, 201, 82), "b": (86, 202, 210)}),
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
        if chapeu_id == "chapeu_ninja":
            # Touca cobre toda a cabeça e a nuca; a abertura deixa apenas os olhos visíveis.
            cam.sprite(grade, pal_h, 35 - len(grade[0]) // 2, 20)
        else:
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
    "bandeira_dragao": (
        ["kkkkrrrrkkkk", "kkkrrrrrrkkk", "kkrrrrrrrrkk", "krrrggggrrrk",
         "kkrrrrrrrrkk", "kkkrrrrrrkkk", "kkkkrrrrkkkk"],
        {"k": (34, 30, 46), "r": (190, 48, 52), "g": (245, 205, 82)}),
    "bandeira_nebulosa": (
        ["bbbbppppbbbb", "bbbppppppbbb", "bbppwwppppbb", "pppwwppppppp",
         "bbppppggppbb", "bbbppppppbbb", "bbbbppppbbbb"],
        {"b": (42, 68, 150), "p": (136, 74, 190), "w": (245, 236, 255),
         "g": (120, 224, 255)}),
    "bandeira_sakura": (
        ["pppppppppppp", "ppppwwpppppp", "pppwwwwppppp", "ppppwwpppppp",
         "ppppggpppppp", "pppppppppppp", "pppppppppppp"],
        {"p": (202, 88, 142), "w": (255, 225, 237), "g": (91, 177, 111)}),
    "bandeira_tempestade": (
        ["bbbbbbbbbbbb", "bbbbyybbbbbb", "bbbbbyybbbbb", "bbbbyybbbbbb",
         "bbbbbyybbbbb", "bbbbbbbyyyyy", "bbbbbbbbbbbb"],
        {"b": (35, 53, 91), "y": (248, 222, 116)}),
    "bandeira_compasso": (
        ["wwwwwwwwwwww", "wwwwwyywwwww", "wwwwyyyywwww", "wwwyybbyywww",
         "wwyybbbbyyww", "wwwyybbyywww", "wwwwyyyywwww",
         "wwwwwyywwwww"],
        {"w": (44, 118, 112), "y": (247, 214, 117), "b": (252, 241, 213)}),
    "bandeira_folhas": (
        ["gggggggggggg", "gggggggggggg", "gggtggggtggg", "gggttgggttgg",
         "gggtggggtggg", "gggggggggggg", "gggggggggggg"],
        {"g": (38, 105, 73), "t": (241, 196, 111)}),
    "bandeira_sol": (
        ["wwwwwwwwwwww", "wwwrrwwwwwww", "wwrrrrwwwwww", "wrrroorrrwww",
         "wwrrrrwwwwww", "wwwrrwwwwwww", "wwwwwwwwwwww"],
        {"w": (246, 215, 166), "r": (183, 54, 62), "o": (250, 183, 84)}),
    "bandeira_kraken": (
        ["nnnnnnnnnnnn", "nnpppppppnnn", "nppnnnnnppnn", "ppnncpcnnppp",
         "nppnpppnnppn", "nnpppnnpppnn", "nnnnnnnnnnnn"],
        {"n": (33, 48, 92), "p": (152, 83, 191), "c": (117, 228, 219)}),
    "bandeira_galaxia": (
        ["nnnnnynnnnnn", "nnnppnnnnncn", "nnpppnnnyynn", "nnppppnnnnnn",
         "nnnpppcnnnnn", "nnnnnnnnnppn", "nnynnnnpppnn"],
        {"n": (28, 39, 91), "p": (112, 77, 181), "c": (105, 214, 228),
         "y": (255, 218, 131)}),
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
    "boneco_robot": (
        ["..sssss..", ".swwswws.", ".sssssss.", "..srrrs..", ".sssssss.",
         "..s...s..", ".ss...ss."],
        {"s": (142, 166, 190), "w": (100, 228, 255), "r": (230, 80, 88)}),
    "boneco_slime": (
        ["....ggg....", "..ggggggg..", ".ggggggggg.", ".ggkgggkgg.",
         ".ggggggggg.", "..ggggggg..", "...ggggg..."],
        {"g": (94, 220, 146), "k": (38, 46, 66)}),
    "boneco_tartaruga": (
        ["...gggg...", ".gggggggg.", "ggkgggkggg", "gggggggggg",
         ".ggGGGGgg.", "..gggggg..", ".gg....gg."],
        {"g": (100, 190, 112), "G": (62, 133, 89), "k": (35, 37, 42)}),
    "boneco_axolote": (
        ["r..yyyy..r", "rryyyyyyrr", ".yyyyyyyy.", "yykgyygkyy",
         "yyyyyyyyyy", ".yyyyyyyy.", "..yyyyyy.."],
        {"y": (244, 164, 178), "r": (228, 99, 150), "g": (242, 110, 130),
         "k": (42, 36, 48)}),
    "boneco_baleia": (
        ["...bbbb....", ".bbbbbbbb..", "bbbbkbbbbbb", "bbwwwwbbbb.",
         ".bbbbbbbb..", "..bbbbbb...", "..bb..bb..."],
        {"b": (71, 133, 200), "w": (204, 231, 243), "k": (37, 43, 56)}),
    "boneco_fantasma": (
        ["....wwww....", "..wwwwwwww..", ".wwwwwwwwww.", "wwkw.ww.kwww",
         "wwwwwwwwwwww", "wwwwwwwwwwww", ".wwwwwwwwww.", "..wwwwwwww..",
         "...wwwwww...", "...ww..ww..."],
        {"w": (239, 243, 255), "k": (45, 48, 77)}),
    "boneco_polvo": (
        ["....pppp....", "..pppppppp..", ".pppppppppp.", "ppkppppkpppp",
         "pppppppppppp", ".pppppppppp.", "p.pp.pp.pp.p", "pp..pp..pppp"],
        {"p": (164, 101, 207), "k": (38, 36, 57)}),
    "boneco_capivara": (
        ["..tt....tt..", ".tttt..tttt.", ".tttttttttt.", "ttkttttktttt",
         "tttttttttttt", ".tttttwwttt.", "..ttwwwwtt..", "...tttttt..."],
        {"t": (174, 112, 70), "w": (235, 207, 168), "k": (39, 34, 36)}),
    "boneco_raposa": (
        ["r..rrrrrr..r", "rr.rrrrrr.rr", ".rrrrrrrrrr.", "rrrrrrrrrrrr",
         "rrkrrwwkrrr.", "rrrrwwwwrrrr", ".rrrwwwwrrr.", "..rrrwwrrr..",
         "...rrrrrr..."],
        {"r": (214, 91, 48), "w": (248, 231, 197), "k": (42, 34, 40)}),
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
    "boia_planeta": (
        ["...bbb...", ".bbbbbbb.", "bbgggbbbb", "bbbbbbbbb", ".bbbbbbb.", "...bbb..."],
        {"b": (78, 126, 234), "g": (74, 220, 152)}),
    "boia_bolha": (
        ["...ccc...", ".ccccccc.", "cccwwcccc", "ccccccccc", ".ccccccc.", "...ccc..."],
        {"c": (118, 220, 242), "w": (245, 255, 255)}),
    "boia_lotus": (
        ["...ppp...", ".ppp.ppp.", "ppppppppp", ".ppp.ppp.", "..ppwpp.."],
        {"p": (222, 105, 174), "w": (255, 235, 245)}),
    "boia_limao": (
        ["....g....", "..ggggg..", ".ggggggg.", "ggggggggg", ".ggggggg.", "..ggggg.."],
        {"g": (170, 220, 74)}),
    "boia_perola": (
        ["...ww...", ".wwggww.", "wwgggwww", "wwwwwwww", ".wwwwww.", "..wwww.."],
        {"w": (235, 246, 255), "g": (154, 226, 235)}),
    "boia_donut": (
        ["...rrr...", ".rrrrrrr.", "rrr...rrr", "rr.....rr",
         "rr.....rr", "rrr...rrr", ".rrrrrrr.", "...rrr..."],
        {"r": (238, 121, 97)}),
    "boia_abacaxi": (
        ["...ggg...", "..ggggg..", "...yyyy..", "..yyyyyy.", ".yyzyzyy.",
         ".yyyyyyy.", "..yyyyy..", "...yyy..."],
        {"g": (77, 173, 91), "y": (248, 193, 69), "z": (211, 140, 47)}),
    "boia_foguete": (
        ["....rr....", "...rrrr...", "...rwwr...", "...rccr...",
         "..rrrrrr..", ".rrrwwrrr.", "..rr..rr..", ".oo....oo.",
         "..o......o"],
        {"r": (217, 69, 66), "w": (243, 238, 219), "c": (101, 211, 233),
         "o": (255, 177, 70)}),
    "boia_kraken": (
        ["...ppp...", ".ppppppp.", "pppcccppp", "ppppppppp", ".ppppppp.",
         "p..p.p..p", ".p.p.p.p."],
        {"p": (133, 79, 177), "c": (120, 232, 215)}),
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


class EnciclopediaDialog(QDialog):
    def __init__(self, jogo):
        super().__init__(jogo, Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.jogo = jogo
        self.especies = [item for item in LOOT if item["tipo"] == "peixe"]
        self.setWindowTitle("Enciclopédia")
        self.setFixedSize(740, 500)

        layout = QVBoxLayout(self)
        instrucao = QLabel(
            "Pesque 1 vez para revelar o valor, 5 vezes para revelar a raridade "
            "e 10 vezes para revelar a curiosidade.")
        instrucao.setWordWrap(True)
        layout.addWidget(instrucao)

        self.progresso = QLabel()
        self.progresso.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.progresso)

        colunas = QHBoxLayout()
        painel_lista = QVBoxLayout()
        self.ordenacao = QComboBox()
        self.ordenacao.addItem("Ordem alfabética", "alfabetica")
        self.ordenacao.addItem("Quantidade pescada (maior primeiro)", "quantidade")
        self.ordenacao.currentIndexChanged.connect(self.atualizar_lista)
        painel_lista.addWidget(self.ordenacao)

        self.lista = QListWidget()
        self.lista.setMinimumWidth(270)
        self.lista.currentItemChanged.connect(self.mostrar_detalhes)
        painel_lista.addWidget(self.lista, 1)
        colunas.addLayout(painel_lista, 2)

        self.detalhes = QLabel()
        self.detalhes.setWordWrap(True)
        self.detalhes.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        colunas.addWidget(self.detalhes, 3)
        layout.addLayout(colunas, 1)

        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.accept)
        layout.addWidget(fechar)

        self.atualizar_progresso()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_progresso)
        self.timer.start(750)

    def atualizar_progresso(self):
        inventario = self.jogo.estado["inventario"]
        registradas = sum(inventario.get(i["nome"], 0) >= 1 for i in self.especies)
        self.progresso.setText(
            f"Espécies registradas: {registradas} / {len(self.especies)}")
        self.atualizar_lista()

    def atualizar_lista(self, *_):
        inventario = self.jogo.estado["inventario"]
        capturadas = [i for i in self.especies if inventario.get(i["nome"], 0) >= 1]
        if self.ordenacao.currentData() == "quantidade":
            capturadas.sort(key=lambda i: (-inventario.get(i["nome"], 0), i["nome"].casefold()))
        else:
            capturadas.sort(key=lambda i: i["nome"].casefold())

        nomes = [i["nome"] for i in capturadas]
        atuais = [self.lista.item(n).data(Qt.UserRole) for n in range(self.lista.count())]
        selecionado = (self.lista.currentItem().data(Qt.UserRole)
                       if self.lista.currentItem() else None)
        if nomes != atuais:
            self.lista.blockSignals(True)
            self.lista.clear()
            for especie in capturadas:
                linha = QListWidgetItem()
                linha.setData(Qt.UserRole, especie["nome"])
                self.lista.addItem(linha)
            if nomes:
                self.lista.setCurrentRow(nomes.index(selecionado)
                                         if selecionado in nomes else 0)
            self.lista.blockSignals(False)

        for indice, especie in enumerate(capturadas):
            quantidade = inventario.get(especie["nome"], 0)
            self.lista.item(indice).setText(f'{especie["nome"]}  ·  {quantidade}x')
        self.mostrar_detalhes()

    def mostrar_detalhes(self, *_):
        linha = self.lista.currentItem()
        if not linha:
            self.detalhes.setText("Pesque uma espécie para adicioná-la à Enciclopédia.")
            return
        nome = linha.data(Qt.UserRole)
        especie = next(item for item in self.especies if item["nome"] == nome)
        quantidade = self.jogo.estado["inventario"].get(nome, 0)
        valor = (f'{fmt_moedas(especie["valor"])} moedas-base por captura'
                 if quantidade >= 1 else "Bloqueado — pesque esta espécie 1 vez.")
        raridade = (raridade_da_especie(especie)
                    if quantidade >= 5 else "Bloqueado — pesque esta espécie 5 vezes.")
        curiosidade = (CURIOSIDADES[nome]
                       if quantidade >= 10 else "Bloqueada — pesque esta espécie 10 vezes.")
        self.detalhes.setText(
            f"{nome}\n{especie['cientifico']}\nRegistrada {quantidade} vez(es)\n\n"
            f"VALOR EM MOEDAS\n{valor}\n\n"
            f"RARIDADE\n{raridade}\n\n"
            f"CURIOSIDADE\n{curiosidade}\n\n"
            "O valor mostrado é a base; o bônus do barco é aplicado na pesca.")


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
            for id_, s, nome, preco in sorted(
                    (item for item in CATALOGO if item[1] == slot),
                    key=lambda item: (item[3], item[2].casefold())):
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
        self._arrastando = False
        self._offset_arraste = QPoint()
        self.rect_icone = QRect(self.ICONE_X - 5, self.ICONE_Y - 4, 30, 26)
        self.fonte = QFont("Consolas", 9, QFont.Bold)
        self.fonte.setStyleStrategy(QFont.NoAntialias)
        self.setCursor(Qt.OpenHandCursor)

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
        self.caixa("Conquistas", "\n\n".join(linhas))

    def equipado(self, slot):
        return self.previa.get(slot, self.estado["equipados"][slot])

    # ---------------------------------------------------------- menu (ícone)
    def mouseMoveEvent(self, ev):
        if self._arrastando and (ev.buttons() & Qt.LeftButton):
            self.move(ev.globalPosition().toPoint() - self._offset_arraste)
            ev.accept()
            return
        sobre = self.rect_icone.contains(ev.position().toPoint())
        if sobre != self.hover:
            self.hover = sobre
            self.update()
        self.setCursor(Qt.PointingHandCursor if sobre else Qt.OpenHandCursor)
        self.setToolTip("Menu" if sobre else self._texto_tooltip())

    def leaveEvent(self, ev):
        if self.hover:
            self.hover = False
            self.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            if self.rect_icone.contains(ev.position().toPoint()):
                self.abrir_menu()
            else:
                self._arrastando = True
                self._offset_arraste = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self.setCursor(Qt.ClosedHandCursor)
                ev.accept()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton and self._arrastando:
            self._arrastando = False
            sobre = self.rect_icone.contains(ev.position().toPoint())
            self.setCursor(Qt.PointingHandCursor if sobre else Qt.OpenHandCursor)
            ev.accept()

    def _texto_tooltip(self):
        e = self.estado
        return (f'Moedas: {fmt_moedas(e["moedas"])}  |  Vara Nv {e["vara"]}  |  '
                f'Barco Nv {e["barco"]}  •  Arraste para mover')

    def abrir_menu(self):
        m = QMenu(self)
        m.addAction("Loja", self.abrir_loja)
        m.addAction("Status e inventário", self.mostrar_status)
        m.addAction("Enciclopédia", self.abrir_enciclopedia)
        m.addAction("Conquistas", self.mostrar_conquistas)
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

    def abrir_enciclopedia(self):
        EnciclopediaDialog(self).exec()

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

        # Céu em faixas de cor e montanhas em pixels, como um cenário de RPG 16-bit.
        sp.setRenderHint(QPainter.Antialiasing, False)
        faixas_ceu = [
            (0, 9, (34, 45, 106)), (9, 18, (48, 68, 137)),
            (18, 27, (76, 96, 158)), (27, 35, (126, 117, 163)),
            (35, 43, (193, 132, 134)), (43, AGUA_Y, (239, 178, 119)),
        ]
        for topo, fim, rgb in faixas_ceu:
            sp.fillRect(0, topo, ART_W, fim - topo, QColor(*rgb))

        # Nuvens em blocos com sombra colorida.
        sp.setPen(Qt.NoPen)
        for x, y, largura in ((9, 12, 20), (47, 8, 17), (75, 15, 15)):
            sp.fillRect(x + 2, y + 2, largura, 3, QColor(111, 102, 165))
            sp.fillRect(x + 4, y, largura - 7, 3, QColor(244, 196, 183))
            sp.fillRect(x, y + 3, largura, 3, QColor(255, 219, 188))

        # Sol em mosaico e pequenos pontos de luz no céu.
        sp.fillRect(91, 17, 10, 10, QColor(255, 211, 119))
        sp.fillRect(93, 15, 6, 14, QColor(255, 226, 147))
        sp.fillRect(89, 19, 14, 6, QColor(255, 226, 147))
        sp.fillRect(94, 19, 4, 4, QColor(255, 244, 187))
        for sx, sy in ((5, 7), (31, 14), (39, 5), (67, 9), (110, 8), (114, 27)):
            sp.fillRect(sx, sy, 1, 1, QColor(255, 238, 181))
            if (sx + sy) % 2 == 0:
                sp.fillRect(sx - 1, sy, 3, 1, QColor(255, 220, 167))

        # Ilhas e serras sobrepostas em índigo e verde-azulado.
        serras = [
            ([(0, 42), (0, 37), (9, 31), (16, 36), (26, 30), (35, 37),
              (46, 33), (57, 41), (57, 52), (0, 52)], (74, 86, 143)),
            ([(49, 47), (61, 39), (70, 42), (83, 32), (94, 39), (105, 31),
              (120, 37), (120, 52), (49, 52)], (54, 111, 132)),
        ]
        for pontos, rgb in serras:
            forma = QPainterPath(QPointF(*pontos[0]))
            for ponto in pontos[1:]:
                forma.lineTo(*ponto)
            forma.closeSubpath()
            sp.fillPath(forma, QColor(*rgb))
        # Filetes de luz nas encostas dão volume sem desfoque.
        for x, y in ((8, 38), (17, 39), (27, 34), (39, 40), (64, 43),
                     (84, 36), (97, 42), (108, 36)):
            sp.fillRect(x, y, 3, 1, QColor(125, 143, 178))

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

        # Água azul-turquesa opaca, com cristas curtas e faixas de profundidade.
        topos = [AGUA_Y + int(round(math.sin(x * 0.45 + f * 2.0))) for x in range(ART_W)]
        sp.fillRect(0, AGUA_Y, ART_W, ART_H - AGUA_Y, QColor(49, 153, 185))
        sp.fillRect(0, 57, ART_W, 5, QColor(35, 130, 176))
        sp.fillRect(0, 62, ART_W, ART_H - 62, QColor(30, 103, 157))
        for x, topo in enumerate(topos):
            sp.fillRect(x, topo, 1, 1, QColor(147, 222, 215))

        # Ondas em marcas de 16-bit, animadas em pequenos passos.
        deslocamento = int(f * 7) % 24
        for faixa in range(7):
            y = 54 + faixa * 2
            x0 = (deslocamento + faixa * 9) % 24 - 24
            cor_onda = QColor(162, 231, 215) if faixa < 3 else QColor(70, 180, 201)
            for x in range(x0, ART_W, 24):
                sp.fillRect(x, y, 6 + faixa % 3, 1, cor_onda)

        # reflexo da lanterna na água
        for i, yy in enumerate(range(AGUA_Y + 3, AGUA_Y + 15, 2)):
            desl = int(round(1.3 * math.sin(yy * 0.8 + f * 3)))
            larg = max(1, 5 - i // 2)
            sp.fillRect(LANT_X + 2 - larg // 2 + desl, yy + dy, larg, 1,
                        QColor(255, 220, 134, max(70, 230 - i * 24)))

        # faíscas na água
        for k, (sx, sy) in enumerate(FAISCAS):
            ph = (f * 0.7 + k * 0.31) % 1.0
            if ph < 0.35:
                sp.fillRect(sx, sy, 1, 1, QColor(210, 249, 235))
                if 0.1 < ph < 0.25:
                    sp.fillRect(sx - 1, sy, 1, 1, QColor(255, 239, 178))
                    sp.fillRect(sx + 1, sy, 1, 1, QColor(255, 239, 178))
        sp.end()
        return cena, dy

    def desenhar_acessorio(self, p, fase):
        id_ = self.equipado("acessorio")
        centro_pescador = QPointF(69, 75)
        p.save()

        if id_ == "anel_verde_esmeralda":
            pulso = 1 + 0.08 * math.sin(fase * 3.2)
            brilho = QRadialGradient(centro_pescador, 45 * pulso)
            brilho.setColorAt(0.0, QColor(50, 255, 115, 85))
            brilho.setColorAt(0.55, QColor(20, 240, 95, 38))
            brilho.setColorAt(1.0, QColor(0, 230, 80, 0))
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            p.setBrush(QBrush(brilho))
            p.setPen(Qt.NoPen)
            p.drawEllipse(centro_pescador, 45 * pulso, 45 * pulso)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(95, 255, 145, 220), 2))
            p.drawEllipse(centro_pescador, 24 * pulso, 34 * pulso)

        elif id_ == "martelo_pesado":
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            for i, x in enumerate((43, 119)):
                pulso = (fase * 0.9 + i * 0.48) % 1.0
                if pulso > 0.24:
                    continue
                alfa = int(230 * (1 - pulso / 0.24))
                caminho = QPainterPath(QPointF(x, -4))
                for passo in range(1, 8):
                    y = passo * 13
                    desvio = math.sin(fase * 13 + passo * 2.1 + i) * (5 + passo)
                    caminho.lineTo(x + desvio, y)
                caminho.lineTo(x - 3, 97)
                p.setPen(QPen(QColor(45, 145, 255, alfa // 2), 9,
                              Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                p.drawPath(caminho)
                p.setPen(QPen(QColor(220, 246, 255, alfa), 2.4,
                              Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                p.drawPath(caminho)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        elif id_ == "teia_aracnidea":
            p.setPen(QPen(QColor(225, 244, 255, 190), 1.2))
            ancora = QPointF(236, 2)
            pontas = [QPointF(177, 2), QPointF(236, 57),
                      QPointF(193, 43), QPointF(211, 17)]
            for ponta in pontas:
                p.drawLine(ancora, ponta)
            p.drawArc(QRectF(183, 2, 54, 54), 180 * 16, 90 * 16)
            p.drawArc(QRectF(195, 2, 42, 42), 180 * 16, 90 * 16)
            p.drawArc(QRectF(207, 2, 30, 30), 180 * 16, 90 * 16)
            p.drawArc(QRectF(219, 2, 18, 18), 180 * 16, 90 * 16)

        elif id_ == "orbe_dragon":
            x = 112 + 5 * math.sin(fase * 1.7)
            y = 55 + 5 * math.cos(fase * 1.4)
            brilho = QRadialGradient(QPointF(x, y), 29)
            brilho.setColorAt(0.0, QColor(255, 244, 170, 205))
            brilho.setColorAt(0.28, QColor(255, 138, 28, 135))
            brilho.setColorAt(1.0, QColor(255, 82, 12, 0))
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            p.setBrush(QBrush(brilho))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(x, y), 29, 29)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            p.setBrush(QColor(244, 121, 28, 225))
            p.setPen(QPen(QColor(255, 218, 104), 1))
            p.drawEllipse(QPointF(x, y), 8, 8)
            p.setBrush(QColor(255, 236, 152))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(x - 2, y - 3), 2, 2)
            for i in range(3):
                ang = fase * 1.8 + i * math.tau / 3
                p.fillRect(int(x + 14 * math.cos(ang)),
                           int(y + 14 * math.sin(ang)), 2, 2,
                           QColor(255, 190, 66, 230))

        elif id_ == "broche_lunar":
            pulso = 0.5 + 0.5 * math.sin(fase * 3.8)
            brilho = QRadialGradient(QPointF(56, 55), 25)
            brilho.setColorAt(0, QColor(255, 222, 92, int(90 + 75 * pulso)))
            brilho.setColorAt(1, QColor(255, 198, 50, 0))
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            p.setBrush(QBrush(brilho))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(56, 55), 25, 25)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            lua = QPainterPath()
            lua.addEllipse(QRectF(49, 48, 18, 18))
            recorte = QPainterPath()
            recorte.addEllipse(QRectF(56, 44, 18, 18))
            p.fillPath(lua.subtracted(recorte), QBrush(QColor(255, 218, 88)))
            p.setBrush(QColor(255, 248, 201))
            p.drawEllipse(QPointF(47, 48), 1.5, 1.5)
            p.drawEllipse(QPointF(69, 67), 1, 1)

        elif id_ == "asas_fenix":
            pulso = 0.5 + 0.5 * math.sin(fase * 4.0)
            for lado in (-1, 1):
                chama = QPainterPath(QPointF(69, 76))
                chama.cubicTo(69 + lado * 20, 63, 69 + lado * 29, 36 - 5 * pulso, 69 + lado * 34, 28)
                chama.cubicTo(69 + lado * 33, 50, 69 + lado * 20, 75, 69, 76)
                p.setCompositionMode(QPainter.CompositionMode_Plus)
                p.setBrush(QColor(255, 117, 34, 65))
                p.setPen(QPen(QColor(255, 167, 55, 170), 2))
                p.drawPath(chama)
                p.setPen(QPen(QColor(255, 237, 137, 190), 1))
                p.drawLine(QPointF(69, 72), QPointF(69 + lado * 27, 38))
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        elif id_ == "aura_cyber":
            pulso = 0.5 + 0.5 * math.sin(fase * 5.0)
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(32, 238, 255, 155), 1.5))
            p.drawRoundedRect(QRectF(48, 42, 42, 62), 8, 8)
            p.setPen(QPen(QColor(255, 54, 202, int(90 + 100 * pulso)), 1))
            p.drawLine(QPointF(47, 57), QPointF(55, 57))
            p.drawLine(QPointF(83, 88), QPointF(91, 88))
            p.drawEllipse(QPointF(50, 48), 2, 2)
            p.drawEllipse(QPointF(87, 98), 2, 2)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        elif id_ == "estrelas_orbitais":
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            for i in range(7):
                ang = fase * 0.8 + i * math.tau / 7
                x = 69 + 31 * math.cos(ang)
                y = 73 + 42 * math.sin(ang)
                raio = 1.4 + 0.6 * (0.5 + 0.5 * math.sin(fase * 3 + i))
                p.setPen(QPen(QColor(255, 235, 160, 210), 1))
                p.drawLine(QPointF(x - raio, y), QPointF(x + raio, y))
                p.drawLine(QPointF(x, y - raio), QPointF(x, y + raio))
                p.setBrush(QColor(165, 221, 255, 200))
                p.setPen(Qt.NoPen)
                p.drawEllipse(QPointF(x, y), raio * 0.65, raio * 0.65)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        elif id_ == "chama_yokai":
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            for i, x in enumerate((48, 90)):
                sobe = (fase * 0.65 + i * 0.5) % 1.0
                y = 81 - sobe * 27
                fogo = QPainterPath(QPointF(x, y + 8))
                fogo.cubicTo(x - 5, y + 2, x + 4, y - 1, x, y - 8)
                fogo.cubicTo(x + 9, y - 1, x + 5, y + 8, x, y + 8)
                p.setBrush(QColor(163, 90, 255, 125))
                p.setPen(QPen(QColor(210, 160, 255, 200), 1))
                p.drawPath(fogo)
                p.setBrush(QColor(255, 197, 88, 190))
                p.setPen(Qt.NoPen)
                p.drawEllipse(QPointF(x, y + 2), 1.5, 2)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        elif id_ == "sabre_energia":
            tremor = 2 * math.sin(fase * 2.4)
            # O punho começa na mão do pescador; a lâmina segue para cima.
            base = QPointF(91, 78)
            punho = QPointF(99, 68)
            ponta = QPointF(112 + tremor, 38)
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            p.setPen(QPen(QColor(35, 190, 255, 95), 12, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(punho, ponta)
            p.setPen(QPen(QColor(78, 221, 255, 220), 5, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(punho, ponta)
            p.setPen(QPen(QColor(240, 255, 255, 245), 1.8, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(punho, ponta)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            p.setPen(QPen(QColor(60, 54, 72), 4, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(base, punho)
            p.setPen(QPen(QColor(230, 178, 74), 2))
            p.drawLine(QPointF(88, 75), QPointF(96, 81))

        elif id_ == "cajado_tempestade":
            brilho = QRadialGradient(QPointF(107, 41), 24)
            brilho.setColorAt(0, QColor(163, 246, 255, 210))
            brilho.setColorAt(0.35, QColor(76, 163, 255, 125))
            brilho.setColorAt(1, QColor(72, 142, 255, 0))
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            p.setBrush(QBrush(brilho))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(107, 41), 24, 24)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            p.setPen(QPen(QColor(116, 75, 43), 4, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(91, 79), QPointF(107, 42))
            p.setPen(QPen(QColor(244, 211, 111), 2))
            p.drawLine(QPointF(91, 79), QPointF(107, 42))
            p.setBrush(QColor(99, 225, 255))
            p.setPen(QPen(QColor(231, 253, 255), 1))
            p.drawEllipse(QPointF(107, 41), 4, 4)

        elif id_ == "escudo_bolhas":
            pulso = 1 + 0.04 * math.sin(fase * 3.0)
            centro = QPointF(69, 73)
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            p.setBrush(QColor(84, 219, 255, 22))
            p.setPen(QPen(QColor(128, 237, 255, 175), 2))
            p.drawEllipse(centro, 24 * pulso, 35 * pulso)
            for i in range(5):
                ang = fase * 1.4 + i * math.tau / 5
                x = centro.x() + 22 * math.cos(ang)
                y = centro.y() + 32 * math.sin(ang)
                p.setBrush(QColor(190, 248, 255, 185))
                p.setPen(QPen(QColor(255, 255, 255, 210), 1))
                p.drawEllipse(QPointF(x, y), 2.3, 2.3)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        elif id_ == "asas_boreais":
            brilho = 0.5 + 0.5 * math.sin(fase * 2.4)
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            for lado in (-1, 1):
                asa = QPainterPath(QPointF(69, 69))
                asa.cubicTo(69 + lado * 18, 37, 69 + lado * 42, 43, 69 + lado * 37, 77)
                asa.cubicTo(69 + lado * 30, 66, 69 + lado * 20, 64, 69, 69)
                cor = QColor(126, 244, 223, int(120 + brilho * 85))
                p.setPen(QPen(cor, 2, Qt.SolidLine, Qt.RoundCap))
                p.setBrush(QColor(80, 215, 225, 24))
                p.drawPath(asa)
                p.setPen(QPen(QColor(237, 177, 255, int(95 + brilho * 60)), 1))
                p.drawLine(QPointF(69, 69), QPointF(69 + lado * 31, 49))

        # Ferramentas cosméticas aparecem presas à mão direita do pescador.
        if id_ == "martelo_pesado":
            p.save()
            p.translate(91, 78)
            p.rotate(40)
            p.setPen(QPen(QColor(42, 36, 43), 7, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(0, 0), QPointF(0, -22))
            p.setPen(QPen(QColor(143, 91, 50), 4, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(0, 0), QPointF(0, -22))
            p.setBrush(QColor(101, 112, 133))
            p.setPen(QPen(QColor(38, 42, 57), 2))
            p.drawRoundedRect(QRectF(-9, -28, 18, 9), 2, 2)
            p.setPen(QPen(QColor(195, 211, 230), 1))
            p.drawLine(QPointF(-6, -25), QPointF(5, -25))
            p.restore()
        elif id_ == "sabre_energia":
            p.setBrush(QColor(58, 51, 68))
            p.setPen(QPen(QColor(224, 177, 80), 1))
            p.drawEllipse(QPointF(91, 78), 3.2, 3.2)

        p.restore()

    def paintEvent(self, _):
        f = self.fase
        cena, dy = self.desenhar_cena()

        p = QPainter(self)
        p.drawImage(QRect(0, 0, self.W, self.H), cena)   # ampliação sem suavização
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)
        p.setPen(Qt.NoPen)

        # Reflexo em pequenos pixels luminosos, sem bloom desfocado.
        flick = 0.82 + 0.18 * math.sin(f * 6.3) * math.sin(f * 2.7 + 1)
        cx, cy = (LANT_X + 2.5) * ESCALA, (LANT_Y + 3) * ESCALA + dy * ESCALA
        p.setCompositionMode(QPainter.CompositionMode_Plus)
        p.fillRect(int(cx - 3), int(cy - 3), 6, 6, QColor(255, 196, 93, int(115 * flick)))
        p.fillRect(int(cx - 1), int(cy - 5), 2, 10, QColor(255, 226, 143, int(105 * flick)))
        p.fillRect(int(cx - 5), int(cy - 1), 10, 2, QColor(255, 226, 143, int(105 * flick)))
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # Vaga-lumes viram pequenos cruzamentos de pixels dourados e verdes.
        p.setCompositionMode(QPainter.CompositionMode_Plus)
        for k, (bx, by) in enumerate(VAGALUMES):
            x = bx + 7 * math.sin(f * 0.6 + k * 2.1)
            y = by + 4 * math.sin(f * 0.8 + k * 1.3)
            a = 0.5 + 0.5 * math.sin(f * 2.2 + k * 1.7)
            cor = QColor(255, 236, 150, int(130 + 120 * a))
            p.fillRect(int(x), int(y), 2, 2, cor)
            p.fillRect(int(x), int(y) - 2, 1, 6, cor)
            p.fillRect(int(x) - 2, int(y), 6, 1, cor)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.setPen(Qt.NoPen)

        # Juncos em primeiro plano com contorno de pixel nítido.
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)
        p.setOpacity(1.0)
        esq, ox, oy = self.sprite("juncos_esq", lambda: montar_juncos(14, 12, JUNCOS_ESQ))
        p.drawImage(QRect(ox * 3, self.H - 12 * 3 + oy * 3, esq.width() * 3, esq.height() * 3), esq)
        dire, ox, oy = self.sprite("juncos_dir", lambda: montar_juncos(10, 11, JUNCOS_DIR))
        p.drawImage(QRect(self.W - 10 * 3 + ox * 3, self.H - 11 * 3 + oy * 3,
                          dire.width() * 3, dire.height() * 3), dire)
        p.setOpacity(1.0)
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)

        self.desenhar_acessorio(p, f)

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
            p.setPen(QPen(QColor(255, 218, 133, int(alpha * 0.9)), 2))
            p.drawRect(x, y - 12, largura, 22)
            p.setPen(QColor(20, 29, 64, int(alpha * 0.85)))
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
        p.setPen(QPen(QColor(35, 31, 68), 2))
        p.setBrush(QColor(246, 219, 155) if self.hover else QColor(30, 54, 101))
        p.drawRect(self.ICONE_X, self.ICONE_Y, 22, 20)
        p.setPen(QPen(QColor(112, 75, 53) if self.hover else QColor(255, 225, 147), 2))
        for yy in (self.ICONE_Y + 5, self.ICONE_Y + 10, self.ICONE_Y + 15):
            p.drawLine(self.ICONE_X + 5, yy, self.ICONE_X + 17, yy)
        p.end()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QWidget { color: #f7e9c7; font-family: Consolas; font-size: 9pt; }
        QDialog { background: #1e3158; border: 2px solid #d7ae5b; }
        QLabel { color: #f7e9c7; }
        QTabWidget::pane { background: #263f69; border: 2px solid #bd9854; }
        QTabBar::tab { background: #26375f; color: #e9d7a6; padding: 6px 10px;
                       border: 1px solid #675181; }
        QTabBar::tab:selected { background: #497b90; color: #fff1c5;
                                 border: 1px solid #f0ce77; }
        QListWidget, QComboBox { background: #14294b; color: #fff0cb;
                                 border: 1px solid #d7ae5b;
                                 selection-background-color: #4e8193; }
        QPushButton { background: #39577d; color: #ffebae;
                      border: 2px solid #d7ae5b; padding: 5px 10px; }
        QPushButton:hover { background: #557d91; color: #ffffff; }
        QPushButton:disabled { color: #9e9a8b; border-color: #736d68; }
        QMenu { background: #20365e; color: #ffebae; border: 2px solid #d7ae5b; }
        QMenu::item:selected { background: #4e8193; }
        QMessageBox { background: #1e3158; }
    """)
    jogo = JogoPesca()
    jogo.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
