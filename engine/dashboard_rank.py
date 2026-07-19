#!/usr/bin/env python3
"""dashboard_rank.py — generate the dashboard RANK block from candidates.json.
Reads _system/candidates.json ('groups'), builds the `const RANK = [...]` array and swaps ONLY that block
in the dashboard, preserving everything else byte-for-byte. Same hardening as refresh_dashboard:
heal-on-read NUL, atomic write + read-back verify, md5 sidecar, dated backup. stdlib-only.
Run candidates.py first. The DATA block (refresh_dashboard.py) is independent and untouched.
Usage: python engine/dashboard_rank.py [--verify] [--dry DIR]
"""
import os, sys, json, hashlib, tempfile, datetime
from pathlib import Path

BASE = Path(os.environ.get("NEXUS_BASE") or Path(__file__).resolve().parent.parent)
SYS = BASE / "_system"

ANCHOR_START = b"const RANK = "
ANCHOR_END = b";\n/* END RANK */"
REQUIRED = (b"const RANK", b"/* END RANK */", b"</html>")

def read_bytes_healed(path):
    raw = path.read_bytes()
    healed = raw.rstrip(b"\x00")
    if b"\x00" in healed:
        raise SystemExit(f"[ABORT] {path} tem NUL no miolo (corrupcao nao-trailing).")
    return healed

def dashboard_path():
    name = "DASHBOARD.html"
    cfg = BASE / "config.json"
    if cfg.exists():
        try:
            name = json.loads(read_bytes_healed(cfg).decode("utf-8")).get("dashboard_file", name)
        except Exception:
            pass
    return BASE / name

def build_rank():
    data = json.loads(read_bytes_healed(SYS / "candidates.json").decode("utf-8"))
    groups = data.get("groups") or {}
    rank = []
    for g in ("engines", "content", "pessoal"):
        for it in groups.get(g, []):
            rank.append({"group": g, "id": it.get("id", ""), "title": it.get("title", ""),
                         "collection": it.get("collection", ""), "projects": it.get("projects", []),
                         "url": it.get("url", "")})
    return rank, data.get("generated_at", "")

def locate(html):
    a = html.find(ANCHOR_START)
    if a < 0:
        raise SystemExit("[ABORT] ancora 'const RANK = ' ausente no dashboard.")
    b = html.find(ANCHOR_END, a)
    if b < 0:
        raise SystemExit("[ABORT] ancora ';<nl>/* END RANK */' ausente apos const RANK.")
    return a, b

def atomic_write(path, content):
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try: os.remove(tmp)
        except OSError: pass
        raise
    back = path.read_bytes()
    if b"\x00" in back:
        raise SystemExit(f"[ABORT] NUL apos escrita de {path}.")
    for m in REQUIRED:
        if m not in back:
            raise SystemExit(f"[ABORT] marcador {m!r} ausente apos escrita de {path}.")
    path.with_suffix(path.suffix + ".md5").write_text(hashlib.md5(back).hexdigest(), encoding="utf-8")

def main():
    argv = sys.argv[1:]
    html_path = dashboard_path()
    healed = read_bytes_healed(html_path)
    rank, gen = build_rank()
    a, b = locate(healed)
    new_literal = json.dumps(rank, ensure_ascii=False).encode("utf-8")
    new_html = healed[:a + len(ANCHOR_START)] + new_literal + healed[b:]

    if "--verify" in argv:
        drift = healed[a + len(ANCHOR_START):b] != new_literal
        print(f"[verify] RANK itens={len(rank)} drift={drift}")
        sys.exit(1 if drift else 0)

    if "--dry" in argv:
        out = Path(argv[argv.index("--dry") + 1]); out.mkdir(parents=True, exist_ok=True)
        atomic_write(out / html_path.name, new_html)
        print(f"[dry] {out / html_path.name} | RANK itens={len(rank)}")
        return

    stamp = datetime.date.today().isoformat()
    atomic_write(html_path.with_suffix(f".backup-{stamp}.html"), healed)
    atomic_write(html_path, new_html)
    print(f"[dashboard_rank] {html_path.name} | RANK itens={len(rank)} (candidates {gen})")

if __name__ == "__main__":
    main()
