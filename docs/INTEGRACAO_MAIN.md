# Revisão para integração na main — 27/10/2026

## Checkout, instruções e preservação

Repositório: `BernardoJ/PescaIdle`, remoto `origin` em
`https://github.com/BernardoJ/PescaIdle.git`.

O checkout recebido estava na branch local `work`, em
`6b29b4a0da3ce403dad4ff46e7f656659d2266f1`, limpo, sem arquivos não rastreados,
sem staged changes e sem outros worktrees. Não foram encontrados `AGENTS.md` ou
`CONTRIBUTING.md` no caminho de trabalho ou nas árvores das branches pertinentes.
Foram lidos README, contrato de migração, documentação do clima, runners e
configurações de empacotamento/CI antes das alterações de produção.

A referência local de `origin/main` era `b4ef8c7`. O fetch de todas as branches,
sem prune ou mudança de configuração, confirmou main remota em `6b29b4a`.
Os seis commits inicialmente listados como não publicados eram efeito dessa
referência atrasada: após fetch, **não havia commits locais inéditos**.

A preparação ocorre em worktree separado, na branch
`codex/preparar-integracao-main`, criada de `a352061`. O checkout original e sua
branch `work` foram preservados. Nenhum reset, stash, clean, force push ou rebase
foi usado. Perfis pessoais e seus backups não foram lidos, copiados ou migrados.

## Relação das branches e destino correto

| Etapa | Base | Head publicado | PR / commits exclusivos |
| --- | --- | --- | --- |
| Main recebida | — | `6b29b4a0da3ce403dad4ff46e7f656659d2266f1` | Ponto de partida remoto |
| Expansão | main | `b4c81121bddff8416fcfa4cbd5b2542f9d8b8f34` | #2 para main; 2 commits |
| Auditoria/Android e museu | expansão | `2a0353ff7c1cae2dca69d08c222b0660770d4385` | #3 para expansão; 19 commits |
| Piloto, aquário, conquistas e clima | auditoria/museu | `a352061bfb97692ff54934e4992406d16c9628b1` | #5 em rascunho para `codex/android-auditoria`; 13 commits |
| Preparação atual | piloto publicado | `fbd10e1` + commits documentais desta revisão | Novo PR em rascunho para main |

Os três heads formam uma cadeia de ancestralidade, sem divergência entre as
etapas. O merge-base main/piloto é `6b29b4a`; o merge-base auditoria/piloto é
`2a0353f`. O diff original do PR #5 cobre somente os 13 commits posteriores à
auditoria: **não cobre tudo que falta na main**.

O caminho proposto é um **PR agregado para main**, partindo do head do piloto e
acrescentando a correção/testes e documentação. Isso inclui as dependências de
expansão, persistência, economia em centésimos, RNG/contexto pendente, museu e
interface. Não basta cherry-pick do clima ou dos commits finais do piloto.
O PR #5 conserva seu destino; nenhum PR existente foi retargetado.

Alternativa válida seria integrar em sequência #2 → #3 → #5, revisando o diff
de cada retarget depois dos merges. O PR agregado permite revisar e aprovar o
estado completo em uma única integração, sem alterar os PRs empilhados.
Recomenda-se merge commit para conservar a ancestralidade publicada; sem squash,
rebase ou reescrita de histórico. Não há autorização de merge nesta preparação.

`codex/etapa6a-revisao` / PR #4 (Fluxo/Precisão) e `android-port` ficam fora do
candidato. A implantação Kotlin separada não é dependência da versão Qt atual.

## Conteúdo que entrará

O candidato acrescenta à main oito mapas/88 espécies/sete períodos, viagem e
expedição, persistência atômica e exclusiva, Android Qt histórico, museu,
comprimentos de quatro espécies, arte/movimento do aquário, 21 decorações,
38 conquistas e cinco climas diários. As evidências históricas, quatro PDFs em
`output/pdf/`, masters e quatro arquivos EXE no diff também vêm dos commits
anteriores. **Esses binários são históricos, não foram recompilados nesta tarefa.**

O range publicado main → `a352061` tem 433 arquivos alterados, 207.881 linhas
adicionadas e 923 removidas: 42 de fonte/configuração, 53 ferramentas, 51 assets,
279 documentos/evidências, 4 PDFs e 4 binários. A maior parte das linhas é dado
e evidência histórica. A preparação muda somente cinco caminhos:

- `pesca_save.py`: quatro linhas para rejeitar schema 5 sem clima no arquivo.
- `tools/test_climate.py`: cinco testes novos, com subcasos de defaults, arquivos,
  recuperação e migração; 85 linhas adicionadas.
- `README.md`: candidato, plataformas, caminhos do perfil, testes e binários históricos.
- `docs/MIGRACAO_SAVE.md`: contrato atual antes da descrição histórica do schema 3.
- `docs/INTEGRACAO_MAIN.md`: esta revisão, commits, validação e limites.

O PR registra o SHA completo final e o diff de todo o range contra main. O
manifesto entregue na revisão fixa base, head, árvore, commits, blobs por caminho
e SHA-256 do diff; qualquer alteração relevante exige nova apresentação.

## Correção e contrato de saves

Em `pesca_idle.py`, `ESTADO_PADRAO` é expandido por `migrate` no import. Antes da
correção, um arquivo v5 sem `clima` herdava o registro dos defaults, incluindo
semente/ativação de outra inicialização. A rejeição agora acontece em `migrate`
antes de combinar defaults, gerar backup de migração ou substituir o arquivo.
`None`/registro inválido continua recusado pelo validador climático existente.

O commit de produção/testes é `fbd10e1`.
Os testes novos falharam antes da correção em quatro verificações e passaram
depois. Cobrem defaults literais e expandidos, ausência/None, entrada e defaults
imutáveis, preservação exata do save rejeitado e backups, recusa de backup v5
incompleto e recuperação explícita de backup válido com arquivo rejeitado intacto.

Migrações válidas de schemas 1–4 continuam criando clima no instante da migração;
backups originais byte a byte e colisões de nomes foram testados para cada versão.
A reabertura v5 não recria clima nem regrava a migração. Extensões desconhecidas,
progresso, museu, RNG, medidas e resultados pendentes são cobertos pelas suítes.
Capturas/ausência anteriores à ativação continuam neutras; não há rerrolagem.

`save.pre-expansao-v1.json` / `save.pre-schema-N.json` guardam o formato antigo;
colisões diferentes usam nome exclusivo. `save.json.bak` guarda o snapshot anterior
e pode já ser schema 5. A recuperação arquiva o rejeitado antes da substituição.
O leitor real schema 4 de `c545ca6` foi executado contra um JSON v5 **sintético**
e recusou o formato sem alterar os bytes. Não existe downgrade automático; voltar
exige uma cópia do backup anterior à migração em perfil separado compatível.

## Validação executada nesta preparação

Linux x86_64, Python 3.12.14, PySide6 6.11.2, Pillow 12.3.0, Qt offscreen.
Foi criado um venv de QA separado; o ambiente preexistente foi preservado.
Todos os perfis vieram de código/fixtures sintéticas, dentro de diretórios novos
de QA; APPDATA/LOCALAPPDATA foram isolados antes de imports do jogo. Nenhum save
real foi usado, nem como fixture, nem para verificar a migração.

| Comando (Python do ambiente de QA) | Resultado atual |
| --- | --- |
| `tools/validate_climate.py --out qa/integracao-clima-corrigido` | 19 testes; 0 falhas/erros; 3.080 pools, 33.880 contextos econômicos, 280 cenas, 1.120 quadros, 45 filtros e clique/teclado |
| `tools/validate_conquistas.py --out qa/integracao-regressao-completa` | 44 testes de conquistas + 17 tamanhos/pendências + 11 auditoria + 11 museu; 0 falhas/erros |
| Runners da regressão acima | 5.920 checks da expansão, 1.359 de cosméticos, 168 pools exatos e 7 inícios × 30 sementes de balanceamento; passaram |
| `tools/run_climate_smoke.py --out qa/integracao-smoke-fonte` | Fonte em três processos: pending, deliver, reopen; passou sem duplicação |
| `tools/validate_mobile.py` com TEMP/TMP e QA no checkout | 15 checks de retrato/paisagem, diálogos, suspensão, retomada única e pausa; passou; prévia desktop |
| `tools/validate_climate_interactions.py --out qa/integracao-interacoes` | 7.360 renders cosméticos, 4.840 pares vara/barco, 50 ciclos de diálogo; estado/RNG preservados |
| `tools/validate_aquarium_motion.py --out qa/integracao-aquario` | 10 testes; 0 falhas/erros; 68 espécies; não criou save |
| Leitor schema 4 de `c545ca6` contra fixture v5 sintética | Recusou schema 5; fixture permaneceu intacta |
| `git diff --check` nas mudanças novas | Passou |

São **112 testes unitários aprovados** nas suítes verdes, além das matrizes,
checks e smoke acima. Não se somam reruns ou a demo falha a esse total.

### Falhas observadas e reproduzidas

- A primeira regressão geral parou no museu: `ModuleNotFoundError: PIL` no venv
  preexistente. Depois de instalar as dependências fixadas em um venv separado,
  a regressão completa passou. Nenhum teste foi removido ou relaxado.
- `tools/test_demo_tamanhos.py --out qa/integracao-demo`: **10 testes, 6 falhas,
  0 erros**. O roteiro antigo de demonstração cria contexto pendente sem `clima`;
  schema 5 recusa a gravação. O mesmo comando em worktree limpo de `a352061`
  reproduziu as mesmas seis falhas, antes desta correção. A demo antiga `--demo`
  permanece com limitação herdada; não é certificada por esta preparação. O jogo
  normal e seu smoke climático em três processos passaram. O reparo da demo é
  uma tarefa separada; esta revisão não alterou seu roteiro nem enfraqueceu o save.
- Qt offscreen emitiu avisos sobre raise/propagateSizeHints; não são teste de
  compositor nativo. Houve avisos de cache de fonte no ambiente antigo.

### O que não foi executado ou certificado

Sem build ou smoke de EXE/APK, emulador Android, aparelho ARM64, Windows nativo,
macOS, sessão humana prolongada, suspensão física, máquina limpa, Play Store,
release, deploy ou mudança de permissões. Não foram repetidos o estudo climático
histórico de 210 execuções de 24h nem o comparador histórico base/piloto; os
resultados anteriores continuam históricos. Os testes atuais de replay e pools
não equivalem a esses estudos de progressão completos.

## Riscos para a aprovação

1. O diff para main agrega **34 commits anteriores mais os commits desta preparação**,
   incluindo alterações amplas de jogo e os binários históricos. Aprovar apenas a
   correção de quatro linhas não aprova a integração completa.
2. Saves do piloto v5 não abrem em leitores antigos. Backups foram validados com
   fixtures sintéticas; não houve ensaio com dados pessoais. Preserve backups
   anteriores à migração ao planejar uma atualização real.
3. A demo histórica de tamanhos falha nos seis casos descritos. Se ela for um
   requisito para integrar, esta falha deve ser reparada e reapresentada antes.
4. O candidato continua isolando o perfil dentro de sua pasta. O bootstrap Android
   herdado seleciona `QStandardPaths.AppDataLocation`/cache privado, enquanto o
   piloto exige o perfil sob a raiz do módulo/executável. Essa incompatibilidade
   estática precisa de adaptação e teste nativo antes de distribuir APK atual.
5. O workflow Android herdado só dispara por push em `codex/android-auditoria`
   ou acionamento manual; não há CI automática do PR agregado para main. Nenhum
   workflow foi disparado manualmente ou alterado nesta preparação.
6. Parâmetros de tamanhos/preços continuam de piloto; clocks históricos usam offset
   fixo. Matrizes e Qt offscreen não certificam hardware, todas as combinações
   simultâneas ou qualidade visual em toda GPU/DPI.

## Conferência antes e depois do merge autorizado

Antes de qualquer merge: buscar novamente main e branch de trabalho, conferir
SHA do head, base, ancestralidade, lista de commits, árvore e diff com o manifesto
aprovado, além de checks/reviews e ausência de alterações locais pertinentes.
Se base, head, diff ou risco relevante mudou, reapresentar e pedir nova aprovação.

Somente após aprovação específica: realizar merge commit do head revisado,
conferir o resultado na main remota e verificar que os commits do candidato são
ancestrais dela. Sincronizar o checkout local por avanço normal/fast-forward quando
seguro; alterações locais que surgirem devem ser preservadas. Não executar build,
publicação, deploy ou mudança de permissões por consequência do merge.

## Commits publicados que compõem a versão desejada

A lista abaixo contém exatamente os 34 commits de `6b29b4a..a352061`.
A correção `fbd10e1` e os commits documentais desta revisão são acrescentados no PR.

- `86f3b2a4740aeefa8533d980d76a6084b7c61bc1` — Implementa expansao de oito mapas, periodos e colecao regional
- `b4c81121bddff8416fcfa4cbd5b2542f9d8b8f34` — Publica executavel Windows da expansao e guia atualizado
- `0edf17f91e87577bba4aade22256fd448769dcd1` — Corrige auditoria, Fashionista e prepara Android completo
- `a77dff7ea8575a38bba144f7828a235eda448c3e` — Ajusta teste de perfis no Linux e contraste das paginas mobile
- `628af6b31a1eaa2c7378b607a207fcf8bf44d66f` — Provisiona NDK e fixa ferramenta de build Android
- `27e7e20b0ec5eb2ad42455bb8dde7c54e25a92e1` — Adiciona verificacao em APK Android isolado e emulador
- `2786d14af72215a7e2b78d2f1887068151cb7712` — Valida encerramento nativo e fluxos completos de conquistas
- `bf570cf697ecc8533b1426fa08c79f0640db8241` — Isola dependencias Android e adapta o SDK atual
- `f52f63fafad2237028372a2cf89eb9e8039d9673` — Isola fixture de conquistas e mostra erros de perfil no Android
- `ce6af8747b7a594d729aeb1348c58b8425e0647d` — Publica executavel Windows corrigido e evidencias da auditoria
- `a59582482eade6cf010d7446160f01a9a6c6587a` — Corrige icone de release e permite testar APK ja compilado
- `928219a8de71251f82518d8ecb2c7686e75b05b3` — Valida PNG no diretorio de recursos Android correto
- `643aa279d83757bdcf5cf67303e9259b03362c3e` — Fix isolated AVD discovery for Android validation [skip ci]
- `b89c476292c5716ab8f64639aef07670ec34227e` — Run emulator with process-scoped existing KVM access [skip ci]
- `ef32b602901bb82065624a64a54357454fec0bd2` — Keep emulator UID with runner privilege launcher [skip ci]
- `35a2483f140b64075befe249a44be8bc9ab1e10d` — Fit Android panels and overlays to safe screen area; verify real rotation
- `dbc6f2e3ada0e327b616e013a0d71bcaa84e3f53` — Publish rebuilt Windows executable after mobile layout fixes
- `0f3759b09289b9902c7b578cdada3308e38fa589` — Keep Android checks and fixtures active under bytecode optimization [skip ci]
- `24e4055911e5d4360faebfdab1b3aaedac5207b4` — test: capture and check Android collection filter geometry [skip ci]
- `f5946680df4599c2c132cee7ca14256dd695b88a` — docs: record native Android tests and signed beta distribution [skip ci]
- `2a0353ff7c1cae2dca69d08c222b0660770d4385` — feat: adicionar museu inicial e relatorios da entrega
- `b05f7820f9dc04ef479c84fad696ae80c8e72c60` — Publica piloto isolado de tamanhos, recordes e museu
- `9d57a465ad418f885af46d11590def0753007e78` — Adiciona comparador reproduzivel entre base e piloto de tamanhos
- `2bbc7a87d7358a0a7fab37769e1ecabe7c5f8ade` — Corrige save pendente e prepara demonstracao isolada de tamanhos
- `5a6efb6d7b849702f6ced5c62ddde071fceb620a` — Recusa redirecionamento do arquivo de demonstracao antes da leitura
- `0f516e89c4bb7b2935a5011801595429941431c6` — Registra validacao e roteiro da demonstracao Windows do piloto
- `e4e9e3f40a6f99d7f40de8dd9bc7d94dc020bfbb` — Improve aquarium-only fish artwork for all 68 species
- `dcd69c9e1a7f1e3d65ff822d192c702450426edd` — Document aquarium artwork with reproducible captures and illustrated PDF
- `0c29196ac261ed04faf153121a1f8a01b1869cfc` — Animate aquarium fish with independent visual frames and isolated review demo
- `9d5d7831752b79f5578007bb51b255329c15cfd0` — Deliver animated aquarium demo, visual evidence and complete five-step PDF
- `d8032d67142bd2e13e36933bcc2238a190aefada` — Add aquarium decorations shop, ownership, previews and proposed prices
- `c545ca652386d74372307bd6d52a91f84d1ed4a0` — Implement 24 approved stage-one achievements with individual and regression tests
- `d1bcd5bb13cb58d7196221450be2a43124dfa233` — Implementa clima diario, afinidades e consulta clicavel
- `a352061bfb97692ff54934e4992406d16c9628b1` — Publica build Windows do clima e evidencias revisadas

## Hashes dos arquivos alterados de produção/testes

- `pesca_save.py`: SHA-256 `012fb0a66b77d1fb365bcbcc6bb7ea72a21711e9f20ee3cb211268a7f7a39037`.
- `tools/test_climate.py`: SHA-256 `5569a46a1d9a16b54b0a7ae1f2c762dc5032cf43680513f7792bff17ffb69765`.
