#!/usr/bin/env python3
"""_meta.py — identidade e assinatura do Nexus Input Engine (fonte unica de versao/atribuicao)."""
NAME = "Nexus Input Engine"
VERSION = "0.1.0"
AUTHOR = "Adan (@adanviajante)"
LICENSE = "Apache-2.0"

def banner() -> str:
    return f"{NAME} v{VERSION} — created by {AUTHOR}"

if __name__ == "__main__":
    print(banner())
