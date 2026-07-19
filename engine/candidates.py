#!/usr/bin/env python3
"""candidates.py — Nexus Input Engine S3a: candidatos priorizados (read-only).
Le index.csv + manifest.destination_axes + adoption_log.csv. Rankeia fichas done+roteadas+nao-adotadas
em 3 grupos por eixo (Engines=system_project, Content=content_channel, Pessoal=personal), POR FICHA,
leverage=nº de projetos desc. Emite _system/candidates.md + _system/candidates.json.
NAO adota, NAO muta acervo/index/manifest/adoption_log. stdlib-only.
Uso: py -3.11 _system\\candidates.py [--per-group N] [--limit L] [--dry DIR]
"""
import os, sys, csv, json, re, io, datetime
from pathlib import Path

BASE = Path(os.environ.get("NEXUS_BASE") or Path(__file__).resolve().parent.parent)
SYS = BASE / "_system"

def read_healed(path):
    raw = path.read_bytes().rstrip(b"\x00")
    if b"\x00" in raw:
        raise SystemExit(f"[ABORT] NUL no miolo de {path}")
    return raw.decode("utf-8")

def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

GROUP_ORDER = ["engines", "content", "pessoal"]
GROUP_LABEL = {"engines": "Engines (system_project)", "content": "Content (content_channel)", "pessoal": "Pessoal (personal)"}
GROUP_RANK = {"engines": 0, "content": 1, "pessoal": 2}

def load_axes():
    m = json.loads(read_healed(SYS / "manifest.json"))
    return {norm(k): v for k, v in m.get("destination_axes", {}).items()}

def adopted_ids():
    p = SYS / "adoption_log.csv"
    ids = set()
    if p.exists():
        for row in csv.DictReader(io.StringIO(read_healed(p))):
            v = (row.get("input_id") or "").strip()
            if v:
                ids.add(v)
    return ids

def atomic_write(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    if b"\x00" in tmp.read_bytes():
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"[ABORT] NUL read-back {path}")
    os.replace(tmp, path)

def main():
    argv = sys.argv[1:]
    def opt(f, d):
        return argv[argv.index(f) + 1] if f in argv else d
    per_group = int(opt("--per-group", "5"))
    limit = int(opt("--limit", "60"))
    out_dir = Path(opt("--dry", str(SYS)))
    out_dir.mkdir(parents=True, exist_ok=True)

    axes = load_axes()
    adopted = adopted_ids()
    groups = {g: [] for g in GROUP_ORDER}
    counts = {"total": 0, "done": 0, "routable": 0, "unrouted": 0,
              "adopted_skip": 0, "candidates": 0, "unmapped": 0}

    for row in csv.DictReader(io.StringIO(read_healed(SYS / "index.csv"))):
        counts["total"] += 1
        if (row.get("status") or "").strip().lower() != "done":
            continue
        counts["done"] += 1
        projs = [p.strip() for p in (row.get("projects") or "").split(";") if p.strip()]
        if not projs:
            counts["unrouted"] += 1
            continue
        counts["routable"] += 1
        fid = (row.get("id") or "").strip()
        if fid and fid in adopted:
            counts["adopted_skip"] += 1
            continue
        axis_types = {axes.get(norm(p)) for p in projs}
        if "system_project" in axis_types:
            g = "engines"
        elif "content_channel" in axis_types:
            g = "content"
        elif "personal" in axis_types:
            g = "pessoal"
        else:
            counts["unmapped"] += 1
            continue
        counts["candidates"] += 1
        groups[g].append({"id": fid, "title": (row.get("title") or "").strip(),
                          "collection": (row.get("collection") or "").strip(),
                          "url": (row.get("url") or "").strip(),
                          "projects": projs, "leverage": len(projs)})

    for g in groups:
        groups[g].sort(key=lambda x: (-x["leverage"], x["id"]))

    today = datetime.date.today().isoformat()
    L = ["# CANDIDATES — Nexus Input Engine (S3a)", f"generated_at: {today}", "",
         "> Fichas status=done, roteadas e AINDA NAO adotadas, agrupadas por eixo de destino.",
         "> Lista de PRIORIDADE (o \"distribui por projeto\"). Operador escolhe ate 3/semana p/ adotar (S3b).",
         "> NENHUMA adocao automatica. sem_destino (nao roteadas) ficam fora — gap de roteamento, nao candidatos.",
         "",
         f"Resumo: {counts['candidates']} candidatos "
         f"(engines {len(groups['engines'])} · content {len(groups['content'])} · pessoal {len(groups['pessoal'])}) "
         f"| done {counts['done']} · roteadas {counts['routable']} · nao-roteadas {counts['unrouted']} · ja-adotadas {counts['adopted_skip']} · unmapped {counts['unmapped']}",
         ""]
    for g in GROUP_ORDER:
        items = groups[g]
        L.append(f"## {GROUP_LABEL[g]} — {len(items)} candidatos (top {min(per_group, len(items))})")
        for it in items[:per_group]:
            title = (it["title"][:70] if it["title"] else "(sem titulo)")
            L.append(f"- **{it['id']}** [{it['collection']}] — {title} · -> {', '.join(it['projects'])} · {it['url']}")
        if not items:
            L.append("*(nenhum)*")
        L.append("")
    md = "\n".join(L) + "\n"

    ranked_flat = []
    for g in GROUP_ORDER:
        for it in groups[g]:
            ranked_flat.append({**it, "group": g})
    ranked_flat.sort(key=lambda x: (GROUP_RANK[x["group"]], -x["leverage"], x["id"]))
    payload = {"generated_at": today, "counts": counts, "per_group": per_group,
               "limit": limit, "candidates": ranked_flat[:limit]}

    atomic_write(out_dir / "candidates.md", md)
    atomic_write(out_dir / "candidates.json", json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"[candidates] candidates.md + candidates.json em {out_dir}")
    print(f"   candidatos={counts['candidates']} engines={len(groups['engines'])} "
          f"content={len(groups['content'])} pessoal={len(groups['pessoal'])} nao-roteadas={counts['unrouted']}")

if __name__ == "__main__":
    main()
