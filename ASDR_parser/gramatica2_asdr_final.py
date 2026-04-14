#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ASDR — Gramática 2
Gramática transformada (recursividad indirecta eliminada):

S   -> B uno | dos C | eps
A   -> B uno tres B C | dos C tres B C | tres B C | cuatro A_P | A_P
A_P -> cinco C seis uno tres B C A_P | eps
B   -> A cinco C seis | eps
C   -> siete B | eps

Nota:
La gramática NO es LL(1), así que en los casos conflictivos
se resuelven decisiones manualmente en el parser.
"""

import re
import sys
import time
import os
import matplotlib

TOKEN_SPEC = [
    ("cinco", "cinco"),
    ("cuatro", "cuatro"),
    ("dos", "dos"),
    ("seis", "seis"),
    ("siete", "siete"),
    ("tres", "tres"),
    ("uno", "uno"),
]

TOKEN_RE = re.compile("|".join(rf"(?P<{n}>\b{p}\b)" for n, p in TOKEN_SPEC))


def tokenizar(texto):
    return [(m.lastgroup, m.group()) for m in TOKEN_RE.finditer(texto)]


class Nodo:
    def __init__(self, etiqueta):
        self.etiqueta = etiqueta
        self.hijos = []

    def agregar(self, hijo):
        self.hijos.append(hijo)
        return hijo


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
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

    # ======================================================
    # S -> B uno | dos C | eps
    # Resolución manual del conflicto:
    # - si empieza por 'dos', tomamos S -> dos C
    # - si empieza por cinco/cuatro/tres/uno, tomamos S -> B uno
    # - si está en $, tomamos eps
    # ======================================================
    def parse_S(self, p):
        n = p.agregar(Nodo("S"))
        t = self.tok()

        if t == "dos":
            n.agregar(Nodo("dos"))
            self.match("dos")
            self.parse_C(n)

        elif t in ("cinco", "cuatro", "tres", "uno"):
            self.parse_B(n)
            n.agregar(Nodo("uno"))
            self.match("uno")

        elif t == "$":
            n.agregar(Nodo("ε"))

        else:
            raise SyntaxError(f"Error en S con token '{t}'")

    # ======================================================
    # A -> B uno tres B C | dos C tres B C | tres B C | cuatro A_P | A_P
    # ======================================================
    def parse_A(self, p):
        n = p.agregar(Nodo("A"))
        t = self.tok()

        # Si empieza por dos, elegimos la rama explícita:
        # A -> dos C tres B C
        if t == "dos":
            n.agregar(Nodo("dos"))
            self.match("dos")
            self.parse_C(n)
            n.agregar(Nodo("tres"))
            self.match("tres")
            self.parse_B(n)
            self.parse_C(n)

        # Si empieza por tres, elegimos:
        # A -> tres B C
        elif t == "tres":
            n.agregar(Nodo("tres"))
            self.match("tres")
            self.parse_B(n)
            self.parse_C(n)

        # Si empieza por cuatro, elegimos:
        # A -> cuatro A_P
        elif t == "cuatro":
            n.agregar(Nodo("cuatro"))
            self.match("cuatro")
            self.parse_AP(n)

        # Si empieza por cinco o uno, usamos la rama A_P o la expansión vía B
        elif t in ("cinco", "uno"):
            # Para mantener coherencia con la gramática transformada,
            # cuando entra por uno/cinco usamos A_P.
            self.parse_AP(n)

        # Si llega un símbolo de seguimiento razonable, tomamos eps
        elif t in ("$", "seis", "siete"):
            n.agregar(Nodo("ε"))

        else:
            raise SyntaxError(f"Error en A con token '{t}'")

    # ======================================================
    # A_P -> cinco C seis uno tres B C A_P | eps
    # ======================================================
    def parse_AP(self, p):
        n = p.agregar(Nodo("A_P"))
        t = self.tok()

        if t == "cinco":
            n.agregar(Nodo("cinco"))
            self.match("cinco")
            self.parse_C(n)
            n.agregar(Nodo("seis"))
            self.match("seis")
            n.agregar(Nodo("uno"))
            self.match("uno")
            n.agregar(Nodo("tres"))
            self.match("tres")
            self.parse_B(n)
            self.parse_C(n)
            self.parse_AP(n)

        elif t in ("$", "seis", "siete", "tres", "uno"):
            n.agregar(Nodo("ε"))

        else:
            raise SyntaxError(f"Error en A_P con token '{t}'")

    # ======================================================
    # B -> A cinco C seis | eps
    # ======================================================
    def parse_B(self, p):
        n = p.agregar(Nodo("B"))
        t = self.tok()

        # Si empieza por símbolos que pueden arrancar A,
        # intentamos B -> A cinco C seis
        if t in ("cinco", "cuatro", "dos", "tres", "uno"):
            pos_inicial = self.pos
            hijos_iniciales = list(n.hijos)

            try:
                self.parse_A(n)
                n.agregar(Nodo("cinco"))
                self.match("cinco")
                self.parse_C(n)
                n.agregar(Nodo("seis"))
                self.match("seis")
            except SyntaxError:
                # retroceso manual a eps
                self.pos = pos_inicial
                n.hijos = hijos_iniciales
                n.agregar(Nodo("ε"))

        elif t in ("$", "seis", "siete"):
            n.agregar(Nodo("ε"))

        else:
            raise SyntaxError(f"Error en B con token '{t}'")

    # ======================================================
    # C -> siete B | eps
    # ======================================================
    def parse_C(self, p):
        n = p.agregar(Nodo("C"))
        t = self.tok()

        if t == "siete":
            n.agregar(Nodo("siete"))
            self.match("siete")
            self.parse_B(n)

        elif t in ("$", "cinco", "seis", "tres", "uno"):
            n.agregar(Nodo("ε"))

        else:
            raise SyntaxError(f"Error en C con token '{t}'")

    def parsear(self):
        raiz = Nodo("ROOT")
        try:
            self.parse_S(raiz)
            if self.tok() != "$":
                raise SyntaxError(f"Tokens sobrantes: '{self.tok()}'")
            return True, raiz.hijos[0] if raiz.hijos else raiz
        except (SyntaxError, RecursionError):
            return False, raiz.hijos[0] if raiz.hijos else raiz


# ======================================================
# DIBUJO DEL ÁRBOL
# ======================================================
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
    col = "#FF8A65" if eps else ("#81C784" if hoja else "#64B5F6")

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
            mp.Patch(color="#64B5F6", label="No terminal"),
            mp.Patch(color="#81C784", label="Terminal"),
            mp.Patch(color="#FF8A65", label="epsilon (vacío)"),
        ],
        loc="upper right",
        fontsize=8,
    )

    ax.set_xlim(min(xs) - 1, max(xs) + 1)
    ax.set_ylim(min(ys) - 1, 1.5)
    plt.tight_layout()

    os.makedirs("Outputs", exist_ok=True)
    nom = re.sub(r"[^a-zA-Z0-9]", "_", expr)[:30]
    fname = f"Outputs/G2_{nom}{str(time.time())[-4:]}.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Árbol: {fname}")


# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python gramatica2_asdr_final.py <entrada.txt>")
        sys.exit(1)

    sys.setrecursionlimit(500)

    with open(sys.argv[1], encoding="utf-8") as f:
        lineas = f.read().splitlines()

    for linea in lineas:
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        ok, arbol = Parser(tokenizar(linea)).parsear()
        print(f'{"ACEPTADA" if ok else "RECHAZADA"}  "{linea}"')
        mostrar_arbol(arbol, linea, ok)