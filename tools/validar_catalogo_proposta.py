#!/usr/bin/env python3
"""Valida somente o documento de conteúdo da expansão Pesca Idle.

Não importa nem executa o jogo, não lê APPDATA e não usa rede.
Opcionalmente compara os nomes legados com uma cópia local de pesca_idle.py,
extraindo a atribuição literal LOOT via AST, sem executar o arquivo.
Python 3.10+; apenas biblioteca padrão.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_MAPS = {
    "Enseada do Poente": 0,
    "Rio das Vitórias": 1,
    "Mangue das Raízes": 2,
    "Píer da Brisa": 3,
    "Recife das Cores": 4,
    "Mar dos Ventos": 6,
    "Mar das Auroras": 8,
    "Fossa das Lanternas": 10,
}
EXPECTED_PERIODS = [
    ("amanhecer", "05:00", "07:00", False),
    ("manhã", "07:00", "09:00", False),
    ("dia", "09:00", "11:00", False),
    ("meio-dia", "11:00", "14:00", False),
    ("tarde", "14:00", "17:00", False),
    ("anoitecer", "17:00", "20:00", False),
    ("noite", "20:00", "05:00", True),
]
EXPECTED_SUMMARY = {
    "mapas_totais": 8,
    "mapas_novos": 7,
    "entradas_unicas_catalogos_peixes": 68,
    "entradas_unicas_encontros_especiais": 20,
    "entradas_aquaticas_unicas_totais": 88,
    "entradas_originais_preservadas": 49,
    "entradas_novas": 39,
    "combinacoes_mapa_periodo_validadas": 56,
    "menor_numero_de_peixes_disponiveis_por_combinacao": 3,
    "lixo_existente_separado": "Bota velha",
}


class ValidationError(ValueError):
    """Conteúdo inválido para esta versão da proposta."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"Chave JSON repetida: {key!r}")
        result[key] = value
    return result


def minute(value: str) -> int:
    hour, minute_value = map(int, value.split(":"))
    require(0 <= hour < 24 and 0 <= minute_value < 60, f"Hora inválida: {value}")
    return hour * 60 + minute_value


def legacy_names_from_source(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        else:
            continue
        if any(isinstance(target, ast.Name) and target.id == "LOOT" for target in targets):
            require(value is not None, "LOOT não possui valor literal.")
            try:
                loot = ast.literal_eval(value)
            except (ValueError, TypeError) as exc:
                raise ValidationError("LOOT não é literal; forneça a fonte histórica adequada.") from exc
            require(isinstance(loot, list), "LOOT não é uma lista literal.")
            require(all(isinstance(item, dict) for item in loot), "Itens de LOOT inválidos.")
            return {item["nome"] for item in loot if item.get("tipo") == "peixe"}
    raise ValidationError("Atribuição literal LOOT não encontrada na fonte fornecida.")


def validate(data: dict[str, Any], legacy_source: Path | None = None) -> dict[str, Any]:
    require(isinstance(data, dict), "Raiz deve ser objeto JSON.")
    periods = data.get("periodos", [])
    require(isinstance(periods, list) and len(periods) == 7, "São necessários sete períodos.")
    actual_periods = [
        (p["nome"], p["inicio"], p["fim"], p["atravessa_meia_noite"]) for p in periods
    ]
    require(actual_periods == EXPECTED_PERIODS, "Períodos diferem da proposta.")
    require(all(type(p["atravessa_meia_noite"]) is bool for p in periods), "Flag horária não booleana.")
    coverage_clock = Counter()
    for period in periods:
        start, end = minute(period["inicio"]), minute(period["fim"])
        for current in range(1440):
            inside = (current >= start or current < end) if end < start else start <= current < end
            if inside:
                coverage_clock[current] += 1
    require(all(coverage_clock[t] == 1 for t in range(1440)), "Há lacuna ou sobreposição no relógio.")

    maps = data.get("locais", {})
    require(set(maps) == set(EXPECTED_MAPS), "Conjunto de locais divergente.")
    for name, level in EXPECTED_MAPS.items():
        require(type(maps[name]["nivel_barco_desbloqueio"]) is int, f"Nível inválido: {name}")
        require(maps[name]["nivel_barco_desbloqueio"] == level, f"Desbloqueio divergente: {name}")
        require(maps[name]["desbloqueio_permanente"] is True, f"Desbloqueio não permanente: {name}")
        require(maps[name]["viagem_gratuita_apos_desbloqueio"] is True, f"Viagem não gratuita: {name}")
        require(bool(maps[name]["direcao_visual"].strip()), f"Direção visual ausente: {name}")

    fish = data.get("catalogos_peixes", {})
    special = data.get("encontros_especiais", {})
    require(set(fish) == set(maps), "Mapas e catálogos de peixes não coincidem.")
    require(set(special) <= set(maps), "Encontro especial em mapa inexistente.")
    valid_periods = {p[0] for p in EXPECTED_PERIODS}
    names_by_category: dict[str, set[str]] = {}
    new_flags: dict[str, bool] = {}
    fish_frequency: Counter[str] = Counter()
    occurrence_count = 0
    coverage: dict[str, dict[str, int]] = {}
    for category, catalogs in (("peixe", fish), ("especial", special)):
        category_names: set[str] = set()
        for location, rows in catalogs.items():
            require(isinstance(rows, list) and bool(rows), f"Catálogo vazio/inválido: {location}")
            local_names: set[str] = set()
            for entry in rows:
                name = entry["nome"]
                require(isinstance(name, str) and bool(name.strip()), "Nome inválido.")
                require(name not in local_names, f"Ocorrência repetida: {location}/{name}")
                local_names.add(name)
                require(type(entry["novo"]) is bool, f"Flag novo inválida: {name}")
                allowed = entry["periodos"]
                require(isinstance(allowed, list) and bool(allowed), f"Sem períodos: {name}")
                require(set(allowed) <= valid_periods, f"Período desconhecido: {name}")
                require(len(allowed) == len(set(allowed)), f"Período repetido: {name}")
                if name in new_flags:
                    require(new_flags[name] == entry["novo"], f"Flag novo contraditória: {name}")
                new_flags[name] = entry["novo"]
                category_names.add(name)
                occurrence_count += 1
                if category == "peixe":
                    fish_frequency[name] += 1
            if category == "peixe":
                coverage[location] = {
                    p[0]: sum(p[0] in item["periodos"] for item in rows) for p in EXPECTED_PERIODS
                }
                require(min(coverage[location].values()) >= 3, f"Menos de três peixes: {location}")
        names_by_category[category] = category_names

    require(not names_by_category["peixe"] & names_by_category["especial"], "Espécie duplicada entre categorias.")
    require(len(names_by_category["peixe"]) == 68, "Total de peixes únicos diferente de 68.")
    require(len(names_by_category["especial"]) == 20, "Total de especiais diferente de 20.")
    require(len(new_flags) == 88, "Total aquático diferente de 88.")
    require(sum(new_flags.values()) == 39, "Total de novas entradas diferente de 39.")
    require("Bota velha" not in new_flags, "Lixo contado como entrada aquática.")
    require(occurrence_count == 90, "Total de ocorrências diferente de 90.")
    require({name for name, count in fish_frequency.items() if count > 1} == {"Lambari", "Pacu"},
            "Espécies compartilhadas entre mapas diferem da proposta.")
    require(data.get("validacao_cobertura") == coverage, "Cobertura declarada difere do catálogo.")
    require(data.get("resumo") == EXPECTED_SUMMARY, "Resumo declarado diverge da proposta.")
    # Checagens explícitas dos exemplos sensíveis às relações local/período.
    def allowed_at(location: str, name: str) -> set[str]:
        return set(next(item["periodos"] for item in fish[location] if item["nome"] == name))
    require("noite" in allowed_at("Rio das Vitórias", "Pacu"), "Pacu deve ser noturno no Rio.")
    require("noite" not in allowed_at("Enseada do Poente", "Pacu"), "Pacu não deve ser noturno na Enseada.")
    examples = [
        ("Rio das Vitórias", "Piabanha", "amanhecer"),
        ("Rio das Vitórias", "Piraputanga", "manhã"),
        ("Recife das Cores", "Peixe-borboleta", "dia"),
        ("Recife das Cores", "Cirurgião-patela", "meio-dia"),
        ("Rio das Vitórias", "Piapara", "tarde"),
        ("Rio das Vitórias", "Jaú", "anoitecer"),
        ("Enseada do Poente", "Jundiá", "noite"),
    ]
    for location, name, period in examples:
        require(allowed_at(location, name) == {period}, f"Exclusividade incorreta: {name}")

    legacy = {name for name, is_new in new_flags.items() if not is_new}
    legacy_check = "não executada; apenas flags do documento foram contadas"
    if legacy_source is not None:
        source_names = legacy_names_from_source(legacy_source)
        require(source_names == legacy, "Legado diverge da fonte: "
                f"ausentes={sorted(source_names - legacy)}, extras={sorted(legacy - source_names)}")
        legacy_check = "comparação de nomes com LOOT literal fornecida: aprovada"

    return {
        "status": "APROVADO_CONTEUDO_PROPOSTA",
        "escopo": "Somente consistência do JSON; não valida runtime, migração, arte, economia ou EXE.",
        "mapas": len(maps), "periodos": len(periods), "entradas_aquaticas_unicas": len(new_flags),
        "peixes_unicos": len(names_by_category["peixe"]),
        "encontros_especiais_unicos": len(names_by_category["especial"]),
        "originais_marcados": len(legacy), "novas_entradas": sum(new_flags.values()),
        "ocorrencias_especie_local": occurrence_count,
        "combinacoes_mapa_periodo": sum(len(x) for x in coverage.values()),
        "minimo_peixes_elegiveis": min(n for row in coverage.values() for n in row.values()),
        "minutos_sem_lacuna_ou_sobreposicao": len(coverage_clock),
        "comparacao_com_fonte_legada": legacy_check,
        "cobertura": coverage,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogo", nargs="?", type=Path,
                        default=Path(__file__).with_name("pescaidle_expansao_catalogo.json"))
    parser.add_argument("--legacy-source", type=Path, help="Fonte histórica com LOOT literal, somente leitura.")
    parser.add_argument("--report", type=Path, help="Gravar relatório nesta saída explícita; sem escrita por padrão.")
    args = parser.parse_args()
    try:
        raw = args.catalogo.read_bytes()
        data = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=no_duplicate_keys)
        report = validate(data, args.legacy_source)
        report["sha256_catalogo"] = hashlib.sha256(raw).hexdigest()
        text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.report is not None:
            # Nunca sobrescreva a entrada por engano.
            output = args.report.resolve()
            require(output != args.catalogo.resolve(), "O relatório não pode sobrescrever o catálogo.")
            if args.legacy_source is not None:
                require(output != args.legacy_source.resolve(), "O relatório não pode sobrescrever a fonte legada.")
            output.write_text(text, encoding="utf-8")
        print(text, end="")
        return 0
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, StopIteration, SyntaxError, AttributeError) as exc:
        print(f"FALHA_CATALOGO_PROPOSTA: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
