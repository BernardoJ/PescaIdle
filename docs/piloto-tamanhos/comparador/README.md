# Comparador reproduzível — 19/10/2026

Esta entrega acrescenta somente ferramentas, testes, fixtures sintéticas e documentação à PR #5. Não muda produto, parâmetros de tamanho, gameplay, economia ou fontes de RNG. Não executa Android, CI, merge ou deploy.

## Revisões fixas e procedência

- Jogo-base: **2a0353ff7c1cae2dca69d08c222b0660770d4385**. Confere com a base documentada: museu de três espaços e schema 3.
- Head da PR #5 conferido no início: **b05f7820f9dc04ef479c84fad696ae80c8e72c60**, branch `codex/piloto-tamanhos`, schema 4 exclusivo do piloto. Este é o candidato efetivamente comparado, não uma referência móvel.
- A base do PR permanece `codex/android-auditoria`, mas o comparador **não usa a branch como base**: exige o SHA fixo acima.

O roteiro original foi recuperado da entrega local anterior, no arquivo `comparar_fluxo_base.py` situado na raiz daquela entrega, **fora de `tools/` e do histórico Git**. A busca por `tools/comparar_fluxo_base.py` no histórico não o encontrou. Referências nos relatórios usavam o nome sem `tools/`. A cópia textual recuperada está em [comparador-original-20261018.py.txt](comparador-original-20261018.py.txt); não é a ferramenta atual e depende do antigo layout `base/` + `candidato/`.

SHA-256 do script recuperado: `4214202616622f51dcf85af24b3d5c2211997b65138c2424504d2db8ca47a6d1`.

Dependências do original: biblioteca padrão e PySide6, importado por `pesca_idle`. Comandos históricos, a partir daquela entrega local: `python comparar_fluxo_base.py base` e `python comparar_fluxo_base.py candidato`. Eles escrevem em `candidato/qa`; não foram executados sobre a pasta histórica para não sobrescrever seus resultados. A nova ferramenta executa os SHAs em cópias novas e verifica a correspondência das projeções.

Foram recuperados também os dois resultados sintéticos originais, que eram iguais. O hash do JSON projetado é `674c75e744a877d4e136d39425bd7560253ef16c78e863573b2b11b3de6f8aaf`. A [referência histórica](referencia-historica.json) preserva esse hash, contagens e 48 hashes individuais; os dumps antigos completos permanecem locais. A ferramenta nova recupera a matriz original e a estende; não apresenta a extensão como código histórico.

## Requisitos e comandos

Ambiente observado: **Python 3.14.8, PySide6 6.11.2 e Git**, no Windows. Foi reutilizado um ambiente existente, sem instalações. PySide6 é necessário porque os módulos reais importam a interface; o comparador não cria uma QApplication/janela. Use esse Python no comando `python` abaixo. Se Git não estiver no PATH, acrescente `--git CAMINHO_DO_GIT` ao primeiro comando.

A partir da raiz do checkout desta PR:

```powershell
python -X utf8 -B tools/comparar_fluxo_base.py --base 2a0353ff7c1cae2dca69d08c222b0660770d4385 --candidate b05f7820f9dc04ef479c84fad696ae80c8e72c60 --out qa/comparador-20261019-verificado
python -X utf8 -B tools/test_comparar_fluxo_base.py --run-dir qa/comparador-20261019-verificado --out qa/controles-20261019-verificado
python -X utf8 -B tools/relatorio_comparacao.py --run-dir qa/comparador-20261019-verificado --controls-dir qa/controles-20261019-verificado --out qa/relatorio-comparador-novo
```

As saídas devem ser **diretórios novos**. Na entrega publicada, os dados já executados estão em `execucao-20261019/`, não em `qa/`; portanto esses comandos não sobrescrevem evidências históricas. Se você já executou os comandos localmente, escolha outros nomes de saída e mantenha as referências correspondentes nos comandos seguintes. Nenhum comando faz fetch, instala dependências ou muda refs Git. Os SHAs precisam existir no clone.

Atributos Git restritos aos arquivos novos preservam os bytes da fixture e do script recuperado, além dos finais de linha das ferramentas. Assim, a configuração autocrlf do clone não muda os hashes usados como evidência. Nenhum atributo de arquivo de produto foi alterado.

O comando de comparação cria `work/base/source`, `work/candidate/source` e `work/candidate_self/source` usando `git archive` de cada SHA. Exporta somente fontes de produto e assets de runtime, sem EXE, Git, ferramentas antigas, CI ou relatórios. Cada revisão roda em processo próprio com seus módulos reais e caminho de importação verificado. O terceiro processo repete o candidato para o controle positivo.

Os perfis sintéticos ficam **dentro de cada fonte exportada**, em `source/qa/comparador/<papel>/`; `PESCA_IDLE_SAVE_PATH`, APPDATA, LOCALAPPDATA, TEMP/TMP e saída de QA são definidos **antes de importar o produto**. Isso respeita também o guard de persistência do piloto. Nenhum save pessoal é lido ou copiado. Os hashes das fontes/assets exportados são conferidos antes/depois.

## Matriz e lógica executada

Fixture exata: [`tools/fixtures/comparacao_tamanhos.json`](../../../tools/fixtures/comparacao_tamanhos.json). Data sintética **18/10/2026**, offset **0** explícito; início inclusivo conforme o produto. Sementes explícitas, identidades sintéticas determinísticas, relógio `time.time` controlado no filho e UTC/offset passados ao motor. O RNG de tamanho continua sendo o original de cada revisão.

| Grupo | Casos | Condições e caminhos reais |
|---|---:|---|
| Histórico recuperado | 48 | Sementes 0–7 × 07h/20h × vara/barco 0/3/10; 3.600 s; Enseada, saldo/inventário inicialmente vazios; `FishingEngine.advance` |
| Transições | 14 | Sementes 0/1, nível 3, 10 s antes de 05/07/09/11/14/17/20h, avanço de 30 s |
| Fisgada/persistência | 2 | Início 13:59:59,5; salvar/reabrir pendente, pausa de 30 s, mudar equipamento, viajar e entregar; confirmar novamente sem duplicar recompensa |
| Offline | 8 | Sementes 0/1 × 07h/20h × ausência 4h/8h; replay real, limite e retorno repetido |
| Pausa | 2 | Ausência de 4h pausada e retorno repetido |
| Expedição | 2 | Agendamento real para +1h, duração 1h; retorno antecipado e retorno após 3h; sem renda paralela |
| Migração/roundtrip | 2 | Fixture schema 3 com 500 capturas históricas sem medidas, saldo 1.234,50, equipamento/cosmético/museu; load/save/reopen reais e backup exato no piloto |
| Progressão | 4 | Sementes 0/1 × 07h/20h; uma hora; a cada 60 s, comprar uma peça de vara e uma de barco quando cabível até nível 3, depois tentar Boné azul se ainda não adquirido e houver saldo |

São **82 cenários por revisão**, não 82 progressões completas do jogo. O grupo histórico mantém níveis fixos. O grupo de progressão é uma política de compras limitada a uma hora; não estima longevidade nem conclusão global de coleção.

O motor, o replay, o catálogo, as probabilidades, o cálculo monetário, SaveStore e migração são os reais de cada revisão. Para compras, executam-se os métodos reais `JogoPesca.comprar_peca` e `LojaDialog.acao`, com um adaptador de apresentação: `tick` é uma ação instantânea porque o tempo já foi avançado pelo motor, e atualização de widgets/tooltip é substituída por stubs. Débito, preço, upgrade, conquistas e `_commit`/SaveStore permanecem reais. Não é teste de cliques ou integração completa da GUI.

A classe `TraceRandom` chama `super().random/getrandbits`, retorna o mesmo resultado e apenas registra chamadas/valores. Ela é usada na referência de Random do núcleo **somente no processo de QA**, sem editar arquivo de produto ou consumir sorteios adicionais. O namespace de tempfile/UUID não é instrumentado. A correspondência com o artefato original, gerado sem esse spy, verifica a transparência na matriz histórica. Os estados finais de RNG, quantidade e sequência das chamadas são comparados estritamente.

São comparados também preços e catálogo efetivos e **168 pools** (8 locais × 7 períodos × níveis 0/3/10), incluindo a ordem dos IDs de cada pool. Isso não significa que a matriz tenha executado pescarias temporais nos oito mapas.

## Normalização explícita

Não há tolerância numérica, arredondamento para comparar ou ordenação das listas de eventos. Capturas de lixo e especiais contam; nenhuma captura é descartada. Eventos, tamanho de listas, espécies, ordem/IDs, contexto/UTC, ganhos float e centésimos, saldo, inventários, registros, compras, equipamentos, desbloqueios, pendentes, tempos, estados e chamadas de RNG são estritos.

| Diferença aditiva admitida | Tratamento e prestação de contas |
|---|---|
| `event.measurement` | Apenas estrutura conhecida mm/faixa/regra; removida da projeção econômica e contada como captura medida; pendentes têm contagem própria |
| `event.size_news` | Somente lista de `primeira/menor/maior`; conta anotações e flags, inclusive listas vazias; não remove o evento |
| `schema_version=4` + `pilot_kind=tamanhos-v1` | Representado como schema 3 na comparação comum; versões originais e número de observações permanecem no relatório |
| `medidas_peixes` | Só estrutura reconhecida v1, semente/contadores e recordes conhecidos coerentes; conta observações, quantidade final e IDs de espécies por cenário |
| Cinco IDs/títulos de conquistas de tamanho | Filtrados das listas de IDs/avisos, com IDs finais e número de notificações contabilizados; toda conquista antiga continua estrita |
| `museu.exemplares` | Apenas seleção de três `menor/maior`, contada se presente; `museu.aquario` permanece estrito |
| Backup extra `pre-schema-3` | Só artefato declarado com bytes exatos na migração sintética; contado separadamente, sem eliminar outros resultados |

Campos desconhecidos não são descartados pela normalização. Um bônus indevido em metadados deixa de ser reconhecido como estrutura permitida e permanece visível à comparação. A normalização não valida todo o comportamento visual ou a distribuição de tamanhos: o alvo é equivalência dos comportamentos comuns, com diferenças aditivas documentadas.

## Códigos e controles

- **0:** comparação concluída e equivalente; na execução completa, reprodução histórica e controles também precisam passar.
- **1:** divergência; o JSON e o console mostram a primeira diferença e o resumo dos cenários.
- **2:** erro/configuração/worker incompleto ou expirado; nunca vira equivalência. Diretório de saída existente é recusado sem ser alterado.

`test_comparar_fluxo_base.py` compara os registros independentes do candidato consigo mesmo e invoca o CLI em controles negativos de **espécie**, **saldo** e **ordem**. As mutações atingem cópias dos registros sintéticos; não os módulos exportados. Inclui controles de execução incompleta, timeline truncada, configuração inválida, saída existente, campos desconhecidos, preços e horários. Não há testes removidos, skips ou falhas ocultadas.

O modo `--compare-records ESQUERDA DIREITA --out NOVO_DIR` compara dois registros completos já gerados, sem iniciar o jogo. A matriz e seu hash devem corresponder à fixture; ele é usado nos controles negativos. O teste cria esses arquivos automaticamente, sem exigir que o usuário edite dados manualmente.

## Resultados e limites

Consulte [relatório observado](execucao-20261019/RELATORIO.md), [resultado por cenário](execucao-20261019/resultado.json) e [testes/controles](execucao-20261019/testes.json). São evidências novas de 19/10/2026, separadas das evidências históricas da PR.

O orçamento é finito: três workers, 82 cenários cada, timeout de 180 s por worker e de 90 s nos subprocessos dos controles. Perfis, fontes exportadas e registros completos ficam em `qa/`, ignorado pelo Git. A publicação contém agregados, hashes, comandos e fixtures, não snapshots completos nem perfis.

Não houve correção de produto. Não cobre GUI real, renderização, sistema operacional suspenso, falhas físicas de disco, concorrência ampla, Android, CI ou progressão de toda a coleção. Não reconstrói fusos/DST históricos: a fixture usa offset zero. A migração é de dados sintéticos; nenhum perfil de jogador foi usado.
