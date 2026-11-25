#!/usr/bin/env python3
"""Freya 2.0 paket planı kayıt üreticisi ve denetleyicisi.

Paket ve aşama dosyalarını (docs/execution/packages/**, docs/execution/stages/*)
okur; görev, test ve kapı kimliklerini toplar; bağımlılıkları, kimlik
benzersizliğini, bölüm yapısını ve göreli bağlantıları denetler.

Üretilen dosyalar (elle düzenlenmez):
  docs/execution/registry.json
  docs/execution/legacy-mapping.md

Kullanım:
  python scripts/build_registry.py           # üret + denetle
  python scripts/build_registry.py --check   # yalnız denetle; dosyalar güncel değilse hata

Yalnız standart kütüphane kullanır.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXEC = ROOT / "docs" / "execution"
PACKAGES = EXEC / "packages"
STAGES = EXEC / "stages"
STAGE_TASK_FILES = sorted((ROOT / "docs" / "stages").glob("F*/tasks.md"))
CROSS_CUTTING = ROOT / "docs" / "cross-cutting"
AIP_DATA = ROOT / "scripts" / "data" / "legacy_aip.json"
REGISTRY_OUT = EXEC / "registry.json"
LEGACY_OUT = EXEC / "legacy-mapping.md"

HEADER_FIELDS = [
    "Kimlik", "Dalga", "Öncelik", "Önkoşullar", "Sonraki", "Bayrak",
    "Ortam", "Eski görevler", "Kaynak", "Durum",
]
SECTIONS = [
    "Amaç", "Başlamadan önce", "Kapsam", "Dosyalar", "Tasarım ve sözleşmeler",
    "Görevler", "Testler", "Kabul kapıları", "Kanıt", "Geri dönüş", "Devir",
    "Başlatma komutu",
]
STATUSES = {"NOT_RUN", "PASS", "FAIL", "HOLD", "DEFERRED"}

# Kapı kimliği öneki istisnaları (K-03).
GATE_PREFIX = {
    "CORE_GATE": "CG",
    "W2_GATE": "WG",
    "G2": "G2-K",
    "G3": "UG",
    "G4": "SG",
    "G5": "RG",
    "PILOT_DECISION": "PILOT-K",
}
# Görev kimliği öneki istisnaları.
TASK_PREFIX = {
    "G3": "UI.",
    "PILOT_DECISION": "PILOT.",
}
OPTIONAL = {"F6-D", "F5-D"}
# execution-order.md "Önerilen seri sıra" tablosuyla aynı olmalı.
PREFERRED_ORDER = [
    "M00", "H01", "M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08", "CORE_GATE",
    "F0-A", "F1-A", "F2-A", "F3-A", "F4-A", "F5-A", "F6-A", "W2_GATE",
    "F1-B", "F6-B", "F2-B", "F3-B", "F4-B", "F5-B",
    "F0-B", "F2-C", "F1-C", "F3-C", "F4-C", "F5-C", "F6-C",
    "F6-D", "G2", "G3", "G4", "G5", "PILOT_DECISION", "F5-D",
]

LEGACY_RE = re.compile(r"\b(F\d-T\d{2}|CC-T\d{2})\b")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
TEST_REF_RE = re.compile(r"\b([A-Z]{2,3})(\d{2,3})(?:\s*[–-]\s*(?:[A-Z]{2,3})?(\d{2,3}))?\b")


class Problems:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def split_row(line: str) -> list[str]:
    cells = line.strip()
    if cells.startswith("|"):
        cells = cells[1:]
    if cells.endswith("|"):
        cells = cells[:-1]
    out, buf, tick = [], [], False
    for ch in cells:
        if ch == "`":
            tick = not tick
        if ch == "|" and not tick:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    out.append("".join(buf).strip())
    return out


def is_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|?\s*:?-{3,}.*", line.strip())) and set(line.strip()) <= set("|-: ")


def parse_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^## (\d+)\. (.+?)\s*$", line)
        if m:
            if current:
                sections[current] = "\n".join(buf)
            current = m.group(2)
            buf = []
            continue
        if current:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf)
    return sections


def parse_table_rows(block: str) -> list[list[str]]:
    rows: list[list[str]] = []
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|") and i + 1 < len(lines) and is_separator(lines[i + 1]):
            i += 2  # başlık + ayırıcı
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            continue
        i += 1
    return rows


def parse_header(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("## "):
            break
        if line.startswith("| ") and not is_separator(line):
            cells = split_row(line)
            if len(cells) >= 2 and cells[0] in HEADER_FIELDS:
                fields[cells[0]] = cells[1]
    return fields


def parse_ids(value: str, known: set[str]) -> list[str]:
    value = re.sub(r"\([^)]*\)", "", value)
    out = []
    for tok in re.split(r"[,+]", value):
        tok = tok.strip().strip("`")
        if tok in known:
            out.append(tok)
    return out


def expand_test_refs(text: str, prefixes: set[str]) -> set[str]:
    refs: set[str] = set()
    for m in TEST_REF_RE.finditer(text):
        prefix, start, end = m.group(1), m.group(2), m.group(3)
        if prefix not in prefixes:
            continue
        width = len(start)
        if end:
            for n in range(int(start), int(end) + 1):
                refs.add(f"{prefix}{n:0{width}d}")
        else:
            refs.add(f"{prefix}{start}")
    return refs


def load_documents(problems: Problems) -> list[dict]:
    docs = []
    files = sorted(PACKAGES.glob("W*/*.md")) + sorted(STAGES.glob("*.md"))
    for path in files:
        text = path.read_text(encoding="utf-8")
        header = parse_header(text)
        sections = parse_sections(text)
        doc_id = header.get("Kimlik", "").strip()
        title_m = re.match(r"^# (.+?) — (.+)$", text.splitlines()[0]) if text else None
        docs.append({
            "path": path,
            "text": text,
            "header": header,
            "sections": sections,
            "id": doc_id,
            "title": title_m.group(2).strip() if title_m else "",
            "kind": "stage" if path.parent == STAGES else "package",
        })
        for field in HEADER_FIELDS:
            if field not in header:
                problems.error(f"{rel(path)}: başlık tablosunda '{field}' yok")
        if title_m and title_m.group(1).strip() != doc_id:
            problems.error(f"{rel(path)}: başlık '{title_m.group(1)}' ile Kimlik '{doc_id}' farklı")
        names = list(sections.keys())
        if names != SECTIONS:
            problems.error(f"{rel(path)}: bölümler şablonla uyuşmuyor: {names}")
        nums = re.findall(r"^## (\d+)\. ", text, flags=re.M)
        if nums != [str(i) for i in range(1, 13)]:
            problems.error(f"{rel(path)}: bölüm numaraları 1–12 değil: {nums}")
        status = header.get("Durum", "").split()[0] if header.get("Durum") else ""
        if status not in STATUSES:
            problems.error(f"{rel(path)}: Durum '{header.get('Durum')}' geçersiz")
    return docs


def collect(docs: list[dict], problems: Problems) -> dict:
    known = {d["id"] for d in docs}
    tasks, tests, gates = [], [], []
    seen_task, seen_test, seen_gate = {}, {}, {}
    for d in docs:
        pid = d["id"]
        secs = d["sections"]
        d["tasks"], d["tests"], d["gates"] = [], [], []
        for row in parse_table_rows(secs.get("Görevler", "")):
            if len(row) < 4:
                problems.error(f"{rel(d['path'])}: görev satırı eksik sütunlu: {row}")
                continue
            tid = row[0]
            expected = TASK_PREFIX.get(pid, f"{pid}.")
            if not tid.startswith(expected):
                problems.error(f"{rel(d['path'])}: görev kimliği '{tid}' '{expected}' ile başlamıyor")
            if tid in seen_task:
                problems.error(f"görev kimliği yinelenmiş: {tid} ({seen_task[tid]}, {pid})")
            seen_task[tid] = pid
            rec = {"id": tid, "package": pid, "title": row[1], "done_when": row[2] + " " + row[3]}
            d["tasks"].append(rec)
            tasks.append(rec)
        for row in parse_table_rows(secs.get("Testler", "")):
            if len(row) < 3:
                problems.error(f"{rel(d['path'])}: test satırı eksik sütunlu: {row}")
                continue
            tid = row[0]
            if tid in seen_test:
                problems.error(f"test kimliği yinelenmiş: {tid} ({seen_test[tid]}, {pid})")
            seen_test[tid] = pid
            rec = {"id": tid, "package": pid, "title": row[1], "expected": row[2]}
            d["tests"].append(rec)
            tests.append(rec)
        for row in parse_table_rows(secs.get("Kabul kapıları", "")):
            if len(row) < 3:
                problems.error(f"{rel(d['path'])}: kapı satırı eksik sütunlu: {row}")
                continue
            gid = row[0]
            expected = GATE_PREFIX.get(pid, f"{pid}-G")
            if not gid.startswith(expected):
                problems.error(f"{rel(d['path'])}: kapı kimliği '{gid}' '{expected}' ile başlamıyor")
            if gid in seen_gate:
                problems.error(f"kapı kimliği yinelenmiş: {gid} ({seen_gate[gid]}, {pid})")
            seen_gate[gid] = pid
            rec = {"id": gid, "package": pid, "title": row[1], "condition": row[2]}
            d["gates"].append(rec)
            gates.append(rec)
        if not d["gates"]:
            problems.error(f"{rel(d['path'])}: kabul kapısı yok")

        # Görevlerin andığı testler mevcut mu; her test bir göreve bağlı mı?
        prefixes = {re.match(r"[A-Z]+", t["id"]).group(0) for t in d["tests"]}
        own = {t["id"] for t in d["tests"]}
        referenced: set[str] = set()
        for t in d["tasks"]:
            referenced |= expand_test_refs(t["done_when"], prefixes)
        missing = sorted(referenced - own)
        if missing:
            problems.error(f"{rel(d['path'])}: görevler tanımsız testlere atıf yapıyor: {', '.join(missing[:10])}")
        if d["tasks"] and d["tests"]:
            orphan = sorted(own - referenced)
            if orphan:
                problems.warn(f"{pid}: hiçbir görevin 'Bitti sayılır' sütununda anılmayan {len(orphan)} test (ör. {', '.join(orphan[:5])})")

    # Bağımlılıklar
    preds = {d["id"]: parse_ids(d["header"].get("Önkoşullar", ""), known) for d in docs}
    succ_declared = {d["id"]: parse_ids(d["header"].get("Sonraki", ""), known) for d in docs}
    for d in docs:
        raw = re.sub(r"\([^)]*\)", "", d["header"].get("Önkoşullar", ""))
        for tok in re.split(r"[,+]", raw):
            tok = tok.strip().strip("`")
            if tok and tok not in {"—", "-"} and tok not in known and re.fullmatch(r"[A-Z0-9_]+(-[A-Z])?", tok):
                problems.error(f"{d['id']}: bilinmeyen önkoşul '{tok}'")
    succ_computed: dict[str, set[str]] = defaultdict(set)
    for pid, ps in preds.items():
        for p in ps:
            succ_computed[p].add(pid)
    for d in docs:
        pid = d["id"]
        declared = set(succ_declared[pid])
        computed = succ_computed.get(pid, set())
        if declared != computed:
            problems.error(
                f"{pid}: Sonraki {sorted(declared)} ≠ önkoşullardan hesaplanan {sorted(computed)}"
            )
    # Döngü denetimi ve topolojik sıra (eşitlikte önerilen seri sıra; execution-order.md)
    rank = {k: i for i, k in enumerate(PREFERRED_ORDER)}
    indeg = {n: len(ps) for n, ps in preds.items()}
    ready = [n for n, k in indeg.items() if k == 0]
    order: list[str] = []
    while ready:
        ready.sort(key=lambda x: (rank.get(x, len(rank)), x))
        n = ready.pop(0)
        order.append(n)
        for m in succ_computed.get(n, ()):
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)
    if len(order) != len(preds):
        problems.error(f"bağımlılık döngüsü: {sorted(set(preds) - set(order))}")
    if [x for x in order if x in rank] != [x for x in PREFERRED_ORDER if x in preds]:
        problems.error("execution-order.md önerilen sırası bağımlılıklarla çelişiyor (PREFERRED_ORDER)")

    return {"tasks": tasks, "tests": tests, "gates": gates, "preds": preds,
            "succ": {k: sorted(v, key=lambda x: order.index(x) if x in order else 999) for k, v in succ_computed.items()},
            "topo": order}


def check_links(problems: Problems) -> None:
    files = list(EXEC.rglob("*.md")) + [ROOT / "CLAUDE.md", ROOT / "README.md"]
    files += list((ROOT / "docs").rglob("*.md"))
    seen = set()
    for path in files:
        if path in seen or not path.exists():
            continue
        seen.add(path)
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        for m in LINK_RE.finditer(text):
            target = m.group(1)
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            file_part, _, anchor = target.partition("#")
            dest = (path.parent / file_part).resolve()
            if not dest.exists():
                problems.error(f"{rel(path)}: kırık bağlantı → {target}")
                continue
            if anchor and dest.suffix == ".md":
                heads = re.findall(r"^#{1,6} (.+?)\s*$", dest.read_text(encoding="utf-8"), flags=re.M)
                slugs = {slugify(h) for h in heads}
                if anchor not in slugs:
                    problems.error(f"{rel(path)}: çapa bulunamadı → {target}")


def slugify(heading: str) -> str:
    h = heading.strip().lower()
    h = re.sub(r"[`*_]", "", h)
    h = re.sub(r"[^\w\- ]", "", h, flags=re.UNICODE)
    return h.replace(" ", "-")


def legacy_tasks() -> dict[str, str]:
    """docs/stages/*/tasks.md ve ortak katman belgelerindeki eski görev kimlikleri."""
    out: dict[str, str] = {}
    for f in STAGE_TASK_FILES:
        for m in re.finditer(r"^### (F\d-T\d{2}) · (.+?)(?: · [SML]{1,2})?\s*$", f.read_text(encoding="utf-8"), flags=re.M):
            out[m.group(1)] = m.group(2).strip()
    for f in CROSS_CUTTING.glob("*.md"):
        for m in re.finditer(r"\| (?:AIP-\d\d / )?(CC-T\d{2}) \| (.+?) \|", f.read_text(encoding="utf-8")):
            out.setdefault(m.group(1), re.sub(r"\s+", " ", m.group(2)).strip())
    return out


def build_legacy(docs: list[dict], problems: Problems) -> tuple[dict, str]:
    old = legacy_tasks()
    mapping: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for d in docs:
        field = d["header"].get("Eski görevler", "")
        for part in field.split(","):
            note = ""
            nm = re.search(r"\(([^)]*)\)", part)
            if nm:
                note = nm.group(1)
            for tid in LEGACY_RE.findall(part):
                if d["id"] == "G2":
                    continue  # G2 alanı yalnız açıklama içerir
                mapping[tid].append((d["id"], note))
    for tid in sorted(old):
        if tid not in mapping:
            problems.error(f"eski görev {tid} hiçbir pakete eşlenmemiş")
        elif len(mapping[tid]) > 1 and not all(n for _, n in mapping[tid]):
            problems.error(f"eski görev {tid} birden çok pakette notsuz: {mapping[tid]}")
    for tid in sorted(mapping):
        if tid not in old:
            problems.error(f"eski görev {tid} eşlenmiş ama eski planda yok")

    aip = json.loads(AIP_DATA.read_text(encoding="utf-8")) if AIP_DATA.exists() else {}
    titles = {d["id"]: d["title"] for d in docs}
    files = {d["id"]: d["path"] for d in docs}

    def link(pid: str) -> str:
        return f"[{pid}]({files[pid].relative_to(EXEC).as_posix()})"

    lines = [
        "# Eski plan → paket planı eşlemesi",
        "",
        "> **Üretilmiş dosya — elle düzenlemeyin.** Kaynak: paket dosyalarındaki `Eski görevler` satırları ve "
        "`scripts/data/legacy_aip.json`. Yeniden üretmek için: `python scripts/build_registry.py`.",
        "",
        "Eski AIP/Faz planı ve aşama `tasks.md` dosyalarındaki görev kimlikleri (`F2-T15`) artık yürütme birimi "
        "değildir; teknik ayrıntı için okunmaya devam eder. Yürütme birimi pakettir.",
        "",
        "## AIP → paket",
        "",
        "| AIP | Ad | Eski görevler | Yeni paket(ler) |",
        "| --- | --- | --- | --- |",
    ]
    for key in sorted(aip):
        rec = aip[key]
        pk: list[str] = []
        for t in rec["tasks"]:
            for pid, _ in mapping.get(t.rstrip("*"), []):
                if pid not in pk:
                    pk.append(pid)
        lines.append(f"| {key} | {rec['name']} | {', '.join(rec['tasks'])} | {', '.join(link(p) for p in pk) or '—'} |")
    lines += [
        "",
        "## Eski görev → paket",
        "",
        "| Eski görev | Başlık | Paket | Not |",
        "| --- | --- | --- | --- |",
    ]

    def sort_key(t: str) -> tuple:
        m = re.match(r"(F\d|CC)-T(\d+)", t)
        return (m.group(1), int(m.group(2))) if m else (t, 0)

    for tid in sorted(set(old) | set(mapping), key=sort_key):
        targets = mapping.get(tid, [])
        pk = ", ".join(f"{link(p)} — {titles[p]}" for p, _ in targets) or "**eşlenmemiş**"
        notes = "; ".join(n for _, n in targets if n)
        lines.append(f"| {tid} | {old.get(tid, '—')} | {pk} | {notes} |")
    lines.append("")
    data = {tid: [p for p, _ in mapping[tid]] for tid in sorted(mapping, key=sort_key)}
    return data, "\n".join(lines)


def build_registry(docs: list[dict], coll: dict, legacy: dict) -> dict:
    packages = []
    for d in docs:
        h = d["header"]
        packages.append({
            "id": d["id"],
            "title": d["title"],
            "kind": d["kind"],
            "wave": h.get("Dalga"),
            "priority": h.get("Öncelik"),
            "optional": d["id"] in OPTIONAL,
            "prerequisites": coll["preds"][d["id"]],
            "successors": coll["succ"].get(d["id"], []),
            "flag": h.get("Bayrak"),
            "environment": h.get("Ortam"),
            "status": h.get("Durum", "").split()[0],
            "file": rel(d["path"]),
            "counts": {"tasks": len(d["tasks"]), "tests": len(d["tests"]), "gates": len(d["gates"])},
        })
    mandatory = [p for p in packages if not p["optional"]]
    totals = {
        "documents": len(packages),
        "tasks": len(coll["tasks"]),
        "tests": len(coll["tests"]),
        "gates": len(coll["gates"]),
        "mandatory": {
            "documents": len(mandatory),
            "tasks": sum(p["counts"]["tasks"] for p in mandatory),
            "tests": sum(p["counts"]["tests"] for p in mandatory),
            "gates": sum(p["counts"]["gates"] for p in mandatory),
        },
    }
    return {
        "generated_by": "scripts/build_registry.py",
        "note": "Plan sayılarıdır; çalıştırılmış test sayısı değildir (decisions.md K-09).",
        "totals": totals,
        "topological_order": coll["topo"],
        "packages": packages,
        "tasks": [{k: v for k, v in t.items() if k != "done_when"} for t in coll["tasks"]],
        "tests": coll["tests"],
        "gates": coll["gates"],
        "legacy_tasks": legacy,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="yalnız denetle; üretilmiş dosyalar güncel değilse hata ver")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    problems = Problems()
    docs = load_documents(problems)
    coll = collect(docs, problems)
    legacy, legacy_md = build_legacy(docs, problems)
    registry = build_registry(docs, coll, legacy)

    reg_text = json.dumps(registry, ensure_ascii=False, indent=1) + "\n"
    if args.check:
        for path, content in ((REGISTRY_OUT, reg_text), (LEGACY_OUT, legacy_md)):
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                problems.error(f"{rel(path)} güncel değil; 'python scripts/build_registry.py' çalıştırın")
    else:
        REGISTRY_OUT.write_text(reg_text, encoding="utf-8")
        LEGACY_OUT.write_text(legacy_md, encoding="utf-8")
    check_links(problems)

    t = registry["totals"]
    if not args.quiet:
        print(f"Belgeler: {t['documents']} · görev: {t['tasks']} · test: {t['tests']} · kapı: {t['gates']}")
        m = t["mandatory"]
        print(f"Zorunlu kapsam (F5-D, F6-D hariç): belge {m['documents']} · görev {m['tasks']} · test {m['tests']} · kapı {m['gates']}")
        for w in problems.warnings:
            print(f"UYARI: {w}")
    for e in problems.errors:
        print(f"HATA: {e}", file=sys.stderr)
    if problems.errors:
        print(f"{len(problems.errors)} hata", file=sys.stderr)
        return 1
    if not args.quiet:
        print("Denetim temiz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
