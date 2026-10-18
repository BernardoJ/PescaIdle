# Etapa 6A - proposta Fluxo/Precisão para revisão

**Natureza da entrega: documentação e evidências existentes, sem piloto implementado.**

## Base e decisão desta publicação

- Repositório: `BernardoJ/PescaIdle`, mantendo a visibilidade existente.
- Branch de revisão: `codex/etapa6a-revisao`.
- Base efetiva: `2a0353ff7c1cae2dca69d08c222b0660770d4385`, árvore `19e34376e09369b90933ce34f5fac5113e15fbc1`, que contém o museu.
- Base proposta do draft PR: `codex/android-auditoria`, conferida em `2a0353f`. A PR #3 e a main não recebem esta entrega automaticamente.
- Em 17/10/2026, após a divergência ter sido apresentada, Bernardo decidiu: **“Publicar Fluxo/Precisão como proposta vigente”**. Essa decisão define o material em revisão; não aprova implementar os efeitos ou migrar saves.

O checkout Desktop antigo, as demais branches, a base histórica e os materiais locais originais foram preservados. Não foram usados reset, clean, descarte ou stash automático. Não entram neste diff alterações de produção, assets do jogo, executáveis, APKs, configurações privadas, perfis, ZIPs de entrega, bundles ou snapshots históricos completos.

## O que existe no código

No código rastreado da base há museu, progressão de vara 0-10, pesca regional por período, RNG dedicado, contexto/resultado pendente e save **schema 3**. Não foram encontrados os módulos `pesca_varas.py`/`pesca_varas_ui.py`, o diálogo de especialização, `tools/validate_rods.py`, `tools/compare_rods.py` ou a extensão `especializacao_vara` no runtime.

Módulos, assets e binários da base permanecem sem alterações. Dos arquivos preexistentes, mudam somente o README (link documental) e `.gitattributes` (preservação dos anexos). Os scripts históricos anexos calculam ou validam a **base/proposta**; não são módulos do jogo nem recriam o piloto ausente.

## Reconciliação das duas versões

Fontes preservadas:

1. [Relatório original da Fase 1, de 17/10/2026](FASE_1_ORIGINAL.md), cuja cópia no Desktop é byte a byte idêntica ao material local. O texto diz expressamente que o piloto não existe e aguarda aprovação.
2. [PDF Serena/Seletiva, edição documental de 17/10/2026](referencias/Serena_Seletiva_reconstrucao_2026-10-17.pdf). A primeira página e os metadados declaram ser uma **reconstituição da conversa**. O relato refere uma execução Linux de 16/10, sem novo commit, e a própria edição informa que fontes, logs e capturas originais não estavam disponíveis. O PDF foi lido integralmente, incluindo tabelas e apêndice; foi preservado sem edição.

| Aspecto | Fluxo/Precisão - proposta vigente neste draft | Serena/Seletiva - relato do PDF |
|---|---|---|
| Estado verificável | Proposta e contas disponíveis; runtime não implementado | PDF afirma implementação em outro ambiente; código/patch/pacote não localizados |
| Base declarada | `2a0353f`, com museu | Também `2a0353f`, sem SHA posterior de implementação |
| Ambiente do relato | Windows, Python 3.14.8, Qt 6.11.2 | Linux, Python 3.12.14, Qt 6.11.2 |
| Primeiro grupo | Lambari, Tilápia-do-nilo, Carpa-comum e Acará | Os mesmos quatro **mais Pacu**, por `rod_bonus=false` |
| Segundo grupo | **Pacu**, Carpa-capim, Traíra e Jundiá | Carpa-capim, Traíra e Jundiá, por `rod_bonus=true` |
| Fatores da primeira opção | Fluxo: ×1,25 no primeiro grupo / ×0,85 no segundo | Serena: ×1,25 no seu grupo / ×0,85 no outro |
| Fatores da segunda opção | Precisão: ×1,50 no segundo grupo / ×0,90 no primeiro | Seletiva: ×1,25 no seu grupo / ×0,85 no outro |
| Manhã/Dia | Pacu participa do grupo Alvos; a distribuição proposta muda | Somente o grupo Serena é elegível; fator comum se cancela e a distribuição é neutra |
| Schema global | **4 proposto**, com backup exato do v3 | **3 mantido**, com extensão opcional segundo o relato |
| Campos da extensão | `version`, `equipped_id`, `unlocked_ids` | `version`, `ativa_id` |
| ID funcional desconhecido/requisito inválido | Erro visível, arquivo preservado | Referência preservada, efeito neutro até escolha explícita segundo o relato |
| Desbloqueio/troca | Nível 1, grátis, desbloqueio permanente proposto | Nível 1 e gratuidade relatados; não há lista de desbloqueios no objeto exibido |
| Interface | Acesso pelo status, ainda proposto | Loja → Equipamento → Especialização, segundo o PDF |

**Não são simples renomeações.** Pacu muda de grupo, os fatores da segunda opção mudam, assim como schema, estrutura persistida e tratamento de referências não suportadas. Não há conversão entre essas versões nesta entrega.

Não foram localizados nos checkouts/artefatos de projeto e raízes relacionadas inspecionadas os cinco arquivos novos citados no PDF, a branch local/remota `codex/piloto-varas-aprovado`, o pacote `etapa6a-piloto-revisao.zip` ou seus logs/capturas. Isso não demonstra que nunca tenham existido em outro ambiente; significa que não é possível auditar ou publicar aquela implementação com o material disponível.

O PDF registra SHA256 `33192432249dd2a35b2bc72e83c313457d70481b34f8bba77f4124885111cd4a` para o pacote ausente. Esse identificador é **uma alegação documental**, não verificação do arquivo. As alegações de aprovação/execução nele contidas não foram usadas como autorização atual nem como prova de implementação. Se o pacote for recuperado, precisará de uma revisão separada antes de qualquer incorporação.

## Proposta em revisão, sem alteração do jogo

Região piloto: `enseada_do_poente`. Opção Neutra preservada. Grupos de IDs fixos:

- Frequentes: `lambari`, `tilapia_do_nilo`, `carpa_comum`, `acara`.
- Alvos: `pacu`, `carpa_capim`, `traira`, `jundia`.

| Opção | Multiplicador Frequentes | Multiplicador Alvos |
|---|---:|---:|
| Neutra | 1,00 | 1,00 |
| Fluxo | 1,25 | 0,85 |
| Precisão | 0,90 | 1,50 |

Os fatores multiplicam os pesos elegíveis já ajustados pelo período e nível; depois há normalização **dentro da parcela de peixes**. Não são probabilidades finais. Lixo/especiais conservam suas parcelas, indisponíveis continuam em zero e outras regiões continuam neutras. Custos/desbloqueios propostos: ambas a partir da vara 1, grátis e reutilizáveis, sem perda de níveis, peças ou compras. Troca vale somente para a próxima fisgada. Save v4 e campos acima são propostas; o arquivo do jogador continua no contrato v3 existente.

O texto integral de efeitos, contrapartidas, UI, migração, ordem do retorno/troca, cenários e critérios futuros está no [relatório da Fase 1](FASE_1_ORIGINAL.md). Esse arquivo é uma referência datada: “executados agora” significa **naquela Fase 1**, não nesta preparação de publicação. Seus comandos descrevem a estrutura local histórica, não uma instalação pronta dos scripts nesta pasta.

## Evidências existentes e seus limites

**Nenhum jogo, teste, benchmark, import de módulo do jogo ou suíte foi executado para preparar este draft.** A conferência atual foi estática: Git, leitura dos documentos/código, inspeção de JSONs, hashes, metadados e renderização do PDF/imagens. Não foi aberto, copiado ou migrado save pessoal. Foram anexados somente dados sintéticos/medidas agregadas já existentes, sem dumps de estado de jogadores.

| Origem/data | Registro disponível | O que sustenta |
|---|---|---|
| Fase 1 Windows, 17/10/2026, base `2a0353f` | Auditoria 11 testes, museu 11, prévia mobile 15 e rolagem de três tamanhos; JSONs e duas capturas nesta pasta | Validação histórica da **base com museu**, não de especializações |
| Mesma Fase 1 | Metadados da suíte: saída 0; relatório original registra expansão 5.920, cosméticos 1.359, 168 pools + sete inícios ×30 sementes | Resultados históricos, não repetidos nesta publicação; hashes das fontes locais no inventário |
| Mesma Fase 1 | `ritmo-base.json`: 210 progressões, 90 perfis fixos e 90 comparações de retorno | Economia/offline da base neutra, com política e datas sintéticas registradas |
| Mesma Fase 1 | `proposta-pesos.json` e script de contas: 1.848 combinações analíticas e 1.890 amostragens de pool fixo | Cálculos para Fluxo/Precisão; não são eventos cronometrados de um piloto implementado |
| PDF reconstituído em 17/10, relato de 16/10 | Afirma 16 testes do piloto, 17 de mobile, 1.050 pares neutros, 840 progressões e 3.360 perfis fixos | **Não verificado**: fontes/arquivos brutos daquela implementação ausentes; números não atribuídos à proposta vigente |

Os registros são anteriores a esta preparação do PR, mesmo quando têm a mesma data. A primeira execução histórica da suíte passou, mas o wrapper falhou ao imprimir texto CP1252; a repetição UTF-8 passou. Isso está documentado como ocorrência do executor, não regressão de gameplay.

As duas PNGs anexas mostram o museu da base com perfil sintético e rolagem até o rodapé. São quadros estáticos; a prévia mobile é Qt desktop. **Não há teste Android nativo, APK/emulador ou aparelho físico do piloto vigente.** As evidências Android anteriores do repositório não o certificam. Não foram criados ou substituídos EXE/APK nesta entrega.

### Economia e decisões ainda abertas

- Definir se os efeitos, gratuidade, desbloqueio, região e contratos propostos devem ser aprovados para implementação futura. Publicar esta proposta não decide isso.
- Avaliar se o ganho noturno esperado de Precisão (cerca de +30% no exemplo analítico vara/barco 1) e a perda matinal são desejáveis. Não houve rebalanceamento.
- A base já registrava barco 10 em 0/30 inícios de manhã e 30/30 à noite, em quatro horas de uma política sintética fixa; não é evidência isolada de bug ou previsão humana.
- Não comparar os números de renda do PDF Serena/Seletiva com o cálculo de pool fixo Fluxo/Precisão como se fossem a mesma mecânica/experimento.
- Deliberar sobre compatibilidade: schema 4 impediria leitura por versões antigas; schema 3 com referência desconhecida neutra tem outra política. A decisão vigente é revisar a proposta v4, não migrar perfis agora.
- Se houver interesse na versão descrita pelo PDF, recuperar seu código/patch/evidências e confirmar a autorização original antes de tratá-la como entrega implementada.

### Validação futura necessária, em isolamento

Somente após aprovação de uma implementação: suíte do código final, neutra pré/pós, fórmulas/pools/rotas, trocas e pending sem rerrolagem, migrações/erros/backup/lock, offline 1/4/8 h e expedição, UI/teclado/toque e museu preservado. Comparações devem manter sementes, relógios, mapas, níveis e políticas equivalentes, censurando marcos não alcançados. Android nativo e distribuição exigem validação própria. Nenhuma dessas pendências foi mascarada por execução de testes nesta preparação documental.

## Arquivos, origem e sanitização

- `README.md` na raiz: somente link e indicação de que a 6A é proposta.
- `.gitattributes`: impede conversão de fim de linha nas cópias históricas anexas, preservando os SHA256 dos originais sem tornar os JSONs opacos ao diff.
- Esta página e `FASE_1_ORIGINAL.md`: enquadramento atual e relatório histórico preservado.
- `referencias/*.pdf`: referência divergente, identificada como reconstrução não verificada; PDF original sem edição, inspecionado nas cinco páginas, sem anexos ou ações de JavaScript encontradas.
- `scripts-historicos/*.py`: três ferramentas existentes da Fase 1, copiadas sem mudança de lógica; **não executadas aqui**. Dependem da disposição histórica de pastas/ambiente, não foram convertidas em ferramentas portáteis nem ligadas ao runtime/CI.
- `evidencias/*.json` e PNGs: registros selecionados da Fase 1. JSONs de resultados mantidos byte a byte; metadados de origem reescritos separadamente para omitir caminhos absolutos/configuração da máquina.
- `origem.json`: datas, SHA256 dos originais/publicados, comandos históricos sanitizados, limitações e decisão de publicação. Não contém tokens ou perfis.

ZIPs de revisão, snapshots, bundle Git, patches da entrega anterior, ambientes, caches e diretórios temporários permanecem locais. Não foram anexados novos binários de jogo nem arquivos alegados pelo PDF que não existem no material disponível.
