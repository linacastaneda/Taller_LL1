"""
ASDR — Gramática 3
Gramática transformada (recursividad directa en S eliminada):
  S   -> A B C S_P
  S_P -> uno S_P | eps
  A   -> dos B C | eps
  B   -> C tres | eps
  C   -> cuatro B | eps

PRED usados en cada if/elif (sin backtracking):
  P(S  -> A B C S_P)    = {$,cuatro,dos,tres,uno}
  P(S_P-> uno S_P)      = {uno}
  P(S_P-> eps)          = {$}
  P(A  -> dos B C)      = {dos}
  P(A  -> eps)          = {$,cuatro,tres}
  P(B  -> C tres)       = {cuatro,tres}   ← conflicto con eps
  P(B  -> eps)          = {$,cuatro,tres,uno}
  P(C  -> cuatro B)     = {cuatro}        ← conflicto con eps
  P(C  -> eps)          = {$,cuatro,tres,uno}

Nota: Conflictos en B y C — la gramática NO es LL(1).
En los tokens conflictivos el ASDR toma la primera producción listada.
"""
import re, sys, time, os

TOKEN_SPEC = [
    ("cuatro","cuatro"),("dos","dos"),("tres","tres"),("uno","uno"),
]
TOKEN_RE = re.compile("|".join(rf"(?P<{n}>\b{p}\b)" for n,p in TOKEN_SPEC))

def tokenizar(t):
    return [(m.lastgroup,m.group()) for m in TOKEN_RE.finditer(t)]

class Nodo:
    def __init__(self,e): self.etiqueta=e; self.hijos=[]
    def agregar(self,h): self.hijos.append(h); return h

class Parser:
    def __init__(self,toks): self.tokens=toks; self.pos=0
    def tok(self):
        return self.tokens[self.pos][0] if self.pos<len(self.tokens) else '$'
    def match(self,exp):
        if self.tok()==exp: self.pos+=1
        else: raise SyntaxError(f"Esperaba '{exp}', llegó '{self.tok()}' pos {self.pos}")

    # S -> A B C S_P
    # PRED(S->A B C S_P) = {$,cuatro,dos,tres,uno}
    def parse_S(self,p):
        n=p.agregar(Nodo("S")); t=self.tok()
        if t in ('$','cuatro','dos','tres','uno'):
            self.parse_A(n); self.parse_B(n); self.parse_C(n); self.parse_SP(n)
        else: raise SyntaxError(f"Error S: '{t}'")

    # S_P -> uno S_P | eps
    # PRED(S_P->uno S_P) = {uno}
    # PRED(S_P->eps)     = {$}
    def parse_SP(self,p):
        n=p.agregar(Nodo("S'")); t=self.tok()
        if t=='uno':
            n.agregar(Nodo("uno")); self.match('uno')
            self.parse_SP(n)
        elif t=='$':
            n.agregar(Nodo("ε"))
        else: raise SyntaxError(f"Error S': '{t}'")

    # A -> dos B C | eps
    # PRED(A->dos B C) = {dos}
    # PRED(A->eps)     = {$,cuatro,tres}
    def parse_A(self,p):
        n=p.agregar(Nodo("A")); t=self.tok()
        if t=='dos':
            n.agregar(Nodo("dos")); self.match('dos')
            self.parse_B(n); self.parse_C(n)
        elif t in ('$','cuatro','tres'):
            n.agregar(Nodo("ε"))
        else: raise SyntaxError(f"Error A: '{t}'")

    # B -> C tres | eps
    # PRED(B->C tres) = {cuatro,tres}   — toma esta rama primero en tokens conflictivos
    # PRED(B->eps)    = {$,cuatro,tres,uno}
    def parse_B(self,p):
        n=p.agregar(Nodo("B")); t=self.tok()
        if t in ('cuatro','tres'):  # PRED(B->C tres) — primera rama en conflicto
            self.parse_C(n); n.agregar(Nodo("tres")); self.match('tres')
        elif t in ('$','uno'):      # solo PRED(B->eps) sin conflicto
            n.agregar(Nodo("ε"))
        else: raise SyntaxError(f"Error B: '{t}'")

    # C -> cuatro B | eps
    # PRED(C->cuatro B) = {cuatro}   — toma esta rama primero en tokens conflictivos
    # PRED(C->eps)      = {$,cuatro,tres,uno}
    def parse_C(self,p):
        n=p.agregar(Nodo("C")); t=self.tok()
        if t=='cuatro':             # PRED(C->cuatro B) — primera rama en conflicto
            n.agregar(Nodo("cuatro")); self.match('cuatro')
            self.parse_B(n)
        elif t in ('$','tres','uno'): # solo PRED(C->eps) sin conflicto
            n.agregar(Nodo("ε"))
        else: raise SyntaxError(f"Error C: '{t}'")

    def parsear(self):
        raiz=Nodo("ROOT")
        try:
            self.parse_S(raiz)
            if self.tok()!='$': raise SyntaxError(f"Tokens sobrantes: '{self.tok()}'")
            return True, raiz.hijos[0] if raiz.hijos else raiz
        except SyntaxError:
            return False, raiz.hijos[0] if raiz.hijos else raiz

# ── Árbol ──────────────────────────────────────────────────────────────────
def calc_pos(n, p=0, c=None):
    if c is None: c=[0]
    if not n.hijos: n._x=c[0]; n._y=-p; c[0]+=1; return
    for h in n.hijos: calc_pos(h,p+1,c)
    n._x=sum(h._x for h in n.hijos)/len(n.hijos); n._y=-p

def draw(n,ax):
    import matplotlib
    eps=n.etiqueta in("ε","eps"); hoja=not n.hijos
    col="#AB47BC" if eps else("#FF7043" if hoja else "#26A69A")
    for h in n.hijos:
        ax.plot([n._x,h._x],[n._y,h._y],color="#888",lw=1,zorder=1); draw(h,ax)
    ax.add_patch(matplotlib.patches.Circle((n._x,n._y),0.35,color=col,zorder=2,ec="white",lw=1.5))
    ax.text(n._x,n._y,n.etiqueta,ha="center",va="center",
            fontsize=7 if len(n.etiqueta)>5 else 8,color="white",fontweight="bold",zorder=3)

def mostrar_arbol(raiz, expr, ok):
    try: import matplotlib.pyplot as plt; import matplotlib.patches as mp
    except: return
    calc_pos(raiz)
    todos=[]; recoger=lambda n:(todos.append(n),[recoger(h) for h in n.hijos]); recoger(raiz)
    xs=[n._x for n in todos]; ys=[n._y for n in todos]
    fig,ax=plt.subplots(figsize=(max(10,(max(xs)-min(xs)+2)*0.65),max(6,(max(ys)-min(ys)+2)*1.1)))
    ax.set_aspect("equal"); ax.axis("off"); draw(raiz,ax)
    estado="ACEPTADA" if ok else "RECHAZADA"
    ax.set_title(f'"{expr}"  →  {estado}',fontsize=12,fontweight="bold",
                 color="#2ecc50" if ok else "#e74c3c",pad=14)
    ax.legend(handles=[mp.Patch(color="#26A69A",label="No terminal"),
                        mp.Patch(color="#FF7043",label="Terminal"),
                        mp.Patch(color="#AB47BC",label="epsilon (vacío)")],
              loc="upper right",fontsize=8)
    ax.set_xlim(min(xs)-1,max(xs)+1); ax.set_ylim(min(ys)-1,1.5); plt.tight_layout()
    os.makedirs("Outputs",exist_ok=True)
    nom=re.sub(r"[^a-zA-Z0-9]","_",expr)[:30]
    fname=f"Outputs/G3_{nom}{str(time.time())[-4:]}.png"
    plt.savefig(fname,dpi=150,bbox_inches="tight"); plt.close(); print(f"  Árbol: {fname}")

if __name__=="__main__":
    if len(sys.argv)<2: print("Uso: python parser_gramatica3.py <entrada.txt>"); sys.exit(1)
    with open(sys.argv[1],encoding="utf-8") as f: lineas=f.read().splitlines()
    for linea in lineas:
        linea=linea.strip()
        if not linea or linea.startswith("#"): continue
        ok,arbol=Parser(tokenizar(linea)).parsear()
        print(f'{"ACEPTADA " if ok else "RECHAZADA"}  "{linea}"')
        mostrar_arbol(arbol,linea,ok)