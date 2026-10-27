# Parâmetros do piloto — 18/10/2026

Todos os comprimentos abaixo são **valores provisórios de design**, não medidas biológicas verificadas. Não foram atribuídas fontes biológicas. São quatro espécies existentes na Enseada; nenhum mapa ou espécie foi criado. As outras espécies preservam suas regras e não recebem comprimento fictício.

Configuração única: `candidato/assets/tamanhos_piloto.json`. As constantes de modelo, faixas, escala e diversidade ficam ali, separadas dos preços/pesos do catálogo.

| Espécie | Mínimo (mm) | Típico / moda (mm) | Máximo (mm) | Diminuto (mm) | Excepcional (mm) | P(diminuto) exata | P(excepcional) exata |
|---|---:|---:|---:|---:|---:|---:|---:|
| Lambari | 40 | 90 | 180 | ≤ 58 | ≥ 155 | 4.889% | 5.161% |
| Tilápia-do-nilo | 120 | 300 | 600 | ≤ 185 | ≥ 516 | 4.966% | 4.959% |
| Carpa-comum | 180 | 500 | 1100 | ≤ 301 | ≥ 934 | 5.014% | 5.022% |
| Traíra | 100 | 350 | 800 | ≤ 193 | ≥ 675 | 4.996% | 5.000% |

## Distribuição e bordas

Triangular contínua limitada por mínimo `a`, moda `m` e máximo `b`. `F(x)=(x-a)²/((b-a)(m-a))` até a moda; acima dela, `F(x)=1-(b-x)²/((b-a)(b-m))`. Fora dos limites, F vale 0 ou 1. O típico é a moda, não a média nem a mediana.

A inversa da CDF recebe `u∈[0,1]`; o comprimento é `floor(x+0,5)` em milímetros e limitado novamente a `[a,b]`. `u=0` e `u=1` produzem os extremos no teste de bordas. O hash de eventos usa 53 bits e produz `0≤u<1`. O arredondamento pode atingir os extremos; nenhuma conquista exige um deles exatamente.

O corte pequeno é `floor(Q(0,05))`; o grande é `ceil(Q(0,95))`. Os cortes são inclusivos; entre eles, a faixa é habitual. Como há arredondamento para mm, as probabilidades efetivas são `F(corte_pequeno+0,5)` e `1-F(corte_grande-0,5)`, listadas acima. A faixa habitual tem a probabilidade restante. A esperança de espera por uma cauda em capturas repetidas de uma espécie fixa é `1/p`, aproximadamente 19,4–20,5 exemplares; isso não é tempo de progressão global ou promessa de retenção.

## Escala visual

Transformação uniforme por exemplar, com interpolação linear em dois trechos: mínimo→típico→máximo corresponde a **0,55→0,90→1,20**. A escala é limitada, monotônica e calculada com uma regra visual comum à espécie na sessão. Comprimentos históricos fora dos parâmetros atuais permanecem numéricos e usam a escala visual limitada. No lançamento da captura aplica-se também o fator-base existente de 2/3; no aquário, o fator-base é 1.

O sprite original 36×24 é desenhado com transformação de QPainter e filtro nearest. Não há regravação, redesenho ou redimensionamento dos recursos compartilhados. O pivô central e a inversão horizontal são mantidos. As três faixas de nado ajustam margens ao tamanho completo de cada sprite, incluindo os pixels transparentes, e preservam movimento e orientação. Ícones da interface continuam em tamanho fixo.

Essa compressão preserva legibilidade; não representa escala literal entre espécies. Peixes de espécies diferentes podem parecer semelhantes em porte mesmo com centímetros diferentes. Os valores numéricos prevalecem.

## Cinco conquistas sem bônus econômico

- Uma fita, muitas histórias: primeira captura medida.
- Pequeno notável: primeiro diminuto.
- Grande encontro: primeiro excepcional.
- Pequena coleção: diminutos de **3 espécies distintas** do piloto.
- Grandes lembranças: excepcionais de **3 espécies distintas** do piloto.

A diversidade usa conjuntos persistidos de IDs, sem contar repetições da mesma espécie. O objetivo 3 e a probabilidade nominal de cauda 0,05 são parâmetros de piloto sujeitos à revisão. Não bloqueiam compra, viagem ou a coleção principal.
