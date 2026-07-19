#!/usr/bin/env python3
"""promotion_queue.py — Nexus Input Engine S2: fila de promocao priorizada (read-only sobre o acervo).
Le backlog.json (S1) + index.csv (perfil de roteamento por colecao) + manifest.destination_axes
+ discovery/ (worklist real). Emite _system/PROMOTION_QUEUE.md + _system/promotion_queue.json.
Prioriza por valor de destino (share roteado p/ system_project) em buckets tier, dentro do tier por volume.
NAO cataloga, NAO muta acervo/index/manifest/fichas. Ficha-writing continua humano (contrato).
stdlib-only.  Uso: py -3.11 _system\\promotion_queue.py [--focus N] [--stale-days D] [--dry DIR]
"""
import os, sys, csv, json, re, io, datetime
from pathlib import Path

BASE = Path(os.environ.get("NEXUS_BASE") or Path(__file__).resolve().parent.parent)
SYS = BASE / "_system"
DISCOVERY = SYS / "discovery"

def read_healed(path):
    raw = path.read_bytes().rstrip(b"\x00")
    if b"\x00" in raw:
        raise SystemExit(f"[ABORT] NUL no miolo de {path}")
    return raw.decode("utf-8")

def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

def load_axes():
    m = json.loads(read_healed(SYS / "manifest.json"))
    return {norm(k): v for k, v in m.get("destination_axes", {}).items()}

def routing_profile(axes_norm):
    prof, unmatched = {}, {}
    reader = csv.DictReader(io.StringIO(read_healed(SYS / "index.csv")))
    for row in reader:
        coll = (row.get("collection") or "").strip()
        if not coll:
            continue
        d = prof.setdefault(coll, {"total": 0, "to_system": 0, "routed": 0})
        d["total"] += 1
        projs = [p.strip() for p in (row.get("projects") or "").split(";") if p.strip()]
        if projs:
            d["routed"] += 1
        has_system = False
        for p in projs:
            axis = axes_norm.get(norm(p))
            if axis is None:
                unmatched[p] = unmatched.get(p, 0) + 1
            elif axis == "system_project":
                has_system = True
        if has_system:
            d["to_system"] += 1
    return prof, unmatched

def extract_worklist(coll, disc_date):
    p = DISCOVERY / f"{disc_date}_{coll}.md" if disc_date else None
    if p is None or not p.exists():
        cands = sorted(DISCOVERY.glob(f"*_{coll}.md"))
        if not cands:
            return None, []
        p = cands[-1]
    lines = read_healed(p).splitlines()
    items = [ln for ln in lines if re.match(r"^\s*\d+\s*\|", ln)]
    return p.name, items

def atomic_write(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    if b"\x00" in tmp.read_bytes():
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"[ABORT] NUL read-back {path}")
    os.replace(tmp, path)

def main():
    argv = sys.argv[1:]
    def opt(flag, default):
        return argv[argv.index(flag) + 1] if flag in argv else default
    focus_n = int(opt("--focus", "3"))
    stale_days = int(opt("--stale-days", "7"))
    out_dir = Path(opt("--dry", str(SYS)))
    out_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.date.today()
    backlog = json.loads(read_healed(SYS / "backlog.json"))
    axes_norm = load_axes()
    prof, unmatched = routing_profile(axes_norm)

    tier_rank = {"high": 0, "med": 1, "low": 2}
    ranked = []
    for r in backlog.get("collections", []):
        pending = r.get("pending_discovery") or 0
        if pending <= 0:
            continue
        coll = r["collection"]
        pr = prof.get(coll, {"total": 0, "to_system": 0, "routed": 0})
        value = (pr["to_system"] / pr["total"]) if pr["total"] else 0.0
        tier = "high" if value >= 0.5 else ("med" if value >= 0.2 else "low")
        dd = r.get("discovery_date") or ""
        stale = False
        if dd:
            try:
                stale = (today - datetime.date.fromisoformat(dd)).days > stale_days
            except ValueError:
                pass
        ranked.append({"collection": coll, "pending": pending, "value": round(value, 3),
                       "tier": tier, "discovery_date": dd, "discovery_stale": stale,
                       "routed": pr["routed"], "total_fichas": pr["total"]})
    ranked.sort(key=lambda x: (tier_rank[x["tier"]], -x["pending"]))
    focus = ranked[:focus_n]

    L = ["# PROMOTION_QUEUE — Nexus Input Engine (S2)",
         f"generated_at: {today.isoformat()}  ·  fonte: backlog.json ({backlog.get('generated_from_manifest','')})",
         "",
         "> Fila de promocao DISCOVERED->ficha, priorizada por valor de destino (share->system_project) x volume.",
         "> Ficha-writing e HUMANO (contrato). Teto de 3/semana e de ADOCAO (S3), nao de promocao.",
         "> discovery_stale = re-rodar discovery antes de promover.",
         "",
         f"## FOCO SUGERIDO (top {len(focus)} por tier x volume)"]
    for r in focus:
        flag = "  ⚠️ discovery STALE — re-scan antes" if r["discovery_stale"] else ""
        L.append(f"- **{r['collection']}** — pendente {r['pending']} · tier {r['tier']} · valor {int(r['value']*100)}% · discovery {r['discovery_date']}{flag}")
    L += ["", "### Worklist inline (só do foco — evita doc gigante; demais coleções por link abaixo)"]
    for r in focus:
        fname, items = extract_worklist(r["collection"], r["discovery_date"])
        L += ["", f"#### {r['collection']} — {len(items)} itens · _system/discovery/{fname}"]
        if items:
            L.append("`#` | code | tipo | autor | url | gist")
            L += items
        else:
            L.append("*(sem linhas de item extraiveis — abrir a discovery manualmente)*")
    L += ["", f"## DEMAIS COLEÇÕES (por link — {max(0, len(ranked) - len(focus))})"]
    for r in ranked[focus_n:]:
        flag = "  ⚠️STALE" if r["discovery_stale"] else ""
        L.append(f"- {r['collection']} — pendente {r['pending']} · tier {r['tier']} · valor {int(r['value']*100)}% · _system/discovery/{r['discovery_date']}_{r['collection']}.md{flag}")
    if unmatched:
        L += ["", "## ⚠️ Projetos no index.csv sem mapa em destination_axes (contam como nao-roteados)"]
        for p, n in sorted(unmatched.items(), key=lambda x: -x[1]):
            L.append(f"- {p} ({n})")
    total_pending = sum(r["pending"] for r in ranked)
    L += ["", f"**TOTAL pendente na fila: {total_pending} em {len(ranked)} coleções.**"]
    md = "\n".join(L) + "\n"

    payload = {"generated_at": today.isoformat(),
               "source_manifest": backlog.get("generated_from_manifest", ""),
               "focus_n": focus_n, "stale_days": stale_days,
               "queue": ranked, "unmatched_projects": unmatched}

    atomic_write(out_dir / "PROMOTION_QUEUE.md", md)
    atomic_write(out_dir / "promotion_queue.json", json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"[promotion_queue] PROMOTION_QUEUE.md + promotion_queue.json em {out_dir}")
    print(f"   {len(ranked)} coleções com backlog · foco: {[r['collection'] for r in focus]}")
    if unmatched:
        print(f"   [warn] projetos sem mapa em destination_axes: {sorted(unmatched)}")

if __name__ == "__main__":
    main()
