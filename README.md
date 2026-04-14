# Informe - Taller ASDR (LL(1))

## 1. Introducción

El objetivo de este taller es analizar gramáticas libres de contexto con el fin de determinar si pueden ser procesadas mediante un Analizador Sintáctico Descendente Recursivo (ASDR) predictivo, el cual requiere que la gramática cumpla la condición LL(1).

Para ello, se implementó un programa que realiza transformaciones sobre las gramáticas y calcula los conjuntos necesarios para verificar dicha condición.

## 2. Metodología

Para cada gramática se realizaron los siguientes pasos:

1. Eliminación de recursividad izquierda
2. Cálculo de conjuntos de PRIMEROS
3. Cálculo de conjuntos de SIGUIENTES
4. Cálculo de conjuntos de PREDICCIÓN
5. Verificación de la condición LL(1)

Una gramática es LL(1) si los conjuntos de predicción de las producciones de un mismo no terminal son disjuntos.

## 3. Resultados

### Ejercicio 1

Se detectó un conflicto en el no terminal S, debido a la intersección en los conjuntos de predicción:

S → A B C  
S → D E  

Ambas producciones comparten símbolos en su predicción, lo que impide decidir la producción correcta con un solo símbolo de entrada.

Conclusión:  
La gramática no es LL(1)

---

### Ejercicio 2

Se encontraron múltiples conflictos en los no terminales S, A y B, debido a:

- Producciones anulables (ε)
- Dependencias entre no terminales
- Intersecciones en los conjuntos de predicción

Conclusión:  
La gramática no es LL(1)

---

### Ejercicio 3

Se identificaron conflictos en los no terminales B y C, donde:

C → cuatro B  
C → ε  

Ambas producciones contienen el símbolo cuatro en sus conjuntos de predicción.

Conclusión:  
La gramática no es LL(1)

---

## 4. Discusión

Aunque se aplicaron transformaciones como la eliminación de recursividad izquierda, los conflictos presentes en las gramáticas no se deben a prefijos comunes, sino a la interacción entre producciones anulables (ε) y los conjuntos FOLLOW.

Este tipo de conflictos no puede resolverse mediante factorización por la izquierda, por lo que no es posible transformar estas gramáticas a una forma LL(1) sin modificar su estructura original.

## 5. Conclusiones

- No todas las gramáticas pueden convertirse a LL(1) mediante transformaciones estándar.
- La condición LL(1) es estricta y requiere ausencia total de conflictos en los conjuntos de predicción.
- En los tres ejercicios analizados no se cumple dicha condición.
- Por lo tanto, no es posible construir un ASDR predictivo para estas gramáticas.

## 6. Observación adicional

Como alternativa, es posible implementar analizadores descendentes recursivos con backtracking, los cuales permiten manejar gramáticas no LL(1), aunque con mayor costo computacional.