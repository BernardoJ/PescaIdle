# Balanceamento reproduzível

Baseline real: `6b29b4a0da3ce403dad4ff46e7f656659d2266f1`, extraído como fixture
imutável antes de editar tabelas. Valores das 49 entradas antigas, preços de
peças/cosméticos e fórmulas de equipamento foram preservados. As 39 novas
entradas receberam preço e peso regional próprios. Raridade é metadado, não
derivada de preço em tempo de execução. Novas entradas de peso 2 são Raras e
recebem bônus de vara; de peso >=3 são Incomuns. Isso é design do jogo, não uma
estimativa científica de abundância ou risco de extinção.

Disponibilidade é filtrada **antes** de bônus e normalização. Preferências são
1,0 em todos os horários permitidos. Indisponíveis têm zero exato. A incidência
de lixo é 4%; especiais usam 10% quando há candidatos, caso contrário essa
parcela volta aos peixes. Um sorteio plano da probabilidade efetiva concede um
único resultado. Nenhum catálogo global serve de fallback.

## Medições

Executado com Python 3.14.8, Windows 11 26100, catálogo v1. Ferramenta:
`python tools/balance_expansion.py`, com perfil temporário. Sementes 0–29.
Todas as 56 células × níveis de vara/barco 0, 3, 10: **168 pools exatos**.

Espera `Uniforme(10,20)/(1+0,15*vara)`, fisgada 1,5 s, recompensa
`round(valor*(1+0,2*barco),2)`. Média/hora usa o ciclo esperado. Percentis/hora são
amostrais, com 30 simulações por pool e sementes exportadas. Probabilidades de
cada espécie e categoria, média e variância/evento, média/hora, p10/mediana/p95
e descoberta elegível média/mediana estão no [JSON completo](evidencias_expansao/balanceamento.json).

Ponderação de 24 h usa 2/2/2/3/3/3/9 horas, sem tratar períodos como equiprováveis.
Cenários de equipamento em mapas ainda bloqueados são análises matemáticas,
identificados separadamente da progressão real de desbloqueio.

## Primeiro barco

Política igual nos dois casos: vara/barco 0, comprar cada peça de barco assim que
houver 30 moedas, sem comprar cosméticos; duas peças alcançam barco 1. Tempo
ativo, incluindo fisgadas. 30 sementes por começo. O catálogo antigo global não
tinha dependência de período, portanto seu resultado inicial se repete.

| Início | Baseline, mediana s | Expansão, mediana s | Razão |
|---|---:|---:|---:|
| Amanhecer | 486,5 | 205,6 | 0,423 |
| Manhã | 486,5 | 317,0 | 0,651 |
| Dia | 486,5 | 317,0 | 0,651 |
| Meio-dia | 486,5 | 233,7 | 0,480 |
| Tarde | 486,5 | 233,7 | 0,480 |
| Anoitecer | 486,5 | 205,6 | 0,423 |
| Noite | 486,5 | 146,2 | 0,301 |

Os sete cenários passaram no alvo mediana <=1,5×baseline. O início é mais rápido
com os peixes novos; não foi necessário alterar moedas antigas ou preços de
equipamento. Ganhos raros continuam muito variáveis. A meta mede a primeira
melhoria, não garante tempos uniformes até equipamento máximo ou coleção total.

Descobertas exportadas são medidas em **tempo ativo elegível** do pool fixo.
Tempo de calendário inclui espera por janelas, e depende das viagens e horários
em que o jogador abre o jogo; não se soma sete medianas como estimativa de uma
coleção completa. Horários e locais são convenções fictícias de conteúdo.
