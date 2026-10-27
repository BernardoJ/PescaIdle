# Comparação observada — 19/10/2026

## Resultado

**82/82 cenários equivalentes; código de saída 0.** Nenhuma divergência de produto encontrada nos comportamentos e no escopo comparados. Nenhuma correção de produto foi feita.

- Base fixa efetivamente executada: `2a0353ff7c1cae2dca69d08c222b0660770d4385` (schema 3).
- Candidato efetivamente executado: `b05f7820f9dc04ef479c84fad696ae80c8e72c60` (head da PR #5 no início; schema 4).
- O commit desta entrega acrescenta somente ferramentas, testes, fixture e documentação; não substitui os SHAs acima por uma branch móvel.
- Ambiente: `Windows-11-10.0.26100-SP0`; versões por processo: `{'base': {'python': '3.14.8', 'pyside6': '6.11.2'}, 'candidate': {'python': '3.14.8', 'pyside6': '6.11.2'}, 'self': {'python': '3.14.8', 'pyside6': '6.11.2'}}`. Git verificado nesta entrega: `git version 2.53.0.windows.3`. Sem instalações.
- Início/data de execução registrado: `2026-10-19T14:41:41.130882+00:00`. A data do relógio simulado é 18/10/2026, offset 0; não é a data de execução.
- Comparação completa em 38.79 s. Três subprocessos com timeout finito; tempos de exportação/execução por worker em resultado.json. Os controles adicionais têm seu tempo no log.

## Matriz e contagens reais

| Grupo | Casos | Eventos base | Eventos piloto | Divergências |
|---|---:|---:|---:|---:|
| historical | 48 | 16010 | 16010 | 0 |
| transition | 14 | 28 | 28 | 0 |
| pending | 2 | 2 | 2 | 0 |
| paused | 2 | 0 | 0 | 0 |
| expedition | 2 | 432 | 432 | 0 |
| migration | 2 | 0 | 0 | 0 |
| progression | 4 | 1104 | 1104 | 0 |
| offline | 8 | 9700 | 9700 | 0 |

Total por revisão: **27,276 eventos**, incluindo lixo e especiais. Não são recompensas somadas das duas revisões nem eventos do controle positivo acrescidos ao total.

Comparados estritamente: catálogo/preços efetivos, 168 pools e ordem dos IDs, sequência e quantidade de eventos, ganhos, saldo, inventários, tempos/contextos/pendentes, compras, upgrades, desbloqueios, saves/roundtrips e conquistas antigas. As fontes/assets exportadas permaneceram byte a byte inalteradas. Não se aplicou tolerância numérica.

Nas quatro progressões, foram executadas **74 ações de compra** reais: `{'buy_part': 72, 'buy_cosmetic': 2}`. A política é a da fixture (cadência 60 s e alvo nível 3), sem dinheiro inicial artificial nem mudança de preço. Não é uma estimativa de progressão até concluir o jogo.

## Consumo do RNG

Foram registradas **54,649 chamadas random() por revisão** e 0 de getrandbits(). A lista ordenada de chamadas/valores e os estados completos do RNG dos checkpoints coincidiram; os hashes por cenário estão no resultado. Não houve sorteio adicional para ajustar o resultado do jogo. O spy é uma classe de QA que retorna os valores de super(), sem editar produto; tempfile/UUID ficam fora dessa instrumentação.

## Alegação histórica verificada

O script recuperado conserva a matriz 8 sementes × dois inícios × três níveis × uma hora. Não houve ajuste para obter um número-alvo. Foram observados **48 fluxos / 16.010 eventos** em cada revisão. As 48 projeções individuais e o JSON projetado completo coincidiram com os artefatos recuperados.

SHA-256 do JSON histórico reproduzido: `674c75e744a877d4e136d39425bd7560253ef16c78e863573b2b11b3de6f8aaf`. O candidato reproduziu o mesmo hash. Isso comprova a correspondência do recorte histórico e de seus campos projetados, não a cobertura de persistência ou compras no comparador antigo; esses caminhos pertencem à extensão nova.

## Diferenças aditivas classificadas

O protocolo completo e a lista de campos normalizados estão no [README](../README.md). Não há descarte silencioso de capturas ou campos desconhecidos.

- 20,894 eventos com medida; pendentes contabilizados separadamente no JSON.
- 27,276 anotações size_news, inclusive listas vazias; 1,912 flags de recorde/primeira medida.
- 63 notificações de conquistas de tamanho, agregadas entre cenários independentes; os IDs finais por cenário também estão preservados. Não são 63 conquistas distintas de um jogador.
- 2 backups adicionais de migração schema 3 com bytes exatos no piloto.
- Observações de schema/estado de medidas e seletores do museu são quantificadas por cenário. Os campos econômicos comuns continuam estritos.

## Controles executados

O candidato foi executado novamente em processo/fonte exportada próprios, no mesmo SHA, com identidade/relógio/sementes equivalentes. O controle positivo coincidiu inclusive nos registros brutos das linhas do tempo.

Testes da ferramenta: **13 aprovados, 0 falhas, 0 erros**, sem skips. Os controles CLI abaixo foram subprocessos reais; as mutações ocorreram só nos registros sintéticos:

| Controle | Saída esperada | Saída observada |
|---|---:|---:|
| positive-self | 0 | 0 |
| negative-species | 1 | 1 |
| negative-balance | 1 | 1 |
| negative-order | 1 | 1 |
| incomplete | 2 | 2 |

Primeiras diferenças nos controles negativos internos:

- species: `$.scenarios.historico-s0-h7-n0.timeline[0].events[0].species_id`; código 1.
- balance: `$.scenarios.historico-s0-h7-n0.timeline[0].state.moedas_centavos`; código 1.
- order: `$.scenarios.historico-s0-h7-n0.timeline[0].events[0].id`; código 1.

Dados incompletos, timelines truncadas, configuração inválida e diretório de saída preexistente não passam. A saída preexistente mantém o sentinela sem receber novos arquivos. Campos de bônus desconhecidos não são removidos pela normalização; preços e horários permanecem observáveis.

## Comandos executados e reprodução

Foram executados os comandos abaixo usando o Python existente 3.14.8/PySide6 6.11.2 e Git 2.53.0.windows.3. Os caminhos privados dos binários foram omitidos; `python` e `git` devem apontar para esse ambiente. Os argumentos, revisões, sementes e diretórios relativos são os reais:

```powershell
python -X utf8 -B tools/comparar_fluxo_base.py --base 2a0353ff7c1cae2dca69d08c222b0660770d4385 --candidate b05f7820f9dc04ef479c84fad696ae80c8e72c60 --out qa/comparador-20261019-verificado
python -X utf8 -B tools/test_comparar_fluxo_base.py --run-dir qa/comparador-20261019-verificado --out qa/controles-20261019-verificado
python -X utf8 -B tools/relatorio_comparacao.py --run-dir qa/comparador-20261019-verificado --controls-dir qa/controles-20261019-verificado --out docs/piloto-tamanhos/comparador/execucao-20261019
```

A base é explícita e imutável; foi passado --git apontando para o Git observado nesta entrega. Acrescente esse argumento se necessário no seu ambiente. A pasta de evidência publicada já existe: para reproduzir o terceiro comando, use --out qa/relatorio-comparador-novo. Todos os diretórios de saída precisam ser novos. A fixture contém a matriz e todas as sementes.

O desenvolvimento da ferramenta teve execuções preliminares em diretórios v1/v2 preservados localmente. Os resultados publicados são da execução final identificada pelos hashes das ferramentas em resultado.json. Não foram sobrescritas evidências históricas da PR ou arquivos originais.

## Limitações

São testes diferenciais dos caminhos reais descritos, não prova formal de ausência de regressões. As compras usam métodos reais com adaptadores de apresentação e scheduler instantâneo; não é teste de clique, GUI ou timers. As pescarias temporais usam principalmente a Enseada, mais a viagem de pendente; os oito mapas têm pools comparados, não uma campanha temporal completa por mapa. Há 82 cenários finitos, não todas as sementes/níveis/horários possíveis.

Migração e persistência usam apenas fixtures sintéticas, sem saves pessoais. Não houve teste Android, CI, build novo, renderização, suspensão física, disco com falha ou concorrência ampla. O relógio usa offset zero, sem reconstrução de DST. Medidas/recordes/conquistas novas são classificados, não certificados quanto a todos os detalhes visuais ou distribuição por esta comparação.

Os JSONs publicados são resumos/hashes e dados sintéticos. Perfis, backups, snapshots exportados e registros completos de cada worker ficam locais e são regeneráveis por comando. Nenhum dado privado, credencial ou configuração de conta foi incluído.
