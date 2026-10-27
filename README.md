# Pesca Idle — candidato de integração

Jogo idle offline em Python/PySide6. O candidato reúne oito mapas, 88 espécies,
sete períodos locais, museu com aquário animado, piloto de tamanhos, 21 decorações,
38 conquistas e cinco climas diários. Comprimentos e preços das decorações ainda
são parâmetros de design do piloto.

## Qual versão está em revisão

A branch de trabalho **`codex/preparar-integracao-main`** parte de
[`a352061`](https://github.com/BernardoJ/PescaIdle/commit/a352061bfb97692ff54934e4992406d16c9628b1)
(`codex/piloto-tamanhos`) e acrescenta a recusa de save schema 5 sem `clima`, testes
de regressão e esta organização documental. **O candidato atual é o código-fonte;
os binários existentes não contêm essa correção.**

A cadeia existente é `main` → expansão (PR #2) → auditoria/Android e museu
(PR #3) → piloto, aquário, conquistas e clima (PR #5). O PR #5 tem como destino
`codex/android-auditoria`; seu diff isolado não representa tudo que falta na main.
A preparação usa um PR em rascunho para `main`, com a cadeia completa, preservando
os PRs anteriores. A proposta Fluxo/Precisão do PR #4 permanece separada.

[Revisão da integração, commits, testes e riscos](docs/INTEGRACAO_MAIN.md).
O merge depende de aprovação específica. Merge não publica uma release nem
certifica os executáveis históricos.

## Plataformas e limites

| Plataforma | Situação deste candidato |
| --- | --- |
| Windows x64 | Plataforma desktop do jogo. Há EXE histórico do clima; a correção atual foi validada na fonte em Linux, sem novo build ou teste nativo Windows nesta preparação. |
| Linux x86_64 | QA com Python 3.12.14 / PySide6 6.11.2 / Qt offscreen. Testes de lógica e widgets não certificam uma sessão gráfica prolongada ou um pacote distribuível. |
| Android | Infraestrutura Qt herdada da auditoria. **Nenhum APK atualizado ou Android nativo foi gerado ou validado para este candidato.** A restrição do perfil do piloto também precisa de revisão antes de portar esta versão. |
| macOS | Não validado. |

A beta Android histórica é anterior ao museu, tamanhos, decorações, conquistas e
clima. Seu alvo era Android 9+, ARM64 e páginas de 4 KB; telefone físico ARM64,
páginas de 16 KB e Play Store continuam pendentes. [Histórico Android](ANDROID.md)
e [evidências daquela auditoria](docs/AUDITORIA_ANDROID.md) não certificam schema 5.

O replay offline usa o primeiro trecho de até quatro horas e o offset salvo;
transições históricas de horário de verão não são reconstruídas. Expedição
substitui o offline normal e só paga tempo decorrido. Prévia mobile Qt não
substitui teste em aparelho. Garantias de escrita não cobrem falha física do disco.

O roteiro antigo `piloto_entry.py --demo` tem seis falhas de teste herdadas por
criar capturas sem contexto climático; não está validado para schema 5. O jogo
normal e o smoke climático da fonte passaram. [Falhas e escopo](docs/INTEGRACAO_MAIN.md).

## Executar o candidato pelo código

Use Python 3.12 e uma pasta gravável. Na raiz do checkout, em PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -B piloto_entry.py
```

O perfil padrão é `perfil-piloto/save.json` **dentro deste checkout**. Na versão
empacotada histórica do piloto/clima, fica na mesma pasta do EXE. A versão atual
recusa caminhos fora da pasta do candidato; não importa o save pessoal de APPDATA.

Para experimentar com outro perfil sintético, estabeleça o caminho antes de abrir:

```powershell
$qa = Join-Path (Get-Location) ('qa/manual-' + [guid]::NewGuid())
$env:PESCA_IDLE_SAVE_PATH = Join-Path $qa 'save.json'
.\.venv\Scripts\python.exe -B piloto_entry.py
Remove-Item Env:PESCA_IDLE_SAVE_PATH
```

Não copie seu save pessoal para QA. A versão principal histórica usa
`%APPDATA%\PescaIdle\save.json` no Windows; o Android histórico usa o diretório
privado do aplicativo. Esses caminhos não são o perfil padrão deste piloto.

## Saves, compatibilidade e backups

- O formato atual é **schema 5**, identificado por `pilot_kind=tamanhos-v1`, com
  clima versão 1. Save v5 sem `clima`, com clima inválido ou schema futuro é recusado.
  Não se completa clima ausente com os defaults de outra inicialização.
- A migração legítima de schemas 1–4 cria clima no instante da migração e mantém
  o período anterior neutro. Progresso, RNG, resultados pendentes e extensões
  desconhecidas são preservados conforme os contratos de cada versão.
- Antes da migração, guarda os bytes originais em `save.pre-expansao-v1.json` ou
  `save.pre-schema-N.json`. Se houver backup diferente, cria outro nome exclusivo.
  Cada gravação mantém o snapshot anterior em `save.json.bak` e usa substituição
  atômica. Há um escritor por perfil.
- Um save rejeitado não é substituído automaticamente. A recuperação exige escolha
  explícita e um backup válido; conserva o rejeitado em `save.rejeitado-*.json`.
- **Downgrade não é automático:** executáveis anteriores ao schema 5 recusam esse
  formato. Para voltar, feche o jogo e restaure uma cópia do backup anterior à
  migração em um perfil separado e compatível. O backup rotativo `.bak` pode já ser
  v5; não substitui o backup anterior à migração.

[Contrato de save e migração](docs/MIGRACAO_SAVE.md) · [Clima e contexto legado](docs/CLIMA.md).
Nenhum save pessoal é fixture ou entrada dos testes.

## Verificar a fonte

Pillow é dependência de QA (`Pillow==12.3.0`); o jogo requer somente as dependências
de `requirements.txt`. Use diretórios novos em `qa/`, ignorado pelo Git:

```powershell
.\.venv\Scripts\python.exe -m pip install Pillow==12.3.0
.\.venv\Scripts\python.exe -X utf8 -B tools/validate_climate.py --out qa/clima-minha-rodada
.\.venv\Scripts\python.exe -X utf8 -B tools/validate_conquistas.py --out qa/regressao-minha-rodada
.\.venv\Scripts\python.exe -X utf8 -B tools/run_climate_smoke.py --out qa/smoke-fonte-minha-rodada
```

Os runners configuram perfis sintéticos, APPDATA e LOCALAPPDATA antes de importar
o jogo. O primeiro cobre schema 5, migrações 1–4, backups/recuperação, pendências,
clima, probabilidades e widgets. O segundo cobre conquistas, tamanhos/pendências,
auditoria, museu, expansão, cosméticos e balanceamento. O terceiro abre três
processos da fonte: pendência, entrega e reabertura sem duplicação.

Comandos e resultados **realmente executados nesta preparação**, incluindo falhas
iniciais e itens não testados: [relatório de integração](docs/INTEGRACAO_MAIN.md).
Relatórios históricos mantêm as datas e o escopo das respectivas entregas.

## Binários históricos e documentação

**Não foi gerado nem publicado EXE/APK nesta preparação.** O EXE de clima de
23/10/2026 foi compilado de `d1bcd5b` e publicado em `a352061`; antecede a correção
atual de save. Tem 50.561.165 bytes e SHA-256
`ba481e9a42d2e992406aaa6380575499274cff3e541e160efd32ea5cf352c0ee`.
[Arquivo histórico fixado no commit](https://github.com/BernardoJ/PescaIdle/raw/a352061bfb97692ff54934e4992406d16c9628b1/PescaIdle-Clima.exe).

`PescaIdle.exe`, `PescaIdle-Tamanhos-Piloto.exe` e `PescaIdle-Aquario-Demo.exe`
permanecem como artefatos históricos de escopos diferentes; não são builds da
correção atual. A demonstração do aquário é um visualizador sem progressão/save.
O spec e o workflow existentes não foram alterados ou executados nesta preparação;
novos builds e publicação são uma etapa separada.

- [Expansão de mapas/períodos](docs/EXPANSAO_MAPAS.md) · [Balanceamento](docs/BALANCEAMENTO_EXPANSAO.md).
- [Museu](docs/MUSEU_PRIMEIRA_ENTREGA.md) · [Piloto de tamanhos](docs/piloto-tamanhos/README.md) · [Demo isolada](docs/piloto-tamanhos/demo/README.md).
- [Arte do aquário](docs/aquario-especies/README.md) · [Movimento](docs/aquario-especies/movimento/README.md) · [Decorações](docs/aquario-decoracoes/README.md).
- [Conquistas](docs/conquistas-etapa1/README.md) · [Clima](docs/CLIMA.md) · [Relatório histórico do clima](docs/clima/RELATORIO.md).
- [Direção de arte](assets/ART_DIRECTION.md) · [Fontes das espécies](docs/FONTES_ESPECIES.md) · [Critérios de raridade](CRITERIOS_RARIDADE.md).
