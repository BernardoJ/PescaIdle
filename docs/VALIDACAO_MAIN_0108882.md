# Validação após o merge do PR #7 — 27/10/2026

## A. Repositório e integração autorizada

O [PR #7](https://github.com/BernardoJ/PescaIdle/pull/7) foi integrado por merge,
sem squash/rebase, no commit oficial da main
`0108882dcf9a6f65b1a4bafeb5bd71cf507e044c`.

Antes do merge foram reconferidos base `f8190f5`, head
`f1828a44006b505991ac3b814c80f1a6a7e30e20`, árvore
`3975691d54b4c3fd392686617045b4c9720eeb60` e SHA-256 do diff completo
`fb0e897f4b59e12e96278bc1f05dd230a4be7f54fc965e8aa6db79fd2bbf6261`.
Tudo permaneceu idêntico ao que o usuário aprovou. Após o merge foram verificados
os dois pais, a árvore, o diff e os seis commits na main remota. O checkout
original, branch local `work`, foi sincronizado por fast-forward e ficou limpo;
nenhum trabalho foi descartado.

O novo build Windows usa **exclusivamente essa main fixa `0108882`** em checkout
limpo, separado das ferramentas. A branch `codex/windows-main-0108882`, em
`6f8a885ac00192dbdb5c82046efacb8b28aa30b1`, acrescenta apenas um caso de QA
Windows e um workflow específico. Essas ferramentas não alteram a fonte
compilada. Um commit posterior registra README, Android e este relatório.
Nenhuma outra alteração foi integrada na main nesta rodada.

## B. Windows

**Novo EXE gerado: SIM. Resultado: APTO PARA DISTRIBUIÇÃO do jogo normal Windows x64.**

[Baixar EXE e metadados](https://github.com/BernardoJ/PescaIdle/actions/runs/40572649866/artifacts/12766630446)
· [Evidências nativas](https://github.com/BernardoJ/PescaIdle/actions/runs/40572649866/artifacts/12765831198)
· [Metadados pequenos](https://github.com/BernardoJ/PescaIdle/actions/runs/40572649866/artifacts/12767160080)
· [Resumo JSON](builds-main-0108882/windows.json).

| Propriedade | Resultado |
| --- | --- |
| Fonte oficial | `0108882dcf9a6f65b1a4bafeb5bd71cf507e044c`, main após PR #7 |
| Ferramentas de build/QA | `6f8a885ac00192dbdb5c82046efacb8b28aa30b1` |
| Data em São Paulo | 27/10/2026, 16:52:31, UTC−03 |
| Executável | `PescaIdle-Windows-0108882.exe` |
| Tamanho | 48.796.094 bytes |
| SHA-256 do EXE | `b00c08a85b48aeb7b50fe27d9fbe66ae06ea637a7c46e7ad9f40ffddf5030404` |
| SHA-256 do ZIP | `54a82ccf0d8774fb9da8adc0c3a1a059589d8d53dd874cdad1897853746b68ba` |
| Versão do aplicativo | Desktop sem versão explícita; nenhum número foi inventado |
| Plataforma | Windows x64, runner windows-2025, Python 3.12.10 |
| Ferramentas fixadas | PyInstaller 6.22.3, PySide6 6.11.2, Pillow 12.3.0 |
| Authenticode | Não aplicado |

Spec original, PyInstaller `--clean`, diretórios/cache novos, sem EXE histórico
reutilizado. Foram conferidos 39 módulos do projeto + entrypoint e
66 recursos PNG/JSON contra a fonte limpa. O pacote acompanha
BUILD/VALIDATION/ARCHIVE JSON e SHA256SUMS; não contém perfis de QA/saves.

As **11 verificações nativas passaram**, incluindo o caso adicional de isolamento
auxiliar pelo próprio EXE. O [workflow 40572649866](https://github.com/BernardoJ/PescaIdle/actions/runs/40572649866)
concluiu com sucesso; cenário e painel climático também foram inspecionados
visualmente. A validação não se limita ao sucesso da compilação.

O teste adicional usa um arquivo válido sintético fora da pasta do EXE e um
`.bak` ligado a ele por symlink nativo Windows. Executa o EXE real, exige saída
de erro sem oferecer recuperação e confere que arquivo principal, link e alvo mantiveram os
bytes, sem arquivo rejeitado. Se o runner não pudesse criar o link, o teste
falharia explicitamente; nenhuma permissão é alterada para viabilizá-lo.

Os outros casos cobrem startup e oito mapas em escalas 100%/125%, assets,
migração v1 com backup exato, clima pending/deliver/reopen em processos distintos,
schema 5 sem clima com backup inválido ou cancelamento de recuperação válida,
migração v4 e recuperação explícita pelo Store da fonte cujo bytecode é igual ao
empacotado. A recuperação positiva pelo botão Sim do EXE não foi exercitada.
Sem instalação Windows de consumidor limpa, Authenticode ou sessão humana longa.

O perfil fica em `perfil-piloto/save.json` ao lado do EXE; extraia numa pasta
gravável. Não precisa instalar Python nem importar o save pessoal de APPDATA.
Este build supera o candidato funcional `f8190f5` da rodada anterior, que não
continha a guarda auxiliar e não foi aprovado para distribuição final.

## C. Android

**Caminho privado: CONCLUÍDO e integrado. Isolamento: SIM nos contratos e QA
nativo. APKs gerados: SIM, sem recompilação nesta rodada.**

Os APKs continuam com origem exata em
`5a2ac60af5d8e093d550a073d763ead082782591`, gerados na branch anterior e agora
ancestral da main. O código Python, assets, requisitos e spec não mudaram entre
essa fonte testada e o merge; a equivalência foi conferida por Git. Isso não
altera o commit de origem dos binários nem os transforma em novos builds `0108882`.

- [QA x86_64](https://github.com/BernardoJ/PescaIdle/actions/runs/40567485121/artifacts/12765575251):
  `PescaIdle-x86_64.apk`, SHA-256
  `ed49d05cca032e7dd8b45aa4a477b0aaacc4052c746d77933f667fefbc29eec2`.
- [Candidato ARM64 assinado](https://github.com/BernardoJ/PescaIdle/actions/runs/40567485121/artifacts/12765141557):
  `PescaIdle-aarch64.apk`, SHA-256
  `b229e725a8fb8a307750499b9100274e406dec8efc0ac0baef81edf22cf7bf3b`.

Use os arquivos assinados acima, não as entradas `-unsigned.apk` do ZIP. Versão
2.1.0/versionCode 21000 preservada. ARM64 usa a assinatura oficial existente;
QA é pacote distinto com certificado debug efêmero. Não houve novas permissões.

Os 24 contratos de perfil e o QA Android 15/API35 x86_64 passaram, incluindo
recusa de schema 5 sem clima e do backup com symlink estrangeiro. Reabertura real
com force-stop e outro PID conservou o mesmo perfil/schema/digest. A captura de
rotação mostrou ANR do Pixel Launcher; há lacuna de logcat nesse intervalo, sem
ANR do jogo confirmado. Persistência foi comprovada; interação visual contínua
não foi certificada. ARM64, namespace de produção, atualização sobre instalação
antiga, páginas de 16 KB e Play Store não foram executados diretamente.

Produção usa `QStandardPaths.AppDataLocation/pilotos/tamanhos-v1/save.json`; QA
separado usa `CacheLocation/qa-tamanhos-v1/save.json`. O save legado privado fica
intacto e não é importado automaticamente. O novo contexto começa separado.
Formato schema 5 e migrações legítimas 1–4 com backup foram preservados.

[Ensaios, evidências, assinatura e limites Android completos](BUILDS_MAIN_20261027.md#c-android).

## D. Documentação

README e ANDROID.md foram atualizados nesta branch para reconhecer o merge já
concluído, a nova origem Windows e a origem histórica exata dos APKs. Os
relatórios anteriores permanecem datados e preservados. Este complemento de
CI/QA/documentação fica em novo PR, sem reutilizar a aprovação do PR #7.

## E. Testes e problemas conhecidos

Os 143 testes únicos de fonte e as matrizes da preparação anterior permanecem
registrados no [relatório original](BUILDS_MAIN_20261027.md#e-problemas-conhecidos-e-regressão).
Não foram apresentados como nova execução pós-merge: a árvore integrada é a
exatamente revisada. A nova execução desta rodada é o build/QA Windows descrito
acima, incluindo o EXE com guarda auxiliar.

As seis falhas em dez testes da demo opcional continuam preexistentes e não
foram corrigidas nem atribuídas ao merge. O roteiro ainda fabrica capturas sem
clima; o jogo normal tem validação separada. As limitações Android continuam.
Nenhum save pessoal foi lido, copiado ou migrado. Nenhuma chave, credencial,
arquivo temporário ou binário pesado foi incluído nos commits.

## F. Parecer de distribuição

- **Windows: APTO PARA DISTRIBUIÇÃO do jogo normal Windows x64.** A guarda auxiliar agora está no
  binário oficial e sua regressão passou no EXE nativo. Mantêm-se os limites
  de demo, assinatura e ambiente descritos, sem certificar plataformas não testadas.
- **Android: NÃO APTO PARA DISTRIBUIÇÃO FINAL ARM64.** QA de persistência e
  isolamento aprovado; falta execução direta do APK de produção e permanecem os
  limites de UI/emulador descritos. Nenhuma beta estável foi substituída.

Somente artefatos de CI foram disponibilizados, sujeitos à retenção do GitHub.
Nenhuma release estável, deploy, force push ou alteração de permissões foi feita.
