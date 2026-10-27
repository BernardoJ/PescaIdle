# Pesca Idle para Android

## Estado da atualização derivada da main — 27/10/2026

O [PR #7](https://github.com/BernardoJ/PescaIdle/pull/7) integrou o caminho
privado e a proteção auxiliar dos saves na main em `0108882`. Os APKs disponíveis
foram gerados de `5a2ac60`, originalmente na branch `codex/builds-main-20261027`
e agora ancestral da main. Não foram recompilados após o merge; seus hashes e
limites continuam os mesmos. [Estado após o merge](docs/VALIDACAO_MAIN_0108882.md)
· [Ensaios Android e hashes originais](docs/BUILDS_MAIN_20261027.md#c-android).

O bootstrap configura o contexto **antes de importar o jogo**:

- Produção: `QStandardPaths.AppDataLocation/pilotos/tamanhos-v1/save.json`.
- Pacote QA separado: `QStandardPaths.CacheLocation/qa-tamanhos-v1/save.json`.
- A raiz vem do Qt Android nativo. Variáveis de ambiente não podem ampliá-la;
  caminhos externos, outros contextos e redirecionamentos por symlink são recusados.
- Save, backups, backups de migração, lock e substituição atômica validam a fronteira
  antes de I/O. Uma regressão específica impede recuperar `.bak` ligado a outro contexto.
- Desktop mantém o perfil dentro da pasta do candidato/EXE; não importa APPDATA.

O schema continua **5**, sem mudança de formato. O save legado Android em
`AppDataLocation/save.json` é preservado e não é lido/importado automaticamente.
O piloto usa contexto próprio; não há migração entre contextos nesta entrega.
Dentro do contexto novo, schemas 1–4 válidos conservam migração com backup exato.
A atualização/reabertura mantém o caminho e o perfil; não exige armazenamento
externo nem novas permissões Android.

Os testes incluem contratos de diretório/persistência e, no APK QA, encerramento
real do processo e reabertura com outro PID, conferindo o mesmo perfil, schema 5
e fingerprint de RNG, clima, medidas, saldo, inventário e pendência. Os resultados
nativos efetivamente obtidos estão no relatório atual; testes Qt desktop não
certificam Android.

O workflow novo `builds-main.yml` usa as ferramentas originais e saídas limpas.
ARM64 só recebe assinatura de distribuição com as credenciais oficiais existentes;
sem elas, o resultado permanece explicitamente não assinado/não instalável.
O APK QA tem pacote distinto e certificado efêmero de teste, não de produção.
Versão `2.1.0`/versionCode `21000` foram preservados; não houve incremento artificial.
Nenhum artefato não validado substitui a beta histórica.

## Registro histórico: beta anterior à versão atual

A descrição e os downloads abaixo pertencem à beta de auditoria anterior ao
museu, tamanhos, decorações, conquistas e clima. Não certificam o APK novo.


A adaptação usa a mesma lógica Python/Qt, os oito mapas, as 88 espécies e todos
os cosméticos da expansão. O APK inclui o runtime e os recursos; o jogador não
precisa de Python, Android Studio, launchers nem serviços externos.

Alvo inicial: Android 9 ou superior, ARM64. A versão x86_64 é produzida para
testes em emulador. O pacote é `br.com.bernardoj.pescaidle`, versão 2.1.0,
versionCode 21000. As confirmações de instalação dependem do Android.

O primeiro pacote é distribuído como beta para ARM64 com páginas de memória
de 4 KB. A análise ELF encontrou bibliotecas do empacotador Python e shiboken
com alinhamento de 4 KB; a compatibilidade nativa com aparelhos configurados
para 16 KB ainda está pendente. `zipalign -P 16` verifica o APK, mas não altera
essas bibliotecas. Não foi publicado na Play Store nem certificado em telefone
físico. [Requisitos de páginas do Android](https://developer.android.com/guide/practices/page-sizes).

## Instalar

Baixe [PescaIdle-Android.apk](https://github.com/BernardoJ/PescaIdle/releases/download/v2.1.0-android-beta.1/PescaIdle-Android.apk), abra o arquivo e confirme a instalação. Se solicitado pelo Android, permita que esse navegador/gerenciador instale aplicativos. Não há configuração de servidor, login nem download de recursos na primeira abertura.

APK assinado: 151.170.080 bytes, SHA256
`beeaeb7354b4215572e15151b1270384fee124645d68dc63c687b8e1b4adc279`.
O APK está nos arquivos da release, pois ultrapassa o limite de arquivo Git.

## Interface e persistência

- Menu e botões maiores para toque, páginas roláveis, orientações vertical e
  horizontal e pixels físicos inteiros.
- Save privado do aplicativo. A pausa intencional continua sem renda offline.
- Ao ir para segundo plano, salva a fisgada pendente e interrompe timers. Ao
  retornar, aplica uma única janela histórica de até quatro horas.
- Sem serviço em segundo plano, alarme, acesso à localização ou permissão de rede.

## Compilação

`.github/workflows/android.yml` gera ARM64 e x86_64 em Linux com Python 3.11,
PySide6 6.11.2 e NDK 27.2.12479018. `tools/build_android.py` prepara uma área
temporária somente com fontes e recursos de produção. Não aceita licenças do
SDK automaticamente: requer um SDK já provisionado.

Os segredos `PESCA_IDLE_ANDROID_KEYSTORE` e `PESCA_IDLE_ANDROID_PASSWORD` contêm
a assinatura estável. Não devem ser incluídos em commits ou substituídos a cada
build. A cópia privada de recuperação fica na área local da tarefa.

O workflow verifica a assinatura, registra hash, manifesto e SHA do código.
Testes de instalação e execução Android são distintos dos ensaios Qt desktop.
Instalação e oito grupos funcionais passaram em Android 15/API 35 x86_64,
mais rotação real por sensor e segundo plano/retorno. O código de jogo e assets
são idênticos aos do ARM64; ABI/empacotamento nativo do ARM64 não foram
executados em um telefone. [Resultados e limites](docs/AUDITORIA_ANDROID.md).
