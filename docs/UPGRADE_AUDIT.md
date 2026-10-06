# Auditoria do objetivo gráfico

Entrega final com arte original inspirada no acabamento dos RPGs de SNES. O código e os assets da atualização estão no branch `codex/upgrade-grafico`. `dist/PescaIdle.exe` foi recompilado e executado com assets locais, de outra pasta e com save temporário. A comparação artística está em `visual/comparacao.png`; o resultado é inspecionável nos PNGs e clipes do renderer real.

| Requisito | Implementação integrada | Evidência |
|---|---|---|
| Personagem | Sprite original, rosto expressivo, antebraço de fisgada/captura, pernas dobradas, banco e sombras de contato; casco dianteiro oculta apenas a parte baixa | `visual/encaixe-personagem.png`, `fisgada.png`, `captura.png`, `animacao.gif` |
| Itens e chapéus | 17 chapéus, 16 roupas, 14 boias, 14 mascotes e acessórios; material sombreado, elmos/capuzes com encaixes próprios, IDs originais | `visual/catalogo-*.png`, `itens-*.png`; 91 compras/prévias/equipamentos testados |
| Cenário | Composição em 256×144, montanhas atmosféricas, árvores orgânicas, cabana, margens rochosas, vegetação e reflexos fragmentados | `visual/comparacao.png`, `ciclo-horarios.png` |
| Barco | Madeira com volume, 11 níveis, cockpit, banco, camadas de casco, contato com água; balanço compartilhado pelo pescador e equipamentos | `visual/barcos.png`, `animacao.gif` |
| Vara | 11 rampas e detalhes próprios, vara segmentada e flexionada, cabo, carretilha e argolas ligados à mão | `visual/varas.png`, `fisgada.png`; 11 artes distintas verificadas |
| Isca | Anzol e pequena isca animada sob a boia; parte visual da pesca original | `pesca_equipamentos.py`, `visual/ambiente.gif`; movimento verificado |
| Mascotes animados | Quatro poses por mascote: repouso, respiração, piscar e movimento de cauda/orelha/nadadeira; pés fixos | `visual/mascotes-quadros.png`, `ambiente.gif`; os 14 verificados |
| Bandeiras animadas | Dobras com variação de luz e silhueta; mastro acompanha o barco | `visual/catalogo-bandeira.png`, `ambiente.gif`; as 13 verificadas |
| Fundo animado | Nuvens, pássaros com asas, vegetação com raiz fixa e estrelas discretas; máscaras preservam planos | `visual/ambiente-quadros.png`, `ambiente.gif`, `noite-animada.gif` |
| Água animada | Ondulações e brilhos em pixels, boia, interação do casco e reflexos de lanterna/lua atrás do barco | `visual/ambiente.gif`, `noite-animada.gif` |
| Sombras animadas | Peixes sob a superfície e sombra/reflexo do casco se deslocam independentemente, sem mover suas âncoras de contato | `pesca_ambiente.py`, `pesca_visual.py`, `visual/ambiente.gif` |
| Dia/noite pelo dispositivo | Relógio civil local lido a cada renderização; amanhecer, dia, meio-dia, entardecer e noite; paletas interpoladas, sol/lua em arcos | `visual/ciclo-horarios.png`, `ciclo-dia-noite.gif`; mudança de hora com jogo em execução testada |
| Eventos diurnos | Pássaros e borboletas nas margens durante a iluminação diurna | `visual/ambiente.gif`; exclusividade conferida |
| Eventos noturnos | Vaga-lumes, coruja sonolenta, estrelas cadentes e reflexos lunares durante a iluminação noturna | `visual/noite-animada.gif`; ausência do meteoro e da coruja de dia conferida |
| UI e menus | Molduras de RPG, ícones dos itens reais, seleção/hover/foco, prévia ao vivo, status/conquistas com rolagem, notificações com quebra de linha | `visual/loja.png`, `menu.png`, `enciclopedia*.png`, `status-painel.png`, `conquistas-painel.png` |
| Cozy/comfy | Luz quente nos focos, noite azul legível, movimentos pequenos e lentos, fauna tranquila e brilho breve no martelo | Clipes de dia/noite e inspeção das seis atmosferas |
| Funcionamento e saves | Economia, probabilidades, progressão, inventário, conquistas e offline preservados; janela arrastável e no topo; recursos sem rede | 337 verificações em cinco configurações; comparação com `b4ef8c7`; smoke test do EXE |

O GIF do ciclo acelera 24 horas apenas para demonstração. O jogo acompanha o relógio real, com faixas locais fixas, sem geolocalização. O save real não foi usado. Uma sessão manual prolongada e movimentação entre monitores físicos com DPIs diferentes não foram realizadas; os testes de interação usam eventos Qt. Detalhes e resultados estão em [VALIDACAO.md](VALIDACAO.md).
