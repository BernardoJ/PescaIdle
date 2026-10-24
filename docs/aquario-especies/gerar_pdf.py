"""Build the shareable visual report; reads sanitized evidence only, no product imports."""
from pathlib import Path
import os
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/aquario-especies'
EVID=DOC/'evidencias'
OUT=ROOT/'output/pdf/PescaIdle_Aquario_Especies.pdf'
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
c.setTitle('PescaIdle - Arte por espécie no aquário')
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
    text(42,H-78,title,24,INK,True)
    if subtitle:lines(subtitle,y=H-100,size=10)
    c.setStrokeColor(HexColor('#d6dbd4'));c.line(42,37,W-42,37)
    text(42,23,'PR #5  |  Código e arte: e4e9e3f40a6f  |  23/10/2026',8,MUTED)
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

start('01','Peixes com identidade própria',
      'Melhoria restrita aos moradores do tanque do museu. Arte original em pixel art.')
lines('68 espécies elegíveis recebem formas e marcas próprias. O tanque conserva três espaços, a regra de tamanho por exemplar e o movimento existente.',y=692,size=12,leading=18)
text(42,619,'ANTES - HEAD DA PR #5 EM 0f516e89c4bb',10,MUTED,True)
pic(EVID/'antes/tanque-iniciais-2x.png',65,378,465)
text(42,349,'DEPOIS - CÓDIGO E ARTE EM e4e9e3f40a6f',10,MUTED,True)
pic(EVID/'depois/tanque-iniciais-2x.png',65,108,465)
lines('Lambari, Tilápia-do-nilo e Carpa-comum no mesmo cenário e fase. Capturas sintéticas dos widgets; nenhuma partida ou save pessoal foi utilizado.',y=83,size=9,leading=12)
end()

start('02','Quatro espécies, quatro desenhos',
      'Mesmo exemplar grande e mesma escala. A diferença está na representação visual.')
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
pic(EVID/'depois/museu-desktop.png',42,320,330)
pic(EVID/'depois/museu-compacto.png',391,379,162)
lines('O painel mantém nomes, recordes, seletores e rolagem. O desenho detalhado é usado quando a escala física comporta 2x; no tanque compacto usa-se a versão simplificada, por vizinho mais próximo.',y=277,size=11,leading=17)
lines('Somente o tanque foi conectado ao novo renderer. Os ícones do seletor, a enciclopédia e a cena de pesca continuam com a arte compartilhada anterior.',y=201,size=11,leading=17)
lines('Estas imagens foram renderizadas em Windows sem exibição na tela. Não comprovam toque, Android nativo ou uso em dispositivo físico.',y=125,size=10,leading=15,color=MUTED)
end()

start('05','Além dos quatro primeiros',
      'Pranchas completas dos 68 desenhos acompanham a documentação no GitHub.')
text(42,695,'RECIFE - PALHAÇO, CIRURGIÃO E BORBOLETA',10,MUTED,True)
pic(EVID/'depois/tanque-recife-2x.png',65,454,465)
text(42,423,'PROFUNDEZAS - PESCADOR, VÍBORA E ENGUIA-PELICANO',10,MUTED,True)
pic(EVID/'depois/tanque-abissal-2x.png',65,182,465)
lines('Barras, manchas e nadadeiras ajudam a distinguir moradores. Outros perfis incluem celacanto de cauda trilobada, peixe-lua sem cauda convencional, cavalinho-do-mar vertical e peixes chatos com olhos do mesmo lado.',y=150,size=10,leading=15)
lines('A representação é estilizada: não reproduz cada raio, escama, variação etária ou população. Nenhuma imagem externa foi incorporada.',y=83,size=9,leading=12,color=MUTED)
end()

start('06','O que foi entregue e conferido',
      'Arte, integração restrita ao tanque, ferramenta reproduzível e evidências sanitizadas.')
y=695
for head,body in [
('Implementação','Novo pesca_museu_visual.py e assets/aquario_especies.json. Em pesca_museu_ui.py, troca do renderer do tanque e seleção de detalhe pela escala física. Gameplay, RNG, catálogo, valores, parâmetros de comprimento e formato do save preservados.'),
('Execução observada','Windows, Python 3.14.8 e PySide6 6.11.2. Em cada lado: 68 imagens distintas, cache compartilhado preservado, nenhum save criado. São 15 PNGs por revisão e manifestos com hashes dos arquivos/imagens.'),
('Comparação reproduzível','Antes: arquivos reais exportados do commit 0f516e89c4bb7b2935a5011801595429941431c6. Depois: código e arte de e4e9e3f40a6f99d7f40de8dd9bc7d94dc020bfbb. Mesmas descobertas e medidas sintéticas; fase zero.'),
('Isolamento','Captura configura perfil, APPDATA e temporários exclusivos antes dos imports. Não inicia o motor de pesca e não lê nem grava save. O host sintético proíbe commit.'),
('Limitações','Sem suíte de integração, simulação, migração, benchmark, build ou smoke de executável nesta tarefa. Executáveis e APKs anteriores não contêm esta arte. Android e aparelho físico não testados.'),
('Revisão artística','Fontes informativas estão no JSON e em referencias.md. Matrinxã, Piabanha, Curimbatá, Pintado e Pirarara têm documentação de microdetalhes mais limitada e isso está sinalizado. Aprovação estética final permanece com o proprietário.')]:
    text(42,y,head,12,INK,True);y=lines(body,y=y-19,size=10,leading=14)-18
link('Abrir a PR #5', 'https://github.com/BernardoJ/PescaIdle/pull/5',42,89)
link('Documentação, comandos e pranchas no GitHub',
     'https://github.com/BernardoJ/PescaIdle/tree/codex/piloto-tamanhos/docs/aquario-especies',42,70)
end()

start('07','Referências e reprodução',
      'Referências de identificação e morfologia, consultadas em 23/10/2026.')
y=695
sources=[
('Lambari - revisão taxonômica, De Lucena e Soares (2016)',
'https://publication.plazi.org/id/4652FFA7FF950E7CFFC1FFEDA47BFFC0'),
('Tilápia-do-nilo - ficha FAO de espécie cultivada',
'https://www.fao.org/fishery/docs/DOCUMENT/aquaculture/CulturedSpecies/file/en/en_niletilapia.htm'),
('Carpa-comum - ficha FAO de espécie cultivada',
'https://www.fao.org/fi/static-media/FI/CDrom/aquaculture/I1129m/file/en/en_commoncarp.htm'),
('Traíra - estudo de linhagens em Brazilian Journal of Biology',
'https://www.scielo.br/j/bjb/a/TVNZcLKcYTSkWfvh8m39jLr/?format=pdf'),
('Outros perfis - museus, NOAA, FishBase, STRI e literatura',
'https://github.com/BernardoJ/PescaIdle/blob/codex/piloto-tamanhos/docs/aquario-especies/referencias.md')]
for title,url in sources:
    text(42,y,title,10,INK,True);y-=18
    link('Consultar fonte',url,42,y);y-=33
text(42,y-2,'Reproduzir sem iniciar uma partida',14,INK,True);y-=29
y=lines('Use as dependências já disponíveis e uma pasta de QA inédita. O comando abaixo apenas captura o museu com estado sintético em memória. Os comandos da revisão anterior e a explicação completa estão no README da entrega.',y=y,size=10,leading=15)-15
for s in ['python tools/capture_aquarium_species.py',
          "  --source . --out qa/aquario-repro",
          "  --label 'Depois | Aquário por espécie'"]:
    text(50,y,s,10);y-=16
y-=22
y=lines('Arquivos de evidência: quatro pranchas de catálogo, uma prancha dos quatro peixes em menor/maior, oito imagens do tanque (quatro cenários x dois níveis) e duas capturas do museu por revisão. Os manifestos guardam as versões e hashes; não contêm perfis pessoais.',y=y,size=10,leading=15)
lines('Entrega de fonte e documentação na branch codex/piloto-tamanhos, mantendo o draft da PR #5. Nenhum merge, release ou mudança de visibilidade.',y=112,size=10,leading=15,color=MUTED)
end()
c.save()
print(OUT.name)
