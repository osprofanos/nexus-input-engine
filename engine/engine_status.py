#!/usr/bin/env python3
"""engine_status.py — Nexus Input Engine backlog reconciliation (S1, read-only sobre o acervo).
Reconcilia catalogado (index.csv) x manifest.total_processed x new_count da discovery mais
recente por coleção. Emite _system/BACKLOG.md + _system/backlog.json. Nao muta acervo/index/
manifest/dashboard/fichas. stdlib-only.
Uso:   py -3.11 _system\\engine_status.py
Flags: --verify (recomputa; exit 1 se houver mismatch manifest x index)
       --dry DIR (escreve em DIR em vez de _system/)
"""
import os, sys, csv, json, re, io, datetime
from pathlib import Path

def resolve_base():
    env = os.environ.get("NEXUS_BASE")
    return Path(env) if env else Path(__file__).resolve().parent.parent

BASE = resolve_base()
SYS = BASE / "_system"
DISCOVERY = SYS / "discovery"

def read_healed(path: Path) -> str:
    raw = path.read_bytes().rstrip(b"\x00")
    if b"\x00" in raw:
        raise SystemExit(f"[ABORT] NUL no miolo de {path} - corrupcao nao-trailing")
    return raw.decode("utf-8")

def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out

def count_index_by_collection() -> dict:
    counts = {}
    reader = csv.DictReader(io.StringIO(read_healed(SYS / "index.csv")))
    for row in reader:
        coll = (row.get("collection") or "").strip()
        if coll:
            counts[coll] = counts.get(coll, 0) + 1
    return counts

def latest_discovery(known: set) -> dict:
    best = {}
    if not DISCOVERY.exists():
        return best
    for p in DISCOVERY.glob("*.md"):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})_(.+)\.md$", p.name)
        if not m:
            continue
        date_s, coll = m.group(1), m.group(2)
        if coll not in known:            # descarta _RELACAO, fragmentos, ruido
            continue
        try:
            d = datetime.date.fromisoformat(date_s)
        except ValueError:
            continue
        if coll not in best or d > best[coll]["date"]:
            fm = parse_frontmatter(read_healed(p))
            def as_int(x):
                try: return int(str(x).strip())
                except Exception: return None
            best[coll] = {"date": d, "new_count": as_int(fm.get("new_count")),
                          "state": str(fm.get("state", "")).strip()}
    return best

def build_rows():
    manifest = json.loads(read_healed(SYS / "manifest.json"))
    mcolls = manifest.get("collections", {})
    known = set(mcolls.keys())
    idx = count_index_by_collection()
    disc = latest_discovery(known)
    rows = []
    for coll in sorted(known):
        m = mcolls.get(coll, {})
        processed = m.get("total_processed", m.get("processed"))
        catalogued = idx.get(coll, 0)
        d = disc.get(coll)
        new_count = d["new_count"] if d else None
        state = d["state"] if d else ""
        disc_date = d["date"].isoformat() if d else ""
        partial = "PARTIAL" in state.upper()
        mismatch = (processed is not None and catalogued != processed)
        if new_count is None:
            promo = "sem-discovery"
        elif new_count == 0:
            promo = "caught_up"
        else:
            promo = f"backlog:{new_count}"
        if partial:
            promo += " (partial)"
        rows.append({"collection": coll, "catalogued_index": catalogued,
                     "manifest_processed": processed, "pending_discovery": new_count,
                     "manifest_index_mismatch": bool(mismatch), "promotion_state": promo,
                     "discovery_date": disc_date})
    tot_cat = sum(r["catalogued_index"] for r in rows)
    tot_pend = sum((r["pending_discovery"] or 0) for r in rows)
    return rows, tot_cat, tot_pend, manifest.get("last_processed_at", "")

def render_md(rows, tot_cat, tot_pend, generated_at) -> str:
    L = ["# BACKLOG — Nexus Input Engine",
         f"generated_from_manifest: {generated_at}", "",
         "> Gerado por engine_status.py (S1, read-only). `pendente` = new_count da discovery mais recente.",
         "> `mismatch` = catalogado(index) difere de manifest.total_processed (inconsistencia de dado-fonte).",
         "",
         "| coleção | catalogado(index) | manifest_proc | pendente(discovery) | mismatch | promotion_state | discovery |",
         "|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append("| {c} | {ci} | {mp} | {pd} | {mm} | {ps} | {dd} |".format(
            c=r["collection"], ci=r["catalogued_index"],
            mp=("" if r["manifest_processed"] is None else r["manifest_processed"]),
            pd=("" if r["pending_discovery"] is None else r["pending_discovery"]),
            mm=("⚠️" if r["manifest_index_mismatch"] else ""),
            ps=r["promotion_state"], dd=r["discovery_date"]))
    L.append(f"| **TOTAL** | **{tot_cat}** |  | **{tot_pend}** |  |  |  |")
    return "\n".join(L) + "\n"

def atomic_write(path: Path, text: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    if b"\x00" in tmp.read_bytes():
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"[ABORT] NUL no read-back de {path}")
    os.replace(tmp, path)

def main():
    argv = sys.argv[1:]
    rows, tot_cat, tot_pend, generated_at = build_rows()
    if "--verify" in argv:
        bad = [r["collection"] for r in rows if r["manifest_index_mismatch"]]
        print(f"[verify] coleções={len(rows)} pendente_total={tot_pend} mismatch={bad}")
        sys.exit(1 if bad else 0)
    out_dir = SYS
    if "--dry" in argv:
        out_dir = Path(argv[argv.index("--dry") + 1])
        out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"generated_from_manifest": generated_at, "total_catalogued": tot_cat,
               "total_pending": tot_pend, "collections": rows}
    atomic_write(out_dir / "BACKLOG.md", render_md(rows, tot_cat, tot_pend, generated_at))
    atomic_write(out_dir / "backlog.json", json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"[engine_status] BACKLOG.md + backlog.json gerados em {out_dir}")
    print(f"   catalogado total={tot_cat} | pendente (descoberto nao catalogado) total={tot_pend}")

if __name__ == "__main__":
    main()
