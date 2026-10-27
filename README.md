# Pesca Idle — main e builds por plataforma

Jogo idle offline em Python/PySide6. A implementação reúne oito mapas, 88 espécies,
sete períodos locais, museu com aquário animado, piloto de tamanhos, 21 decorações,
38 conquistas e cinco climas diários. Comprimentos e preços das decorações ainda
são parâmetros de design do piloto.

## Versão oficial e rastreabilidade

A **branch `main` é a referência oficial**. O [PR #6](https://github.com/BernardoJ/PescaIdle/pull/6)
foi integrado no commit [`f8190f5`](https://github.com/BernardoJ/PescaIdle/commit/f8190f5e6a7b2690a6d00eb8f1ef727cfe0bba34),
incluindo a correção que recusa save schema 5 sem `clima`, preserva os arquivos
rejeitados e mantém as migrações legítimas de schemas 1–4 com backup.

Expansão, auditoria/museu, piloto/aquário, decorações, conquistas e clima já estão
na main. O [relatório de integração](docs/INTEGRACAO_MAIN.md) é um registro histórico
da revisão anterior ao merge; suas referências a aprovação pendente não descrevem
o estado atual. A proposta Fluxo/Precisão do PR #4 permanece separada.

A preparação de builds está em `codex/builds-main-20261027`. O Windows usa um
checkout limpo da **main fixa `f8190f5`**, com ferramentas de build/QA separadas.
O Android usa o commit derivado que acrescenta o caminho privado isolado; essa
correção ainda requer revisão e integração. Um APK dessa branch não é anunciado
como compilado exclusivamente da main.

[Builds atuais: commits, hashes, testes, downloads e pendências](docs/BUILDS_MAIN_20261027.md).
Os quatro EXEs e o APK antigo abaixo são históricos; não são a nova distribuição.

## Plataformas e limites

| Plataforma | Situação atual |
| --- | --- |
| Windows x64 | Novo EXE da main `f8190f5` gerado e validado funcionalmente em runner Windows nativo: pacote, assets, startup, save e clima. Ainda é candidato: falta incorporar e testar a guarda auxiliar de backups da branch. [Download validado](https://github.com/BernardoJ/PescaIdle/actions/runs/40563588483/artifacts/12760794913). Sem instalação Windows limpa, Authenticode ou sessão humana prolongada. |
| Linux x86_64 | QA com Python 3.12.14 / PySide6 6.11.2 / Qt offscreen. Testes de lógica e widgets não certificam uma sessão gráfica prolongada ou um pacote distribuível. |
| Android | Caminho privado corrigido nesta branch; 24 contratos e QA nativo x86_64 aprovados. APK ARM64 assinado gerado, sem execução direta; distribuição final pendente. Hashes/downloads no [relatório atual](docs/BUILDS_MAIN_20261027.md); não confundir APK da branch com a beta histórica ou main exclusiva. |
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

## Baixar o candidato Windows testado

[Baixar o pacote Windows validado da main `f8190f5`](https://github.com/BernardoJ/PescaIdle/actions/runs/40563588483/artifacts/12760794913).
Extraia o ZIP em uma pasta gravável e abra `PescaIdle-Windows-f8190f5.exe`.
Ele inclui runtime e recursos; não exige instalar Python. O pacote acompanha
BUILD/VALIDATION/ARCHIVE JSON e SHA256SUMS, sem saves ou perfis de QA.

SHA-256 do EXE: `e77e80d3da9aaf3b2cd8d8fce3c38c612cb8a8315d406fe496db608e3571feae`.
São artefatos de CI sujeitos à retenção do GitHub; a release estável histórica
não foi substituída. A assinatura Authenticode não foi aplicada. **Não é aprovação de distribuição
final:** este EXE da main ainda não inclui a proteção adicional de backups da
branch; é necessário integrar a correção e repetir build/QA Windows. Veja o
[achado e os limites](docs/BUILDS_MAIN_20261027.md#e-problemas-conhecidos-e-regressão).

## Executar pelo código

Use Python 3.12 e uma pasta gravável. Na raiz do checkout, em PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -B piloto_entry.py
```

Pelo código, o perfil padrão é `perfil-piloto/save.json` **dentro deste checkout**.
No novo EXE Windows e nos executáveis históricos do piloto/clima, fica em
`perfil-piloto/save.json` ao lado do EXE. O desktop
recusa caminhos fora da sua pasta e não importa o save pessoal de APPDATA. Na
correção Android desta branch, o perfil usa o diretório privado Qt
`AppDataLocation/pilotos/tamanhos-v1/save.json`; o pacote QA separado usa
`CacheLocation/qa-tamanhos-v1/save.json`. O save Android legado da raiz privada
não é importado nem modificado automaticamente.

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

Os runners de clima, conquistas e smoke configuram perfis sintéticos, APPDATA e
LOCALAPPDATA antes de importar o jogo. Cobrem schema 5, migrações 1–4,
backups/recuperação, pendências, clima, probabilidades, widgets, conquistas,
tamanhos, auditoria, museu, expansão, cosméticos e balanceamento. O smoke abre
três processos da fonte: pendência, entrega e reabertura sem duplicação.

Para os contratos novos de Android e do verificador de reabertura:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B tools/test_android_profiles.py --out qa/android-minha-rodada
.\.venv\Scripts\python.exe -X utf8 -B -m unittest -v tools.test_android_emulator_harness
```

Esses contratos simulam os diretórios Qt; o APK precisa passar também pelo
emulador nativo.

Comandos e resultados **realmente executados na preparação atual**:
[relatório de builds](docs/BUILDS_MAIN_20261027.md). A
[integração anterior](docs/INTEGRACAO_MAIN.md) e os demais relatórios históricos
mantêm suas datas, falhas e escopos.

## Compilar e validar a versão Windows

Em Windows x64, use o Python 3.12 e as dependências fixadas. As ferramentas desta
revisão mantêm o código oficial num checkout separado e verificam módulos/assets
empacotados contra o commit antes do smoke nativo:

```powershell
git worktree add --detach ../PescaIdle-main-build f8190f5e6a7b2690a6d00eb8f1ef727cfe0bba34
.\.venv\Scripts\python.exe -m pip install -r ../PescaIdle-main-build/requirements-build.txt
$buildOut = Join-Path $env:TEMP ('pesca-main-build-' + [guid]::NewGuid())
.\.venv\Scripts\python.exe -X utf8 -B tools/build_windows_main.py --source ../PescaIdle-main-build --expected-commit f8190f5e6a7b2690a6d00eb8f1ef727cfe0bba34 --out $buildOut
```

A saída `deliverables/` só é criada após build limpo, conferência do pacote e
smoke Windows nativo. Contém EXE, BUILD/VALIDATION/ARCHIVE JSON e SHA256SUMS;
perfis e imagens sintéticos ficam separados em QA. Não é cross-build Linux.
O procedimento Android e os limites de assinatura estão em [ANDROID.md](ANDROID.md).

## Binários históricos e documentação

O estado dos novos EXE/APK está no [relatório atual](docs/BUILDS_MAIN_20261027.md).
Os arquivos desta seção são **históricos**. O EXE de clima de
23/10/2026 foi compilado de `d1bcd5b` e publicado em `a352061`; antecede a correção
atual de save. Tem 50.561.165 bytes e SHA-256
`ba481e9a42d2e992406aaa6380575499274cff3e541e160efd32ea5cf352c0ee`.
[Arquivo histórico fixado no commit](https://github.com/BernardoJ/PescaIdle/raw/a352061bfb97692ff54934e4992406d16c9628b1/PescaIdle-Clima.exe).

`PescaIdle.exe`, `PescaIdle-Tamanhos-Piloto.exe` e `PescaIdle-Aquario-Demo.exe`
permanecem como artefatos históricos de escopos diferentes; não são builds da
correção atual. A demonstração do aquário é um visualizador sem progressão/save.
O spec original continua sendo usado para empacotar o Windows. O workflow
`builds-main.yml` gera artefatos de CI com metadados; um build só recebe o rótulo
validado após os testes correspondentes. Artefatos de CI não substituem a release
estável nem equivalem a validação em toda plataforma física.

- [Expansão de mapas/períodos](docs/EXPANSAO_MAPAS.md) · [Balanceamento](docs/BALANCEAMENTO_EXPANSAO.md).
- [Museu](docs/MUSEU_PRIMEIRA_ENTREGA.md) · [Piloto de tamanhos](docs/piloto-tamanhos/README.md) · [Demo isolada](docs/piloto-tamanhos/demo/README.md).
- [Arte do aquário](docs/aquario-especies/README.md) · [Movimento](docs/aquario-especies/movimento/README.md) · [Decorações](docs/aquario-decoracoes/README.md).
- [Conquistas](docs/conquistas-etapa1/README.md) · [Clima](docs/CLIMA.md) · [Relatório histórico do clima](docs/clima/RELATORIO.md).
- [Direção de arte](assets/ART_DIRECTION.md) · [Fontes das espécies](docs/FONTES_ESPECIES.md) · [Critérios de raridade](CRITERIOS_RARIDADE.md).
