#!/usr/bin/env python3
"""
build_index.py - fonte de verdade UNICA e BLINDADA do acervo (IG + X). v3.1
Hardening: single-writer lock; consistencia checada ANTES de escrever; atomic write +
read-back verify (NUL/contagem); auto-heal NUL on read; md5 sidecar; dimensao source;
tombstones ('# ARQUIVO OBSOLETO' ou status: obsolete) ignorados.
index.csv/manifest.json = CACHE derivado das fichas (collections/*/NN_*.md = verdade).
Uso:
  py -3.11 build_index.py            # regenera _system/ (lock)
  py -3.11 build_index.py --dry DIR  # preview em DIR (sem lock)
  py -3.11 build_index.py --verify   # so checa integridade (read-only)
"""
import csv, io, json, re, os, sys, tempfile, hashlib, time
from collections import Counter
from datetime import date

BASE = os.environ.get("NEXUS_BASE") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS = os.path.join(BASE, "collections")
SYS  = os.path.join(BASE, "_system")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config import load_config
CFG = load_config()
KNOWN_ORDER     = CFG["known_order"]
SAVED_IDS       = CFG["saved_ids"]
SOURCE_MAP      = CFG["source_map"]
URL_MAP         = CFG["url_map"]
ACCOUNT         = CFG["account"]
IG_URL_TEMPLATE = CFG["ig_url_template"]
DESTINATION_AXES = CFG["destination_axes"]
PERSONAL_PROJECT = CFG["personal_project"]
HEADER = ["order","id","collection","source","url","file","type","author","title","themes","projects","status"]
LOCK = os.path.join(SYS, ".build.lock")
STALE_LOCK_SEC = 600
TOMBSTONE_RE = re.compile(r"^\s*#\s*ARQUIVO OBSOLETO", re.I)

def acquire_lock():
    try:
        fd = os.open(LOCK, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:
        try:
            age = time.time() - os.path.getmtime(LOCK); holder = open(LOCK).read().strip()
        except FileNotFoundError:
            return acquire_lock()
        if age > STALE_LOCK_SEC:
            os.remove(LOCK); return acquire_lock()
        raise SystemExit("ABORT: lock ativo (%s, %ds). Outro escritor? Se stale, remova %s" % (holder, int(age), LOCK))
    os.write(fd, ("pid=%d %s %s" % (os.getpid(), date.today().isoformat(), time.strftime("%H:%M:%S"))).encode())
    os.close(fd)

def release_lock():
    try: os.remove(LOCK)
    except FileNotFoundError: pass

def read_json_healed(path):
    if not os.path.exists(path): return None, "missing"
    raw = open(path, "rb").read(); healed = raw.rstrip(b"\x00"); nul = len(raw) - len(healed)
    try:
        return json.loads(healed.decode("utf-8")), ("healed(%d NUL)" % nul if nul else "ok")
    except Exception as e:
        return None, "invalid:%s" % e

def atomic_write_verified(path, data, kind, expect_rows=None):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)
    back = open(path, "rb").read()
    if back.count(b"\x00"):
        raise SystemExit("VERIFY FAIL: NUL em %s apos escrita (cloud-sync). Reexecute." % path)
    if kind == "json":
        json.loads(back.decode("utf-8"))
    if kind == "csv" and expect_rows is not None:
        got = back.decode("utf-8").rstrip("\n").count("\n") + 1
        if got != expect_rows:
            raise SystemExit("VERIFY FAIL: %s tem %d linhas, esperado %d (truncamento)." % (path, got, expect_rows))
    md5 = hashlib.md5(back).hexdigest(); open(path + ".md5", "w").write(md5); return md5

def fm_parse(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m: return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line: continue
        k, v = line.split(":", 1); k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            fm[k] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()] if inner else []
        else:
            fm[k] = v.strip('"').strip("'")
    return fm, m.group(2)

def is_tombstone(body, fm):
    return bool(TOMBSTONE_RE.match(body or "")) or str(fm.get("status", "")).lower() == "obsolete"

def title_of(body, fm):
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith("# ") and "resumo" not in s.lower(): return s[2:].strip()
    m = re.search(r"##\s*Resumo\s*\n+(.+)", body)
    if m: return re.split(r"(?<=[.!?])\s", m.group(1).strip())[0][:90].strip()
    t = fm.get("temas")
    return ", ".join(t[:3]) if isinstance(t, list) and t else "(sem titulo)"

def canonize(source):
    out = []
    for term in CFG["canon_terms"]:
        if term in source:
            norm = CFG["alias_to_canon"][term]
            if norm not in out: out.append(norm)
    return out

def is_sensitive(fm):
    v = fm.get("sensivel")
    if v is None: return False
    if isinstance(v, list): return bool(v)
    s = str(v).strip().lower()
    return s != "" and s not in ("false","no","0","none","nao","nao se aplica","n/a")

def projects_of(body, fm):
    out = []
    p = fm.get("projetos")
    if isinstance(p, list) and p:
        out.extend(canonize(" + ".join(p)))
    pd = fm.get("plataformas_destino")
    if isinstance(pd, list) and pd:
        for v in canonize(" + ".join(pd)):
            if v not in out: out.append(v)
    if out:
        if is_sensitive(fm) and PERSONAL_PROJECT and PERSONAL_PROJECT not in out:
            out.append(PERSONAL_PROJECT)
        return out
    m = re.search(r"\*\*[ÁA]rea-alvo:\*\*\s*(.+)", body)
    if m:
        out = canonize(m.group(1))
    else:
        out = canonize(body)
    if is_sensitive(fm) and PERSONAL_PROJECT and PERSONAL_PROJECT not in out:
        out.append(PERSONAL_PROJECT)
    return out

def reuse_filled(body, fm=None):
    if fm:
        for key in ("reuse_angle","ghostwriter_angle"):
            v = fm.get(key)
            if isinstance(v, list) and v: return True
            if isinstance(v, str) and v.strip(): return True
    m = re.search(r"##\s*[AÂaâ]ngulo de reuso.*?\n+(.+?)(?:\n##|\Z)", body, re.S)
    if not m: m = re.search(r"\*\*[AÂaâ]ngulo de reuso.*?:\*\*\s*(.+)", body)
    return bool(m and re.sub(r"\s+", " ", m.group(1)).strip())

def discover_collections():
    if not os.path.isdir(COLS): return list(KNOWN_ORDER), []
    found = [d for d in sorted(os.listdir(COLS)) if os.path.isdir(os.path.join(COLS, d))]
    return [c for c in KNOWN_ORDER if c in found] + [c for c in found if c not in KNOWN_ORDER], []

def build_rows():
    rows, stats, tombstones = [], {}, []
    ordered, _ = discover_collections()
    for c in ordered:
        d = os.path.join(COLS, c)
        if not os.path.isdir(d): continue
        files = sorted(f for f in os.listdir(d) if re.match(r"^\d+_.*\.md$", f))
        complete = 0; processed = 0; src = SOURCE_MAP.get(c, "instagram")
        for fn in files:
            fm, body = fm_parse(open(os.path.join(d, fn), encoding="utf-8").read())
            if is_tombstone(body, fm):
                tombstones.append("collections/%s/%s" % (c, fn)); continue
            processed += 1
            order = fm.get("order") or re.match(r"^(\d+)_", fn).group(1)
            cid = fm.get("id") or fm.get("shortcode") or ""
            src_f = fm.get("source") or src
            url = (fm.get("url") or "") if src_f == "x" else (fm.get("url") or (("https://www.instagram.com/p/%s/" % cid) if cid else ""))
            temas = fm.get("temas")
            themes = "; ".join(temas) if isinstance(temas, list) else (temas or "")
            filled = reuse_filled(body, fm); complete += 1 if filled else 0
            rows.append({"order": int(order), "id": cid, "collection": c, "source": src_f, "url": url,
                         "file": "collections/%s/%s" % (c, fn), "type": fm.get("tipo") or fm.get("type") or "",
                         "author": fm.get("autor") or fm.get("author") or "", "title": title_of(body, fm),
                         "themes": themes, "projects": ";".join(projects_of(body, fm)),
                         "status": "done" if filled else "stub"})
        stats[c] = {"fichas": processed, "complete": complete}
    rows.sort(key=lambda r: (ordered.index(r["collection"]), r["order"]))
    return rows, stats, ordered, tombstones

def assert_consistency(rows, stats):
    total = len(rows); per = Counter(r["collection"] for r in rows)
    assert total == sum(s["fichas"] for s in stats.values()), "DRIFT linhas!=fichas"
    for c in per:
        orders = [r["order"] for r in rows if r["collection"] == c]
        if len(set(orders)) != per[c]:
            dups = [o for o in set(orders) if orders.count(o) > 1]
            raise AssertionError("ORDER dup em %s: %s" % (c, dups))
    return total, dict(per)

def render_index(rows):
    sio = io.StringIO(); w = csv.DictWriter(sio, fieldnames=HEADER); w.writeheader()
    for r in rows: w.writerow(r)
    return sio.getvalue()

def main():
    args = sys.argv[1:]; dry = None; verify = "--verify" in args
    if "--dry" in args:
        dry = args[args.index("--dry")+1]; os.makedirs(dry, exist_ok=True)
    rows, stats, ordered, tombstones = build_rows()
    # CONSISTENCIA ANTES DE QUALQUER ESCRITA (nao grava cache ruim)
    total, per = assert_consistency(rows, stats)
    index_data = render_index(rows); expect = len(rows) + 1

    if verify:
        ipath = os.path.join(SYS, "index.csv")
        cur = open(ipath, "rb").read() if os.path.exists(ipath) else b""
        cur_rows = cur.decode("utf-8","replace").rstrip("\n").count("\n")+1 if cur else 0
        nul = cur.count(b"\x00"); man, mstate = read_json_healed(os.path.join(SYS, "manifest.json"))
        print("VERIFY: fichas=%d | tombstones=%d | index.csv linhas=%d (esperado %d) NUL=%d | manifest=%s" %
              (total, len(tombstones), cur_rows, expect, nul, mstate))
        drift = (cur_rows != expect) or nul or (man is None)
        print("RESULT:", "DRIFT/CORRUPCAO -> rodar build_index.py" if drift else "OK")
        sys.exit(1 if drift else 0)

    sysdir = dry or SYS
    if not dry: acquire_lock()
    try:
        index_path = os.path.join(sysdir, "index.csv"); manifest_path = os.path.join(sysdir, "manifest.json")
        stamp = date.today().isoformat()
        if not dry and os.path.exists(index_path):
            atomic_write_verified(index_path.replace(".csv", ".backup-%s.csv" % stamp), open(index_path, encoding="utf-8").read(), "csv")
        idx_md5 = atomic_write_verified(index_path, index_data, "csv", expect_rows=expect)
        man, mstate = read_json_healed(os.path.join(SYS, "manifest.json"))
        if man is None: man = {"collections": {}}
        if not dry and os.path.exists(manifest_path):
            atomic_write_verified(manifest_path.replace(".json", ".backup-%s.json" % stamp), json.dumps(man, ensure_ascii=False, indent=2), "json")
        cols = man.get("collections", {})
        for c in ordered:
            if c not in stats: continue
            sid = SAVED_IDS.get(c); src = SOURCE_MAP.get(c, "instagram"); prev = cols.get(c, {}).get("status")
            if src != "instagram":
                url = URL_MAP.get(c, cols.get(c, {}).get("url", "")); sidv = None
                status = "complete" if prev=="complete" else ("complete" if stats[c]["complete"]==stats[c]["fichas"] else "in_progress")
            elif sid is None:
                url = cols.get(c, {}).get("url"); sidv = cols.get(c, {}).get("saved_collection_id"); status = "discovered"
            else:
                url = IG_URL_TEMPLATE.format(account=ACCOUNT, name=c, saved_collection_id=sid); sidv = sid
                status = "complete" if prev=="complete" else ("complete" if stats[c]["complete"]==stats[c]["fichas"] else "in_progress")
            cols.setdefault(c, {})
            cols[c].update({"url": url, "saved_collection_id": sidv, "source": src,
                            "total_enumerated": stats[c]["fichas"], "total_processed": stats[c]["fichas"],
                            "fichas_com_reuso": stats[c]["complete"], "status": status})
        man["collections"] = cols; man["last_processed_at"] = stamp; man["index_schema_version"] = 3
        man["index_md5"] = idx_md5; man["posts_note"] = "DEPRECATED; index.csv e cache derivado das fichas"
        man["destination_axes"] = DESTINATION_AXES
        atomic_write_verified(manifest_path, json.dumps(man, ensure_ascii=False, indent=2), "json")
    finally:
        if not dry: release_lock()
    print("[%s] index -> %s | manifest source-state: %s" % ("DRY" if dry else "WRITE", index_path, mstate))
    print("total fichas:", total, "| por colecao:", per)
    if tombstones: print("tombstones ignorados (%d):" % len(tombstones), tombstones)
    print("OK: consistencia pre-escrita; write-verify + md5 + lock")

if __name__ == "__main__":
    main()
