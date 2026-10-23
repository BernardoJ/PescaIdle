"""Build the shareable visual report; reads sanitized evidence only, no product imports."""
from pathlib import Path
import os
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
DOC=ROOT/'docs/aquario-especies'
EVID=DOC/'evidencias'
NEW=DOC/'movimento/evidencias'
OUT=ROOT/'output/pdf/PescaIdle_Aquario_Completo.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
fontdir=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
if (fontdir/'arial.ttf').exists() and (fontdir/'arialbd.ttf').exists():
    pdfmetrics.registerFont(TTFont('Body',str(fontdir/'arial.ttf')))
    pdfmetrics.registerFont(TTFont('Bold',str(fontdir/'arialbd.ttf')))
else:
    pdfmetrics.registerFont(pdfmetrics.Font('Body','Helvetica','WinAnsiEncoding'))
    pdfmetrics.registerFont(pdfmetrics.Font('Bold','Helvetica-Bold','WinAnsiEncoding'))
W,H=595.276,841.89
INK='#203b48';MUTED='#536875';GOLD='#b58c48'
c=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
c.setTitle('PescaIdle - Aquário completo, passos 1 a 5')
c.setAuthor('PescaIdle')
c.setSubject('Comparação visual e escopo da entrega sobre a PR 5')
c.setCreator('PescaIdle - relatório visual reproduzível')
page=0
def text(x,y,value,size=10,color=INK,bold=False):
    c.setFillColor(HexColor(color));c.setFont('Bold' if bold else 'Body',size)
    c.drawString(x,y,value)
def lines(value,x=42,y=0,width=511,size=10,leading=15,color=INK):
    for paragraph in value.split('\n'):
        words=paragraph.split();line=''
        for word in words:
            test=(line+' '+word).strip()
            if pdfmetrics.stringWidth(test,'Body',size)>width and line:
                text(x,y,line,size,color);y-=leading;line=word
            else:line=test
        if line:text(x,y,line,size,color);y-=leading
        else:y-=leading/2
    return y
def start(section,title,subtitle=''):
    global page
    page+=1
    c.setFillColor(HexColor('#f7f7ef'));c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(HexColor('#1b3543'));c.rect(0,H-13,W,13,fill=1,stroke=0)
    text(42,H-43,'PESCAIDLE / AQUÁRIO POR ESPÉCIE',9,MUTED,True)
    title_size=min(24,24*511/pdfmetrics.stringWidth(title,'Bold',24))
    text(42,H-78,title,title_size,INK,True)
    if subtitle:lines(subtitle,y=H-100,size=10)
    c.setStrokeColor(HexColor('#d6dbd4'));c.line(42,37,W-42,37)
    text(42,23,'PR #5  |  Código atual: 0c29196a  |  23/10/2026',8,MUTED)
    text(W-62,23,str(page),8,MUTED)
def end():c.showPage()
def pic(path,x,y,width,height=None):
    img=Image.open(path)
    if height is None:height=width*img.height/img.width
    c.drawImage(ImageReader(img),x,y,width,height,mask='auto')
    return height
def crop_pic(path,box,x,y,width):
    img=Image.open(path).crop(box)
    height=width*img.height/img.width
    c.drawImage(ImageReader(img),x,y,width,height,mask='auto')
    return height
def link(label,url,x,y):
    text(x,y,label,9,'#1d657a')
    c.linkURL(url,(x,y-2,x+pdfmetrics.stringWidth(label,'Body',9),y+10),relative=0)

start('01','Peixes: arte e movimento',
      'Passos 1-5: arte, escala, isolamento, movimento discreto e revisão visual.')
lines('68 espécies elegíveis recebem formas e marcas próprias. O tanque conserva três espaços, a regra de tamanho por exemplar e os percursos existentes.',y=692,size=12,leading=18)
text(42,619,'ANTES - HEAD DA PR #5 EM 0f516e89c4bb',10,MUTED,True)
pic(EVID/'antes/tanque-iniciais-2x.png',65,378,465)
text(42,349,'ARTE DOS PASSOS 1-3 PRESERVADA (e4e9e3f)',10,MUTED,True)
pic(EVID/'depois/tanque-iniciais-2x.png',65,108,465)
lines('Lambari, Tilápia-do-nilo e Carpa-comum no mesmo cenário e fase. Capturas sintéticas dos widgets; nenhuma partida ou save pessoal foi utilizado.',y=83,size=9,leading=12)
end()

start('02','Quatro espécies, quatro desenhos',
      'Capturas preservadas dos passos 1-3; quadro de repouso revalidado nesta etapa.')
text(42,694,'ANTES',11,MUTED,True);text(304,694,'DEPOIS',11,MUTED,True)
names=[
('Lambari','Astyanax lacustris','Mancha umeral oval, marca caudal e nadadeiras amareladas.'),
('Tilápia-do-nilo','Oreochromis niloticus','Corpo alto, dorsal contínua e barras na cauda.'),
('Carpa-comum','Cyprinus carpio','Bronze e oliva, dorsal longa e barbilhões curtos.'),
('Traíra','Hoplias malabaricus','Cabeça larga, boca comprida, manchas e cauda arredondada.')]
for n,(name,science,trait) in enumerate(names):
    y=550-n*144
    text(42,y+112,name+'  /  '+science,11,INK,True)
    for side,label in enumerate(('antes','depois')):
        crop_pic(EVID/label/'quatro-especies.png',(800,54+n*140,1170,158+n*140),42+side*262,y+28,249)
    lines(trait,y=y+13,size=9,leading=12)
end()

start('03','Tamanho sem deformar o corpo',
      'Menor e maior exemplar seguem as regras que já existiam no piloto da PR #5.')
text(230,692,'MENOR',10,MUTED,True);text(440,692,'MAIOR',10,MUTED,True)
for n,(name,science,_) in enumerate(names):
    y=548-n*136
    text(42,y+110,name,12,INK,True)
    crop_pic(EVID/'depois/quatro-especies.png',(480,54+n*140,1170,158+n*140),80,y+20,470)
    text(42,y+5,'Escala uniforme: 0,55 a 1,20 nos extremos sintéticos do piloto.',9,MUTED)
lines('O envelope lógico continua 36x24. Medidas permanecem provisórias de design e não comparam o comprimento real de espécies diferentes. Desenhos detalhados usam 72x48; em 1x, a microtextura é simplificada.',y=97,size=9,leading=13)
end()

start('04','Dentro da interface existente',
      'Capturas reais dos widgets Qt com descobertas sintéticas e movimento congelado.')
text(42,697,'640x700 - DESKTOP',10,MUTED,True)
text(390,697,'320x568 - COMPACTO',10,MUTED,True)
pic(NEW/'museu-640.png',42,320,330)
pic(NEW/'museu-320.png',391,379,162)
lines('O painel mantém nomes, recordes, seletores e rolagem. O desenho detalhado é usado quando a escala física comporta 2x; no tanque compacto usa-se a versão simplificada, por vizinho mais próximo.',y=277,size=11,leading=17)
lines('Somente o tanque foi conectado ao novo renderer. Os ícones do seletor, a enciclopédia e a cena de pesca continuam com a arte compartilhada anterior.',y=201,size=11,leading=17)
lines('Estas imagens foram renderizadas em Windows sem exibição na tela. Não comprovam toque, Android nativo ou uso em dispositivo físico.',y=125,size=10,leading=15,color=MUTED)
end()

start('05','Além dos quatro primeiros',
      'Arte dos passos 1-3 preservada. Pranchas completas dos 68 desenhos estão no GitHub.')
text(42,695,'RECIFE - PALHAÇO, CIRURGIÃO E BORBOLETA',10,MUTED,True)
pic(EVID/'depois/tanque-recife-2x.png',65,454,465)
text(42,423,'PROFUNDEZAS - PESCADOR, VÍBORA E ENGUIA-PELICANO',10,MUTED,True)
pic(EVID/'depois/tanque-abissal-2x.png',65,182,465)
lines('Barras, manchas e nadadeiras ajudam a distinguir moradores. Outros perfis incluem celacanto de cauda trilobada, peixe-lua sem cauda convencional, cavalinho-do-mar vertical e peixes chatos com olhos do mesmo lado.',y=150,size=10,leading=15)
lines('A representação é estilizada: não reproduz cada raio, escama, variação etária ou população. Nenhuma imagem externa foi incorporada.',y=83,size=9,leading=12,color=MUTED)
end()


# Steps 4-5: newly executed evidence, distinguished from the preserved stills above.
start('06','Movimento discreto',
      'Passo 4: cauda e peitorais. Quadros reais do renderer ampliados, sem mover o corpo inteiro.')
for col,frame in enumerate((0,2,6)):
    text(45+col*174,695,'QUADRO '+str(frame),10,MUTED,True)
for row,(name,science,_) in enumerate(names):
    y=552-row*136
    text(42,y+120,name+' / '+science,11,INK,True)
    for col,frame in enumerate((0,2,6)):
        crop_pic(NEW/'quadros.png',(20+145*frame,60+128*row,160+145*frame,153+128*row),
                 42+174*col,y+7,157)
lines('Cada ciclo tem oito fases visuais. As cadências de 0,18 a 0,24 s por quadro são escolhas artísticas. A pequena alteração de cauda/nadadeiras mantém o perfil reconhecível e os percursos existentes.',y=112,size=10,leading=15)
end()

start('07','Formas especiais também se movem',
      'Nadadeiras para formas altas; pequena articulação posterior nos corpos alongados.')
for n,(row,name) in enumerate(((4,'Cavalinho-do-mar-pigmeu'),(5,'Peixe-lua'))):
    y=506-n*180
    text(42,y+125,name,13,INK,True)
    for col,frame in enumerate((0,2,6)):
        crop_pic(NEW/'quadros.png',(20+145*frame,60+128*row,160+145*frame,153+128*row),
                 42+174*col,y+7,157)
        text(43+174*col,y-9,'Quadro '+str(frame),9,MUTED)
lines('Cavalo-marinho e peixe-lua recebem movimento nas nadadeiras. Moreia, tubarão-lagarto, peixe-lobo e enguia-pelicano articulam suavemente a região posterior. Não se trata de um modelo biomecânico.',y=273,size=11,leading=16)
lines('A fase é calculada somente pelo relógio visual do widget. Nenhum RNG da pesca é consumido, nenhuma captura é recalculada e nenhum estado de jogo é gravado. O cache guarda até 512 imagens pequenas.',y=194,size=10,leading=15)
link('Ver animação ampliada (GIF)',
     'https://github.com/BernardoJ/PescaIdle/blob/codex/piloto-tamanhos/docs/aquario-especies/movimento/evidencias/movimento-ampliado.gif',42,108)
link('Ver três peixes no tanque (GIF)',
     'https://github.com/BernardoJ/PescaIdle/blob/codex/piloto-tamanhos/docs/aquario-especies/movimento/evidencias/aquario-piloto.gif',42,87)
text(42,62,'Os GIFs do tanque são clipes de 3,84 s; o reinício não representa o percurso contínuo.',8,MUTED)
end()

start('08','Conferência de geometria e custo',
      'Passo 5: evidência nova do código 0c29196a, usando apenas estado sintético.')
y=lines('10 testes aprovados. Revalidados os 68 quadros de repouso dos passos 1-3; todas as espécies apresentam ao menos cinco imagens distintas em cada nível de detalhe.',y=695,size=11,leading=16)
y=lines('1.088 desenhos em canvas expandido sem cortes; 122.400 amostras de posição com três peixes, dentro da água e sem sobreposição das vagas; 144 renderizações com combinações menor/maior e reversão.',y=y-15,size=10,leading=15)
y=lines('Estado, RNG global, arte compartilhada e seus caches preservados. Pausa/fechamento e retomada do timer conferidos. A verificação inicial detectou uma colisão bool/int no cache; ela foi corrigida e o teste definitivo passou.',y=y-15,size=10,leading=15)
text(42,505,'Percentil 95 do renderer, em milissegundos',12,INK,True)
headers=['Cena','Base quente','Novo quente','Base frio','Novo frio']
columns=[42,176,270,366,462]
for x,h in zip(columns,headers):text(x,482,h,9,MUTED,True)
import json
baseline=json.loads((NEW/'performance-base.json').read_text(encoding='utf-8'))['timings']
current=json.loads((NEW/'performance.json').read_text(encoding='utf-8'))['timings']
for row,(key,name) in enumerate((('empty_1x','Vazio 1x'),('empty_2x','Vazio 2x'),('pilot_1x','Piloto 1x'),('pilot_2x','Piloto 2x'),('special_1x','Formas 1x'),('special_2x','Formas 2x'))):
    yy=458-row*24
    values=[name,baseline[key]['p95_ms'],current[key]['p95_ms'],baseline[key]['cold']['p95_ms'],current[key]['cold']['p95_ms']]
    for x,value in zip(columns,values):
        text(x,yy,value if isinstance(value,str) else f'{value:.4f}'.replace('.',','),10)
y=lines('Por revisão: 7.200 amostras aquecidas e 180 com cache limpo, após aquecimento. Execuções seriais com o mesmo ambiente. Timer existente: 66 ms. Novo maior p95: 0,3429 ms aquecido e 2,1216 ms frio.',y=287,size=10,leading=15)
lines('Microbenchmark local, sem IC estatístico: não mede FPS do jogo, compositor, GPU, bateria ou Android. Pequenas diferenças não demonstram melhora nem equivalência. Android nativo e outras máquinas continuam sem teste.',y=190,size=10,leading=15,color=MUTED)
lines('Windows / Python 3.14.8 / PySide6 6.11.2 / Pillow 12.3.0. Nenhuma instalação foi necessária. Não foram repetidas as suítes históricas de economia, migração e offline, cujos componentes não mudaram.',y=101,size=9,leading=13,color=MUTED)
end()

start('09','Demonstração com dois cliques',
      'Executável Windows separado: visualizador em memória, sem motor de pesca nem save.')
text(42,695,'EXE - 640x700',10,MUTED,True)
text(390,695,'EXE - 320x568',10,MUTED,True)
pic(NEW/'demo-exe-640.png',42,318,330)
pic(NEW/'demo-exe-320.png',391,377,162)
lines('Baixe e abra. Escolha um grupo ou qualquer uma das 68 espécies. Pause e avance quadros; nos quatro peixes medidos, compare menor e maior. As seleções duram apenas nesta sessão.',y=281,size=11,leading=16)
lines('Smoke da fonte e do EXE aprovado: controles, tamanhos de janela, mudança de exemplar, timer e fechamento. Inspeção do pacote confirmou sete módulos compilados e 63 assets. Módulos de motor e persistência estão ausentes.',y=211,size=10,leading=15)
text(42,135,'50.401.961 bytes | código: 0c29196ac261ed04faf153121a1f8a01b1869cfc',9,MUTED)
text(42,117,'SHA-256: 8d0bbd23dacd826cf2eede09b78fba470d76261527120205b417a43eaad8fffb',8,MUTED)
link('Baixar a demonstração visual',
     'https://github.com/BernardoJ/PescaIdle/raw/refs/heads/codex/piloto-tamanhos/PescaIdle-Aquario-Demo.exe',42,88)
text(42,64,'Esta demonstração não substitui o executável histórico do jogo completo.',9,MUTED)
end()

start('10','Fontes, reprodução e limites',
      'O relatório reúne os cinco passos e distingue evidências preservadas de verificações atuais.')
y=695
for title,url in [
('Passos 1-3: referências individuais dos 68 desenhos',
'https://github.com/BernardoJ/PescaIdle/blob/codex/piloto-tamanhos/docs/aquario-especies/referencias.md'),
('Lambari: revisão taxonômica (De Lucena e Soares, 2016)',
'https://publication.plazi.org/id/4652FFA7FF950E7CFFC1FFEDA47BFFC0'),
('Tilápia-do-nilo: ficha FAO de espécie cultivada',
'https://www.fao.org/fishery/docs/DOCUMENT/aquaculture/CulturedSpecies/file/en/en_niletilapia.htm'),
('Carpa-comum: ficha FAO de espécie cultivada',
'https://www.fao.org/fi/static-media/FI/CDrom/aquaculture/I1129m/file/en/en_commoncarp.htm'),
('Traíra: estudo de linhagens em Brazilian Journal of Biology',
'https://www.scielo.br/j/bjb/a/TVNZcLKcYTSkWfvh8m39jLr/?format=pdf')]:
    text(42,y,title,10,INK,True);link('Consultar fonte',url,42,y-18);y-=48
text(42,432,'Reproduzir em uma pasta de QA nova',13,INK,True)
for yy,value in [(409,'python -B tools/validate_aquarium_motion.py --out qa/revisao-movimento'),
                 (389,'python -B aquario_demo.py --smoke --out qa/demo-fonte'),
                 (369,'python -B aquario_demo.py')]:
    text(42,yy,value,9)
link('Comandos completos, build, pacote e resultados observados',
     'https://github.com/BernardoJ/PescaIdle/tree/codex/piloto-tamanhos/docs/aquario-especies/movimento',42,341)
lines('As pranchas estáticas dos passos 1-3 são da execução anterior em 23/10/2026. O quadro zero foi revalidado agora em todas as espécies. Os testes de movimento, limites, UI e pacote deste relatório foram executados no código 0c29196a.',y=303,size=10,leading=15)
lines('Arte e movimento são estilizados. As medidas continuam parâmetros de design. O isolamento da captura e da demonstração configura perfil e temporários antes dos imports; nenhum save pessoal foi lido, migrado ou gravado.',y=224,size=10,leading=15)
lines('Screenshots e QTest Windows não equivalem a teste em aparelho Android ou a uma sessão humana prolongada. A avaliação estética final cabe ao proprietário. Publicação na PR #5 em rascunho, sem merge, release ou mudança de visibilidade.',y=144,size=10,leading=15,color=MUTED)
end()
c.save()
print(OUT.name)
