"""
Agente de búsqueda: DFS, podando con heurística

Es un DFS normal al que se le agregan tres cosas:
    - una heurística
    - un reloj
    - el registro de la mejor partida vista.

Estado  (colores de las N^2 celdas, i), donde i es el índice de la próxima ficha. 
          Como los valores no cambian la decisión, solo importan los colores
Hijos   Colocar la ficha i en cada celda vacía.
Costo   |G|, el tamaño de la componente fusionada. También se busca minimizar la cantidad de fichas ocupadas.
Meta    i == M. Si hay empate, la de menor costo.

Heurística laxa: h(s) = max(0, o + p - N^2 - 4*A(i))
    - o: celdas ocupadas
    - p: fichas pendientes
    - A(i): cantidad de fichas pendientes que se pueden unir
Siempre es menor o igual al total de las celdas ocupadas finales y por tanto ADMISIBLE.
h(s) > 0 marca un callejón sin salida y entonces se poda
"""

import time
from typing import List, Optional
from tileup import GameState, Instance
from . import Result

# Máximo de celdas que puede liberar una ficha p, al colocarla
# Como se pueden unir pares y no se apilan fusiones, realmente solo se pueden unir p con otras 4 fichas
MAX_FREED = 4


class Timeout(Exception):
    """Se agotó el tiempo límite; el agente devuelve lo que tenga mejor."""


def _mergeable_suffix(inst: Instance) -> List[int]:
    """
    suffix[i] = cuántas de las fichas con índice i..M-1 pueden fusionar.

    Una ficha solo fusiona si ya hay otra ficha del mismo color.
    Al colocarla siempre queda una ficha de ese color.
    """
    m = inst.m
    can_merge = [0] * m
    seen = set()
    for i, tile in enumerate(inst.tiles):
        can_merge[i] = 1 if tile.color in seen else 0
        seen.add(tile.color)

    suffix = [0] * (m + 1)
    for i in range(m - 1, -1, -1):
        suffix[i] = suffix[i + 1] + can_merge[i]
    return suffix


def solve(inst: Instance, deadline: float) -> Result:
    """Busca la mejor partida hasta el deadline (time.monotonic) y la devuelve."""
    m, cells = inst.m, inst.n * inst.n
    mergeable = _mergeable_suffix(inst)

    # estados ya explorados
    visited: set = set()
    expanded = 0

    # mejor partida final
    best_occupied: Optional[int] = None     
    best_win: List[int] = []

    # mejor partida no ganada (criterio: más fichas, luego menos ocupadas)
    partial: List[int] = []          
    partial_depth, partial_occupied = -1, 0
    # ¿terminó sin agotar el tiempo?
    exhausted = True

    def dfs(state: GameState, path: List[int]) -> None:
        nonlocal expanded, best_occupied, best_win, partial, partial_depth, partial_occupied, exhausted

        if time.monotonic() > deadline:
            exhausted = False
            raise Timeout()

        i = state.next_index
        occupied = state.occupied

        if i == m:                                   # goal test
            if best_occupied is None or occupied < best_occupied:
                best_occupied, best_win = occupied, list(path)
            return

        # actualizar estado parcial. todo estado alcanzado es legal y se puede usar si se queda sin tiempo
        if i > partial_depth or (i == partial_depth and occupied < partial_occupied):
            partial_depth, partial_occupied, partial = i, occupied, list(path)

        # heurística (explicada arriba)
        # solo empieza a podar cuando ha encontrado al menos 1 gane
        # si occupied + h no es mejor que el best_occupied, lo poda
        h = max(0, occupied + (m - i) - cells - MAX_FREED * mergeable[i])
        if best_occupied is not None and occupied + h >= best_occupied: return

        key = (i, tuple(state.colors))
        if key in visited: return       # estado repetido
        visited.add(key)
        expanded += 1

        # orden greedy: primero las jugadas que liberan más espacio
        children = []
        for cell in state.legal_actions():
            child = state.copy()
            g = child.place(cell)
            children.append((g, cell, child))
        children.sort(key=lambda t: (-t[0], t[1]))

        # ir por cada hijo
        for _, cell, child in children:
            dfs(child, path + [cell])

    try: dfs(GameState(inst), [])
    except Timeout: pass

    return Result(
        best_win if best_occupied is not None else partial,
        expanded,
        "nodos_expandidos",
        {"completo": exhausted}
    )