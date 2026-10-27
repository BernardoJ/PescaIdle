# Clima diário

Implementação aprovada em 23/10/2026 sobre a PR #5, base fixa `c545ca652386d74372307bd6d52a91f84d1ed4a0`.

## Como usar

O botão com ícone de clima, ao lado do menu, abre **Clima de hoje**. Mostra as espécies com bônus e ônus, os percentuais, o mapa, a disponibilidade no horário e a justificativa da afinidade. O filtro permite consultar todos os mapas ou um local. O botão também aceita foco/tecla Espaço, e o menu oferece a mesma consulta. A enciclopédia mostra as afinidades das espécies descobertas.

O percentual modifica o **peso de encontro**, antes da normalização dentro do grupo de peixes ou encontros especiais. Não são pontos percentuais acrescentados à chance final. Casos † usam os fatores leves aprovados; por exemplo, Salmão-rosa +10% e Tainha -10% em ventania. Outras afinidades usam +20% ou -20%. Todos os fatores são positivos e os horários/mapas existentes continuam sendo respeitados.

## Calendário e regras

- Um clima por data civil do perfil, compartilhado pelos oito mapas: chuva, sol forte, neve/frio, ventania ou ameno, com chances nominais iguais de 20%.
- Mudança às 00:00 locais, com início inclusivo/fim exclusivo; datas consecutivas podem repetir o clima.
- O calendário v1 usa SHA256 de semente própria persistida e data ISO, em ordem de climas fixa. Não consome o RNG da pesca. Viajar, consultar, pausar ou reabrir não gera outro sorteio da mesma data.
- Os pesos são `peso_base * preferência_do_período * bônus_da_vara * fator_climático`, normalizados dentro dos grupos existentes. A participação de lixo e encontros especiais é preservada. Espécies indisponíveis seguem com chance zero.
- `ameno` e `legado` têm fator 1.0 e preservam as probabilidades anteriores. As animações são independentes de todos os sorteios da pesca.
- O contexto climático é congelado no começo da fisgada, com data/versão/ID/fim do dia. A entrega não sorteia de novo nem altera seu prêmio após meia-noite, viagem ou reabertura.
- Offline usa cada data/horário histórico dentro do primeiro trecho de até quatro horas. Expedição continua substituindo essa janela; só tempo decorrido é pago.
- O relógio online é o local do dispositivo. O replay mantém a política anterior de offset salvo; transições históricas de horário de verão não são reconstruídas.

## Conteúdo aprovado e arte

`assets/clima_especies.json` é a fonte das afinidades, grupos, justificativas e referências. Há 25 espécies com alguma afinidade e representantes nos oito mapas. Demais entradas são neutras. Os percentuais são decisões de jogo, não estimativas biológicas.

O peixe-lanterna-de-müller responde a chuva/sol somente com luz ou crepúsculo; à noite fica neutro. As afinidades de ventania, cirurgião-patela, mexilhão e peixe-lanterna são adaptações indiretas, explicitadas no painel e no catálogo. Chuva no píer representa o aporte costeiro de água doce nessa abstração; ventania usa referências de ressurgência, migração ou dispersão, sem simular direção de vento/hidrologia.

Arte original desenhada em Qt na grade lógica existente: nuvens com silhuetas já usadas pelo jogo, gotas/impactos, reflexos e luz quente, flocos, névoa fria e linhas de vento/espuma. Neve cai no Mar das Auroras; os demais locais usam apresentação fria/nublada. Sol forte à noite mantém o tratamento quente sem desenhar um sol noturno. A ventania acelera bandeiras e movimentos ambientais. Máscaras dos mapas e área do personagem são respeitadas. Efeitos cosméticos continuam independentes do calendário.

## Save e compatibilidade

Schema **5**, com marcador `pilot_kind=tamanhos-v1` preservado e campo `clima` versão 1. A migração de schemas 1-4 preserva progresso e cria backup pelas rotinas atômicas existentes, inclusive `.pre-schema-4.json`. Reabertura de v5 conserva a semente e instante de ativação; migração é idempotente.

O período anterior à ativação usa as regras anteriores (`legado`), sem inventar clima para capturas antigas. Uma fisgada já pendente recebe somente metadados legados: espécie, recompensa, medida e contexto anterior são preservados. Dados climáticos desconhecidos, inválidos ou fora do calendário suportado são recusados, preservando o arquivo.

O executável continua sendo o candidato isolado: perfil padrão `perfil-piloto/save.json` ao lado do EXE. Um perfil antigo encontrado nesse caminho é migrado com backup. Binários anteriores ao schema 5 não conseguem abrir o perfil atualizado; o backup anterior permite a recuperação da versão antiga. Esta entrega não acessa nem importa automaticamente o save pessoal em APPDATA.

## Reprodução das verificações

Usar o Python/PySide6/PyInstaller já disponíveis. Ferramentas abaixo estabelecem o perfil antes dos imports e aceitam somente diretórios novos em `qa/`, ignorado pelo Git.

```powershell
python -X utf8 -B tools/validate_climate.py --out qa/clima-minha-rodada
python -X utf8 -B tools/validate_climate_interactions.py --out qa/clima-interacoes-minha-rodada
python -X utf8 -B tools/validate_conquistas.py --out qa/regressao-minha-rodada
python -X utf8 -B tools/run_climate_smoke.py --out qa/smoke-fonte-minha-rodada
python -X utf8 -B tools/visual_climate_animation.py --out qa/animacao-minha-rodada
```

Comparação de progressão com os motores reais, em processos separados. BASE deve ser um checkout limpo do SHA fixo acima:

```powershell
python -X utf8 -B tools/compare_climate.py --base CAMINHO-BASE-c545ca6 --out qa/pares-minha-rodada
```

São 35 condições iniciais (sete períodos x cinco sementes), duas políticas de consulta do melhor destino por renda (3h/30min), 24h por execução, três modos (base real/ameno/clima). Upgrades são imediatos; compra completa de cosméticos é representada pelo saldo necessário, sem efetuar gastos cosméticos. Não é uma simulação da conclusão integral do jogo. Os dados base/ameno devem coincidir em ledger ordenado, RNG, inventário, moeda e marcos.

Build Windows e smoke sobre o EXE novo:

```powershell
$climaBuild = Join-Path (Get-Location) 'qa/build-minha-rodada'
New-Item -ItemType Directory -Path $climaBuild -ErrorAction Stop | Out-Null
foreach ($parte in @('tmp','appdata','localappdata')) {
    New-Item -ItemType Directory -Path (Join-Path $climaBuild $parte) -ErrorAction Stop | Out-Null
}
$env:TEMP = Join-Path $climaBuild 'tmp'
$env:TMP = $env:TEMP
$env:APPDATA = Join-Path $climaBuild 'appdata'
$env:LOCALAPPDATA = Join-Path $climaBuild 'localappdata'
$env:PESCA_IDLE_SAVE_PATH = Join-Path $climaBuild 'guard.json'
$env:PESCA_IDLE_CLIMATE_BUILD = '1'
python -m PyInstaller --noconfirm --distpath (Join-Path $climaBuild 'dist') --workpath (Join-Path $climaBuild 'work') PescaIdle.spec
# O novo arquivo é dist/PescaIdle-Clima.exe dentro de $climaBuild.
# O smoke aceita esse caminho; não é preciso substituir nenhum EXE histórico.
python -X utf8 -B tools/run_climate_smoke.py --exe (Join-Path $climaBuild 'dist/PescaIdle-Clima.exe') --out qa/smoke-exe-minha-rodada
```

## Evidências e limites

O relatório desta entrega e as evidências sanitizadas ficam em `docs/clima/`. Resultados históricos anteriores continuam nos seus diretórios, com as respectivas datas. Qt offscreen, prévias mobile e smoke Windows não equivalem a teste Android nativo ou sessão humana prolongada. A matriz enumera todas as combinações de clima/mapa/período/vara suportadas; não enumera cada data possível ou todas as combinações simultâneas de cosméticos.
