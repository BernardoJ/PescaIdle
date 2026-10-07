# Executável Windows da expansão

Build novo concluído com Python 3.14.8 / PyInstaller 6.22.3 no Windows 11.
Artefato: `PescaIdle.exe`, 50,151,105 bytes.
SHA256: `2fea9bb9d6fd35888010450723957345312e393ba2d2ca2f1484fdaf131cce1e`.
Snapshot de entradas: `a6a0f9d19b97d9041e5e1ff8acd0cf7673fa94437b5413f776ba67ecaaabe717`.

O [manifesto](evidencias_expansao/build-windows.json) lista o hash de cada entrada
de produção; código, spec e assets são identificados independentemente do EXE.
Masters, fontes, saves, ZIP e evidências não entram no pacote. O spec preserva os
filtros anteriores de DLLs, UCRT e ICU. [Log real](evidencias_expansao/build-windows.log).

`tools/smoke_exe.py <QA>/dist/PescaIdle.exe` passou, com plugin Windows, cwd
temporário estrangeiro, APPDATA/LOCALAPPDATA e save sintéticos: 8 mapas,
schema 2, backup de migração v1, 10 Lambaris preservados, relógio local,
96 placas de luz, 14 mascotes e 13 bandeiras animadas e diálogos reais.
Não se usou o executável antigo como prova. A substituição na branch publicada
é autorizada pelo usuário; a versão anterior permanece no histórico Git.

O programa é um EXE sem instalador e sem assinatura de código. O teste confirma
este Windows e os fluxos automatizados, sem prometer cobertura de todos os
drivers/GPUs ou uma sessão longa de jogo humano. As capturas do executável foram
inspecionadas separadamente das imagens offscreen do código.
