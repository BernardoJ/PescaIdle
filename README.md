# Pesca Idle

Jogo idle de pesca para Windows, feito em Python com PySide6.

A tabela de capturas reúne peixes e outras espécies aquáticas; os critérios e as fontes usados para ajustar raridade e recompensa estão em [`CRITERIOS_RARIDADE.md`](CRITERIOS_RARIDADE.md).

## Jogar

Baixe `PescaIdle.exe` e dê dois cliques para abrir. O executável inclui o runtime necessário e não requer uma instalação separada de Python.

## Executar pelo código-fonte

Requer Python 3 e PySide6:

```powershell
python -m pip install PySide6
python pesca_idle.py
```

## Gerar o executável

Com PyInstaller instalado:

```powershell
python -m pip install PyInstaller PySide6
python -m PyInstaller --noconfirm PescaIdle.spec
```

O executável é gerado em `dist/PescaIdle.exe`.
