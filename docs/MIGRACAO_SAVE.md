# Save v2 e ausência

O caminho normal permanece `%APPDATA%\PescaIdle\save.json`. Nenhum conteúdo do
perfil pessoal foi lido ou usado nesta tarefa. Todos os testes utilizaram dados
sintéticos e `PESCA_IDLE_SAVE_PATH` explícito, com APPDATA/LOCALAPPDATA isolados.

## Migração

Antes da primeira migração de um JSON válido v1, uma cópia byte a byte é gravada
em `save.pre-expansao-v1.json`. Se já existir uma cópia diferente, usa outro nome
exclusivo, sem sobrescrever a anterior. O save v2 é gravado em temporário no mesmo
diretório, seguido de flush/fsync e substituição atômica por `os.replace`.

Saldo, níveis, peças, equipamentos, compras, conquistas, total histórico e campos
desconhecidos são preservados. Os nomes antigos são mapeados explicitamente para
IDs duráveis. Nomes não reconhecidos permanecem recuperáveis em
`inventario_legado_desconhecido`, inclusive na tela de status. Inventário por ID
é canônico; `inventario` é apenas uma projeção em memória, excluída do JSON v2.

Capturas antigas ficam em `legado_sem_contexto` e contam globalmente nos marcos
1/5/10. Não se atribuem mapa ou período retroativamente. Mapas já elegíveis pelo
barco são liberados; desbloqueios anteriores válidos permanecem mesmo se um nível
for reduzido. Mapa inválido volta à Enseada, mantendo diagnóstico do ID anterior.

JSON corrompido, schema futuro, RNG inválido, contagens inválidas ou uma fisgada
inconsistente impedem a abertura sem substituir o arquivo. A mensagem informa o
erro. Um lock exclusivo por caminho evita dois escritores. O lock é liberado ao
fechar; sua presença no disco não significa que ainda existe outro processo.

Uma falha de escrita preserva o estado durável anterior, informa o jogador e
pausa a pesca. Recompensa, resultado, inventário, conquistas e watermark são
confirmados juntos. Não se usa pickle. O saldo legado continua numérico compatível;
somas de recompensas utilizam Decimal sobre o valor textual, sem quantizar ou
arredondar o saldo antigo na migração. Recompensas novas conservam duas casas.

## Offline e suspensão

`ultimo_salvo` é metadado de gravação, separado de `ultimo_processado_utc`.
Na ausência normal conta-se **o primeiro trecho** de até quatro horas:
`[saída, min(retorno, saída+14400))`. Cada fisgada usa seu horário histórico,
mapa e equipamento. O excesso é descartado e o marcador avança até o retorno;
reabrir não paga novamente. Resíduos e fisgadas incompletas são preservados,
sem usar a cauda descartada para terminá-los.

Tempo ativo usa relógio monotônico; disponibilidade usa relógio civil. Suspensão
com intervalo monotônico e civil de pelo menos 30 s é reconciliada pelo mesmo
offline. Retrocesso civil não diminui watermark nem gera dívida. Pausa intencional
persiste e não rende pesca offline até retomar; ambiente e iluminação continuam.

UTC e offset do dispositivo são salvos. O replay usa esse offset fixo para a
ausência, sem inventar localização. **Limite conhecido:** uma mudança de horário
de verão durante a ausência não é reconstruída por uma base histórica de zonas.
A sessão ativa retorna ao fuso atual. Sem servidor, não há proteção absoluta
contra edição deliberada do relógio ou do próprio JSON.

## Expedição

Um único agendamento futuro, nas próximas 24 h, em mapa desbloqueado e por até
quatro horas. Substitui a janela offline daquela ausência; não gera renda em
paralelo. O equipamento é o snapshot real salvo ao sair.

- Retorno antes do início: zero; mantém o plano futuro ou permite cancelar.
- Durante: paga só a interseção decorrida, consome o plano e descarta o futuro.
- Depois: paga a janela completa uma vez, sem parcela normal adicional.
- Jogo aberto no início: expira e grava esse status imediatamente.
- Cancelamento após retorno não torna aquela ausência novamente elegível.

Nenhum serviço, wakeup, job externo ou acesso à rede é necessário. O cálculo
ocorre na retomada. Agendamento, consumo e recompensas entram na mesma transação.

## Verificações

SAV-01–05, EVT-01–05, OFF-01–06 e EXP-01–03 estão na suíte determinística:
migração idempotente, backup exato, round-trip, contexto histórico, resultado
pendente sem rerrolagem, falha de fsync/replace, commit/reload sem dupla renda,
erro visível e lock exclusivo. O smoke Windows também migra fixture v1.
