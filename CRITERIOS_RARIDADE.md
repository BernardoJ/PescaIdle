# Critérios de raridade das capturas

O campo `peso` em `pesca_idle.py` é um peso relativo usado pelo sorteio: valores maiores tornam o encontro mais frequente. Ele não representa uma estimativa científica de indivíduos por área nem uma probabilidade natural exata. As faixas foram escolhidas para refletir, de forma jogável, a distribuição, a abundância, a dificuldade de observação e o risco de conservação descritos nas referências.

As avaliações da Lista Vermelha da IUCN classificam risco de extinção, não a abundância absoluta de todas as espécies. Por isso, a categoria de conservação é apenas uma das referências para os pesos; espécies abundantes em grandes cardumes ou em altas densidades recebem pesos maiores, enquanto espécies com populações muito pequenas, distribuição restrita ou pouquíssimos registros recebem pesos menores.

Alguns exemplos que orientaram os extremos da tabela:

- A NOAA reporta a vaquita como uma espécie à beira da extinção, com estimativa de até cerca de dez animais restantes: [NOAA Fisheries — Vaquita](https://www.fisheries.noaa.gov/species/vaquita/overview).
- Em outubro de 2025, o governo australiano estimava menos de 250 peixes-mão-vermelhos selvagens, mesmo após a soltura de animais criados em cativeiro: [DCCEEW — Red handfish](https://www.dcceew.gov.au/about/news/tiny-fish-big-future-65-red-handfish-released).
- A NOAA documenta que a lula-magnapinna foi confirmada em apenas cerca de uma dúzia de avistamentos: [NOAA Ocean Exploration — Bigfin squid](https://oceanexplorer.noaa.gov/expedition-feature/okeanos-ex2107-features-bigfin-squid/).
- A NOAA descreve o celacanto-africano como uma população pequena e isolada em uma das suas áreas de ocorrência, e manteve seu status de espécie ameaçada nessa região após a revisão de 2025: [NOAA Fisheries — African coelacanth](https://www.fisheries.noaa.gov/species/african-coelacanth/resources).
- Como contraste de abundância e pesca em grande escala, a anchoveta peruana respondeu por 5,7 milhões de toneladas de captura em 2024: [FAO — SOFI 2026, Americas](https://fao.sitefinity.cloud/americas/news/news-detail/sofi-2026/en). O Alaska pollock também é descrito pela NOAA como espécie de cardume amplamente distribuída e alvo de uma das maiores pescarias do mundo: [NOAA Fisheries — Alaska pollock](https://www.fisheries.noaa.gov/species/alaska-pollock/management).
- A IUCN explica as categorias de risco e ressalta que “Data Deficient” significa que faltam dados adequados para avaliar a espécie: [IUCN Red List — categorias](https://nrl.iucnredlist.org/).

A lista inclui mamíferos, tartaruga, moluscos e organismos planctônicos, além de peixes. Todos aparecem como encontros abstratos do jogo; isso não significa que sejam apropriados para pesca com vara na vida real. Os menores valores-base são 0,1 moeda. O multiplicador de nível do barco continua sendo aplicado ao valor de cada captura.
