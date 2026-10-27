# Relatório visual - Aquário por espécie

Data: 23/10/2026. Entrega sobre a PR [#5](https://github.com/BernardoJ/PescaIdle/pull/5), mantida em rascunho.

## Revisões

- Fonte anterior conferida: `0f516e89c4bb7b2935a5011801595429941431c6`.
- Código e arte capturados: `e4e9e3f40a6f99d7f40de8dd9bc7d94dc020bfbb`.
- Branch local de trabalho: `codex/aquario-especies-20261023`.
- Destino da publicação: `BernardoJ/PescaIdle:codex/piloto-tamanhos`, PR #5, base `codex/android-auditoria`.
- Commit-base da PR conferido: `2a0353ff7c1cae2dca69d08c222b0660770d4385`.

O commit documental posterior acrescenta este relatório, as capturas e o PDF. Não altera o código/arte capturados. O corpo antigo da PR contém evidências de outras datas e links para executáveis anteriores: não são evidências desta alteração.

## Implementado

1. Desenhos originais dos 68 peixes elegíveis, com silhuetas, boca, nadadeiras, cauda, paletas e marcas características por espécie. Perfis especiais incluem cavalo-marinho vertical, linguados com dois olhos do mesmo lado, Mola com clavus, celacanto com cauda trilobada e peixes abissais de mandíbulas distintas.
2. Comparação inicial de Lambari, Tilápia-do-nilo, Carpa-comum e Traíra, inclusive menor/maior segundo as regras preexistentes do piloto.
3. Renderer exclusivo do tanque, mestre 72x48 no envelope lógico 36x24. Detalhe 2 em escala física >=2; detalhe simplificado em 1x. Transformação uniforme e orientação compatível com o movimento existente.
4. Ferramenta de captura reproduzível e documentação das referências e limitações.

Não foram alterados gameplay, catálogo de pesca, economia, RNG, parâmetros de comprimento, conquistas ou save. O único arquivo de produto preexistente alterado é `pesca_museu_ui.py`: troca do renderer do tanque e escolha do nível de detalhe. `pesca_especies_visual.py` e `pesca_tamanho_visual.py` permanecem byte a byte iguais ao head anterior.

## Execuções observadas

Ambiente Windows, Python 3.14.8 e PySide6 6.11.2 já disponíveis. Não houve instalação.

### Capturas definitivas

```powershell
python tools/capture_aquarium_species.py --source . --out qa/aquario-e4e9e3f --label 'Depois | e4e9e3f40a6f'
python tools/capture_aquarium_species.py --source qa/base-source --out qa/base-source/qa/aquario-antes --label 'Antes | PR5 0f516e89c4bb'
```

A segunda execução importou os arquivos reais exportados de `0f516e89c4bb7b2935a5011801595429941431c6` por `git archive`, não uma imitação do renderer anterior. Os comandos com `python` usaram o interpretador local já disponível; caminhos pessoais foram omitidos.

Resultado de cada execução: **68 elegíveis / 68 imagens distintas; cache compartilhado preservado; nenhum save criado**. Cada lado produziu 15 PNGs e um manifesto JSON. O manifesto registra versões, hashes de imagens e hashes dos arquivos Python/JSON do produto. As imagens de antes e depois usam o mesmo cenário, descoberta sintética, valores extremos de tamanho e fase de movimento zero.

Verificação estática dos manifestos: entre os arquivos Python/JSON já existentes, somente `pesca_museu_ui.py` mudou. Foram acrescentados o módulo visual e o JSON de arte. A leitura do diff confirmou ausência de mudança nos caminhos de pesca/economia/RNG/persistência.

### Inspeção visual

- Quatro pranchas cobrem todos os 68 desenhos.
- Quatro espécies iniciais foram comparadas em escala mínima 0,55 e máxima 1,20.
- Museu real capturado em 640x700 e 320x568, com rolagem, texto e seletor anteriores.
- Tanques em 1x e 2x para espécies iniciais, rio, recife e profundezas.
- Conferidos silhuetas, cores, posição nas três faixas e direção de nado. A orientação dos novos mestres foi alinhada à convenção anterior do tanque.
- PDF renderizado para inspeção de layout antes da entrega.
- `git diff --check` sem erros no conteúdo final.

## Evidências e alcance

`evidencias/antes` e `evidencias/depois` contêm os widgets e pranchas. Pranchas são comparações de arte, não screenshots de uma partida. As imagens `museu-*.png` são os widgets Qt reais, renderizados sem exibição na tela. As capturas usam um host sintético em memória; o motor de pesca não é executado e o host proíbe commit.

Todos os diretórios de ambiente/perfil foram desviados explicitamente antes de importar Qt/produto. Nenhum save pessoal foi lido, migrado ou escrito. Saídas temporárias, arquivos ZIP de exportação, caches e perfis vazios não integram a publicação.

## Limitações e pendências

- Não foram executados jogo completo, suítes de integração, benchmarks, simulações, migração, build ou smoke de EXE nesta tarefa visual. Executáveis/APKs anteriores não contêm esta arte.
- Android nativo, toque e legibilidade em dispositivo físico não verificados. A janela compacta é uma captura desktop Qt, não um emulador.
- Arte é uma interpretação estilizada: não reproduz cada raio/escama, variação sexual/juvenil ou cor de todas as populações. Perfis com documentação morfológica mais limitada são sinalizados no JSON e em `README.md`.
- Medidas do piloto continuam parâmetros de design provisórios; a escala não compara comprimentos reais entre espécies.
- Nenhuma animação nova foi introduzida; o movimento anterior foi preservado.
- A avaliação estética final depende da revisão do proprietário. Nenhum merge, release ou mudança de visibilidade faz parte desta publicação.

## PDF

`output/pdf/PescaIdle_Aquario_Especies.pdf` descreve a mudança e traz exemplos visuais. Pode ser recriado com o script `gerar_pdf.py`, usando ReportLab e Pillow em ambiente de documentos já disponível, a partir da raiz do repositório:

```powershell
python docs/aquario-especies/gerar_pdf.py
```
