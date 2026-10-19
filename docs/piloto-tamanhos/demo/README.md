# Demonstração de tamanhos e aquário — 19/10/2026

Esta entrega parte da PR #5 em `9d57a465ad418f885af46d11590def0753007e78`. Acrescenta correção do ID pendente, apresentação de recordes e um modo **explicitamente sintético**. A base econômica continua `2a0353ff7c1cae2dca69d08c222b0660770d4385`. Não implementa Fluxo/Precisão ou Android, nem muda parâmetros, distribuição de espécies ou recompensas.

[Relatório observado, identificação da build e evidências](RELATORIO.md).

## Experimentar

Use a build local **PescaIdle-Tamanhos-Demo-<revisão>.exe**, em uma pasta gravável: basta dar dois cliques. É um executável separado; o EXE histórico e o piloto anterior não foram substituídos. Não há build nova publicada no Git ou em Releases nesta entrega. O relatório desta pasta identifica caminho, SHA de origem e hash do arquivo efetivamente gerado.

Pelo código, com Python/PySide6 já disponíveis, a partir da raiz:

```powershell
python -B piloto_entry.py --demo
```

O painel e a cena indicam **DEMONSTRAÇÃO / DADOS SINTÉTICOS**. O perfil fica em `perfil-demo-tamanhos/save.json`, **ao lado do EXE** ou **na raiz do checkout** ao executar pelo código. Backups e lock permanecem nessa pasta. APPDATA/LOCALAPPDATA/TEMP/TMP são desviados para subpastas dela antes de importar o jogo; um `PESCA_IDLE_SAVE_PATH` herdado é ignorado neste modo. O perfil normal `perfil-piloto` não é aberto. Fechar, autosave e reabrir usam o mesmo perfil de demonstração.

A sessão reabre de onde parou. Para repetir do zero sem apagar nada, escolha uma subpasta nova de `qa`, dentro da pasta-base do candidato:

```powershell
$env:PESCA_IDLE_DEMO_DIR = "$PWD/qa/minha-demo-01"
python -B piloto_entry.py --demo
Remove-Item Env:PESCA_IDLE_DEMO_DIR
```

O override aceita somente a pasta padrão ou subpastas de `qa`. Um arquivo preexistente sem o marcador da demonstração é recusado e preservado. Não copie o perfil de demonstração para o jogo normal. Sair do modo exige fechar a demonstração e abrir a entrada normal; facilidades sintéticas não são habilitadas em partidas comuns.

## Roteiro curto para avaliação humana

1. Abra o museu vazio e volte ao painel.
2. Clique quatro vezes em **Próxima captura**: Lambari de 9 cm (primeiro registro), 4 cm (novo menor), 18 cm (novo maior), 11 cm (sem novo recorde). Compare texto e tamanho do sprite.
3. Termine as dez capturas. Tilápia-do-nilo e Carpa-comum completarão os três espaços, com extremos pequenos/grandes próprios.
4. Abra o museu. Em cada espaço, o seletor informa **maior/menor e comprimento**. Troque o Lambari de 18 cm para 4 cm e compare o tanque. As moedas/capturas não são consumidas.
5. Confira os recordes na Enciclopédia. Feche por **Salvar e fechar** e reabra a mesma demonstração: registros, roteiro e escolhas devem permanecer, sem outra recompensa.

Perguntas para você: é fácil distinguir primeiro registro de recorde superado? Os tamanhos pequenos/grandes são reconhecíveis? O recorde é satisfatório? Fica claro qual exemplar está exposto? A escala comprimida por espécie está compreensível? São perguntas de experiência humana; os testes não comprovam diversão, retenção ou progressão prolongada.

## Como os cenários funcionam

[`tools/fixtures/demo_tamanhos.json`](../../../tools/fixtures/demo_tamanhos.json) contém dez capturas preparadas, semente `20261019` e relógio civil local fixo em **19/10/2026 12:00**. Não é o relógio normal do jogo. Em outra zona, o UTC muda para conservar o mesmo horário civil. Os comprimentos são **dados sintéticos**, dentro das regras provisórias existentes, não amostras aleatórias ou afirmações biológicas.

O controlador cria somente a fixture pendente. `FishingEngine.advance/finish_strike` reais fazem entrega, crédito, inventários, aplicação de medidas e recordes; `grant`, `change_exhibit` e SaveStore também são os reais. Há commit da fisgada antes da entrega, e o cursor do roteiro é salvo na mesma transação da recompensa. Interromper/reabrir não cria outro sorteio nem repete a captura já entregue.

O jogo fica pausado, com menu da demonstração limitado a museu, enciclopédia, roteiro e saída. Não há pesca paralela/offline na demonstração. O RNG de produção não é substituído. As regras normais online/offline são cobertas pelos testes existentes e pela regressão diferencial, separadamente dos cenários preparados.

## Mudanças de apresentação

- Captura diferencia primeiro registro, novo menor, novo maior e ausência de recorde, com comprimento em cm.
- Um contorno escuro de um pixel lógico destaca o peixe capturado contra a água, preservando arte e escala uniforme. O tanque conserva a composição e as três faixas existentes.
- Museu identifica cada espaço, explicita o exemplar ativo e inclui comprimentos nas duas opções. Vazio/legado ficam sem seleção de medidas fictícias.
- Falha ao salvar restaura a escolha anterior, explica o erro e revela a mensagem por rolagem em janelas pequenas.

## Validação focada e build

Requisitos reutilizados: Python 3.14.8, PySide6 6.11.2; Windows para build/Qt nativo; PyInstaller 6.22.3 para empacotar. Nenhuma instalação é realizada pelos comandos abaixo. Execute em saídas novas para preservar evidências.

```powershell
python -X utf8 -B -m unittest tools.verificar_tamanhos.SizeTests tools.test_save_pendente_piloto.PendingIdTests -v
python -X utf8 -B tools/test_demo_tamanhos.py --out qa/demo-validacao-nova
python -X utf8 -B tools/build_demo.py --out dist/demo-build-nova
```

A build exige código/assets commitados, usa o spec existente com entrada separada e escreve caches/logs somente em `qa/build-demo-<SHA>`. A saída nova fica em `dist`; nenhum EXE anterior é removido. O arquivo `BUILD.json` e o recurso interno `demo_build.json` registram commit, snapshot de fontes/assets, versões e hash do EXE. Uma nova tentativa de build exige outra revisão ou outro nome de área de trabalho, preservando a saída anterior.

Smoke em **dois processos**, a partir da pasta do EXE, com perfil e saída novos dentro dela:

```powershell
$env:PESCA_IDLE_DEMO_DIR = "$PWD/qa/smoke-01/perfil"
$env:PESCA_IDLE_DEMO_QA_DIR = "$PWD/qa/smoke-01/evidencias"
foreach ($fase in @('capture','reopen')) {
    $p = Start-Process -FilePath .\PescaIdle-Tamanhos-Demo-<revisão>.exe -ArgumentList @('--demo-smoke',$fase) -Wait -PassThru -WindowStyle Hidden
    if ($p.ExitCode -ne 0) { throw "Smoke falhou: $fase" }
}
Remove-Item Env:PESCA_IDLE_DEMO_DIR, Env:PESCA_IDLE_DEMO_QA_DIR
```

Substitua `<revisão>` pelo nome real. O primeiro processo exige uma demonstração vazia, entrega dez capturas e seleciona menor/maior/menor; o segundo verifica persistência e ausência de recompensa extra. São widgets Qt Windows ocultos e eventos QTest, não entrada física nem Android. JSONs/PNG completos permanecem em QA; somente evidências pequenas e sanitizadas são publicadas.

## Limites

A inspeção visual usa capturas reais de widgets Qt, além de verificação geométrica. Viewports 320×568 e 360×800 são testes desktop, não aparelhos Android. Não houve campanha nova de balanceamento/amostragem, teste de disco físico defeituoso, múltiplos jogadores ou prova de retenção. A opinião humana sobre clareza, escala e satisfação continua necessária.

Os resultados históricos do comparador em `9d57a465` permanecem preservados e separados; não substituem a execução contra o código novo. O relatório desta entrega registra somente os testes efetivamente executados agora.
