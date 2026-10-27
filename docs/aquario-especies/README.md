# Aquário: arte por espécie

Este documento registra a entrega dos passos 1-3. A continuação dos passos 4-5, com movimento, verificações e demonstração, está em [movimento/README.md](movimento/README.md). O [PDF completo](../../output/pdf/PescaIdle_Aquario_Completo.pdf) reúne os cinco passos.

Implementação visual sobre o head da PR #5 `0f516e89c4bb7b2935a5011801595429941431c6`, em área isolada. A base da PR continua `codex/android-auditoria` (`2a0353ff7c1cae2dca69d08c222b0660770d4385` na conferência inicial). Data: 23/10/2026.

## Escopo

- 68 peixes elegíveis para o aquário recebem geometria e paleta próprias, conferidas pelos nomes científicos do catálogo existente.
- As quatro espécies iniciais são Lambari, Tilápia-do-nilo, Carpa-comum e Traíra. Pranchas com menor e maior exemplar usam os limites já existentes do piloto, sem alterar parâmetros.
- Mestres originais de 72x48 pixels, apresentados no mesmo envelope lógico de 36x24. Contorno, proporção corporal e transformação uniforme respeitam o espécime.
- No tanque com escala física de pelo menos 2x, o desenho detalhado é preservado. Em 1x, omitimos microtexturas e reduzimos por vizinho mais próximo. Sem suavização.
- Somente o tanque chama o novo renderer. Ícones do seletor, enciclopédia, pesca e demais telas mantêm o renderer compartilhado anterior.
- Permanecem as três vagas, regras de descoberta, movimento, escolha menor/maior, moeda, RNG, catálogo e formato do save. Esta entrega não acrescenta animações.

## Arquivos

| Arquivo | Finalidade |
|---|---|
| `pesca_museu_visual.py` | Leitura/cache dos desenhos e transformação uniforme, exclusivamente no tanque. |
| `assets/aquario_especies.json` | Geometria, cores, marcas e referências dos 68 peixes. |
| `pesca_museu_ui.py` | Integração do renderer e seleção do nível de detalhe pela escala física. |
| `tools/capture_aquarium_species.py` | Capturas reproduzíveis dos widgets reais com estado sintético em memória. |
| Esta pasta | Evidências, referências, comandos, relatório e exemplos. |

## Referências e limites artísticos

As fontes por espécie constam de `referencias.md` e do JSON. São referências informativas, não assets incorporados: nenhuma fotografia ou sprite externo foi copiado. O desenho é uma interpretação em pixel art, não um diagnóstico taxonômico. Cores variam com idade, sexo e ambiente; escolhemos uma apresentação consistente, sem inferir esses fatores do save.

Alguns perfis consultados servem principalmente para identificação/fotografia de referência, não para comprovar cada microdetalhe: Matrinxã, Piabanha, Curimbatá, Pintado e Pirarara. Isso está indicado no JSON. Contagens exatas de raios, escamas e dentes não são reproduzidas. A Traíra pertence a um complexo taxonômico; preservamos o nome científico do jogo. Os 20 encontros especiais continuam fora do aquário.

## Reprodução das capturas

Requer Python e PySide6 já disponíveis; não há dependência nova de runtime.

PowerShell, a partir da raiz desta revisão (use uma pasta de saída inédita em cada execução):

```powershell
python tools/capture_aquarium_species.py --source . --out qa/aquario-repro --label 'Depois | Aquário por espécie'
git archive 0f516e89c4bb7b2935a5011801595429941431c6 --output=qa/aquario-base.zip -- '*.py' assets
python -c 'import zipfile;zipfile.ZipFile("qa/aquario-base.zip").extractall("qa/aquario-base")'
python tools/capture_aquarium_species.py --source qa/aquario-base --out qa/aquario-base/qa/capturas --label 'Antes | PR5 0f516e89c4bb'
```

A ferramenta recusa saída existente e saída fora de `source/qa`. Antes de qualquer import do produto/Qt, configura `PESCA_IDLE_SAVE_PATH`, APPDATA, LOCALAPPDATA, TEMP e TMP em uma subpasta sintética. Não importa `pesca_idle`, não inicia o motor, não carrega/grava save e não simula capturas. Usa o widget real do museu com um host sintético cuja operação de commit é proibida.

A fase de movimento é congelada em zero. Os 68 peixes são descobertos somente no estado sintético em memória. Pranchas de sprites são ilustrações de comparação; `museu-desktop.png` e `museu-compacto.png` são capturas dos widgets Qt reais, renderizados sem exibição na tela. Não são testes de toque, Android ou interação física.

## Verificações desta tarefa

Resultados e hashes estão em `evidencias/*/manifest.json`; detalhes finais em `relatorio.md`. As capturas não constituem testes de integração, persistência, economia, Android nem empacotamento. Nenhuma suíte ampla ou simulação do jogo foi executada para esta mudança visual. Nenhum executável novo foi compilado nesta entrega.
