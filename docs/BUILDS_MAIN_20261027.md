# Builds Windows e Android — 27/10/2026

## A. Estado do repositório e origem

A referência oficial foi confirmada por fetch: `BernardoJ/PescaIdle`, remoto
`https://github.com/BernardoJ/PescaIdle.git`, main em
`f8190f5e6a7b2690a6d00eb8f1ef727cfe0bba34` (merge do PR #6).
O checkout original, branch local `work`, estava limpo e foi preservado. Não
havia commits locais inéditos. Nenhuma alteração local não relacionada foi
descartada. Não foram encontrados AGENTS.md/CONTRIBUTING.md nas árvores pertinentes.
README, contratos de save, spec, scripts e workflows existentes foram lidos antes
de editar; PyInstaller e Python/Qt/Buildozer foram mantidos.

Trabalho em `codex/builds-main-20261027`, derivada dessa main:

- `1416b8b`: isolamento privado Android, contratos e reabertura nativa.
- `f8962fe0f28e9403e685f5197ed38eb2b2c51609`: ferramentas de build/QA e workflow.
- `7b0dfd2`: coleta dos metadados dos artefatos grandes, sem recompilar.
- `5a2ac60af5d8e093d550a073d763ead082782591`: validação de caminhos auxiliares do save.
- `29b3110`: coleta de metadados da rodada Android final, sem recompilar.
- Commit documental posterior: README, Android, este relatório e evidências sanitizadas.

**Windows foi compilado exclusivamente de um checkout limpo da main fixa
`f8190f5`; ferramentas de build/QA vieram de `f8962fe` e ficaram separadas.**
Android foi recompilado de `5a2ac60`, que incorpora as correções ainda em revisão;
**os APKs não são builds exclusivos da main**. Não houve novo merge nesta tarefa.

[Build/QA nativos — workflow 40563588483](https://github.com/BernardoJ/PescaIdle/actions/runs/40563588483)
concluiu com sucesso nos quatro jobs. Os APKs dessa primeira rodada foram
superados pela rodada Android com a guarda de arquivos auxiliares. A
[coleta de metadados — 40565453844](https://github.com/BernardoJ/PescaIdle/actions/runs/40565453844)
também passou. Ela apenas baixou os artefatos já produzidos e separou metadados;
não recompilou ou alterou os binários.

A rodada Android final [40567485121](https://github.com/BernardoJ/PescaIdle/actions/runs/40567485121)
passou nos dois builds e no QA nativo; Windows foi pulado, pois sua fonte oficial
fixa não mudou. A coleta final [40567850107](https://github.com/BernardoJ/PescaIdle/actions/runs/40567850107)
também concluiu. Os hashes Android abaixo pertencem somente à nova rodada `5a2ac60`.

## B. Windows

**Novo EXE gerado: SIM. Validação funcional nativa: APROVADA.
Distribuição final: NÃO APTO até incorporar a guarda auxiliar descrita abaixo.**

[Baixar o pacote validado](https://github.com/BernardoJ/PescaIdle/actions/runs/40563588483/artifacts/12760794913)
· [Evidências Windows](https://github.com/BernardoJ/PescaIdle/actions/runs/40563588483/artifacts/12762870174)
· [Resumo JSON](builds-main-20261027/windows.json).

Extraia em pasta gravável e abra `PescaIdle-Windows-f8190f5.exe`. O ZIP acompanha
BUILD.json, VALIDATION.json, ARCHIVE.json e SHA256SUMS.txt; não contém saves/QA.
O rótulo “validado” do artefato registra os testes funcionais realizados; não
significa aprovação final após o achado de isolamento auxiliar. Não exige
instalar Python. O perfil fica em `perfil-piloto/save.json` ao lado do
EXE; não importa APPDATA.

| Propriedade | Resultado |
| --- | --- |
| Fonte | `f8190f5e6a7b2690a6d00eb8f1ef727cfe0bba34`, main |
| Geração em São Paulo | 27/10/2026, 15:52:19, UTC−03 |
| Executável | `PescaIdle-Windows-f8190f5.exe` |
| Tamanho | 48.793.907 bytes |
| SHA-256 do EXE | `e77e80d3da9aaf3b2cd8d8fce3c38c612cb8a8315d406fe496db608e3571feae` |
| SHA-256 do ZIP do artefato | `e5b141a478f5cdc002b642b3b35ef644274a2820acd621219e8d87f698d49542` |
| Plataforma de build/teste | Windows x64, runner `windows-2025`, Python 3.12.10 |
| Dependências fixadas | PyInstaller 6.22.3, PySide6 6.11.2, Pillow 12.3.0 |
| Versão do app | Spec desktop sem versão explícita; nenhum número foi inventado |
| Authenticode | Não assinado |

Build com spec original, `--clean`, diretórios/cache novos e checkout limpo
conferido antes/depois. Nenhum EXE ou build anterior foi reaproveitado.
O arquivo PyInstaller foi inspecionado: **39 módulos do projeto + entrypoint**
com bytecode igual ao checkout e **66 PNG/JSON de produção** com hashes iguais.
Masters de arte e perfis não entram no pacote de distribuição.

Dez verificações passaram no Windows nativo:

1. EXE em cwd estrangeiro, plugin Qt `windows`, PATH sem Python/venv; inicialização,
   assets, UI e oito mapas, em escalas 100% e 125% (dois casos).
2. Migração de fixture v1, inventário mantido e backup byte a byte nas duas escalas.
3. EXE climático em três processos: pending → deliver → reopen; contexto e
   recompensa preservados, sem duplicação, consulta climática e clique funcionando.
4. EXE recusa schema 5 sem clima com backup inválido; original e backup intactos.
5. Com backup válido, EXE pergunta pela recuperação; cancelar conserva ambos e
   não cria arquivo de recuperação sem consentimento.
6. Store Windows migra v4→v5 com backup exato e reabre v5 sem reset do clima.
7. Recuperação explícita preserva arquivo rejeitado e backup válido.

Os itens 6–7 usam o Store da fonte no Windows, cujo bytecode foi comprovado
idêntico ao pacote. A recuperação positiva pelo botão Sim do EXE **não foi
exercitada**; o cancelamento foi. Startup e painel climático foram inspecionados
visualmente. Não houve instalação Windows de consumidor limpa nem sessão humana
prolongada; runner nativo não equivale a esses ensaios.

## C. Android

**Correção do caminho de save: CONCLUÍDA. Política de isolamento validada: SIM,
por contratos e pelo contexto QA nativo. APKs gerados: SIM.**

O bootstrap escolhe o contexto antes de importar o jogo:

- Produção: `QStandardPaths.AppDataLocation/pilotos/tamanhos-v1/save.json`.
- Pacote QA separado: `QStandardPaths.CacheLocation/qa-tamanhos-v1/save.json`.
- A raiz vem do Qt Android nativo; variável de ambiente não pode ampliá-la.
  Outros contextos, travessia de diretórios e symlinks de fuga são recusados.
- Desktop conserva a raiz da pasta do checkout/EXE. Nenhuma mudança de schema.

No Qt 6.11, AppDataLocation usa `Context.getFilesDir()` e CacheLocation usa
`Context.getCacheDir()` ([fonte Qt](https://github.com/qt/qtbase/blob/v6.11.2/src/corelib/io/qstandardpaths_android.cpp)).
Nenhum caminho absoluto de aparelho foi codificado. O pacote QA é diferente do
aplicativo de produção e não pode selecionar o perfil de produção.

**Atualização de uma instalação antiga:** `AppDataLocation/save.json` permanece
intacto e não é lido/importado automaticamente. O piloto abre um perfil novo no
seu contexto dedicado. Não foi implementada transferência entre contextos nem
migração destrutiva. No mesmo contexto, os contratos simulam atualização e
conferem preservação; a reabertura foi exercitada em processo Android novo. Uma
atualização sobre instalação antiga de produção não foi executada;
schemas 1–4 válidos mantêm migração com backup exato. O schema 5 sem clima continua
recusado. Nenhum save pessoal foi usado para testar isso.

A revisão final encontrou um desvio de isolamento nos arquivos auxiliares: um
`.bak` previamente ligado por symlink a outro contexto podia ser recuperado,
embora o acesso direto ao save estrangeiro fosse recusado. O caso foi reproduzido
somente com arquivos sintéticos. Exige acesso prévio de mesmo UID ao diretório
privado; o jogo não cria esses links. A correção verifica também backup, backup
de migração, lock, arquivo rejeitado e destino de substituição atômica antes do
I/O. Os APKs foram reconstruídos após essa correção. A main e o EXE Windows
compilado exclusivamente dela ainda não contêm essa guarda adicional.

Antes dos builds, passaram **24 contratos** de criação, inexistência, load,
reabertura, corrupção, backup, lock, schema 5, migração v4, pendência e isolamento,
inclusive sob `-OO`. Sete testes do harness evitam falsos positivos da reabertura
nativa. Esses contratos de diretório simulam QStandardPaths no desktop; não são
apresentados isoladamente como certificação de Android.

### APK QA x86_64 — teste nativo aprovado

[Baixar APK QA e metadados](https://github.com/BernardoJ/PescaIdle/actions/runs/40567485121/artifacts/12765575251)
· [Evidências Android](https://github.com/BernardoJ/PescaIdle/actions/runs/40567485121/artifacts/12765565281)
· [Resumo JSON](builds-main-20261027/android.json).

Use **`PescaIdle-x86_64.apk`**, não o arquivo `-unsigned.apk` de entrada. É pacote
de teste `br.com.bernardoj.pescaidle.qa`, assinado com certificado efêmero debug;
não atualiza o aplicativo de produção e não é APK para telefone ARM64.

| Propriedade | Resultado |
| --- | --- |
| Fonte efetiva | `5a2ac60af5d8e093d550a073d763ead082782591`, branch derivada |
| Geração em São Paulo | 27/10/2026, 16:22:44, UTC−03 |
| Arquivo | `PescaIdle-x86_64.apk` |
| Tamanho | 159.742.333 bytes |
| SHA-256 | `ed49d05cca032e7dd8b45aa4a477b0aaacc4052c746d77933f667fefbc29eec2` |
| Identidade | `br.com.bernardoj.pescaidle.qa`, 2.1.0, versionCode 21000 |
| Teste executado | Android 15/API 35, x86_64, QPA `android`, bytecode optimize=2 |

A execução nativa passou em dez grupos iniciais (mapas, loja/compra, diálogos,
pesca, Fashionista, save/reload, pausa/retorno, schema 5 sem clima e rejeição do
backup ligado a outro contexto), três grupos de reabertura e cinco verificações externas. Incluiu instalação real, rotação
retrato/paisagem por sensor e background/retorno reais.

O host encerrou o processo com force-stop, confirmou sua ausência e abriu outro
PID: `3145` → `3789`. O perfil e o fingerprint durável de saldo, inventário, RNG,
clima, medidas, pendência e demais dados permaneceram iguais:
`f155cabf9ff4033f6fe4ab16d450382205abde22410b8e70dc5810e09093bc01`.
A verificação do snapshot ocorreu antes da inicialização do jogo no segundo
processo. As imagens nativas de cenário/HUD, loja e filtros foram inspecionadas;
o letterbox vertical é comportamento existente, sem redesenho nesta tarefa.

**Ocorrência do emulador:** as capturas finais de retrato e paisagem mostram
“Pixel Launcher isn’t responding”. A captura após retorno está limpa. O aviso
nomeia o launcher; nenhum ANR do jogo foi confirmado nos logs preservados. Há
uma lacuna de logcat durante rotação/background (19:33:15–19:33:27 UTC), pois o
harness limpa o buffer antes da reabertura sem arquivar esse intervalo. Portanto,
a causa exata não foi estabelecida. A rotação comprova as dimensões da tela, mas
as capturas encobertas não certificam interação visual sem interrupções. Os
resultados de save e reabertura com digest igual permanecem comprovados.

### APK ARM64 — candidato assinado, execução direta pendente

[Artefato de build ARM64](https://github.com/BernardoJ/PescaIdle/actions/runs/40567485121/artifacts/12765141557).
Use **`PescaIdle-aarch64.apk`** para identificar o candidato assinado; o arquivo
`-unsigned.apk` é somente a entrada intermediária. O artefato conserva o rótulo
“não validado” porque este APK ARM64 não foi instalado/executado diretamente.

| Propriedade | Resultado |
| --- | --- |
| Fonte efetiva | `5a2ac60af5d8e093d550a073d763ead082782591`, branch derivada |
| Geração em São Paulo | 27/10/2026, 16:30:22, UTC−03 |
| Arquivo | `PescaIdle-aarch64.apk` |
| Tamanho | 151.292.960 bytes |
| SHA-256 | `b229e725a8fb8a307750499b9100274e406dec8efc0ac0baef81edf22cf7bf3b` |
| Identidade preservada | `br.com.bernardoj.pescaidle`, 2.1.0, versionCode 21000 |
| SDK / ABI do manifesto | minSdk 28, targetSdk 36, arm64-v8a |
| Assinatura | APK Signature Scheme v3 verificado, certificado oficial existente |
| SHA-256 do certificado | `3b0c2615f5b32c0a05b8eca81a95c1c282f00639d8fdb40264c3d20613310e31` |

O certificado é igual ao registro histórico `docs/evidencias_android/apk/signature-arm64.txt`.
Somente as credenciais oficiais já existentes do GitHub foram usadas para ARM64;
nenhuma identidade de produção foi criada. O certificado debug novo é exclusivo
do pacote QA. Nenhuma chave ou senha entrou no Git/artefatos de distribuição.

Builds Android limpos usaram PySide6 6.11.2, NDK 27.2.12479018, Buildozer 1.5.0 e
python-for-android `94ffd5f31d816414ad1fe66c0fe587c61daac757`.
O Python do host de build foi 3.11.17; o runtime é fixado em 3.11.11 pelo script.
Não foram acrescentadas permissões Android; o badging não lista permissões de
armazenamento/rede. Zipalign foi verificado no APK alinhado antes de assinar;
apksigner verificou o APK final. Isso não certifica alinhamento ELF de 16 KB.

Limites: o APK de produção ARM64 e seu namespace AppDataLocation não foram
executados diretamente; o ensaio nativo usa o pacote QA e CacheLocation. A seleção
do namespace de produção foi coberta pelos contratos de QStandardPaths, com a
mesma persistência compartilhada. Sem telefone físico ARM64, dispositivo de
páginas de 16 KB ou Play Store. A beta histórica não foi substituída.

## D. Documentação e evidências

**README atualizado: SIM.** Main reconhecida como oficial, merge concluído,
correção schema 5 incorporada, novos comandos de build/QA, download Windows e
caminhos reais de save. ANDROID.md separa a atualização atual da beta histórica,
explica os contextos e a ausência de importação automática do progresso antigo.
Os relatórios antigos mantêm datas e limitações; não foram apagados ou reescritos.

[Metadados Windows da primeira rodada](https://github.com/BernardoJ/PescaIdle/actions/runs/40565453844/artifacts/12761259615)
e [metadados Android da rodada final](https://github.com/BernardoJ/PescaIdle/actions/runs/40567850107/artifacts/12765332051)
contêm BUILD/VALIDATION/ARCHIVE conforme a plataforma, manifestos, assinatura
pública, hashes e resultados nativos, sem chaves/saves. Os APKs da primeira
coleta são preliminares e foram superados; use apenas os links finais da seção C.
O JSON de cada build Android registra “Pending separate emulator job” porque foi gerado antes desse job; o `result.json` posterior comprova
sua conclusão para o pacote QA, não para ARM64.

Os artefatos CI estão sujeitos à retenção do GitHub (metadados: até 25/01/2027,
conforme API na coleta). Não houve nova release estável, deploy ou alteração de
permissões do repositório. Nenhum binário pesado foi commitado.

Arquivos pertinentes alterados/novos:

- Produção: `pesca_piloto.py`, `pesca_android.py`, `pesca_save.py`.
- QA Android: `tools/android_smoke.py`, `tools/test_android_profiles.py`,
  `tools/test_android_emulator.py`, `tools/test_android_emulator_harness.py`.
- Build/QA: `tools/build_windows_main.py`, `tools/smoke_windows_main.py`,
  `tools/record_android_build.py`, `.github/workflows/builds-main.yml`,
  `.github/workflows/collect-build-evidence.yml`.
- Documentação: README.md, ANDROID.md, este relatório e resumos sanitizados em
  `docs/builds-main-20261027/`.

## E. Problemas conhecidos e regressão

[Validação inicial da fonte](builds-main-20261027/source-validation.json) e
[regressão após a guarda auxiliar](builds-main-20261027/aux-isolation.json):
**143 testes unitários nas suítes verdes**, sem somar reruns ou a demo falha. São 19 clima,
44 conquistas, 17 tamanhos/pendências, 11 auditoria, 11 museu, 10 aquário,
24 perfis Android e 7 harness. Linux x86_64/Python 3.12.14/Qt offscreen.
Passaram ainda 5.920 checks de expansão, 1.359 cosméticos, 3.080 pools climáticos,
33.880 contextos econômicos, 168 pools e 210 progressões de balanceamento,
280 cenas climáticas e 1.120 quadros. A matriz climática completa precedeu a
guarda auxiliar; depois dela foram
repetidos os 19 contratos de clima, os 83 testes de regressão com matrizes de
expansão/cosméticos/balanceamento, os 24 perfis (normal e `-OO`) e os 10 de aquário.
O harness de sete casos passou também antes de cada APK. Smoke normal da fonte
main passou em três processos. Os testes nativos Windows/Android estão descritos separadamente acima.

A demo antiga tem **as mesmas seis falhas em dez testes** na main `f8190f5` e
no publicado `a352061`; fontes da demo byte a byte iguais. Falha `test_02` até
`test_07`: o roteiro fabrica pendência sem clima; um caso não alcança a interrupção
simulada porque o commit já é recusado. [Casos e comandos reproduzidos](builds-main-20261027/DEMO_PREEXISTENTE.md)
· [JSON sanitizado](builds-main-20261027/demo-classification.json).
Prioridade P2, impacto no modo opcional `--demo`, que permanece não certificado.
Não impede o jogo normal validado. Não foi atribuído à correção schema 5 nem
“corrigido” relaxando a validação.

A revisão adicional reproduziu um **defeito preexistente do SaveStore**: um link
auxiliar criado previamente por alguém com acesso de mesmo usuário podia cruzar
a fronteira do piloto. Foi corrigido na branch, com regressões sintéticas; a main
`f8190f5` e o EXE exclusivamente dela ainda o conservam. O jogo não cria tais
links e não houve evidência de perda de dados nos fluxos normais testados. Esse
achado impede aprovar o EXE atual para distribuição final. Após revisão/merge,
será necessário novo build limpo da main e regressão nativa Windows desse caso.

Nenhuma nova regressão foi detectada nas suítes executadas. Os runners antigos
`smoke_exe.py` e `run_climate_smoke.py --exe` tinham expectativas/caminhos de QA
incompatíveis com o piloto; um harness novo, separado da fonte compilada, executou
a validação nativa. Não foi alterado o roteiro funcional da demo para esconder
falhas históricas. Estudos históricos completos base/piloto e sessões longas não
foram repetidos. Mac, Windows de consumidor limpo e aparelho físico Android não
foram testados. Save pessoal nunca foi fixture, lido, copiado ou migrado.

## F. Resultado para distribuição

- **Windows: NÃO APTO PARA DISTRIBUIÇÃO FINAL.** O EXE novo da main passou nos
  dez checks nativos, contém a correção de schema 5 e tem pacote/recursos
  conferidos. Porém, foi produzido antes da guarda auxiliar ainda fora da main.
  É candidato funcionalmente validado, não release final. Falta integrar a
  correção mediante aprovação e compilar/testar novamente a nova main em Windows,
  incluindo regressão do link auxiliar. Authenticode, instalação de consumidor
  limpa, demo e sessão longa também não foram certificados, mas não são a causa
  deste bloqueio concreto.
- **Android: NÃO APTO PARA DISTRIBUIÇÃO FINAL do aplicativo ARM64.** Há APK QA
  x86_64 com persistência/isolamento aprovados em emulador e APK ARM64 assinado
  gerado, mas não houve
  execução direta do artefato de produção/namespace AppDataLocation em ARM64. O
  candidato fica disponível como artefato de build com esses limites; não substitui
  a release estável nem é anunciado como APK da main ou suporte a 16 KB/Play Store.

A correção Android, ferramentas e documentação ficam em PR para main, sem merge
automático. A aprovação anterior cobria apenas o PR #6; não foi reutilizada para
integrar esta nova alteração. Não houve force push, rebase ou reescrita da main.
