> Instruções da área local original. A estrutura publicada e o link do EXE estão no [README da publicação](README.md).

# Piloto isolado — tamanhos e recordes

## Abrir

Dê dois cliques em `executavel/PescaIdle-Tamanhos-Piloto.exe`. Não requer instalar Python.

O piloto começa com um perfil novo. Seu progresso fica em `executavel/perfil-piloto/save.json`, ao lado deste executável. A pasta precisa permitir gravação. Não copie seu save pessoal para cá. O piloto recusa caminhos de perfil fora da própria pasta, inclusive quando a variável `PESCA_IDLE_SAVE_PATH` estiver definida.

O EXE é uma entrega local para revisão. Não substitui o executável do jogo principal.

## Experimentar

1. Pesque na Enseada do Poente. Lambari, Tilápia-do-nilo, Carpa-comum e Traíra recebem comprimentos neste piloto; as demais espécies continuam sem medidas inventadas.
2. A captura mostra o comprimento, a faixa e, quando houver, um aviso de recorde.
3. Abra **Enciclopédia** e selecione uma espécie descoberta para ver o menor e o maior exemplar. Os filtros existentes continuam disponíveis; os textos têm rolagem.
4. Abra **Museu**, escolha uma espécie em um dos três espaços e selecione **Maior exemplar conhecido** ou **Menor exemplar conhecido**. Sem medida conhecida, a representação permanece padrão e esse seletor fica desativado.
5. Em **Conquistas**, confira os cinco objetivos de medidas. Não concedem moedas ou bônus.

Os comprimentos são parâmetros provisórios de design, não dados biológicos. O aquário comprime a escala por espécie; os centímetros são a referência exata.

## Voltar ao estado anterior

Feche o piloto e abra seu executável anterior, no local original. O candidato, sua base e seus perfis estão em pastas separadas. Nenhum save pessoal foi lido ou migrado e nenhuma alteração foi enviada ao GitHub.

Não transfira o save schema 4 deste piloto para o jogo principal, que usa schema 3 nesta base. O marcador `pilot_kind=tamanhos-v1` distingue esse candidato de outras propostas de schema 4. Uma eventual integração depende de revisão e migração própria; não foi feita.

## Material de revisão

- `RELATORIO.md`: implementação, testes observados, resultados, limitações e recomendações.
- `PARAMETROS.md`: recorte, distribuição, faixas e compressão visual.
- `ALTERACOES.patch`: diff textual completo do candidato contra a cópia-base.
- `BASE.json`: origem e hashes dos 373 arquivos copiados.
- `ENTREGA.json`: hashes do snapshot, arquivos alterados e identificação do build.
- `candidato/qa/visual/`: capturas e comparações desktop/mobile.
- `candidato/qa/`: resultados sintéticos, logs e perfis exclusivos dos testes. Não contêm dados pessoais do jogador.
- `base/`: cópia preservada de referência; `candidato/`: código do piloto.

Os README/ANDROID originais dentro das cópias descrevem o projeto-base. Para este piloto, siga estas instruções e os comandos do relatório.
