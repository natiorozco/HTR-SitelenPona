"""Juego manual para probar el motor a mano.

Uso:  python jugar.py instances/ejemplo.txt
En cada turno escriba 'fila columna' (base cero). 'q' para salir.
"""

import sys

from tileup import GameState, IllegalMoveError, InstanceError, load_instance


def main():
    if len(sys.argv) != 2:
        print("uso: python jugar.py <instancia>")
        return 2
    try:
        inst = load_instance(sys.argv[1])
    except InstanceError as e:
        print(f"error: {e}")
        return 1

    g = GameState(inst)
    while not g.is_terminal():
        t = g.current_tile()
        print(f"\n{g.render()}\n")
        print(f"ficha {g.placed}/{inst.m}: color={t.color} valor={t.value}  "
              f"(ocupadas={g.occupied})")
        try:
            entrada = input("fila columna > ").strip().lstrip("﻿")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if entrada.lower() == "q":
            return 0
        try:
            r, c = map(int, entrada.split())
            fusionadas = g.place_rc(r, c)
        except ValueError:
            print("escriba dos enteros, p. ej. '0 1'")
            continue
        except IllegalMoveError as e:
            print(f"jugada ilegal: {e}")
            continue
        if fusionadas > 1:
            print(f"-> fusión de {fusionadas} fichas")

    print(f"\n{g.render()}\n")
    print(f"FIN: {g.status().value}  colocadas={g.placed} "
          f"ocupadas={g.occupied} mayor={g.max_value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
