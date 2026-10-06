# Validação da atualização gráfica

Todos os testes usaram `TemporaryDirectory` ou `PESCA_IDLE_SAVE_PATH` próprio. O save real em APPDATA não foi carregado nem escrito.

## Cobertura

`tools/validate_game.py` executa **337 verificações**: renderizações de repouso, fisgada, captura e conquista; todos os 91 cosméticos e 11 níveis de barco; prévia sem mudança de equipamento; compra/equipamento de cada item; ausência de cobrança repetida; descarte da prévia; enciclopédia vazia, descobertas e ordenação; upgrades; recompensa; save antigo com slot ausente; salvamento e recarga; limite offline; pausa, retomada, captura ao final da fisgada; eventos de arraste; flags da janela; posição inicial; menu; fechamento; limite do cache e ampliação inteira em pixels físicos na cena e na prévia. Status e conquistas são exercitados pelo fluxo modal real; um inventário longo exige rolagem sem perder textos ou exceder a tela.

A animação ambiental foi verificada por mudanças visíveis nas camadas de céu, água e vegetação, máscaras que preservam a sobreposição de árvores e margens, presença do meteoro noturno e sua ausência diurna, borboletas diurnas e coruja noturna, e preservação do gerador aleatório da pesca. Respiração, piscar e movimento de cauda/orelha/nadadeira foram conferidos para cada um dos 14 mascotes, incluindo pés fixos entre poses. As 13 bandeiras têm quadros distintos; as 11 varas têm artes distintas e a isca se move sob a boia.

O teste substitui o relógio local em 00h, 06h, 09h, 12h, 18h e 22h, verifica as seis atmosferas, paleta própria de meio-dia, interpolação entre camadas e alpha do primeiro plano. O renderer em execução acompanha uma mudança do relógio sem mudança de fase de animação ou progresso salvo. Todos os 91 cosméticos são renderizados também à meia-noite, ao amanhecer, ao meio-dia e ao entardecer.

Os quatro clipes de 12 segundos `animacao.gif`, `ambiente.gif`, `noite-animada.gif` e `ciclo-dia-noite.gif` mostram o renderer real. O último acelera 24 horas exclusivamente para demonstração; o jogo usa o horário real do dispositivo. `ciclo-horarios.png` registra os seis horários; `mascotes-quadros.png` registra as quatro poses de cada mascote. Sprites, máscaras e 96 camadas de iluminação são preparados uma vez, sem caches por instante da animação.

A simulação offline foi comparada à versão original do commit `b4ef8c7`, com as mesmas sementes aleatórias, nos níveis 0, 3 e 10. Texto do resumo e estado final coincidiram, incluindo moedas, inventário e conquistas.

As médias da versão final ficaram entre **1,9 e 2,2 ms** nesta máquina, incluindo execuções paralelas e interpolação da iluminação, diante do intervalo de 66 ms do relógio. Assets estáticos são carregados uma vez; cache de sprites é limitado a 192 entradas. As 96 camadas de cenário e primeiro plano ocupam aproximadamente 27 MiB fixos.

## Escalas e executável

As 337 verificações passaram no render offscreen padrão, no backend Windows nativo e com fatores Qt 1,25, 1,5 e 2. As imagens e resultados ficam em `docs/visual/dpi-native/`, `dpi-1.25/`, `dpi-1.5/` e `dpi-2/`. Esses fatores são simulações de escala Qt; não representam troca física de monitores ou alteração da configuração de DPI do Windows.

O Windows desta máquina já estava em 125%. Por isso os fatores adicionais Qt produziram DPRs de 1,5625, 1,875 e 2,5, registrados nos JSONs. O viewport adaptado usa respectivamente 3×, 4× e 5× em pixels físicos. No executável sem fator adicional, o DPR 1,25 usa 3×. O texto permanece na escala normal do Qt.

O smoke test de `dist/PescaIdle.exe` passou com o backend Windows, save isolado e outra pasta de trabalho. Exporta cena, seis horários, loja e enciclopédia; verifica execução congelada, assets, 45 sprites dos novos atlases, ícones, 96 camadas de iluminação, 14 mascotes animados e 13 bandeiras animadas. O horário real foi registrado como NOITE nesta execução. Os resultados ficam em `docs/visual/executavel/resultado.json`.

## Limites

Arraste e menu foram exercitados por eventos Qt; não houve uma sessão manual prolongada de jogo nem teste em vários monitores físicos. O comportamento de DPI ao mover a janela entre monitores de escalas diferentes deve ser conferido nesses equipamentos. A tipografia usa fontes do Windows, sem redistribuir os arquivos de fonte. Amanhecer e entardecer usam faixas fixas do horário local, sem localização ou astronomia; a isca é visual, preservando as regras originais de pesca.

## Evidências visuais

`antes.png` registra a versão original. `comparacao.png` mostra a arte original com ampliação inteira de 4× e a nova cena a 2×, em áreas equivalentes. Os PNGs de estados, as galerias do catálogo e `animacao.gif` são saídas do renderer integrado, não mockups.

Os masters gerados foram integrados em `assets/source/`, preparados em paletas limitadas sem dithering e refinados com rostos, roupas, animação de antebraço, assento e contato em pixels. Os prompts completos e o modo usado estão em `assets/ART_DIRECTION.md`.

Os atlases de chapéus, mascotes e boias substituem as grades antigas na cena e nos ícones da loja. `itens-chapeus.png`, `itens-mascotes.png` e `itens-boias.png` exibem os sprites finais com ampliação inteira; as galerias `catalogo-*.png` mostram cada item no barco.
