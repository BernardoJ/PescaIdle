# Pesca Idle para Android

A adaptação usa a mesma lógica Python/Qt, os oito mapas, as 88 espécies e todos
os cosméticos da expansão. O APK inclui o runtime e os recursos; o jogador não
precisa de Python, Android Studio, launchers nem serviços externos.

Alvo inicial: Android 9 ou superior, ARM64. A versão x86_64 é produzida para
testes em emulador. O pacote é `br.com.bernardoj.pescaidle`, versão 2.1.0,
versionCode 21000. As confirmações de instalação dependem do Android.

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
Resultados finais e limites serão registrados em `docs/AUDITORIA_ANDROID.md`.
