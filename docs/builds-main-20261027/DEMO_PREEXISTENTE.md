# Demo antiga: comparação reproduzida em 27/10/2026

Somente perfis sintéticos novos, com ambiente configurado antes dos imports.
Save pessoal não foi lido, copiado ou migrado. Fonte e ferramentas da demo não
foram alteradas.

| Código | Resultado |
| --- | --- |
| Main `f8190f5e6a7b2690a6d00eb8f1ef727cfe0bba34` | 10 testes, 6 falhas, 0 erros |
| Publicado `a352061bfb97692ff54934e4992406d16c9628b1` | 10 testes, as mesmas 6 falhas, 0 erros |
| Smoke normal da fonte main | pending, deliver, reopen: passaram, sem duplicação |

Os três arquivos da demo examinados são byte a byte idênticos nos dois commits:
`tools/demo_tamanhos.py`, `tools/demo_tamanhos_ui.py` e `tools/test_demo_tamanhos.py`.

## Causa e impacto

`DemoGame.next_capture` fabrica uma captura pendente com `snapshot` de horário,
mapa, vara, barco e catálogo, mas não preenche `context.clima`. O validador schema 5
recusa a gravação. O defeito já ocorre em `a352061`; não foi introduzido pelo guard
novo que recusa ausência de clima no próprio save v5.

Prioridade P2: bloqueia o modo opcional `--demo` e sua certificação. O smoke do
jogo normal passou e essa falha não o bloqueia. Se a demo for requisito da
entrega, deve ser reparada separadamente antes de considerar esse modo aprovado.

## Casos exatos

- `test_02_capture_record_flow_and_evidence`.
- `test_03_exhibit_choices_autosave_close_reopen`.
- `test_04_interrupted_pending_resumes_without_reroll`.
- `test_05_save_failure_restores_choice_and_shows_error`.
- `test_06_empty_legacy_and_supported_viewports`.
- `test_07_three_fish_bounds_separation_and_art_unchanged`.

Cinco casos terminam em `0 != 1 : Captura não salva: Contexto/ID da fisgada inválido;
save preservado. 'clima'`. O caso 04 termina em `Interrupted not raised`: sua
interrupção controlada ocorre somente depois do commit da pendência, mas esse
commit já foi recusado pela mesma ausência de clima.

## Comandos executados

```text
python -X utf8 -B tools/test_demo_tamanhos.py --out qa/distribuicao-demo-main-20261027
python -X utf8 -B tools/test_demo_tamanhos.py --out qa/distribuicao-demo-published-20261027
python -X utf8 -B tools/run_climate_smoke.py --out qa/distribuicao-smoke-main-20261027
```

O segundo comando foi executado no checkout fixo `a352061`; os outros na main
fixa `f8190f5`. Qt offscreen não é teste Windows ou Android nativo. `classification.json`
registra SHA dos logs e os snapshots identificados pelo próprio runner.

## Outros bloqueios herdados de ferramentas

- `tools/smoke_exe.py` ainda espera schema 3 e perfil TEMP fora da raiz do EXE.
- `run_climate_smoke.py --exe` força QA sob raiz da fonte, o que pode ficar fora da
  raiz congelada do EXE em dist, e força Qt offscreen. Um harness Windows adequado
  deve manter QA dentro da pasta isolada do novo EXE e usar o backend nativo.
- O teste Android anterior faz reload no mesmo processo e background/retorno,
  sem prova de force-stop/relaunch. O QA anterior troca uuid em cada launch.
  A validação Android nova deve conferir a mesma identidade/ledger em dois
  processos reais antes de aprovar persistência.

Nenhuma dessas ferramentas foi usada aqui para alegar aprovação de binário novo.
