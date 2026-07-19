#!/usr/bin/env python3
"""_config.py — carrega config.json (identidade do usuario, semeada pelo onboarding docs/SETUP.md).
Sem config.json valido, o engine para com instrucao clara. stdlib-only."""
import os, json

def base_dir():
    return os.environ.get("NEXUS_BASE") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def config_path():
    return os.path.join(base_dir(), "config.json")

def load_config():
    p = config_path()
    if not os.path.exists(p):
        raise SystemExit(
            "ABORT: config.json ausente. Rode a entrevista de onboarding (docs/SETUP.md) para gerar sua "
            "config, ou copie config.example.json para config.json e edite.")
    raw = open(p, "rb").read().rstrip(b"\x00")
    if b"\x00" in raw:
        raise SystemExit("ABORT: config.json com NUL no miolo (corrupcao).")
    return normalize(json.loads(raw.decode("utf-8")))

def normalize(cfg):
    cols = cfg.get("collections", [])
    known_order = [c["name"] for c in cols]
    saved_ids = {c["name"]: c.get("saved_collection_id") for c in cols
                 if c.get("source", "instagram") == "instagram" and c.get("saved_collection_id")}
    source_map = {c["name"]: c.get("source", "instagram") for c in cols
                  if c.get("source", "instagram") != "instagram"}
    url_map = {c["name"]: c.get("url") for c in cols if c.get("url")}
    canon_terms, alias_to_canon, dest_axes = [], {}, {}
    personal_project = None
    for p in cfg.get("projects_canon", []):
        term, axis = p["term"], p.get("axis", "")
        dest_axes[term] = axis
        canon_terms.append(term); alias_to_canon[term] = term
        for al in p.get("aliases", []):
            canon_terms.append(al); alias_to_canon[al] = term
        if axis == "personal" and personal_project is None:
            personal_project = term
    return {
        "account": cfg.get("account", ""),
        "known_order": known_order, "saved_ids": saved_ids, "source_map": source_map,
        "url_map": url_map,
        "ig_url_template": cfg.get("instagram_saved_url_template",
                                   "https://www.instagram.com/{account}/saved/{name}/{saved_collection_id}/"),
        "canon_terms": canon_terms, "alias_to_canon": alias_to_canon,
        "destination_axes": dest_axes, "personal_project": personal_project,
        "dashboard_file": cfg.get("dashboard_file", "DASHBOARD.html"),
    }
