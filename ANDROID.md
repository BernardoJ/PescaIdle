# Pesca Idle — Android

Porta nativa do jogo Windows original para Android.

## Conteúdo da versão Android

- Pesca idle automática.
- Mesma tabela de espécies, valores e pesos do jogo original.
- Bônus da vara para encontros raros.
- Bônus do barco no valor das capturas.
- Vara e barco até nível 10.
- Sistema de peças e compras.
- Progresso offline limitado a 4 horas.
- Salvamento local no Android.
- Enciclopédia com desbloqueio de valor (1 captura), raridade (5) e curiosidade (10).
- Interface pixel-art desenhada com Canvas, sem dependências externas.

## Abrir no Android Studio

Abra a pasta android-port como projeto. O Android Studio pode sincronizar o Gradle e gerar o APK em:

app/build/outputs/apk/debug/app-debug.apk

Também existe um workflow em .github/workflows/android.yml para gerar o APK automaticamente no GitHub Actions.

## Observação

A versão Android foi criada em uma branch separada para preservar a versão Windows/PySide6.