"""
Pesca Idle - v1.0 (Enseada do Poente)
Arte original em 256×144: assets locais, animação de sprites e painéis de RPG.
Renderização em pesca_visual.py; identidade da interface em pesca_ui.py.
Janela arrastável, sempre visível, com início no canto inferior direito.

Requisitos:  pip install PySide6
Executar:    python pesca_idle.py        (ou pythonw pesca_idle.py)
"""
import sys
import os
import json
import random
import time
import math
from pathlib import Path

from pesca_visual import SceneRenderer, WIDTH, HEIGHT, SCALE, integer_viewport
from pesca_ui import configure_app, paint_overlay, rpg_icon, cosmetic_icon, InfoDialog

from PySide6.QtCore import Qt, QTimer, QRect, QPoint, QSize, QEvent
from PySide6.QtGui import QPainter

from PySide6.QtWidgets import (
    QApplication, QWidget, QMenu, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QListWidget, QListWidgetItem, QPushButton, QComboBox, QScrollArea,
)

# ----------------------------------------------------------------------------
# Configurações (mexa à vontade)
# ----------------------------------------------------------------------------
INTERVALO_PESCA = (10, 20)     # segundos entre uma pesca e outra (vara nível 0)
NIVEL_MAX = 10
LIMITE_OFFLINE = 4 * 3600      # máximo de segundos de progresso offline (4 horas)
SAVE_PATH = (Path(os.environ["PESCA_IDLE_SAVE_PATH"]) if os.getenv("PESCA_IDLE_SAVE_PATH")
             else Path(os.getenv("APPDATA", str(Path.home()))) / "PescaIdle" / "save.json")

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
# Catálogo original de cosméticos; renderização em pesca_visual.py (256×144).
# ============================================================================
ART_W, ART_H = WIDTH, HEIGHT
ESCALA = SCALE


# ------------------------------------------------------------------ casco


# ------------------------------------------------------------- personagem


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

# Grades históricas de referência; os sprites equipados vêm de assets/chapeus.png.
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


# --------------------------------------------------- lanterna, ícone e juncos


# Brilhos fixos na água e pontos de luz (coordenadas em pixels de arte / tela)

# ============================================================================
# === JOGO (Qt) ==============================================================
# ============================================================================


class EnciclopediaDialog(QDialog):
    def __init__(self, jogo):
        super().__init__(jogo, Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.jogo = jogo
        self.especies = [item for item in LOOT if item["tipo"] == "peixe"]
        self.setWindowTitle("Enciclopédia")
        geo = QApplication.primaryScreen().availableGeometry()
        self.resize(min(800,geo.width()-20), min(560,geo.height()-20))
        self.setMinimumSize(min(740,geo.width()-20), min(480,geo.height()-20))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        heading = QLabel("Caderno do pescador")
        heading.setProperty("heading", True)
        layout.addWidget(heading)
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
        self.lista.setIconSize(QSize(24,24))
        self.lista.setMinimumWidth(min(270,geo.width()//3))
        self.lista.currentItemChanged.connect(self.mostrar_detalhes)
        painel_lista.addWidget(self.lista, 1)
        colunas.addLayout(painel_lista, 2)

        self.detalhes = QLabel()
        self.detalhes.setProperty("panel", True)
        self.detalhes.setWordWrap(True)
        self.detalhes.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        details_scroll = QScrollArea()
        details_scroll.setWidgetResizable(True)
        details_scroll.setFrameShape(QScrollArea.NoFrame)
        details_scroll.setWidget(self.detalhes)
        colunas.addWidget(details_scroll, 3)
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
                linha.setIcon(rpg_icon("peixe"))
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
            self.detalhes.setText("O caderno ainda está em branco.\n\nCada espécie descoberta deixa uma nova história aqui.\n\nPesque para revelar o valor; com 5 encontros, a raridade; com 10, uma curiosidade.")
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


class PreviaCena(QWidget):
    def __init__(self, jogo, parent=None, scale=ESCALA):
        super().__init__(parent)
        self.jogo = jogo
        self.scene_scale=scale
        self.resize_viewport()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    def resize_viewport(self):
        self.scene_rect,self.physical_scale=integer_viewport(self.devicePixelRatioF(),self.scene_scale)
        self.setFixedSize(math.ceil(self.scene_rect.width()),math.ceil(self.scene_rect.height()))

    def event(self, event):
        result=super().event(event)
        if event.type()==QEvent.DevicePixelRatioChange and hasattr(self,'scene_scale'):
            self.resize_viewport()
        return result

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)
        cena, _ = self.jogo.desenhar_cena()
        p.drawImage(self.scene_rect, cena)
        p.end()


class LojaDialog(QDialog):
    def __init__(self, jogo):
        super().__init__(None, Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.jogo = jogo
        self.setWindowTitle("Loja")
        geo = QApplication.primaryScreen().availableGeometry()
        self.preview_scale = 2 if geo.width() >= 1000 and geo.height() >= 600 else 1
        preview_rect,_=integer_viewport(self.devicePixelRatioF(),self.preview_scale)
        self.resize(min(max(920,math.ceil(preview_rect.width())+390),geo.width()-20),
                    min(max(560,math.ceil(preview_rect.height())+250),geo.height()-20))
        self.setMinimumSize(min(620,geo.width()-20), min(480,geo.height()-20))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        heading = QLabel("Armazém da enseada")
        heading.setProperty("heading", True)
        lay.addWidget(heading)
        body = QHBoxLayout()
        controls = QVBoxLayout()
        self.lbl_moedas = QLabel()
        self.lbl_moedas.setStyleSheet("font-weight: bold;")
        controls.addWidget(self.lbl_moedas)

        self.abas = QTabWidget()
        self.abas.tabBar().hide()
        self.categoria = QComboBox()
        self.categoria.addItem(rpg_icon("vara"), "Equipamento")
        for slot, title in SLOTS.items():
            self.categoria.addItem(rpg_icon(slot), title)
        self.categoria.currentIndexChanged.connect(self.abas.setCurrentIndex)
        self.abas.currentChanged.connect(self.categoria.setCurrentIndex)
        controls.addWidget(self.categoria)

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
            lista.setIconSize(QSize(32,32))
            lista.setWordWrap(True)
            lista.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            lista.currentItemChanged.connect(self.ao_selecionar)
            self.listas[slot] = lista
            self.abas.addTab(lista, titulo)
        self.abas.currentChanged.connect(self.ao_selecionar)
        controls.addWidget(self.abas, 1)

        self.dica = QLabel("Selecione um item para experimentá-lo no barco. "
                           "Os acessórios são apenas visuais.")
        self.dica.setWordWrap(True)
        controls.addWidget(self.dica)

        self.btn = QPushButton("Comprar")
        self.btn.clicked.connect(self.acao)
        controls.addWidget(self.btn)
        body.addLayout(controls, 1)
        preview = QVBoxLayout()
        preview_title = QLabel("Seu barco • prévia ao vivo")
        preview_title.setStyleSheet("color: #efc581; font-weight: 600;")
        preview.addWidget(preview_title)
        self.preview_scene = PreviaCena(jogo, self, self.preview_scale)
        preview.addWidget(self.preview_scene)
        hint = QLabel("Experimente antes de comprar. Ao fechar, a prévia é descartada.\n"
                      "Chapéus, roupas e acessórios acompanham as animações.")
        hint.setWordWrap(True)
        preview.addWidget(hint)
        preview.addStretch(1)
        close = QPushButton("Voltar à pescaria")
        close.clicked.connect(self.accept)
        preview.addWidget(close)
        body.addLayout(preview)
        lay.addLayout(body, 1)

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
                    status = "equipado"
                    linha_equipada = lista.count()
                elif id_ in e["cosmeticos"]:
                    status = "comprado"
                else:
                    status = f"{fmt_moedas(preco)} moedas"
                it = QListWidgetItem(f"{nome}\n{status}")
                it.setIcon(cosmetic_icon(self.jogo._render,slot,id_))
                it.setSizeHint(QSize(0,54))
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
    ICONE_X, ICONE_Y = ART_W * ESCALA - 44, 10

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.resize_viewport()

        self.estado = self.carregar()
        self.previa = {}             # itens em teste na loja (não comprados)
        self.fase = 0.0
        self.pausado = False
        self.fisgando = 0.0
        self.capturando = 0.0
        self.popup = None            # [texto, cor, tempo_restante]
        self.hover = False
        self._render = SceneRenderer(ROUPAS, HATS, BANDEIRAS, BONECOS, BOIAS, CORES_BARCO)
        self._arrastando = False
        self._offset_arraste = QPoint()
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

    def resize_viewport(self):
        self.scene_rect,self.physical_scale=integer_viewport(self.devicePixelRatioF())
        self.W,self.H=math.ceil(self.scene_rect.width()),math.ceil(self.scene_rect.height())
        self.ICONE_X=self.W-44
        self.rect_icone=QRect(self.ICONE_X,self.ICONE_Y,32,32)
        self.setFixedSize(self.W,self.H)

    def event(self, event):
        result=super().event(event)
        if event.type()==QEvent.DevicePixelRatioChange and hasattr(self,'scene_rect'):
            self.resize_viewport()
        return result

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
            self.capturando = max(0.0, self.capturando - dt)

        if not self.pausado:
            if self.fisgando > 0:
                self.fisgando -= dt
                if self.fisgando <= 0:
                    r = self.sortear()
                    self.capturando = 1.2 if r["tipo"] == "peixe" else 0.0
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
        m.addAction(rpg_icon("loja"), "Loja", self.abrir_loja)
        m.addAction(rpg_icon("barco"), "Status e inventário", self.mostrar_status)
        m.addAction(rpg_icon("livro"), "Enciclopédia", self.abrir_enciclopedia)
        m.addAction(rpg_icon("conquistas"), "Conquistas", self.mostrar_conquistas)
        m.addSeparator()
        m.addAction(rpg_icon("pausa"), "Retomar" if self.pausado else "Pausar", self.alternar_pausa)
        m.addAction(rpg_icon("sair"), "Sair", self.sair)
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
        InfoDialog(self,titulo,texto).exec()

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

    # Scene and effects are rendered at one logical pixel scale.
    fmt_currency = staticmethod(fmt_moedas)

    def desenhar_cena(self):
        return self._render.render(self)

    def paintEvent(self, _):
        paint_overlay(self)

    def closeEvent(self, event):
        self.salvar()
        self.relogio.stop()
        self.timer_save.stop()
        event.accept()
        QApplication.quit()


def main(dev_access):
    dev_access.validate_launch()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    configure_app(app)
    jogo = JogoPesca()
    dev_access.prepare_window(jogo)
    jogo.show()
    dev_access.schedule_smoke_test(
        jogo, LojaDialog, EnciclopediaDialog, rpg_icon,
        BONECOS, BANDEIRAS, (ART_W, ART_H),
    )
    sys.exit(app.exec())


if __name__ == "__main__":
    from tools.dev_access import DevAccess

    dev_access = DevAccess()
    try:
        main(dev_access)
    except Exception:
        if dev_access.enabled:
            dev_access.write_failure()
            sys.exit(1)
        raise
