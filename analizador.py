import os
import copy
from collections import OrderedDict

# Constantes
EPSILON = "eps"
ENDMARK = "$"


# 1. PARSEO DE GRAMÁTICA


def analizar_gramatica(grammar_text):
    grammar = OrderedDict()
    lines = grammar_text.strip().splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"): continue
        if "->" not in line: continue
        left, right = line.split("->", 1)
        left = left.strip()
        productions = [alt.strip().split() for alt in right.split("|")]
        grammar.setdefault(left, []).extend(productions)
    return grammar


# 2. ALGORITMO DE NORMALIZACIÓN 


def eliminar_recursividad_directa(grammar, nt):
    prods = grammar[nt]
    recursivas = [p for p in prods if p[0] == nt]
    no_recursivas = [p for p in prods if p[0] != nt]

    if not recursivas:
        return grammar, False

    nt_prime = f"{nt}_P"

    # CORRECCIÓN 1: Si la producción es epsilon, se reemplaza por el NT prima solo
    nuevas_no_rec = []
    for p in no_recursivas:
        if p == [EPSILON]:
            nuevas_no_rec.append([nt_prime])
        else:
            nuevas_no_rec.append(p + [nt_prime])

    grammar[nt] = nuevas_no_rec if nuevas_no_rec else [[nt_prime]]
    
    # El NT prima lleva la parte derecha de la recursiva + el prima
    grammar[nt_prime] = [p[1:] + [nt_prime] for p in recursivas]
    grammar[nt_prime].append([EPSILON])
    return grammar, True

def normalizar_gramatica(grammar):
    while True:
        gramatica_previa = copy.deepcopy(grammar)
        cambio_en_iteracion = False
        nts = list(grammar.keys())

        for i in range(len(nts)):
            ai = nts[i]
            for j in range(i):
                aj = nts[j]
                nuevas_prods = []
                for prod in grammar[ai]:
                    if prod[0] == aj:
                        cambio_en_iteracion = True
                        sufijo = prod[1:]
                        for delta in grammar[aj]:
                            # CORRECCIÓN 2: Evitar "eps + sufijo"
                            if delta == [EPSILON]:
                                if sufijo:
                                    nuevas_prods.append(sufijo)
                                else:
                                    nuevas_prods.append([EPSILON])
                            else:
                                nuevas_prods.append(delta + sufijo)
                    else:
                        nuevas_prods.append(prod)
                grammar[ai] = nuevas_prods
            
            grammar, hubo_cambio = eliminar_recursividad_directa(grammar, ai)
            if hubo_cambio:
                cambio_en_iteracion = True

        if not cambio_en_iteracion or grammar == gramatica_previa:
            break
            
    return grammar


# 3. CÁLCULO DE CONJUNTOS


def calcular_primeros(grammar):
    first = {nt: set() for nt in grammar}
    changed = True
    while changed:
        changed = False
        for nt, prods in grammar.items():
            for prod in prods:
                before = len(first[nt])
                if prod[0] == EPSILON:
                    first[nt].add(EPSILON)
                elif prod[0] not in grammar:
                    first[nt].add(prod[0])
                else:
                    for symbol in prod:
                        if symbol in grammar:
                            first[nt].update(first[symbol] - {EPSILON})
                            if EPSILON not in first[symbol]: break
                        else:
                            first[nt].add(symbol); break
                    else: first[nt].add(EPSILON)
                if len(first[nt]) > before: changed = True
    return first

def calcular_siguientes(grammar, first, start_symbol):
    follow = {nt: set() for nt in grammar}
    follow[start_symbol].add(ENDMARK)
    changed = True
    while changed:
        changed = False
        for nt, prods in grammar.items():
            for prod in prods:
                for i, symbol in enumerate(prod):
                    if symbol in grammar:
                        before = len(follow[symbol])
                        if i + 1 < len(prod):
                            next_s = prod[i+1]
                            if next_s in grammar:
                                follow[symbol].update(first[next_s] - {EPSILON})
                                if EPSILON in first[next_s]: follow[symbol].update(follow[nt])
                            else: follow[symbol].add(next_s)
                        else: follow[symbol].update(follow[nt])
                        if len(follow[symbol]) > before: changed = True
    return follow

def calcular_prediccion(grammar, first, follow):
    prediction = OrderedDict()
    for nt, prods in grammar.items():
        prediction[nt] = []
        for prod in prods:
            lookahead = set()
            if prod[0] == EPSILON:
                lookahead.update(follow[nt])
            elif prod[0] not in grammar:
                lookahead.add(prod[0])
            else:
                for sym in prod:
                    if sym in grammar:
                        lookahead.update(first[sym] - {EPSILON})
                        if EPSILON not in first[sym]: break
                    else:
                        lookahead.add(sym); break
                else: lookahead.update(follow[nt])
            prediction[nt].append({"prod": prod, "lookahead": lookahead})
    return prediction


# 4. IMPRESIÓN Y VALIDADOR LL(1)

def formatear_conjunto(symbols):
    return "{" + ", ".join(sorted(symbols)) + "}"


def imprimir_y_validar_ll1(grammar, first, follow, prediction):
    print("\n")
    print("GRAMÁTICA Luego de borrar recursividad")

    for nt, prods in grammar.items():
        print(f"{nt.ljust(10)} -> {' | '.join([' '.join(p) for p in prods])}")

    print("\n" + "="*60)
    print(f"{'No Terminal'.ljust(15)} {'Primeros'.ljust(25)} {'Siguientes'}")
    for nt in grammar:
        f_str = "{" + ", ".join(sorted(first[nt])) + "}"
        s_str = "{" + ", ".join(sorted(follow[nt])) + "}"
        print(f"{nt.ljust(15)} {f_str.ljust(25)} {s_str}")

    print("\n")
    print("CONJUNTOS DE PREDICCIÓN Y VALIDACIÓN LL(1)")
        
    es_ll1 = True
    for nt, rules in prediction.items():
        lookaheads_vistos = []
        for r in rules:
            p_str = " ".join(r['prod'])
            l_str = "{" + ", ".join(sorted(r['lookahead'])) + "}"
            print(f"P({nt} -> {p_str.ljust(15)}) = {l_str}")
            
            for previo in lookaheads_vistos:
                interseccion = r['lookahead'] & previo
                if interseccion:
                    es_ll1 = False
                    print(f"   [!] CONFLICTO: Intersección en {nt}: {interseccion}")
            lookaheads_vistos.append(r['lookahead'])

    print(f"RESULTADO FINAL: {'ES LL(1)' if es_ll1 else 'NO ES LL(1)'}")
    print("\n")
    return es_ll1



# 6. EJECUCIÓN 


def procesar_gramatica_completa(archivo_entrada):
    if not os.path.exists(archivo_entrada): return
    with open(archivo_entrada, "r", encoding="utf-8") as f: g_raw = analizar_gramatica(f.read())
    print("GRAMÁTICA ORIGINAL")
    for nt, prods in g_raw.items():
        print(f"{nt} -> {' | '.join([' '.join(p) for p in prods])}")
    print()
    g_final = normalizar_gramatica(g_raw)
    start_node = next(iter(g_final))
    primeros = calcular_primeros(g_final)
    siguientes = calcular_siguientes(g_final, primeros, start_node)
    prediccion = calcular_prediccion(g_final, primeros, siguientes)
    
    # 1. Mostrar resultados en consola
    es_ll1 = imprimir_y_validar_ll1(g_final, primeros, siguientes, prediccion)
    
    # 2. Informar resultado LL(1)
    if es_ll1:
        print("Gramatica ES LL(1)")
    else:
        print("NO es LL(1): puede generar ambiguedad")


if __name__ == "__main__":
    import sys
    archivo = sys.argv[1] if len(sys.argv) > 1 else "gramatica3.txt"
    procesar_gramatica_completa(archivo)