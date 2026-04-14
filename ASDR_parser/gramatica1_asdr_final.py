#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import time
import os
import matplotlib

TOKEN_SPEC = [
    ("dos", "dos"),
    ("tres", "tres"),
    ("cuatro", "cuatro"),
    ("cinco", "cinco"),
    ("seis", "seis"),
    ("uno", "uno"),
]
TOKEN_RE = re.compile("|".join(rf"(?P<{n}>\b{p}\b)" for n, p in TOKEN_SPEC))


def tokenizar(t):
    return [(m.lastgroup, m.group()) for m in TOKEN_RE.finditer(t)]


class Nodo:
    def __init__(self, e):
        self.etiqueta = e
        self.hijos = []

    def agregar(self, h):
        self.hijos.append(h)
        return h


class Parser:
    def __init__(self, toks):
        self.tokens = toks
        self.pos = 0

    def tok(self):
        return self.tokens[self.pos][0] if self.pos < len(self.tokens) else "$"

    def match(self, esperado):
        if self.tok() == esperado:
            self.pos += 1
        else:
            raise SyntaxError(
                f"Esperaba '{esperado}', llegó '{self.tok()}' en posición {self.pos}"
            )

    # S -> dos B_P tres B_P C | uno A E E | B_P S_R
    def parse_S(self, p):
        n = p.agregar(Nodo("S"))
        t = self.tok()

        if t == "dos":
            n.agregar(Nodo("dos"))
            self.match("dos")
            self.parse_BP(n)
            n.agregar(Nodo("tres"))
            self.match("tres")
            self.parse_BP(n)
            self.parse_C(n)

        elif t == "uno":
            n.agregar(Nodo("uno"))
            self.match("uno")
            self.parse_A(n)
            self.parse_E(n)
            self.parse_E(n)

        elif t in ("$", "cuatro", "seis", "tres"):
            self.parse_BP(n)
            self.parse_SR(n)

        else:
            raise SyntaxError(f"Error en S con token '{t}'")

    # S_R -> C | E
    def parse_SR(self, p):
        n = p.agregar(Nodo("S_R"))
        t = self.tok()

        if t in ("$", "seis"):
            self.parse_C(n)
        elif t == "tres":
            self.parse_E(n)
        else:
            raise SyntaxError(f"Error en S_R con token '{t}'")

    # A -> dos B_P tres | eps
    def parse_A(self, p):
        n = p.agregar(Nodo("A"))
        t = self.tok()

        if t == "dos":
            n.agregar(Nodo("dos"))
            self.match("dos")
            self.parse_BP(n)
            n.agregar(Nodo("tres"))
            self.match("tres")
        elif t in ("$", "cinco", "cuatro", "tres"):
            n.agregar(Nodo("ε"))
        else:
            raise SyntaxError(f"Error en A con token '{t}'")

    # B_P -> cuatro C cinco B_P | eps
    def parse_BP(self, p):
        n = p.agregar(Nodo("B_P"))
        t = self.tok()

        if t == "cuatro":
            n.agregar(Nodo("cuatro"))
            self.match("cuatro")
            self.parse_C(n)
            n.agregar(Nodo("cinco"))
            self.match("cinco")
            self.parse_BP(n)
        elif t in ("$", "cinco", "seis", "tres"):
            n.agregar(Nodo("ε"))
        else:
            raise SyntaxError(f"Error en B_P con token '{t}'")

    # C -> seis A B_P | eps
    def parse_C(self, p):
        n = p.agregar(Nodo("C"))
        t = self.tok()

        if t == "seis":
            n.agregar(Nodo("seis"))
            self.match("seis")
            self.parse_A(n)
            self.parse_BP(n)
        elif t in ("$", "cinco"):
            n.agregar(Nodo("ε"))
        else:
            raise SyntaxError(f"Error en C con token '{t}'")

    # E -> tres
    def parse_E(self, p):
        n = p.agregar(Nodo("E"))
        t = self.tok()

        if t == "tres":
            n.agregar(Nodo("tres"))
            self.match("tres")
        else:
            raise SyntaxError(f"Error en E con token '{t}'")

    def parsear(self):
        raiz = Nodo("ROOT")
        try:
            self.parse_S(raiz)
            if self.tok() != "$":
                raise SyntaxError(f"Tokens sobrantes: '{self.tok()}'")
            return True, raiz.hijos[0] if raiz.hijos else raiz
        except SyntaxError:
            return False, raiz.hijos[0] if raiz.hijos else raiz


def calc_pos(n, p=0, c=None):
    if c is None:
        c = [0]
    if not n.hijos:
        n._x = c[0]
        n._y = -p
        c[0] += 1
        return
    for h in n.hijos:
        calc_pos(h, p + 1, c)
    n._x = sum(h._x for h in n.hijos) / len(n.hijos)
    n._y = -p


def draw(n, ax):
    eps = n.etiqueta in ("ε", "eps")
    hoja = not n.hijos
    col = "#FF6B6B" if eps else ("#4ECDC4" if hoja else "#45B7D1")

    for h in n.hijos:
        ax.plot([n._x, h._x], [n._y, h._y], color="#888", lw=1, zorder=1)
        draw(h, ax)

    ax.add_patch(
        matplotlib.patches.Circle(
            (n._x, n._y), 0.35, color=col, zorder=2, ec="white", lw=1.5
        )
    )
    ax.text(
        n._x,
        n._y,
        n.etiqueta,
        ha="center",
        va="center",
        fontsize=7 if len(n.etiqueta) > 5 else 8,
        color="white",
        fontweight="bold",
        zorder=3,
    )


def mostrar_arbol(raiz, expr, ok):
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mp
    except:
        print("  (instalar matplotlib)")
        return

    calc_pos(raiz)
    todos = []

    def recoger(n):
        todos.append(n)
        for h in n.hijos:
            recoger(h)

    recoger(raiz)

    xs = [n._x for n in todos]
    ys = [n._y for n in todos]

    fig, ax = plt.subplots(
        figsize=(max(10, (max(xs) - min(xs) + 2) * 0.65), max(6, (max(ys) - min(ys) + 2) * 1.1))
    )
    ax.set_aspect("equal")
    ax.axis("off")
    draw(raiz, ax)

    estado = "ACEPTADA" if ok else "RECHAZADA"
    ax.set_title(
        f'"{expr}"  →  {estado}',
        fontsize=12,
        fontweight="bold",
        color="#2ecc50" if ok else "#e74c3c",
        pad=14,
    )
    ax.legend(
        handles=[
            mp.Patch(color="#45B7D1", label="No terminal"),
            mp.Patch(color="#4ECDC4", label="Terminal"),
            mp.Patch(color="#FF6B6B", label="epsilon (vacío)"),
        ],
        loc="upper right",
        fontsize=8,
    )

    ax.set_xlim(min(xs) - 1, max(xs) + 1)
    ax.set_ylim(min(ys) - 1, 1.5)
    plt.tight_layout()

    os.makedirs("Outputs", exist_ok=True)
    nom = re.sub(r"[^a-zA-Z0-9]", "_", expr)[:30]
    fname = f"Outputs/G1_{nom}{str(time.time())[-4:]}.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Árbol: {fname}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python gramatica1_asdr_final.py <entrada.txt>")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        lineas = f.read().splitlines()

    for linea in lineas:
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        ok, arbol = Parser(tokenizar(linea)).parsear()
        print(f'{"ACEPTADA" if ok else "RECHAZADA"}  "{linea}"')
        mostrar_arbol(arbol, linea, ok)