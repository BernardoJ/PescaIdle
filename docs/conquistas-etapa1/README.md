# Conquistas - primeira etapa

Implementação das 24 sugestões aprovadas por Bernardo em 23/10/2026. Fonte: PR #5 em d8032d67142bd2e13e36933bcc2238a190aefada, branch remota codex/piloto-tamanhos. Área local isolada: codex/conquistas-etapa1-20261023. A base da PR continua codex/android-auditoria em 2a0353ff7c1cae2dca69d08c222b0660770d4385.

## Entrega

- 24 novas conquistas: oito fáceis, dez moderadas e seis difíceis. Total do candidato: 38, preservando as 14 anteriores.
- Tela Conquistas existente mostra descrição, dificuldade, grupo e progresso das novas metas.
- Coleção, exploração, museu, decoração, estilo e melhorias; IDs estáveis etapa1_cXX.
- Sem recompensa monetária, desconto, modificador de pesca ou exigência nova para viajar/progredir.
- Conjuntos de espécies, locais, períodos, cosméticos e decorações fixados pela versão 1 do catálogo de conquistas. IDs futuros desconhecidos não contam como itens atuais.
- As oito sugestões opcionais C06, C08, C14, C26 e C29-C32 não foram implementadas.

## Critérios implementados

| Código | Nome | Dificuldade | Condição |
|---|---|---|---|
| C01 | Primeiro cardume | Fácil | Somar 25 capturas das 68 espécies da categoria peixe. |
| C02 | Primeiras páginas | Fácil | Registrar pelo menos uma vez 10 espécies distintas das 88 atuais. |
| C03 | Álbum de muitas águas | Moderado | Registrar pelo menos uma vez 25 espécies distintas das 88 atuais. |
| C04 | Curioso de carteirinha | Moderado | Ter 20 espécies com pelo menos 5 registros cada, revelando suas raridades. |
| C05 | Conheço esses rostos | Difícil | Ter 20 espécies com pelo menos 10 registros cada, revelando suas curiosidades. |
| C07 | Um encontro fora da curva | Difícil | Registrar uma espécie classificada como Épico no catálogo atual. |
| C09 | Olhar de observador | Moderado | Registrar cinco espécies distintas da categoria especial. |
| C10 | Cartão-postal | Fácil | Registrar ao menos uma espécie em cada um de dois mapas diferentes. |
| C11 | Passaporte carimbado | Difícil | Ter ao menos um registro de espécie em cada um dos oito mapas. |
| C12 | Três tons de água | Fácil | Ter registros em três períodos diferentes do dia, em quaisquer mapas. |
| C13 | Sete luzes de uma jornada | Difícil | Ter registros nos sete períodos do dia, acumulados entre sessões e dias. |
| C15 | Três margens, muitas histórias | Moderado | Registrar três peixes distintos em cada um de três mapas diferentes. |
| C16 | Primeiro morador | Fácil | Exibir um peixe descoberto em um espaço válido do aquário. |
| C17 | Três é um cardume | Moderado | Manter os três espaços ocupados simultaneamente por espécies distintas e elegíveis. |
| C18 | Curadoria de contrastes | Difícil | Com três espécies expostas, exibir um registro diminuto e um excepcional, de espécies diferentes do piloto. |
| C19 | Lar, doce aquário | Fácil | Comprar a primeira decoração do aquário. |
| C20 | Por dentro e por fora | Moderado | Possuir ao menos uma decoração interna e uma externa. |
| C21 | Arquiteto das águas | Moderado | Equipar simultaneamente uma decoração adquirida em cada um dos sete tipos. |
| C22 | Acervo de cenários | Difícil | Comprar as 21 decorações do catálogo atual. |
| C23 | Primeiro estilo | Fácil | Possuir três cosméticos vendidos, de pelo menos três categorias diferentes. |
| C24 | Armário versátil | Moderado | Possuir dez cosméticos vendidos, distribuídos por pelo menos quatro categorias. |
| C25 | Dojo flutuante | Moderado | Equipar simultaneamente Touca ninja e Traje de ninja. |
| C27 | Primeiro investimento | Fácil | Chegar ao nível 1 da vara ou do barco. |
| C28 | Ritmo de cruzeiro | Moderado | Ter vara e barco no nível 3 ou superior. |

## Integração e persistência

O avaliador novo é somente de leitura. O progresso é derivado dos registros existentes, sem novos contadores, migração ou mudança do schema 4/tamanhos-v1. A lista de conquistas usa a validação e a escrita atômica já existentes. IDs conquistados nunca são retirados quando o jogador muda uma seleção.

Os pontos de pesca online, replay offline, melhorias, abertura e tela de conquistas continuam usando grant. A loja agora avalia depois de equipar o item, permitindo reconhecer Dojo flutuante na mesma compra/equipagem. As seleções de peixe/exemplar e as transações de decoração usam commit_with_achievements: avaliam no snapshot candidato, gravam junto com a ação e só notificam depois da confirmação. A rota de compatibilidade sortear também passa a anunciar as concessões confirmadas.

Para C16/C17/C18, validar a espécie e o exemplar efetivamente selecionado. C18 usa somente as quatro espécies medidas do piloto, com comprimentos provisórios de design. Para C21, o item precisa ser adquirido e corresponder ao tipo equipado. Uma prévia não concede conquistas.

Capturas globais antigas continuam válidas nas metas globais. Sem origem/período conhecidos não se reconhecem metas regionais ou temporais. Desbloquear mapa não prova registro nele. O avaliador não faz sorteios, não altera pendentes e não cria capturas; usa somente entregas presentes no inventário/contexto.

O limite offline continua quatro horas e as expedições substituem a janela da ausência. Não foram adicionados contadores de renda histórica, lixo ou registros offline. Fashionista continua exigindo os 84 cosméticos vendidos, excluindo Enciclopédia Viva, decorações, itens grátis e peças. O livro gratuito e as outras 13 conquistas existentes mantêm seus critérios/recompensas.

## Testes executados nesta entrega

Windows, Python 3.14.8, PySide6 6.11.2, backend Qt offscreen e dependências já disponíveis. Dados e perfis exclusivamente sintéticos. O ambiente é definido antes das importações; o save pessoal não foi lido, migrado ou escrito. Nenhuma instalação foi necessária.

| Verificação | Resultado observado |
|---|---|
| Suíte nova | 44 testes, zero falhas/erros |
| Cada uma das 24 conquistas | Condição negativa, positiva, concessão única, não revogação, save/load e invariância econômica/RNG |
| Núcleo de tamanhos e IDs pendentes | 17 testes aprovados |
| Auditoria | 11 testes aprovados |
| Museu | 11 testes aprovados |
| Expansão | 5.920 verificações aprovadas |
| Cosméticos | 1.359 verificações aprovadas |
| Balanceamento existente | 168 pools exatos e sete inícios com 30 sementes cada, aprovados |

São 83 testes unittest, além das verificações e medições citadas em suas unidades próprias. Não confundir 24 métodos individuais com 24 suítes completas ou somar pools e cenários como se fossem testes iguais.

A suíte nova também exerce compra de todas as decorações pelos widgets reais, prévia sem alteração, par ninja, upgrades, seleção de menores/maiores, reconhecimento retroativo com dados válidos, erro de save sem anúncio indevido, reabertura, 38 anúncios reais simultâneos e navegação/rolagem. Usa o motor real para verificar sequência de eventos/RNG/economia com e sem concessão (semente 104729, 20 passos de 120 segundos) e equivalência online/offline em quatro horas na Enseada. Não é uma simulação de longevidade global.

### Ajustes de testes e ocorrências iniciais

A primeira execução da suíte nova revelou uma fixture de compatibilidade que reduzia três contagens ao criar medidas; a fixture foi corrigida para manter as dez capturas exigidas por Enciclopédia Viva. Não houve mudança de regra de produto para satisfazer esse teste.

Foram reproduzidas três expectativas históricas desatualizadas na fonte d8032d6, exportada por Git para uma área de QA isolada: auditoria esperava schema 3 (uma falha em 11); museu esperava que v3 não fosse migrado (uma falha em 11); expansão comparava a entrega sem a anotação size_news introduzida pelo piloto (falha EVT-02). Os testes agora exigem explicitamente v4, conferem bytes dos backups e comparam o evento completo com a anotação exata esperada. As outras verificações de integridade não foram removidas.

Dois testes do museu foram atualizados para o novo comportamento aprovado: C16/C17 podem ser concedidas ao expor espécies. A exceção é nominal e exata; os demais campos, outras conquistas, ordem, moeda e RNG continuam comparados. Todas as rodadas finais passaram após esses ajustes.

## Reprodução

Use um checkout isolado e o Python do ambiente existente com PySide6. Não aponte para seu perfil de jogo. O comando abaixo recusa saída existente e saída fora de qa do próprio candidato.

```powershell
python -X utf8 -B tools/validate_conquistas.py --out qa/conquistas-minha-rodada
```

O comando executa, nesta ordem:

1. python -X utf8 -B tools/test_conquistas_etapa1.py --out qa/conquistas-minha-rodada/individual
2. python -X utf8 -B -m unittest -v tools.verificar_tamanhos tools.test_save_pendente_piloto
3. python -X utf8 -B tools/validate_game.py

Cada etapa tem limite de 300 segundos e erro/execução incompleta retorna código diferente de zero. O agregador registra os comandos, saídas e hashes de módulos/JSON do snapshot. O teste individual também pode ser executado separadamente com uma saída inédita dentro de qa. Os testes históricos usam subpastas sintéticas dentro deste checkout; não os execute no diretório de um perfil pessoal.

## Evidências sanitizadas

- [Resumo, comandos e hashes do snapshot](resumo.json).
- [Resultados por conquista e por teste da suíte nova](individual.json).
- [Desktop: início](imagens/conquistas-640-topo.png) e [fim da lista](imagens/conquistas-640-rodape.png).
- [Prévia compacta: início](imagens/conquistas-320-topo.png) e [fim da lista](imagens/conquistas-320-rodape.png).

As quatro imagens são widgets Qt reais com fixtures sintéticas, conferidos visualmente. Logs brutos, saves/locks/backups de teste, arquivos ZIP da base e diretórios de execução ficam em qa, fora da publicação. O resumo corresponde ao diff local testado, identificável pelos hashes de produto; o SHA de publicação aparece no histórico da PR.

## Arquivos e finalidade

| Grupo | Arquivos |
|---|---|
| Catálogo fechado | assets/conquistas_etapa1.json |
| Predicados e progresso | pesca_conquistas_etapa1.py |
| Concessão e transação | pesca_conquistas.py |
| Pontos de ação | pesca_idle.py, pesca_museu_ui.py, pesca_aquario_decor_ui.py |
| Testes e execução isolada | tools/test_conquistas_etapa1.py, tools/validate_conquistas.py |
| Compatibilidade dos testes existentes | tools/validate_audit.py, tools/validate_museum.py, tools/validate_expansion.py |
| Documentação/evidências | README da raiz e esta pasta |

## Limitações

Esta entrega é de código-fonte e testes locais. Não houve novo build ou smoke de EXE/APK, teste Android nativo, toque físico ou sessão humana prolongada. As prévias compactas são Qt desktop; não certificam Android. Os executáveis históricos não contêm estas 24 conquistas. Não se afirma perfeição universal a partir das verificações cobertas. A PR permanece em rascunho, sem merge ou release.

### Finais de linha e hashes

source_sha256 identifica os bytes usados na execução local. canonical_source_sha256 normaliza apenas CRLF para LF, e git_product_blob_shas identifica os blobs Git correspondentes. A revisão conferiu igualdade integral entre o produto testado e o índice após essa única normalização; o checkout Windows pode converter finais de linha. Nenhuma diferença de código foi normalizada ou omitida.
