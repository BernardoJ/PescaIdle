"""Package only reviewed weather QA summaries, charts and the delivery report.

No product imports, profile data or network access. Requires previously completed
QA directories listed below; never runs the game or alters historical reports.
"""
import argparse,csv,hashlib,json,shutil
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
CODE='d1bcd5bb13cb58d7196221450be2a43124dfa233'
BASE='c545ca652386d74372307bd6d52a91f84d1ed4a0'
DEST=ROOT/'docs/clima'
MAPS=dict(enseada_do_poente='Enseada do Poente',rio_das_vitorias='Rio das Vitórias',mangue_das_raizes='Mangue das Raízes',pier_da_brisa='Píer da Brisa',recife_das_cores='Recife das Cores',mar_dos_ventos='Mar dos Ventos',mar_das_auroras='Mar das Auroras',fossa_das_lanternas='Fossa das Lanternas')
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evidence_sha(p):
    data=p.read_bytes()
    if p.suffix.lower() in {'.json','.csv','.md','.py'}:data=data.replace(b'\r\n',b'\n')
    return hashlib.sha256(data).hexdigest()
def package():
    # Explicit allowlist. No profile, save, seed/measurement dump or private log.
    ev=DEST/'evidencias';im=DEST/'imagens';ev.mkdir(parents=True,exist_ok=True);im.mkdir(exist_ok=True)
    sources={'clima':'qa/clima-publicacao/summary.json','interacoes':'qa/clima-interacoes-build/summary.json',
       'regressao':'qa/clima-regressao-publicacao/resumo.json','conquistas':'qa/clima-regressao-publicacao/individual/resultado.json',
       'auditoria':'qa/clima-regressao-publicacao/regressao/validate_audit/audit.json',
       'museu':'qa/clima-regressao-publicacao/regressao/validate_museum/museum.json',
       'expansao':'qa/clima-regressao-publicacao/regressao/validate_expansion/validacao-expansao.json',
       'cosmeticos':'qa/clima-regressao-publicacao/regressao/validate_cosmetics/cosmetics-validation.json',
       'comparacao':'qa/clima-paired/comparison.json','smoke-fonte':'qa/clima-source-build/summary.json',
       'smoke-exe':'qa/clima-frozen/summary.json','animacao':'qa/clima-animacao/summary.json',
       'arquivo-exe':'qa/clima-build/archive-verification.json'}
    for label,src in sources.items():
        data=read(src)
        # Already synthetic reports; additionally scrub machine-dependent paths.
        raw=json.dumps(data,ensure_ascii=False,indent=2)
        for prefix in [str(ROOT),str(ROOT).replace('\\','/'),str(ROOT).replace('\\','\\\\')]:raw=raw.replace(prefix,'.')
        (ev/(label+'.json')).write_text(raw+'\n',encoding='utf-8')
    shutil.copyfile(ROOT/'qa/clima-publicacao/economy-contexts.csv',ev/'economia-contextos.csv')
    image_names=['matriz-'+p+'.png' for p in ['amanhecer','manha','dia','meio_dia','tarde','anoitecer','noite']]
    image_names += [prefix+c+'.png' for prefix in ['hud-','painel-','mobile-','painel-mobile-'] for c in ['chuva','sol_forte','neve','ventania','ameno']]
    for name in image_names:shutil.copyfile(ROOT/'qa/clima-publicacao/images'/name,im/name)
    for name in ['exe-chuva.png','exe-neve.png','exe-painel-ventania.png']:shutil.copyfile(ROOT/'qa/clima-frozen/evidence'/name,im/name)
    shutil.copyfile(ROOT/'qa/clima-animacao/climas.gif',im/'climas.gif')
    rows=[]
    for mode in ['base','ameno','clima']:
        for r in read('qa/clima-paired/'+mode+'.json')['runs']:
            flat={k:v for k,v in r.items() if k not in ['inventory','milestones','weather_event_counts']}
            flat['mode']=mode;flat.update(r['milestones']);rows.append(flat)
    with (ev/'progressao-210.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    content=read('assets/clima_especies.json');species={s['id']:s['nome'] for s in read('assets/catalogo_expansao.json')['species']}
    affinities=[]
    for g in content['groups']:
        for mid in g['maps']:
            for sid in g['species']:
                for climate,value in g['factors'].items():
                    affinities.append(dict(mapa=MAPS[mid],especie=species[sid],clima=climate,modificador_percentual=value-100,
                      experimental=climate in g['experimental_climates'],periodos=','.join(g.get('periods',[])) or 'todos os períodos elegíveis',
                      justificativa=g['reason'],fontes=' | '.join(content['sources'][s]['url'] for s in g['sources'])))
    with (ev/'afinidades.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(affinities[0]));w.writeheader();w.writerows(affinities)
    manifest=dict(date_local='2026-10-23',repository='BernardoJ/PescaIdle',pr=5,branch='codex/piloto-tamanhos',
       starting_head=BASE,pr_base='2a0353ff7c1cae2dca69d08c222b0660770d4385',source_commit=CODE,
       executable='PescaIdle-Clima.exe',exe_bytes=(ROOT/'PescaIdle-Clima.exe').stat().st_size,exe_sha256=sha(ROOT/'PescaIdle-Clima.exe'),
       source_hashes=read('qa/clima-publicacao/summary.json')['source_sha256'],
       hash_policy='source_hashes: bytes efetivamente testados no checkout Windows. evidence_sha256: textos com CRLF normalizado para LF; binários em bytes originais. EXE sempre em bytes originais.',
       observations='Resultados desta tarefa, 23/10/2026 local; não são evidências históricas reapresentadas como novas.',
       evidence_origins=sources,
       excluded='Perfis, saves sintéticos ou pessoais, dumps de estado, caches, ambientes e logs de máquina não incluídos.')
    for name,h in manifest['source_hashes'].items():assert sha(ROOT/name)==h,name
    manifest['evidence_sha256']={str(p.relative_to(DEST)).replace('\\','/'):evidence_sha(p) for p in sorted(DEST.rglob('*')) if p.is_file() and p.name not in ['manifesto.json','RELATORIO.md']}
    write(ev/'manifesto.json',manifest)
    report=f'''# Sistema climático - entrega de 23/10/2026

Implementado e testado localmente; publicação destinada à PR #5, em rascunho. Não houve merge na main. As evidências abaixo foram produzidas nesta tarefa com dados sintéticos, em clone isolado, sem ler saves pessoais.

## Revisões e executável

- Repositório: `BernardoJ/PescaIdle`; branch remota: `codex/piloto-tamanhos`.
- Head de partida: `{BASE}`.
- Base da PR: `codex/android-auditoria`, `2a0353ff7c1cae2dca69d08c222b0660770d4385`.
- Commit do código compilado: `{CODE}`; branch local `codex/sistema-climatico-20261023`.
- Executável novo: `PescaIdle-Clima.exe`, {manifest['exe_bytes']:,} bytes; SHA-256 `{manifest['exe_sha256']}`.
- Build Windows x64: Python 3.14.8, PySide6/Qt 6.11.2, PyInstaller 6.22.3. Relatórios/PDF: Python 3.12.14 e ReportLab já disponíveis.
- O executável inclui os avanços anteriores desta branch: piloto, aquário, decorações e conquistas. Binários históricos foram preservados. Não é uma atualização do APK.

## Comportamento entregue

Cinco eventos diários: chuva, sol forte, neve/frio, ventania e ameno. Um calendário por perfil para os oito mapas; probabilidades nominais iguais de 20%, podendo repetir em dias consecutivos. Troca às 00:00 locais. Viajar, reabrir e consultar não rerrolam a data. Semente própria e SHA256 não consomem o RNG da pesca.

O ícone ao lado do menu é clicável e aceita teclado. O painel Clima de hoje lista bônus/ônus, porcentagens, disponibilidade atual e justificativas, com filtro por mapa. As afinidades também aparecem na enciclopédia das espécies descobertas. A consulta é somente leitura.

Foram integradas as 25 espécies aprovadas, incluindo todos os casos †, com representantes nos oito mapas. Modificadores usuais de +20%/-20%; experimentais † de +10%/-10%. São fatores de **peso**, não pontos percentuais de chance final nem percentuais biológicos. Pesos são normalizados dentro dos grupos anteriores; preços, duração de pesca, participação do lixo e encontros especiais não foram alterados. Espécies fora de mapa/horário continuam em zero. A tabela completa está em [afinidades.csv](evidencias/afinidades.csv) e as fontes/ressalvas no [catálogo](../../assets/clima_especies.json).

Peixe-lanterna-de-müller responde à luz/crepúsculo e fica neutro à noite. Chuva costeira, vento e afinidades indiretas são abstrações de jogo explicitadas com †; não há simulação de vento direcional, salinidade ou estações astronômicas. Ameno é neutro.

Efeitos originais em Qt: chuva com impactos; luz quente/reflexos; flocos no Mar das Auroras e atmosfera fria nos demais mapas; vento com espuma e movimento ambiental. Sol forte não desenha sol durante a noite. Pixels lógicos, máscaras de mapas e personagem foram mantidos. [Animação dos cinco eventos](imagens/climas.gif).

## Persistência, captura e offline

Schema 5, marcador `tamanhos-v1` preservado. Migração de v1-4 com backup e escrita atômica pelas rotinas existentes; v5 é idempotente. Saldo, inventário, cosméticos, conquistas e medidas preservados nos testes sintéticos. Clima/data/equipamento ficam congelados no início da fisgada; meia-noite, viagem, pausa ou reabertura não duplicam nem rerrolam a recompensa.

Antes da ativação climática, capturas/offline anteriores usam modo legado neutro; não foi inventado clima histórico para saves antigos. Offline percorre os horários históricos, limitado ao primeiro trecho de até quatro horas da ausência; expedição substitui a janela, sem renda paralela ou tempo futuro. Replay usa offset salvo como antes; não reconstrói mudanças históricas de horário de verão.

O EXE usa `perfil-piloto/save.json` junto dele, sem importar APPDATA. Se já houver perfil piloto ali, será migrado com backup. Um EXE antigo não abre schema 5; para voltar, é necessário restaurar uma cópia do backup anterior. Não executamos migração sobre o save do jogador.

## Verificações executadas agora

| Grupo | Resultado observado |
|---|---|
| Contratos novos | 14 testes; calendário, meia-noite, offsets, migração, idempotência, pending, RNG, offline e expedição |
| Regressão existente | 83 unitários: 44 conquistas, 17 tamanhos/pendências, 11 auditoria, 11 museu |
| Matriz de probabilidades | 3.080 contextos: 8 mapas x 7 períodos x 5 climas x 11 níveis de vara; zero erros de direção e zero bônus/ônus anulados |
| Economia por contexto | 33.880 combinações, acrescentando 11 níveis de barco; preços e limites preservados |
| Expansão/cosméticos | 5.920 verificações da expansão e 1.359 de cosméticos passaram |
| Arte | 280 cenas + 1.120 quadros adicionais; sete pranchas, um GIF com 48 quadros/240 cenas |
| Interações | 7.360 renders de itens individuais e 4.840 de pares vara/barco; 50 ciclos de diálogo sem timers vivos nem alteração de estado/RNG |
| Interface | 45 filtros; clique, teclado, viewport mobile 320x568, legibilidade e ausência de sobreposição do ícone |
| Windows EXE novo | Três processos passaram: salvar pendência, entregar e reabrir; schema 5, prêmio único e consulta clicável |

Desempenho observado offscreen: p95 entre 1,61 e 2,64 ms por cena nesta máquina. Isso não é benchmark de telefone ou garantia de FPS no dispositivo final. A regressão de conquistas mantém um campo histórico `base=d8032d6` no seu JSON; ele não identifica o código executado nesta rodada. Os hashes em [manifesto.json](evidencias/manifesto.json) identificam os arquivos efetivamente testados e compilados.

Durante a validação foram corrigidos recortes/contraste do painel e sobreposição do ícone na prévia mobile. Duas expectativas antigas de schema 4 foram atualizadas para a constante atual, mantendo as demais verificações de moeda/integridade. Nenhum teste de segurança foi removido.

## Estudo delimitado de progressão

Motores reais em processos separados: versão de partida, candidato em ameno e candidato com calendário. São 35 condições iniciais (7 horários x 5 sementes explícitas, 2026102300-2026102334), 2 políticas de consulta, 24h online por execução, 3 modos: **210 execuções e 2.383.508 eventos reais**. Data inicial 23/10/2026, UTC-03. As decisões usam renda esperada disponível, sem conhecimento de capturas futuras. Upgrades imediatos; cosméticos não são comprados: mede-se somente saldo suficiente para eles após upgrades.

**Base e ameno coincidiram exatamente** nos 70 pares: sequência ordenada, RNG final, inventário, moeda, equipamento e marcos. Com clima ativo:

| Medida pareada | Consulta a cada 3h | Consulta a cada 30min |
|---|---:|---:|
| Média das variações relativas de renda | -0,976% | +0,021% |
| Mediana da diferença de renda (moedas) | 0,00 | +826,10 |
| Média da diferença de renda (moedas) | -35.312,29 | +777,02 |
| IC95 aproximado da diferença média (moedas) | -70.837,33 a +212,76 | -1.018,73 a +2.572,77 |
| Diferença média de espécies descobertas | +0,314 | +0,200 |
| Diferença média de espécies com 10 registros | +0,571 | +0,457 |

Os dois intervalos de renda incluem zero e são condicionados a apenas 35 pares por política. Não demonstram ausência de efeito ou um limite universal. O arquivo [comparacao.json](evidencias/comparacao.json) contém médias, medianas, extremos, marcos atingidos e intervalos; [progressao-210.csv](evidencias/progressao-210.csv) contém as sementes e métricas por execução.

A consulta mais frequente teve vantagem média relativa de renda de **2,904% na base e 4,058% com clima**, mas descobriu menos espécies (-5,339%/-5,576%). São heurísticas econômicas, não estratégias ótimas de coleção; a consulta não implica viagem em toda decisão. Não é possível concluir que trocar seja necessário para jogar bem. Vale acompanhar essa vantagem em um estudo maior antes de qualquer novo balanceamento.

Nos cálculos de contexto fixo, a renda esperada por fisgada variou entre **-13,929% e +11,782%**. Isso é consequência de redistribuir encontros com valores diferentes, não de mudar preços. Esse cálculo não substitui a progressão de 24h, nem mede a conclusão integral. Não foram refeitas as 10.000 simulações antigas; seus tempos não são validados para o clima novo.

## Arquivos e reprodução

- Regras: `assets/clima_especies.json`, `pesca_clima.py`, integração pequena em catálogo/motor/save.
- Interface/arte: `pesca_clima_ui.py`, `pesca_clima_visual.py`, HUD, menu, enciclopédia e adaptação mobile.
- Empacotamento: spec/entrypoint para EXE novo e smoke isolado. Binários históricos inalterados.
- Testes: sete ferramentas climáticas/worker, contratos e atualização de duas expectativas de schema existentes.
- Documentação/evidências: este relatório, guia, CSV/JSON agregados, imagens, GIF, PDF e manifesto de hashes. Nenhum save, cache ou ambiente publicado.

Os comandos exatos de validação, comparação e build estão no [guia](../CLIMA.md); usam pastas novas em `qa/`, ignoradas pelo Git. Para recriar apenas este relatório a partir das saídas existentes: `python tools/report_climate.py --package` e, com ReportLab disponível, `python tools/report_climate.py --pdf`. Não importam o produto.

## Limites e pendências

Android nativo/APK não compilado nem testado nesta tarefa. GUI verificada por imagens de renderização Qt real e smoke automático do EXE, sem sessão humana longa ou teste de todos os dispositivos. Todas as combinações finitas da matriz indicada foram cobertas; não todas as datas, falhas de hardware, fusos/DST históricos ou combinações simultâneas de cosméticos. O estudo não mede offline de longo prazo, conclusão de todos os objetivos, retenção, museu completo nem ótimo global. A migração foi testada somente em fixtures sintéticas. Não houve instalação de dependências, mudança de segurança, visibilidade, merge ou release.

## Evidências gráficas

![Painel de bônus/ônus](imagens/painel-ventania.png)
![Prévia mobile](imagens/painel-mobile-sol_forte.png)
![Animação](imagens/climas.gif)

'''
    for p in ['amanhecer','manha','dia','meio_dia','tarde','anoitecer','noite']:report+=f'![Oito mapas / {p}](imagens/matriz-{p}.png)\n\n'
    (DEST/'RELATORIO.md').write_text(report.rstrip()+'\n',encoding='utf-8')
    print(json.dumps(dict(packaged=len(list(DEST.rglob('*'))),exe_sha256=manifest['exe_sha256']),ensure_ascii=False))

def pdf():
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PIL import Image as PILImage
    for name,file in [('Arial','arial.ttf'),('ArialB','arialbd.ttf')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
    output=ROOT/'output/pdf/PescaIdle_Relatorio_Clima.pdf';output.parent.mkdir(parents=True,exist_ok=True)
    W,H=A4;body=ParagraphStyle('body',fontName='Arial',fontSize=10,leading=14,textColor=colors.HexColor('#203244'),spaceAfter=9)
    small=ParagraphStyle('small',parent=body,fontSize=8,leading=11)
    title=ParagraphStyle('title',parent=body,fontName='ArialB',fontSize=23,leading=28,spaceAfter=16,textColor=colors.HexColor('#0b6a78'))
    sub=ParagraphStyle('sub',parent=body,fontName='ArialB',fontSize=14,leading=18,spaceAfter=10)
    story=[]
    def p(txt,style=body):return Paragraph(txt,style)
    def add(txt,style=body):story.append(p(txt,style))
    def heading(txt):story.append(p(txt,title))
    def section(txt):story.append(p(txt,sub))
    def image(name,width=490,maxheight=400):
        path=DEST/'imagens'/name;wi,hi=PILImage.open(path).size;scale=min(width/wi,maxheight/hi)
        return Image(str(path),width=wi*scale,height=hi*scale)
    def table(rows,widths):
        t=Table([[p(str(x),small) for x in row] for row in rows],colWidths=widths,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d8edf0')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),1,colors.HexColor('#0b6a78')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#d9e1e5'))]));return t
    heading('PescaIdle<br/>Sistema climático diário')
    add('Entrega de implementação e validação | 23 de outubro de 2026')
    add('Cinco eventos, oito mapas, 25 espécies com afinidades aprovadas e consulta clicável de bônus e ônus. Novo executável Windows compilado e testado com perfil temporário.')
    story.append(image('exe-chuva.png',maxheight=240));story.append(Spacer(1,12))
    section('O que o jogador recebe')
    add('Um clima para todos os mapas a cada data local: chuva, sol forte, neve/frio, ventania ou ameno. O botão do clima abre uma lista com percentuais, disponibilidade, justificativas e filtro de mapa. A enciclopédia também mostra as afinidades descobertas.')
    add('Neve visível no Mar das Auroras; nos outros mapas, atmosfera fria/nublada. Chuva tem impactos na água, o sol acrescenta luz e reflexos e o vento movimenta o ambiente. A identidade visual e o conteúdo anterior foram preservados.')
    add('PR de destino: github.com/BernardoJ/PescaIdle/pull/5. Branch codex/piloto-tamanhos. Esta entrega não faz merge na main.',small)
    story.append(PageBreak())
    heading('Regras e proteção do progresso')
    section('Calendário e captura')
    add('Chances nominais de 20% por clima; mudança às 00:00 locais, permitindo repetição. Semente própria persistida e SHA256 evitam consumir o RNG de pesca. Viajar ou reabrir não muda o clima da mesma data.')
    add('Modificadores usuais de +20%/-20% e experimentais † de +10%/-10% alteram o peso antes da normalização. Não são pontos percentuais de chance final. Mapas/horários inelegíveis continuam em zero; preços, duração e participação de lixo/encontros especiais foram preservados.')
    add('Clima, data e equipamento ficam congelados no início da fisgada. Meia-noite, troca de mapa ou reabertura não geram novo sorteio nem recompensa duplicada. O ameno reproduz as probabilidades anteriores.')
    section('Save schema 5 e offline')
    add('Migração v1-4 com backup e escrita atômica pelas rotinas existentes; v5 idempotente. Antes da ativação, o histórico recebe contexto legado neutro, sem inventar clima passado. Testes sintéticos preservaram saldo, inventário, medidas, cosméticos e conquistas.')
    add('Offline segue cada horário histórico até o limite existente de quatro horas. A expedição substitui essa janela; não paga em paralelo nem remunera tempo futuro. O replay mantém o offset salvo; não reconstrói DST histórico.')
    add('<b>Perfil do EXE:</b> perfil-piloto/save.json ao lado do arquivo, sem importar APPDATA. Se houver perfil antigo ali, migra com backup. Binários antigos não abrem schema 5: voltar exige restaurar uma cópia do backup. Nenhum save pessoal foi aberto durante esta tarefa.')
    section('Referência científica e abstração')
    add('As 25 afinidades aprovadas e suas fontes estão em assets/clima_especies.json. Percentuais são parâmetros de jogo. Casos indiretos de vento, salinidade, cirurgião e peixe-lanterna são sinalizados com †. O peixe-lanterna-de-müller permanece neutro à noite. O painel explica essas ressalvas.')
    story.append(PageBreak())
    heading('Consulta real: desktop e mobile')
    story.append(image('painel-ventania.png',maxheight=350));story.append(Spacer(1,9))
    add('Acima: filtro por mapa e lista de bônus/ônus em ventania. Abaixo: viewport 320 x 568, com título/ícone ajustados e duas áreas de rolagem legíveis. Prévia Qt; não é teste Android nativo.',small)
    story.append(image('painel-mobile-sol_forte.png',maxheight=270))
    story.append(PageBreak())
    heading('Evidências dos cinco climas')
    for c,label in [('chuva','Chuva'),('sol_forte','Sol forte'),('neve','Neve / frio'),('ventania','Ventania'),('ameno','Ameno')]:
        story.append(p(label,small));story.append(image('hud-'+c+'.png',maxheight=100))
    add('Capturas do renderer real. Sete pranchas completas em docs/clima/imagens cobrem os oito mapas e sete períodos; climas.gif mostra 48 quadros animados.',small)
    story.append(PageBreak())
    heading('Validações executadas')
    story.append(table([['Verificação','Resultado'],['Unitários','97: 14 climáticos + 83 de regressão'],['Probabilidades','3.080 contextos; zero erros de direção ou efeitos anulados'],['Economia','33.880 contextos com todos os níveis de vara/barco'],['Regressão adicional','5.920 verificações da expansão; 1.359 de cosméticos'],['Arte e UI','280 cenas + 1.120 quadros; 45 filtros; clique/teclado; 320 x 568'],['Interação visual','7.360 renders de cosméticos + 4.840 de pares vara/barco'],['Diálogos','50 ciclos; timers encerrados; estado/RNG intactos'],['EXE Windows novo','3 processos: pendência, entrega única e reabertura; todos passaram']], [145,350]))
    story.append(Spacer(1,16))
    add('p95 de desenho offscreen entre 1,61 e 2,64 ms nesta máquina. Não é garantia de FPS em outro hardware. As imagens foram inspecionadas; isso não substitui uma sessão humana prolongada.')
    add('Foram corrigidos recorte/contraste do painel e sobreposição do ícone mobile encontrados pela QA. Duas expectativas antigas de schema foram atualizadas; verificações de moeda e integridade mantidas.')
    add('O JSON da ferramenta antiga de conquistas ainda traz um campo de base histórica d8032d6. Os hashes do manifesto identificam o código desta rodada; esse campo antigo não foi usado como prova de revisão executada.',small)
    story.append(PageBreak())
    heading('Progressão: comparação delimitada')
    add('210 execuções com motores reais: base, ameno e clima; 70 por modo. Cada política tem 35 condições pareadas, sete horários e cinco sementes, com 24h online. Total de 2.383.508 eventos. Upgrades imediatos; consulta econômica de destinos a cada 3h ou 30min.')
    add('<b>Base e ameno foram exatamente iguais</b> nos 70 pares em sequência, RNG, inventário, moeda e marcos. Clima versus base:')
    story.append(table([['Medida','Consulta 3h','Consulta 30min'],['Média da variação relativa de renda','-0,976%','+0,021%'],['Mediana da diferença (moedas)','0,00','+826,10'],['Média da diferença (moedas)','-35.312,29','+777,02'],['IC95 da diferença média (moedas)','-70.837,33 a +212,76','-1.018,73 a +2.572,77'],['Descobertas: diferença média','+0,314','+0,200'],['Espécies com 10 registros: diferença média','+0,571','+0,457']], [225,135,135]))
    story.append(Spacer(1,12))
    add('IC95 normal aproximado, 35 pares por política. Ambos os intervalos de renda incluem zero; não demonstram equivalência universal. Os CSV/JSON incluem as sementes, marcos, extremos e hashes.')
    add('Rever destinos a cada 30min teve vantagem média relativa de renda de 2,904% na base e 4,058% com clima, mas menos descobertas (-5,339%/-5,576%). São heurísticas de renda, sem prova de ótimo; não demonstram necessidade de trocas frequentes. Cabe acompanhar esse efeito antes de rebalancear.')
    add('Renda esperada em contexto fixo: -13,929% a +11,782%. Isso vem da redistribuição de espécies, com preços preservados. Não equivale à progressão completa nem à duração de conclusão. Não foram refeitas as 10.000 simulações históricas.')
    story.append(PageBreak())
    heading('Reprodução e rastreabilidade')
    manifest=read('docs/clima/evidencias/manifesto.json')
    add('Head inicial: '+BASE,small);add('Código compilado: '+CODE,small)
    add('Base da PR: 2a0353ff7c1cae2dca69d08c222b0660770d4385.',small)
    add('Executável: PescaIdle-Clima.exe | 50.561.165 bytes.',small);add('SHA-256: '+manifest['exe_sha256'],small)
    add('Python 3.14.8, Qt/PySide6 6.11.2 e PyInstaller 6.22.3; Windows x64. Dependências já existentes. O PDF é gerado com ReportLab no Python 3.12.14 disponível.')
    section('Comandos principais')
    for line in ['python -X utf8 -B tools/validate_climate.py --out qa/nova-clima','python -X utf8 -B tools/validate_climate_interactions.py --out qa/nova-interacao','python -X utf8 -B tools/validate_conquistas.py --out qa/nova-regressao','python -X utf8 -B tools/compare_climate.py --base CAMINHO-BASE --out qa/novos-pares','python -X utf8 -B tools/run_climate_smoke.py --exe PescaIdle-Clima.exe --out qa/novo-smoke']:
        add(escape(line),small)
    add('Cada ferramenta exige pasta nova, isola perfil antes dos imports e escreve somente em qa/. O checkout-base deve estar no head inicial acima. Build e opções completas: docs/CLIMA.md. Relatório extenso: docs/clima/RELATORIO.md.')
    section('Limitações explícitas')
    add('Sem teste Android nativo, novo APK, sessão humana longa ou enumeração de todas as datas e combinações simultâneas de cosméticos. Sem estudo de retenção, conclusão de todos os objetivos ou ótimo global. Migrações somente sintéticas. Offline validado por contratos, fora do estudo online de 24h.')
    add('Código e evidências em branch de revisão; binários históricos preservados. Sem merge, release, deploy, alteração de visibilidade ou novas dependências. Nenhum save, segredo, perfil, cache ou ambiente virtual foi incluído nas evidências.')
    def footer(c,doc):
        c.saveState();c.setStrokeColor(colors.HexColor('#bed3d8'));c.line(48,40,W-48,40);c.setFont('Arial',8);c.setFillColor(colors.HexColor('#527080'));c.drawString(48,26,'PescaIdle | Clima diário | 23/10/2026');c.drawRightString(W-48,26,str(doc.page));c.restoreState()
    SimpleDocTemplate(str(output),pagesize=A4,leftMargin=50,rightMargin=50,topMargin=42,bottomMargin=54,title='PescaIdle - Relatório do sistema climático',author='PescaIdle').build(story,onFirstPage=footer,onLaterPages=footer)
    print(str(output))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--package',action='store_true');ap.add_argument('--pdf',action='store_true');args=ap.parse_args()
    if not args.package and not args.pdf:ap.error('Selecione --package ou --pdf')
    if args.package:package()
    if args.pdf:pdf()
