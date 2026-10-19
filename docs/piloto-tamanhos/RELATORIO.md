> Registro da entrega local de 18/10/2026, anterior à publicação. Layout e comandos históricos foram preservados com caminhos privados removidos. Para baixar/executar esta branch, use [README da publicação](README.md). Nenhum teste foi repetido para este push.

# Piloto de tamanhos — entrega para revisão

Data: 18/10/2026. Implementação local, testes focados e build Windows; sem stage, commit, push, PR alterada, merge ou publicação.

## Base, isolamento e escopo

- Repositório de origem verificado: `BernardoJ/PescaIdle`, remote `https://github.com/BernardoJ/PescaIdle.git`.
- Checkout-fonte: `PescaIdle-museu-20261015`, branch `codex/museu-aquario-inicial`, HEAD **2a0353ff7c1cae2dca69d08c222b0660770d4385**. Museu de três espaços; save schema 3. Checkout limpo ao copiar e na conferência final. Não foram encontradas instruções AGENTS.md aplicáveis nas buscas e ancestrais verificados.
- A PR #4 foi consultada nesta tarefa: aberta, draft, head `1a7b10d3092de372b519ece8d2bb1f82c4a155a5`, base `codex/android-auditoria` em `2a0353ff7c1cae2dca69d08c222b0660770d4385`. Seus 17 arquivos são documentação/evidência, sem implementação de Fluxo/Precisão. A campanha anterior está na pasta irmã `avaliacao-fluxo-precisao-20261018`; não foi repetida nem integrada. Não houve nova busca por Serena/Seletiva.
- A pasta antiga do Desktop não foi usada como base: seu Git informou proteção de propriedade. Nenhum `safe.directory` foi adicionado. A cópia-fonte do museu forneceu uma base limpa verificável, sem trocar sua branch.
- Área isolada: `<entrega-local>`. Cópias `base/` e `candidato/`, sem `.git`; 373 arquivos versionados copiados com hashes. Distribuições antigas, ZIPs/PDFs, assets/source e CI não foram copiados; a lista exata está em BASE.json. Arquivos originais e não rastreados foram preservados. Nenhum arquivo preexistente foi apagado.
- Perfil padrão do EXE: `executavel/perfil-piloto/save.json`. Guardas validam o caminho antes de diretórios, lock e leitura; perfis fora da pasta do candidato são recusados. Todos os testes configuram perfis sintéticos explicitamente. Nenhum conteúdo de save pessoal foi lido.

## Implementado

Comprimento inteiro em mm para Lambari, Tilápia-do-nilo, Carpa-comum e Traíra, existentes na Enseada; exibição em cm. Parâmetros provisórios de design e distribuição triangular em PARAMETROS.md. As demais espécies seguem sem medida; preços, equipamentos, catálogo, disponibilidades e velocidades existentes não foram alterados.

O tamanho é anexado ao evento no início da fisgada, depois do sorteio da espécie/recompensa. O uniforme vem de SHA-256 da semente persistida do perfil + ID do evento + espécie, sem consumir o RNG do jogo. Medida e regra de origem são persistidas em `pesca_pendente`; uma medida já anexada não é recalculada. Entrega e recordes passam pela mesma transação de save da captura. Counter monotônico e ID aplicado impedem repetição no fluxo suportado.

Primeira medida estabelece ambos os recordes; comparações seguintes usam mm estritos. Empates preservam os metadados anteriores. Guardam comprimento, faixa, versão/limites de origem, ID do evento, instante UTC da fisgada, mapa e período. Não há inventário completo de exemplares individuais: persistem o pendente e os extremos; o resultado recém-entregue existe para a animação.

A enciclopédia mostra menor/maior e quantidade medida. A captura mostra aviso discreto de recorde. O offline processa todos os eventos do motor existente, mantém o limite de quatro horas e reúne novidades num resumo. As cinco conquistas não dão moeda/bônus e não afetam objetivos antigos.

O mesmo desenho original recebe escala por exemplar na captura e no museu, com pivô, proporção, inversão e filtro nearest. Os três espaços do museu escolhem menor/maior conhecido; escolhas anteriores de espécies são preservadas, com padrão maior. Espécie sem medida usa ilustração padrão e seletor de exemplar desativado. Os extremos exibidos acompanham novos recordes da espécie escolhida.

## Persistência e migração

Extensão aditiva: **schema 4 exclusivo deste piloto**, marcador obrigatório `pilot_kind=tamanhos-v1`, `medidas_peixes.version=1` e seleção opcional `museu.exemplares`. Não é a proposta de save v4 das varas. Não há intercâmbio automático com outros candidatos.

O código de escrita atômica, fsync, backup e lock exclusivo foi mantido. Em migração sintética v3, o arquivo original é copiado byte a byte para `save.pre-schema-3.json` antes da versão nova. Recarregar/migrar é idempotente. Saldo em centésimos, inventários, melhorias, cosméticos, conquistas e escolhas do museu permanecem. Capturas e pendentes antigos sem medida continuam sem medida; nenhum local/horário ou exemplar é criado retroativamente.

Schema 4 com extensão ausente, versão desconhecida, medidas inválidas ou quantidades incoerentes é rejeitado, sem redefinir silenciosamente os recordes. Arquivo válido anterior é preservado quando uma gravação inválida é tentada. Recuperação segue o mecanismo explícito existente; não foi implementada conversão de perfil pessoal.

Cada extremo conserva sua regra de origem. Alterar parâmetros numéricos da versão 1 não invalida recordes antigos nem muda faixas já conquistadas. A validação usa o snapshot, não os limites novos. Escala visual usa uma regra comum atual por espécie, com clamp. Um algoritmo/versão de regra futura exige suporte explícito; versões desconhecidas são recusadas. Não há downgrade automático ao jogo-base.

## Arquivos revisáveis

Diff completo: `ALTERACOES.patch`; inventário e hashes: `ENTREGA.json`. 16 arquivos no diff do candidato, sem remoções.

| Grupo | Arquivos | Finalidade |
|---|---|---|
| Modelo | assets/tamanhos_piloto.json; pesca_tamanhos.py | Parâmetros, sorteio independente, validação, recordes, faixas e metas |
| Integração | pesca_pescaria.py; pesca_conquistas.py; pesca_idle.py | Fisgada/entrega, conquistas, descrição e resumo offline |
| Persistência/isolamento | pesca_save.py; pesca_piloto.py | Schema aditivo, validação e limite de perfil |
| Visual/interface | pesca_tamanho_visual.py; pesca_visual.py; pesca_museu_ui.py; pesca_viagens_ui.py | Transformação por exemplar, seleção e recordes legíveis com rolagem |
| Candidato/build | piloto_entry.py; PescaIdle.spec; tools/pilot_smoke.py | Entrada separada, nome de EXE próprio e smoke sintético |
| Verificação | tools/verificar_tamanhos.py; tools/visual_tamanhos.py | Testes focados, amostragem e evidências de tela |

Os scripts auxiliares no nível desta entrega geram comparações, manifesto, resumo e relatório. Os documentos originais, módulo de museu de regras, catálogo, preços e todos os assets anteriores têm hashes preservados. Somente a configuração nova de tamanhos foi adicionada aos assets.

## Testes observados nesta tarefa

Ambiente disponível, sem instalações: Windows 11 build 26100, Python 3.14.8, PySide6 6.11.2, PyInstaller 6.22.3. Foi reutilizado o ambiente local `PescaIdle-integracao-20261006/.venv`. As evidências históricas do projeto não foram contadas como execuções novas.

| Verificação | Resultado |
|---|---|
| Núcleo | **12 testes, 0 falhas/erros**; execução final focada 1.665 s, log em candidato/qa/testes-nucleo.log |
| Distribuição | 100.000 amostras por espécie, quatro espécies; limites, monotonicidade e caudas verificadas |
| Repetição/recordes | Extremos, empates, concessão única, diversidade distinta, edição de parâmetros e reabertura sem rerrolagem |
| Migração | v3 sintético → piloto, backup exato, repetição idempotente, sem medidas retroativas; dados inválidos/futuros recusados |
| Online/offline | Quatro sementes, equipamento nível 3, quatro horas: mesmos inventários, saldo, RNG, pendentes, medidas e conquistas; retorno de oito horas respeita teto, retorno repetido não paga novamente |
| Pausa/expedição | Pausa sem medidas; expedição sintética de uma hora substitui a janela; repetição não duplica |
| Regressão comparada | **48 fluxos pareados e 16.010 eventos**, 8 sementes × 2 inícios (07/20h, offset 0) × níveis 0/3/10, uma hora cada: projeções exatamente iguais entre base e candidato |
| Visual | Windows Qt; 600 quadros/1.800 bboxes do aquário dentro dos limites; imagens de pequeno/típico/grande das quatro espécies, aquário misto e animação; cache original inalterado |
| Interface | Seleção menor por tecla e retirada por clique via **eventos injetados QTest**; demais filtros/ordenação por seleção programática; persistência/fallback de espécie sem medida conferidos |
| Viewport mobile | 320×568 e 360×800, museu/enciclopédia com rolagem; pequeno/típico/grande em 320×568. **Não é Android nativo** |
| EXE novo | Build completo; smoke Windows em três processos (pendente, entrega após reabrir, nova reabertura), todos exit 0, sem duplicar medida/saldo/conquista ou perder seleção |
| Conteúdo do EXE | Bytecode de 13 módulos/entrada igual ao fonte correspondente; 61 assets empacotados iguais byte a byte ao candidato |

A regressão compara IDs/ordem de espécies, UTC/contexto, recompensa em centésimos, inventário, saldo, fase/tempo restante e digest do estado RNG. Não é uma auditoria de todos os sistemas nem teste de progressão com compras.

Durante preparação visual, uma fixture sintética sem `gain` falhou; a fixture foi corrigida. A revisão das imagens encontrou recordes cortados na enciclopédia desktop; o candidato ganhou rolagem e o texto de recordes foi reposicionado. Os horários da medição foram corrigidos para partir de meia-noite UTC sintética antes das execuções finais; os resultados finais usam 07h/20h e offset 0 explicitamente. Os testes afetados passaram depois dessas correções. O build definitivo usou pasta de trabalho nova após congelar o fonte, sem aproveitar o primeiro build intermediário.

Avisos de empacotamento estão em `build-verificado/PescaIdle/warn-PescaIdle.txt`; há módulos opcionais de outras plataformas e alerta estático de collections.abc. Os caminhos exercitados pelo EXE não apresentaram erro de importação; isso não prova cobertura de módulos opcionais.

## Frequência medida das caudas

Cada espécie usa 100.000 uniformes de random.Random(20261018), com a mesma sequência reutilizada entre espécies. São amostras marginais por espécie, não 400.000 eventos independentes agregados. IC95% Wilson, sem correção de multiplicidade; não são garantias para cada sessão.

| Espécie | Diminutos observados | IC95% | Excepcionais observados | IC95% |
|---|---:|---|---:|---|
| Lambari | 4.875% | 4.743%–5.010% | 5.053% | 4.919%–5.190% |
| Tilápia-do-nilo | 4.953% | 4.820%–5.089% | 4.866% | 4.734%–5.001% |
| Carpa-comum | 5.006% | 4.873%–5.143% | 4.921% | 4.789%–5.057% |
| Traíra | 4.978% | 4.845%–5.115% | 4.906% | 4.774%–5.042% |

## Esforço observado — somente este recorte

32 sementes, pareadas entre inícios 07h e 20h, equipamento fixo nível 0, Enseada, horizonte de quatro horas; usa o motor efetivo, sem compras, viagens ou varas alternativas. Uma linha por horário tem 32 execuções. Os dois horários não são amostras independentes entre si. Tempos são minutos de pesca contados pelo modelo, não sessões reais ou tempo de retenção. Não extrapolar ao catálogo inteiro.

| Início | Marco | Mediana (min) | P10–P90 (min) | Média (min) | IC95% bootstrap da mediana (min) | Mediana de capturas medidas | Não atingido em 4h |
|---|---|---:|---|---:|---|---:|---:|
| 7h | Primeira medida | 0.31 | 0.23–0.67 | 0.42 | 0.28–0.47 | 1 | 0/32 |
| 7h | Primeiro diminuto | 5.86 | 1.26–18.66 | 8.29 | 2.85–11.13 | 14 | 0/32 |
| 7h | Primeiro excepcional | 4.29 | 0.63–16.07 | 7.52 | 2.19–7.47 | 10.5 | 0/32 |
| 7h | Diminutos de 3 espécies | 43.26 | 23.49–98.87 | 55.62 | 35.55–60.82 | 116 | 0/32 |
| 7h | Excepcionais de 3 espécies | 51.32 | 17.63–111.33 | 58.65 | 40.19–62.31 | 135 | 0/32 |
| 20h | Primeira medida | 0.28 | 0.21–0.54 | 0.32 | 0.26–0.31 | 1 | 0/32 |
| 20h | Primeiro diminuto | 4.48 | 1.31–16.58 | 7.87 | 2.84–11.13 | 14 | 0/32 |
| 20h | Primeiro excepcional | 4.29 | 0.63–12.24 | 5.94 | 2.19–6.26 | 13.5 | 0/32 |
| 20h | Diminutos de 3 espécies | 34.00 | 14.73–52.23 | 35.57 | 25.80–39.53 | 105.5 | 0/32 |
| 20h | Excepcionais de 3 espécies | 32.32 | 9.34–78.24 | 38.83 | 19.25–42.25 | 100.5 | 0/32 |

Quantis com interpolação linear. IC da mediana por 2.000 reamostragens de sementes, separado por horário, semente do bootstrap 20261018; amostra pequena, sobretudo para caudas. Todos os marcos foram observados nas execuções finais; nenhuma meta ausente foi convertida em tempo de quatro horas. JSON bruto inclui cada semente, contagem e instante. Os marcos de diversidade têm variabilidade grande e diferenças por disponibilidade das espécies. Isso não demonstra conteúdo adicional duradouro ou retenção humana.

## Executável e associação ao fonte

- Arquivo: `executavel/PescaIdle-Tamanhos-Piloto.exe`, **50,200,863 bytes**.
- SHA-256 do EXE: `4229707d91ed82b519178e18ea6143cc8a86b3e164f02aaf5826abce32eaff27`.
- SHA-256 do manifesto de fontes/assets: `3118f7966ad9a3070a06cd81796709b39927b31e12064f8edc45521f038bc8d9`.
- Base Git identificada acima; candidato sem commit. ENTREGA.json associa hashes dos arquivos, diff e build. `qa/pacote-verificado.json` confere diretamente o arquivo empacotado, sem importar seu código.
- Build final: `qa/build-verificado.log`; smoke: `qa/smoke-executavel.json`, saídas em `<entrega-local>/executavel/qa-smoke-da0e51a3`. As imagens `exe-captura.png` e `exe-museu.png` vieram desse build novo. O executável antigo não foi usado como evidência.

## Reprodução sem instalações

Na pasta desta entrega, em PowerShell, use o Python já disponível (ou ambiente equivalente existente). O caminho observado nesta máquina é:

```powershell
$py = '<caminho-local>'
Set-Location '<entrega-local>/candidato'
& $py -X utf8 -B -m unittest tools.verificar_tamanhos.SizeTests -v
& $py -X utf8 -B tools/verificar_tamanhos.py
& $py -X utf8 -B tools/visual_tamanhos.py
Set-Location '<entrega-local>'
& $py -X utf8 -B comparar_fluxo_base.py base
& $py -X utf8 -B comparar_fluxo_base.py candidato
& $py -X utf8 -B resumir_evidencias.py
& $py -X utf8 -B smoke_executavel.py
& $py -X utf8 -B verificar_pacote.py
```

O comando unittest executa só os 12 testes; `verificar_tamanhos.py` também executa a amostragem/64 cenários. Os scripts configuram perfis/saídas exclusivos antes de importar o produto; o smoke cria uma pasta UUID nova junto ao EXE. Reexecuções dos testes de fonte atualizam apenas as saídas sintéticas deste candidato.

Para novo build, a partir de `candidato/`, com diretório de trabalho/saída próprio e sem reaproveitar build intermediário:

```powershell
$env:PESCA_IDLE_SAVE_PATH = "$PWD/qa/build-profile/save.json"
$env:APPDATA = "$PWD/qa/appdata"
$env:LOCALAPPDATA = "$PWD/qa/localappdata"
$env:TEMP = "$PWD/qa/tmp"
$env:TMP = $env:TEMP
$env:PYINSTALLER_CONFIG_DIR = "$PWD/qa/pyinstaller"
& $py -X utf8 -B -m PyInstaller --noconfirm --distpath ../executavel --workpath ../build-repro PescaIdle.spec
```

A abertura normal do fonte é `& $py -B piloto_entry.py`, com perfil padrão `candidato/perfil-piloto/save.json`. Não execute os scripts históricos de auditoria integral como se fossem testes deste piloto. `preparar.py` documenta a cópia inicial e exige diretórios inexistentes; não é necessário reexecutá-lo para validar a entrega.

## Evidências visuais e limitações

`candidato/qa/visual/variacao-*.png`: pequeno/típico/grande das quatro espécies; `variacao-mobile-*.png`: o mesmo recorte em viewport 320×568; `aquario-misto.png`, `aquario-animacao.png`: convivência e três fases de movimento. Imagens de enciclopédia/museu têm topo e rodapé para os dois viewports. `museu-legado-sem-medida.png` mostra a alternativa sem tamanho fictício.

As imagens foram inspecionadas visualmente, além das asserções geométricas. Qt usa o plugin Windows com janelas não mostradas; QTest injeta eventos de tecla/clique nos widgets. Não houve clique humano, ensaio de arraste por SO ou toque físico. Prévia de 320/360 pixels não comprova Android: APK, instalação, safe areas reais, desempenho e toque em dispositivo Android não foram testados. O smoke Windows cobriu inicialização/persistência/renderização, não uma sessão manual prolongada em outra máquina.

Não foi repetida a auditoria completa de integridade, falhas de disco ou concorrência do projeto; os mecanismos existentes foram mantidos e somente os caminhos afetados foram verificados. Não foi instalada dependência nem implementada migração para varas. Nenhum save pessoal foi acessado.

## Recomendações e decisões pendentes

Manter o recorte pequeno, o RNG independente, os recordes sem bônus e o seletor de extremos para revisão humana. As medições sustentam o comportamento técnico nesses cenários, não uma meta de longevidade. Os cinco marcos podem terminar cedo; não recomendo alongá-los apenas reduzindo probabilidades.

Decidir após experimentar: validar ou trocar os comprimentos provisórios com fontes biológicas adequadas; aceitar faixas próximas de 5% e diversidade de 3/4 espécies; avaliar legibilidade dos menores e a compressão entre espécies; escolher se esse piloto deverá integrar alguma versão futura. Novas espécies, economia, varas e publicação dependem de pedido separado. Nenhuma dessas decisões foi aplicada automaticamente.

Para voltar: feche este EXE e abra o executável original. Não copie schema 4 sobre o perfil principal. A área isolada permanece disponível para revisão, sem exigir apagar ou restaurar os dados anteriores.
