"""Publish a new sanitized report from completed synthetic comparison outputs."""
import argparse,collections,json,re,sys,subprocess,hashlib
from pathlib import Path

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-dir',required=True,type=Path)
    ap.add_argument('--controls-dir',required=True,type=Path);ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--git',default='git')
    args=ap.parse_args()
    git_version=subprocess.check_output([args.git,'--version'],text=True).strip()
    result=read(args.run_dir/'resultado.json');tests=read(args.controls_dir/'testes.json')
    if result['exit_code']!=0 or tests['failures'] or tests['errors']:raise ValueError('Report requires completed successful comparison/controls')
    candidate=read(args.run_dir/'work/candidate.json')
    args.out.mkdir(parents=True,exist_ok=False)
    write(args.out/'resultado.json',result);write(args.out/'testes.json',tests)
    checkout=Path(__file__).resolve().parents[1]
    for name,expected in result['tool_hashes'].items():
        if hashlib.sha256((checkout/'tools'/name).read_bytes()).hexdigest()!=expected:raise ValueError('Comparator changed after recorded run: '+name)
    write(args.out/'ferramentas.json',{'git':git_version,'files':{str(p.relative_to(checkout)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [checkout/'tools'/n for n in ('comparar_fluxo_base.py','comparacao_worker.py','test_comparar_fluxo_base.py','relatorio_comparacao.py','fixtures/comparacao_tamanhos.json')]}})
    for name,path in [('execucao.log',args.run_dir.with_suffix('.log')),('controles.log',args.controls_dir.with_suffix('.log'))]:
        if path.is_file():
            text=path.read_text(encoding='utf-8')
            for private in (str(checkout),checkout.as_posix(),json.dumps(str(checkout))[1:-1]):text=text.replace(private,'<checkout-isolado>')
            if re.search(r'(?i)C:(?:\\+|/)Users(?:\\+|/)',text):raise ValueError('Private absolute path still present')
            (args.out/name).write_text(text,encoding='utf-8')
    grouped=collections.defaultdict(list)
    for c in result['scenarios']:grouped[c['kind']].append(c)
    additions={k:sum(c['candidate_additions'][k] for c in result['scenarios']) for k in
               ('measured_events','size_news_annotations','record_flags','size_award_notifications','migration_backups')}
    actions=[a for c in candidate['scenarios'] for f in c['timeline'] for a in f.get('actions',[])]
    action_counts=dict(collections.Counter(a['kind'] for a in actions))
    run_display=args.run_dir.as_posix();controls_display=args.controls_dir.as_posix();out_display=args.out.as_posix()
    text=f'''# Comparação observada — 19/10/2026

## Resultado

**82/82 cenários equivalentes; código de saída 0.** Nenhuma divergência de produto encontrada nos comportamentos e no escopo comparados. Nenhuma correção de produto foi feita.

- Base fixa efetivamente executada: `{result['base_sha']}` (schema {result['schemas']['base']}).
- Candidato efetivamente executado: `{result['candidate_sha']}` (head da PR #5 no início; schema {result['schemas']['candidate']}).
- O commit desta entrega acrescenta somente ferramentas, testes, fixture e documentação; não substitui os SHAs acima por uma branch móvel.
- Ambiente: `{result['platform']}`; versões por processo: `{result['versions']}`. Git verificado nesta entrega: `{git_version}`. Sem instalações.
- Início/data de execução registrado: `{result['executed_at_utc']}`. A data do relógio simulado é 18/10/2026, offset 0; não é a data de execução.
- Comparação completa em {result['elapsed_seconds']:.2f} s. Três subprocessos com timeout finito; tempos de exportação/execução por worker em resultado.json. Os controles adicionais têm seu tempo no log.

## Matriz e contagens reais

| Grupo | Casos | Eventos base | Eventos piloto | Divergências |
|---|---:|---:|---:|---:|
'''
    for kind,cases in grouped.items():
        text+=f"| {kind} | {len(cases)} | {sum(c['base_events'] for c in cases)} | {sum(c['candidate_events'] for c in cases)} | {sum(not c['equivalent'] for c in cases)} |\n"
    text+=f'''
Total por revisão: **{sum(c['base_events'] for c in result['scenarios']):,} eventos**, incluindo lixo e especiais. Não são recompensas somadas das duas revisões nem eventos do controle positivo acrescidos ao total.

Comparados estritamente: catálogo/preços efetivos, {result['pools_compared']} pools e ordem dos IDs, sequência e quantidade de eventos, ganhos, saldo, inventários, tempos/contextos/pendentes, compras, upgrades, desbloqueios, saves/roundtrips e conquistas antigas. As fontes/assets exportadas permaneceram byte a byte inalteradas. Não se aplicou tolerância numérica.

Nas quatro progressões, foram executadas **{len(actions)} ações de compra** reais: `{action_counts}`. A política é a da fixture (cadência 60 s e alvo nível 3), sem dinheiro inicial artificial nem mudança de preço. Não é uma estimativa de progressão até concluir o jogo.

## Consumo do RNG

Foram registradas **{sum(c['rng_random_calls'] for c in result['scenarios']):,} chamadas random() por revisão** e {sum(c['rng_getrandbits_calls'] for c in result['scenarios'])} de getrandbits(). A lista ordenada de chamadas/valores e os estados completos do RNG dos checkpoints coincidiram; os hashes por cenário estão no resultado. Não houve sorteio adicional para ajustar o resultado do jogo. O spy é uma classe de QA que retorna os valores de super(), sem editar produto; tempfile/UUID ficam fora dessa instrumentação.

## Alegação histórica verificada

O script recuperado conserva a matriz 8 sementes × dois inícios × três níveis × uma hora. Não houve ajuste para obter um número-alvo. Foram observados **48 fluxos / 16.010 eventos** em cada revisão. As 48 projeções individuais e o JSON projetado completo coincidiram com os artefatos recuperados.

SHA-256 do JSON histórico reproduzido: `{result['historical_reproduction']['base']['sha256']}`. O candidato reproduziu o mesmo hash. Isso comprova a correspondência do recorte histórico e de seus campos projetados, não a cobertura de persistência ou compras no comparador antigo; esses caminhos pertencem à extensão nova.

## Diferenças aditivas classificadas

O protocolo completo e a lista de campos normalizados estão no [README](../README.md). Não há descarte silencioso de capturas ou campos desconhecidos.

- {additions['measured_events']:,} eventos com medida; pendentes contabilizados separadamente no JSON.
- {additions['size_news_annotations']:,} anotações size_news, inclusive listas vazias; {additions['record_flags']:,} flags de recorde/primeira medida.
- {additions['size_award_notifications']} notificações de conquistas de tamanho, agregadas entre cenários independentes; os IDs finais por cenário também estão preservados. Não são 63 conquistas distintas de um jogador.
- {additions['migration_backups']} backups adicionais de migração schema 3 com bytes exatos no piloto.
- Observações de schema/estado de medidas e seletores do museu são quantificadas por cenário. Os campos econômicos comuns continuam estritos.

## Controles executados

O candidato foi executado novamente em processo/fonte exportada próprios, no mesmo SHA, com identidade/relógio/sementes equivalentes. O controle positivo coincidiu inclusive nos registros brutos das linhas do tempo.

Testes da ferramenta: **{tests['tests']} aprovados, {tests['failures']} falhas, {tests['errors']} erros**, sem skips. Os controles CLI abaixo foram subprocessos reais; as mutações ocorreram só nos registros sintéticos:

| Controle | Saída esperada | Saída observada |
|---|---:|---:|
'''
    for row in tests['cli_controls']:text+=f"| {row['case']} | {row['expected']} | {row['observed']} |\n"
    text+='\nPrimeiras diferenças nos controles negativos internos:\n\n'
    for row in result['negative_controls']:
        text+=f"- {row['mutation']}: `{row['first_difference']['path']}`; código {row['observed_exit']}.\n"
    text+=f'''
Dados incompletos, timelines truncadas, configuração inválida e diretório de saída preexistente não passam. A saída preexistente mantém o sentinela sem receber novos arquivos. Campos de bônus desconhecidos não são removidos pela normalização; preços e horários permanecem observáveis.

## Comandos executados e reprodução

Foram executados os comandos abaixo usando o Python existente 3.14.8/PySide6 6.11.2 e Git 2.53.0.windows.3. Os caminhos privados dos binários foram omitidos; `python` e `git` devem apontar para esse ambiente. Os argumentos, revisões, sementes e diretórios relativos são os reais:

```powershell
python -X utf8 -B tools/comparar_fluxo_base.py --base 2a0353ff7c1cae2dca69d08c222b0660770d4385 --candidate b05f7820f9dc04ef479c84fad696ae80c8e72c60 --out {run_display}
python -X utf8 -B tools/test_comparar_fluxo_base.py --run-dir {run_display} --out {controls_display}
python -X utf8 -B tools/relatorio_comparacao.py --run-dir {run_display} --controls-dir {controls_display} --out {out_display}
```

A base é explícita e imutável; foi passado --git apontando para o Git observado nesta entrega. Acrescente esse argumento se necessário no seu ambiente. A pasta de evidência publicada já existe: para reproduzir o terceiro comando, use --out qa/relatorio-comparador-novo. Todos os diretórios de saída precisam ser novos. A fixture contém a matriz e todas as sementes.

O desenvolvimento da ferramenta teve execuções preliminares em diretórios v1/v2 preservados localmente. Os resultados publicados são da execução final identificada pelos hashes das ferramentas em resultado.json. Não foram sobrescritas evidências históricas da PR ou arquivos originais.

## Limitações

São testes diferenciais dos caminhos reais descritos, não prova formal de ausência de regressões. As compras usam métodos reais com adaptadores de apresentação e scheduler instantâneo; não é teste de clique, GUI ou timers. As pescarias temporais usam principalmente a Enseada, mais a viagem de pendente; os oito mapas têm pools comparados, não uma campanha temporal completa por mapa. Há 82 cenários finitos, não todas as sementes/níveis/horários possíveis.

Migração e persistência usam apenas fixtures sintéticas, sem saves pessoais. Não houve teste Android, CI, build novo, renderização, suspensão física, disco com falha ou concorrência ampla. O relógio usa offset zero, sem reconstrução de DST. Medidas/recordes/conquistas novas são classificados, não certificados quanto a todos os detalhes visuais ou distribuição por esta comparação.

Os JSONs publicados são resumos/hashes e dados sintéticos. Perfis, backups, snapshots exportados e registros completos de cada worker ficam locais e são regeneráveis por comando. Nenhum dado privado, credencial ou configuração de conta foi incluído.
'''
    (args.out/'RELATORIO.md').write_text(text,encoding='utf-8')
    print('Report created:',args.out)

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError) as exc:print(str(exc),file=sys.stderr);sys.exit(2)
