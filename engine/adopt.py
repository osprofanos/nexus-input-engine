#!/usr/bin/env python3
"""adopt.py — Nexus Input Engine S3b: registra UMA adocao no adoption_log.csv (append-only, operador-invocado).
Valida: input_id existe como ficha em index.csv; nao esta ja no log; project existe em destination_axes;
decision no vocabulario do contrato; TRAVA de 3 decisoes ADOTAVEIS (READY/ADOPTED) por semana ISO.
Preenche title/source_collection do index. NAO decide, NAO adota automatico. NAO muta fichas/index/manifest.
stdlib-only.
Uso:
  py -3.11 _system\\adopt.py --id <ID> --project "<Projeto>" --decision READY --reason "<motivo>" [--next-step "<...>"] [--dry]
  py -3.11 _system\\adopt.py --list-week
"""
import os, sys, csv, io, json, re, datetime
from pathlib import Path

BASE = Path(os.environ.get("NEXUS_BASE") or Path(__file__).resolve().parent.parent)
SYS = BASE / "_system"
LOG = SYS / "adoption_log.csv"
COLS = ["date", "input_id", "title", "source_collection", "project", "decision", "reason", "next_step", "result", "review_date"]
DECISIONS = {"READY", "GATED", "WATCH", "BLOCKED", "HELD", "ADOPTED", "REJECTED", "DEFERRED"}
ADOPT_DECISIONS = {"READY", "ADOPTED"}   # contam contra o teto de 3/semana
WEEK_CAP = 3

def read_healed(path):
    raw = path.read_bytes().rstrip(b"\x00")
    if b"\x00" in raw:
        raise SystemExit(f"[ABORT] NUL no miolo de {path}")
    return raw.decode("utf-8")

def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

def load_index_ids():
    out = {}
    for row in csv.DictReader(io.StringIO(read_healed(SYS / "index.csv"))):
        fid = (row.get("id") or "").strip()
        if fid:
            out[fid] = {"title": (row.get("title") or "").strip(),
                        "collection": (row.get("collection") or "").strip()}
    return out

def load_axes():
    m = json.loads(read_healed(SYS / "manifest.json"))
    return {norm(k): k for k in m.get("destination_axes", {})}

def read_log_rows():
    if not LOG.exists():
        return []
    return list(csv.DictReader(io.StringIO(read_healed(LOG))))

def iso_key(date_str):
    try:
        y, w, _ = datetime.date.fromisoformat(date_str).isocalendar()
        return (y, w)
    except Exception:
        return None

def opt(argv, flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default

def atomic_write(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    if b"\x00" in tmp.read_bytes():
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"[ABORT] NUL read-back {path}")
    os.replace(tmp, path)

def main():
    argv = sys.argv[1:]
    today = datetime.date.today()
    cur = today.isocalendar()[:2]
    rows = read_log_rows()
    week_adopts = [r for r in rows if iso_key(r.get("date", "")) == cur
                   and (r.get("decision", "").strip().upper() in ADOPT_DECISIONS)]
    remaining = WEEK_CAP - len(week_adopts)

    if "--list-week" in argv:
        print(f"[adopt] semana ISO {cur[0]}-W{cur[1]:02d}: {len(week_adopts)}/{WEEK_CAP} adotaveis usados · restante {max(0, remaining)}")
        for r in week_adopts:
            print(f"   {r.get('date')} · {r.get('input_id')} -> {r.get('project')} [{r.get('decision')}]")
        return

    fid = opt(argv, "--id")
    project = opt(argv, "--project")
    decision = (opt(argv, "--decision") or "").strip().upper()
    reason = opt(argv, "--reason")
    next_step = opt(argv, "--next-step", "")
    dry = "--dry" in argv

    missing = [f for f, v in [("--id", fid), ("--project", project), ("--decision", decision), ("--reason", reason)] if not v]
    if missing:
        raise SystemExit(f"[ABORT] faltam args obrigatorios: {missing}. Ver --list-week ou o cabecalho do script.")
    if decision not in DECISIONS:
        raise SystemExit(f"[ABORT] decision '{decision}' invalida. Use: {sorted(DECISIONS)}")

    idx = load_index_ids()
    if fid not in idx:
        raise SystemExit(f"[ABORT] input_id '{fid}' nao existe como ficha em index.csv (nao inventar).")
    if any((r.get("input_id", "").strip() == fid) for r in rows):
        raise SystemExit(f"[ABORT] '{fid}' ja esta no adoption_log (sem dupla adocao).")

    axes = load_axes()
    if norm(project) not in axes:
        raise SystemExit(f"[ABORT] project '{project}' nao existe em destination_axes (candidato deve apontar p/ projeto EXISTENTE).")
    project_canon = axes[norm(project)]

    is_adopt = decision in ADOPT_DECISIONS
    if is_adopt and remaining <= 0:
        raise SystemExit(f"[HALT] teto de {WEEK_CAP} adocoes/semana ISO atingido ({cur[0]}-W{cur[1]:02d}). "
                         f"Parquear (WATCH/HELD) ou esperar a proxima semana (anti-dispersao, contrato).")

    review_date = (today + datetime.timedelta(days=14)).isoformat() if is_adopt else ""
    new_row = {"date": today.isoformat(), "input_id": fid,
               "title": idx[fid]["title"], "source_collection": idx[fid]["collection"],
               "project": project_canon, "decision": decision, "reason": reason,
               "next_step": next_step, "result": "", "review_date": review_date}

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: (r.get(c, "") or "") for c in COLS})
    w.writerow(new_row)
    text = buf.getvalue()

    if dry:
        print("[adopt --dry] linha que SERIA gravada (nada foi escrito):")
        print("   " + json.dumps(new_row, ensure_ascii=False))
        print(f"   cota apos gravar: {len(week_adopts) + (1 if is_adopt else 0)}/{WEEK_CAP}")
        return

    atomic_write(LOG, text)
    print(f"[adopt] gravado: {fid} -> {project_canon} [{decision}] · semana {cur[0]}-W{cur[1]:02d} "
          f"{len(week_adopts) + (1 if is_adopt else 0)}/{WEEK_CAP} adotaveis")

if __name__ == "__main__":
    main()
