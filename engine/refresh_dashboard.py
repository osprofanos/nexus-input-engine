#!/usr/bin/env python3
"""
refresh_dashboard.py - re-embeda o bloco DATA do DASHBOARD a partir do cache.
Le SOMENTE _system/index.csv + _system/manifest.json (sem re-parsear fichas .md).
Preserva const RANK e o resto do <script> byte-a-byte. Mesmo hardening do build_index:
heal-on-read NUL, pre-condicao de consistencia (index_md5), atomic write +
read-back verify (NUL + ancoras), md5 sidecar, backup datado.
Uso:
  py -3.11 refresh_dashboard.py            # regrava DASHBOARD com DATA atualizado
  py -3.11 refresh_dashboard.py --verify   # so checa integridade (read-only, exit 1 em drift)
  py -3.11 refresh_dashboard.py --dry DIR  # preview em DIR (sem tocar no arquivo real)
"""
import csv, io, json, os, sys, tempfile, hashlib
from collections import OrderedDict

# KNOWN_ORDER + DESTINATION_AXES sao fonte unica do build_index: importar evita drift.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_index import KNOWN_ORDER, DESTINATION_AXES, CFG  # noqa: E402

BASE = os.environ.get("NEXUS_BASE") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYS  = os.path.join(BASE, "_system")
HTML = os.path.join(BASE, CFG["dashboard_file"])
INDEX_CSV = os.path.join(SYS, "index.csv")
MANIFEST  = os.path.join(SYS, "manifest.json")

ANCHOR_START = b"const DATA = "
ANCHOR_END   = b";\nconst RANK"
REQUIRED_SUFFIX_MARKERS = (b"const RANK", b"</html>")

def read_bytes_healed(path):
    raw = open(path, "rb").read()
    healed = raw.rstrip(b"\x00")
    nul_trailing = len(raw) - len(healed)
    nul_inside = healed.count(b"\x00")
    return raw, healed, nul_trailing, nul_inside

def read_csv_rows(path):
    raw, healed, nul_t, nul_i = read_bytes_healed(path)
    if nul_i:
        raise SystemExit("ABORT: %s tem %d NUL no miolo (corrupcao nao-trailing)." % (path, nul_i))
    text = healed.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader), nul_t

def read_manifest(path):
    raw, healed, nul_t, nul_i = read_bytes_healed(path)
    if nul_i:
        raise SystemExit("ABORT: %s tem %d NUL no miolo (corrupcao nao-trailing)." % (path, nul_i))
    return json.loads(healed.decode("utf-8")), nul_t

def compute_data(rows, manifest):
    # collections (ordenadas por KNOWN_ORDER): fichas + complete (status==done)
    collections = OrderedDict()
    matrix = OrderedDict()
    project_count = {}
    sem_destino = 0
    total_fichas = 0
    for c in KNOWN_ORDER:
        cr = [r for r in rows if r["collection"] == c]
        if not cr:
            continue
        fichas = len(cr)
        complete = sum(1 for r in cr if r["status"] == "done")
        collections[c] = {"fichas": fichas, "complete": complete}
        # matrix: contagem por projeto dentro da colecao (ordem = primeira aparicao no CSV)
        m = OrderedDict()
        for r in cr:
            projs = [p for p in (r["projects"] or "").split(";") if p]
            for p in projs:
                m[p] = m.get(p, 0) + 1
                project_count[p] = project_count.get(p, 0) + 1
        matrix[c] = m
        total_fichas += fichas
    for r in rows:
        if not (r["projects"] or "").strip():
            sem_destino += 1

    # ordem dos eixos = ordem de aparicao em DESTINATION_AXES (insercao)
    axis_order = []
    for p, ax in DESTINATION_AXES.items():
        if ax not in axis_order:
            axis_order.append(ax)
    # projects: agrupados por eixo (na ordem dos eixos), dentro de cada eixo ordenado por count desc, tie-break alfabetico
    projects = OrderedDict()
    for ax in axis_order:
        ax_projects = [(p, c) for p, c in project_count.items() if DESTINATION_AXES.get(p) == ax]
        ax_projects.sort(key=lambda x: (-x[1], x[0]))
        for p, c in ax_projects:
            projects[p] = c
    dest_axis = OrderedDict((p, DESTINATION_AXES.get(p, "")) for p in projects)
    axes = OrderedDict()
    for ax in axis_order:
        axes[ax] = sum(c for p, c in project_count.items() if DESTINATION_AXES.get(p) == ax)

    data = OrderedDict()
    data["generated_at"] = manifest.get("last_processed_at", "")
    data["total_fichas"] = total_fichas
    data["n_collections"] = len(collections)
    data["collections"] = collections
    data["projects"] = projects
    data["dest_axis"] = dest_axis
    data["axes"] = axes
    data["sem_destino"] = sem_destino
    data["matrix"] = matrix
    return data

def locate_anchors(html_bytes):
    a = html_bytes.find(ANCHOR_START)
    if a < 0:
        raise SystemExit("ABORT: ancora '%s' ausente no HTML (forma mudou)." % ANCHOR_START.decode())
    b = html_bytes.find(ANCHOR_END, a)
    if b < 0:
        raise SystemExit("ABORT: ancora '%s' ausente no HTML apos DATA." % ANCHOR_END.decode())
    return a, b

def render_html(html_healed, data):
    a, b = locate_anchors(html_healed)
    prefix = html_healed[:a + len(ANCHOR_START)]
    suffix = html_healed[b:]
    new_literal = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return prefix + new_literal + suffix

def atomic_write_verified(path, content_bytes):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content_bytes); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try: os.remove(tmp)
        except OSError: pass
        raise
    back = open(path, "rb").read()
    if back.count(b"\x00"):
        raise SystemExit("VERIFY FAIL: NUL em %s apos escrita (cloud-sync). Reexecute." % path)
    for marker in REQUIRED_SUFFIX_MARKERS:
        if marker not in back:
            raise SystemExit("VERIFY FAIL: marcador %r ausente apos escrita de %s." % (marker, path))
    md5 = hashlib.md5(back).hexdigest()
    open(path + ".md5", "w").write(md5)
    return md5

def parse_args(argv):
    args = {"verify": False, "dry": None}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--verify":
            args["verify"] = True
        elif a == "--dry":
            if i + 1 >= len(argv):
                raise SystemExit("ABORT: --dry exige DIR")
            args["dry"] = argv[i + 1]; i += 1
        else:
            raise SystemExit("ABORT: flag desconhecida %r" % a)
        i += 1
    return args

def main():
    args = parse_args(sys.argv[1:])

    # 1. Cache hardened-read
    manifest, m_nul = read_manifest(MANIFEST)
    rows, c_nul = read_csv_rows(INDEX_CSV)

    # 2. Pre-condicao: index.csv tem que bater com manifest.index_md5
    csv_md5 = hashlib.md5(open(INDEX_CSV, "rb").read().rstrip(b"\x00")).hexdigest()
    man_md5 = manifest.get("index_md5", "")
    if csv_md5 != man_md5:
        raise SystemExit(
            "ABORT: cache fora de sync — index.csv md5=%s, manifest.index_md5=%s. "
            "Rode `py -3.11 _system\\build_index.py` antes." % (csv_md5, man_md5))

    # 3. HTML hardened-read
    raw, healed, h_nul_t, h_nul_i = read_bytes_healed(HTML)
    if h_nul_i:
        raise SystemExit("ABORT: %s tem %d NUL no miolo (corrupcao nao-trailing) — nao seguro para swap." % (HTML, h_nul_i))

    # 4. Recompute DATA + render novo HTML (sem escrever ainda)
    data = compute_data(rows, manifest)
    new_html = render_html(healed, data)

    if args["verify"]:
        # Comparar DATA embedded vs DATA recomputado
        a, b = locate_anchors(healed)
        embedded_literal = healed[a + len(ANCHOR_START):b]
        try:
            embedded = json.loads(embedded_literal.decode("utf-8"))
        except Exception as e:
            print("VERIFY: HTML NUL_trail=%d NUL_inside=%d | DATA invalido: %s" % (h_nul_t, h_nul_i, e))
            print("RESULT: DRIFT/CORRUPCAO -> rodar refresh_dashboard.py")
            sys.exit(1)
        drift = embedded != json.loads(json.dumps(data))
        print("VERIFY: HTML size_raw=%d healed=%d NUL_trail=%d NUL_inside=%d | "
              "ancoras=OK | DATA_drift=%s | csv_rows=%d manifest_md5=OK" %
              (len(raw), len(healed), h_nul_t, h_nul_i, drift, len(rows)))
        bad = drift or h_nul_t or h_nul_i
        print("RESULT:", "DRIFT/CORRUPCAO -> rodar refresh_dashboard.py" if bad else "OK")
        sys.exit(1 if bad else 0)

    # 5. Backup datado + atomic write + read-back verify
    if args["dry"]:
        os.makedirs(args["dry"], exist_ok=True)
        out_path = os.path.join(args["dry"], os.path.basename(HTML))
        md5 = atomic_write_verified(out_path, new_html)
        print("[DRY] %s | size=%d | md5=%s" % (out_path, len(new_html), md5))
        return

    from datetime import date
    stamp = date.today().isoformat()
    backup = HTML.replace(".html", ".backup-%s.html" % stamp)
    # backup = snapshot DO ESTADO ATUAL (raw ou healed?). Usar healed para nao perpetuar NUL.
    if os.path.exists(HTML):
        atomic_write_verified(backup, healed)
    md5 = atomic_write_verified(HTML, new_html)
    note = []
    if h_nul_t: note.append("healed %d NUL trailing" % h_nul_t)
    if c_nul or m_nul: note.append("cache healed (csv=%d, manifest=%d NUL)" % (c_nul, m_nul))
    print("[WRITE] %s | size=%d | md5=%s%s" %
          (HTML, len(new_html), md5, " | " + "; ".join(note) if note else ""))
    print("backup -> %s" % backup)
    print("OK: read-back verify (NUL=0, marcadores presentes) + md5 sidecar")

if __name__ == "__main__":
    main()
