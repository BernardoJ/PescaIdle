# Aquário: passos 4 e 5 - movimento e revisão

Data: 23/10/2026. Continuação dos [passos 1 a 3](../README.md), preservados na PR #5.

## Experimentar com dois cliques

[Baixar PescaIdle-Aquario-Demo.exe](https://github.com/BernardoJ/PescaIdle/raw/refs/heads/codex/piloto-tamanhos/PescaIdle-Aquario-Demo.exe).

Salve em uma pasta gravável e abra. É uma **demonstração visual**, sem progressão, renda ou save. Mostra o widget real do museu com descobertas sintéticas em memória. Permite escolher entre os 68 peixes, trocar menor/maior das quatro espécies medidas do piloto, pausar a animação e avançar quadros. O botão de grupos facilita comparar formas diferentes.

- Build Windows do código `0c29196ac261ed04faf153121a1f8a01b1869cfc`.
- 50.401.961 bytes. SHA-256: `8d0bbd23dacd826cf2eede09b78fba470d76261527120205b417a43eaad8fffb`.
- Sem Python instalado para executar o EXE. Cria apenas diretórios vazios de ambiente temporário em `qa/aquario-demo-*`, junto ao EXE; não cria nem abre save.
- O executável do jogo completo preexistente não foi substituído por este visualizador. A alteração de animação está no código-fonte do museu.

## O que foi implementado

1. Mantidos os 68 desenhos específicos, suas referências e o envelope lógico 36x24 dos passos 1-3.
2. Ciclo curto de oito quadros visuais, com cauda/peitorais discretas; articulação da região posterior nos corpos alongados; nadadeiras de formas especiais, como cavalo-marinho e peixe-lua.
3. Cadências de 0,18 a 0,24 s por quadro são escolhas artísticas, não taxas de nado biológicas. Os percursos e o timer de 66 ms existentes permanecem.
4. A fase usa somente o relógio visual do widget. Não há sorteio nem alteração de estado do jogo. Cache limitado a 512 imagens pequenas; o quadro zero preserva a arte anterior.
5. Demonstração isolada, testes focados, microbenchmark comparativo, PNGs e GIFs. O [PDF consolidado](../../../output/pdf/PescaIdle_Aquario_Completo.pdf) descreve os cinco passos.

## Código e procedência

- Fonte verificada no GitHub antes da alteração: `dcd69c9e1a7f1e3d65ff822d192c702450426edd`, branch `codex/piloto-tamanhos`.
- Código/artes/animação/build testados: `0c29196ac261ed04faf153121a1f8a01b1869cfc`.
- Base da PR: `codex/android-auditoria`, `2a0353ff7c1cae2dca69d08c222b0660770d4385`.
- Branch isolada usada: `codex/aquario-movimento-20261023`. Publicação normal na branch da PR #5, sem merge.
- O commit documental posterior inclui este material, o verificador do pacote e o binário verificado; não altera a implementação capturada.

## Reprodução

Use Python 3.14.8/PySide6 6.11.2, Pillow 12.3.0 e, para build/verificação de pacote, PyInstaller 6.22.3 já disponíveis. Nenhuma instalação integra estes comandos. Use pastas de saída inéditas.

```powershell
python -B tools/validate_aquarium_motion.py --out qa/revisao-movimento
git archive dcd69c9e1a7f1e3d65ff822d192c702450426edd --output=qa/passos123.zip -- '*.py' assets
python -c 'import zipfile;zipfile.ZipFile("qa/passos123.zip").extractall("qa/passos123")'
python -B tools/validate_aquarium_motion.py --source qa/passos123 --out qa/passos123/qa/performance --benchmark-only
python -B aquario_demo.py --smoke --out qa/demo-fonte
python -B aquario_demo.py
```

A ferramenta configura save, APPDATA, LOCALAPPDATA, TEMP e TMP sintéticos antes dos imports Qt/produto. O estado é construído em memória. Nenhum motor de pesca, migração ou SaveStore é importado pela demonstração. No museu real do jogo, apenas o renderer do tanque recebe a fase visual; regras de jogo não foram alteradas.

Build separado (Windows; código/assets devem estar commitados):

```powershell
python -B tools/build_aquarium_demo.py --out dist/aquario-revisao
```

O nome produzido contém o prefixo do SHA. Para conferir o pacote, use esse nome real:

```powershell
python -B tools/verify_aquarium_bundle.py --exe dist/aquario-revisao/PescaIdle-Aquario-Demo-SHA.exe --out qa/pacote-verificado.json
```

Substitua `SHA` pelo prefixo exibido pela build. O comando exato desta execução e o smoke do EXE estão no [relatório](RELATORIO.md).

## Evidências

- [Movimento ampliado](evidencias/movimento-ampliado.gif), para distinguir cauda/nadadeiras do deslocamento pelo tanque.
- [Três peixes do piloto](evidencias/aquario-piloto.gif) e [formas especiais](evidencias/aquario-formas.gif), clipes de 3,84 s. A volta ao início do GIF é reinício do clipe, não do percurso do jogo.
- [Oito quadros de seis espécies](evidencias/quadros.png).
- [Museu em 640x700](evidencias/museu-640.png) e [320x568](evidencias/museu-320.png).
- [Demonstração compilada em 640x700](evidencias/demo-exe-640.png) e [320x568](evidencias/demo-exe-320.png).
- `checks.json`, `performance*.json`, `smoke-*.json` e `bundle.json`: resultados observados nesta etapa.

## Limites

As prévias são widgets Qt Windows, renderizados sem exibição na tela. Testes de UI usam QTest; não comprovam toque/Android ou avaliação humana prolongada. As medições são do renderer isolado, não de FPS do jogo inteiro, compositor, GPU, bateria ou celular. Não foram repetidas as suítes históricas de economia, RNG do motor, migração ou offline: nenhum desses componentes foi alterado. A revisão estética final cabe ao proprietário.
