# Resultado observado - passos 4 e 5 do aquário

23/10/2026. Código capturado/compilado: `0c29196ac261ed04faf153121a1f8a01b1869cfc`. Base real conferida: `dcd69c9e1a7f1e3d65ff822d192c702450426edd` (passos 1-3 já publicados). Ambiente Windows, Python 3.14.8, PySide6 6.11.2, Pillow 12.3.0 e PyInstaller 6.22.3 existentes.

## Plano completo e evidência

| Passo | Entrega | Evidência |
|---|---|---|
| 1. Espécies específicas | 68 desenhos, formas, paletas e marcas | JSON de arte e quatro pranchas anteriores preservadas; quadro zero revalidado em todos os 68. |
| 2. Quatro iniciais e expansão | Lambari, Tilápia-do-nilo, Carpa-comum, Traíra e demais elegíveis | Comparação anterior, limites de tamanho preservados; oito quadros dos quatro no painel novo. |
| 3. Isolamento no tanque | Renderer exclusivo, 36x24 lógico/72x48 detalhado | Arquivos de pesca compartilhados inalterados; teste de cache e comparação por hash. |
| 4. Movimento discreto | Oito quadros por ciclo, cauda/nadadeiras e corpos alongados | 68 espécies animadas nos dois níveis; GIF ampliado e GIFs do tanque. |
| 5. Conferência e demonstração | Limites, sobreposição, tamanhos, tela compacta, desempenho e EXE visual | Testes focados, microbenchmark, QTest fonte/EXE, bytecode/assets e screenshots. |

## Verificações atuais

`python -B tools/validate_aquarium_motion.py --out qa/movimento-0c29196`

**10 testes aprovados**, 0 falhas/erros, 9,387 s na suíte (o comando inclui também medição e capturas).

- 68 IDs cobertos pelo arquivo de movimento; modos e índices de partes válidos.
- 68 mestres de repouso com hashes idênticos aos passos 1-3.
- Todas as espécies mudam de aparência em 1x e 2x; pelo menos cinco imagens distintas entre as oito fases do ciclo em cada nível.
- 1.088 desenhos em canvas expandido sem extrapolar a área original.
- 122.400 amostras de posição em um percurso completo: cada espécie em cada uma das três vagas, com os maiores exemplares disponíveis. Retângulos dentro da água e sem interseção entre vagas.
- 144 renderizações de tanque com combinações de menor/maior, reversão e dois níveis, preservando o estado.
- Fase finita, passagem de quadro, volta do ciclo e entradas inválidas conferidas.
- Nenhum consumo dos métodos de RNG instrumentados; estado, RNG global, arte e cache compartilhados da pesca preservados.
- Cache reutilizado e limitado; timer interrompe ao ocultar/fechar e retoma ao mostrar.

Na execução inicial, o teste de entrada inválida detectou que `True` podia reutilizar a chave inteira `1` do cache. O cache passou a distinguir tipos. A execução definitiva acima ocorreu depois dessa correção e no commit registrado; não foi removido ou relaxado o teste.

## Desempenho

Base exportada com `git archive dcd69c9e1a7f1e3d65ff822d192c702450426edd --output=qa/passos123.zip -- '*.py' assets`. Executados serialmente, com o mesmo interpretador:

```powershell
python -B tools/validate_aquarium_motion.py --out qa/movimento-0c29196
python -B tools/validate_aquarium_motion.py --source qa/passos123 --out qa/passos123/qa/performance-final --benchmark-only
```

Por revisão: seis combinações de cena/detalhe; 30 renderizações limpando cache, 120 de aquecimento e 1.200 aquecidas em cada combinação. **7.200 amostras aquecidas e 180 frias por revisão**. Percentil 95, em milissegundos:

| Cena | Base aquecido | Novo aquecido | Base frio | Novo frio |
|---|---:|---:|---:|---:|
| Vazio 1x | 0,0725 | 0,0746 | 0,0852 | 0,0836 |
| Vazio 2x | 0,2023 | 0,1871 | 0,2994 | 0,2681 |
| Piloto 1x | 0,2079 | 0,2262 | 1,3690 | 1,5621 |
| Piloto 2x | 0,3492 | 0,3429 | 1,9794 | 2,1216 |
| Formas 1x | 0,1088 | 0,1180 | 1,0239 | 1,1423 |
| Formas 2x | 0,2456 | 0,2662 | 1,3333 | 1,5004 |

O maior p95 novo aquecido foi 0,3429 ms; frio, 2,1216 ms. O maior valor frio individual observado foi 2,1938 ms. O timer preexistente continua em 66 ms. Estes tempos locais ficaram abaixo desse intervalo, mas não medem o custo completo da aplicação ou de um dispositivo Android. Não há IC estatístico nem afirmação de melhora/equivalência de desempenho a partir de diferenças tão pequenas. Cache maior é uma troca explícita por reutilização: até 512 imagens pequenas, sem crescimento por instante do relógio.

## Demonstração e pacote

Comandos executados:

```powershell
python -B aquario_demo.py --smoke --out qa/demo-0c29196
python -B tools/build_aquarium_demo.py --out dist/aquario-0c29196
python -B tools/verify_aquarium_bundle.py --exe dist/aquario-0c29196/PescaIdle-Aquario-Demo-0c29196a.exe --out qa/bundle-0c29196.json
```

O EXE novo também foi executado com `--smoke --out` apontando para uma pasta nova em `dist/aquario-0c29196/qa/smoke-visual`. Antes de iniciar o processo, TEMP/TMP/APPDATA e o caminho de perfil foram desviados para pastas de QA; a entrada reforça o isolamento antes dos imports Qt/produto.

**Fonte e EXE passaram:** pausa, avanço de quadro, troca de grupo, troca de exemplar menor/maior, janelas 640x700 e 320x568, avanço real do timer e interrupção ao fechar. Nenhum save foi criado.

Inspeção do pacote: **sete módulos compilados** correspondem às fontes (normalizando apenas o nome de arquivo do bytecode), e **63 assets** têm o hash esperado. Os módulos `pesca_idle`, `pesca_pescaria`, `pesca_save` e `pesca_offline` estão ausentes da demonstração.

Binário publicado com o nome `PescaIdle-Aquario-Demo.exe`; conteúdo idêntico à build identificada:

- 50.401.961 bytes.
- SHA-256: `8d0bbd23dacd826cf2eede09b78fba470d76261527120205b417a43eaad8fffb`.
- Código: `0c29196ac261ed04faf153121a1f8a01b1869cfc`.
- Visualizador em memória, sem progressão; não substitui o executável antigo do jogo.

## Escopo de arquivos

- Alterados: `pesca_museu_visual.py` (quadros/cache/partes) e uma chamada em `pesca_museu_ui.py` (fase).
- Adicionados: `assets/aquario_movimento.json`, entrada/spec e ferramentas de demonstração, build, pacote e verificação visual.
- Documentação, evidências, PDF completo e EXE visual em nomes novos; arquivos históricos preservados.
- Arte estática, catálogo, parâmetros de tamanho, gameplay, RNG de pesca, economia, saves, migração e offline não foram editados.
- Não foram feitas novas animações na pesca/enciclopédia ou funcionalidades paralelas.

## Evidência histórica versus atual

As pranchas e o relatório dos passos 1-3 são evidências preservadas de sua execução anterior, em 23/10/2026; não são novos testes de gameplay. A igualdade do quadro de repouso foi revalidada agora, assim como movimento, geometria, UI e pacote descritos acima. Testes antigos de regressão e migração da PR não foram repetidos e não foram apresentados como resultados desta etapa.

## Limites

QTest e screenshots de widgets Qt sem exibição na tela não equivalem a toque ou sessão humana prolongada. Android nativo, GPU/compositor, bateria, FPS completo do jogo e outras máquinas não testados. Os GIFs do tanque são clipes; seu reinício pode mudar a posição, enquanto a demonstração usa o percurso contínuo preexistente. Cadência e articulação são estilizadas, não uma simulação biológica.

A avaliação estética final continua aberta ao proprietário. PR mantida em rascunho, sem merge na main, release ou mudança de visibilidade/permissões.
