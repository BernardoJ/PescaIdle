# Pesca Idle para Android

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
