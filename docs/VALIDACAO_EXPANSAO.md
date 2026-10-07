# Validação da expansão

Ambiente observado: Windows 11 26100, Python 3.14.8, PySide6 6.11.2,
PyInstaller 6.22.3, Pillow 12.3.0. Dependências do ambiente local foram reutilizadas;
nenhuma instalação global. Diretórios de QA, saves, imagens e build ficaram em
uma pasta temporária exclusiva; artefatos de referência anteriores não foram
sobrescritos. Save pessoal nunca foi lido.

## Execuções observadas

| Verificação | Resultado |
|---|---|
| Documento, SHA/manifest e comparação contra base atual | 8 mapas, 88 entradas, 90 ocorrências, 56 células válidas |
| Baseline antes de editar | 337 verificações do jogo + 1.359 de cosméticos passaram |
| Matriz integrada CAT/CLK/EVT/OFF/EXP/SAV/ACH/UI/ART/PERF | 5.920 verificações passaram |
| Regressão de cosméticos preservada | 1.359 verificações, incluindo 1.232 composições de mascotes |
| BAL-01/02 | 168 pools exatos e 7 começos ×30 sementes passaram |
| Arte | 56 cenas do renderer montadas e inspecionadas visualmente; dois chapéus e efeitos também |
| Perf | 100 trocas; cache pesado <=2, cosméticos <=192; 60 diálogos abertos/fechados sem timer órfão |

Relatórios brutos em [evidencias_expansao](evidencias_expansao). O relatório
matricial inclui as descrições de cada assert; não são resultados históricos
atribuídos a esta versão. A suíte global antiga e seu código foram preservados
em `docs/design`. Expectativas antigas de offline/probabilidade global mudaram
por design, com substituição explícita por testes históricos e pools regionais;
não foram reinterpretadas como uma comparação idêntica.

## Regressões encontradas e corrigidas

- Perfil novo herdava timestamp/UUID do default expandido: agora são próprios de
  cada perfil e o marcador legado vem do timestamp realmente salvo.
- Compra podia equipar em uma referência antiga do estado após conceder conquista:
  saldo, compra, equipamento e conquistas agora entram em um snapshot atômico.
- Segundo escritor encontrava erro de leitura do byte do lock no Windows antes
  do handler: a aquisição inteira trata o erro e fecha o handle.
- Enseada fora do cache tentava carregar caminho dos mapas novos: recarrega seu
  fundo/margem e ambiente originais.
- Identidades visuais de algumas espécies coincidiam: paleta/variante agora
  produz 88 sprites distintos, compartilhados por ícones e eventos.

Falhas de teste por nome de fixture (Cirurgião-patela) foram corrigidas no teste,
sem modificar o contrato do catálogo. Nenhum teste foi removido para aceitar
chance positiva de espécie proibida, perda de save ou renda duplicada.

## Desempenho observado

Baseline independente, mesma máquina: mediana 1,548 ms, p95 1,634 ms de render,
86,4 MiB de working set com um mapa e sem galerias grandes.

Matriz final: mediana 1,433 ms, p95 1,587 ms de render; carregamento de mapa fora
do cache mediana 317,9 ms, p95 343,6 ms. Working set no ensaio amplo variou
148,7–169,2 MiB e voltou a 149,4 MiB na amostra da viagem 90. Esse processo também
mantinha galerias de QA e widgets/sprites exercitados; a comparação de RAM com o
baseline mínimo tem cargas distintas. Cache limitado e amostras após 100 trocas
não comprovam ausência de todo vazamento em sessões indefinidamente longas.

## Reprodução

```powershell
$env:PESCA_IDLE_QA_DIR = Join-Path $env:TEMP ('pesca-qa-' + [guid]::NewGuid())
.\.venv\Scripts\python.exe tools\validar_catalogo_proposta.py docs\design\pescaidle_expansao_catalogo.json --legacy-source docs\design\pesca_idle_base_6b29b4a.py.txt --report "$env:PESCA_IDLE_QA_DIR\documento.json"
.\.venv\Scripts\python.exe tools\validate_game.py
.\.venv\Scripts\python.exe tools\smoke_exe.py dist\PescaIdle.exe
```

A suíte cria seus próprios perfis sintéticos antes de importar o jogo. `smoke_exe`
usa plugin Windows e cwd estrangeiro, testa migração v1 e os oito mapas. O build
inclui assets aninhados de produção, com masters, ZIP, fontes, saves e QA excluídos.
Proveniência do executável e resultado Windows constam no relatório de build.

## Limites

Qt offscreen exercitou widgets reais, filtros, compra, menus, arraste por eventos
Qt, pausa, fechamento e a composição visual. As imagens foram realmente
inspecionadas; isso não equivale a uma sessão longa de jogo humano, ou à cobertura
de todas as GPUs, resoluções e DPIs. As regras de escala física foram verificadas
em 100/125/150/175/200%. Teste Windows do executável é registrado separadamente.

O build novo passou no smoke Windows a 100% e com `QT_SCALE_FACTOR=1.25`: janela
base 512×288, ampliação física 2×; em 125%, janela 615×346 e ampliação física 3×
(a cena Qt utiliza retângulo fracionário para preservar os pixels físicos).
Na inspeção Windows, os campos de data e duração inicialmente tinham fundo
branco e texto claro; foram estilizados, e o executável foi recompilado e
retestado. Não se publicou o build com esses campos ilegíveis.

Replay usa offset salvo; mudança histórica de horário de verão não é reconstruída.
As curiosidades novas têm fatos taxonômicos conservadores e fontes verificadas;
curiosidades antigas foram preservadas, sem alegar nova revisão científica.
