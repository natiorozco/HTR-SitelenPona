"""Agente de búsqueda: beam search anytime con heurística.

Formulación (detalle y justificación en el informe):
    - Estado: tablero (colores de cada celda) + índice de la próxima ficha.
      Los valores de las fichas no influyen en qué jugadas son legales ni en
      cuántas celdas quedan ocupadas, así que para detectar duplicados basta
      con los colores.
    - Sucesores: colocar la ficha actual en una celda vacía (motor.place).
    - Costo de una acción: cambio en celdas ocupadas = 1 - (vecinos del mismo
      color). La suma de costos de un camino es la ocupación final.
    - Meta: las M fichas colocadas. Entre metas, la de menor costo.
    - Evaluación: h(s) = ocupadas(s) + penalización por las próximas fichas
      cuyo color no tendrá dónde fusionarse (ver `heuristic`). No es admisible.

Beam search: se avanza por capas (todas las fichas colocadas en el mismo
orden), en cada capa se generan los hijos de los W mejores estados y se
conservan los W mejores según h. Se repite con W = 1, 2, 4, ... mientras quede
tiempo y se devuelve la mejor partida encontrada.
"""

import random
import time
from dataclasses import dataclass
from typing import List, Optional

from tileup import GameState, Instance, Status, result_key
from tileup.engine import EMPTY, neighbors_table

from . import AgentResult


@dataclass
class Params:
    branch: int = 8         # jugadas por estado que se expanden (las mejores según el orden local)
    lookahead: int = 8      # fichas futuras que mira la heurística
    decay: float = 0.85     # peso de la ficha futura j: decay**j
    max_width: int = 1 << 14


class _Node:
    __slots__ = ("state", "parent", "move")

    def __init__(self, state: GameState, parent: Optional["_Node"], move: Optional[int]):
        self.state = state
        self.parent = parent
        self.move = move

    def moves(self) -> List[int]:
        out = []
        node = self
        while node.parent is not None:
            out.append(node.move)
            node = node.parent
        out.reverse()
        return out


class _Timeout(Exception):
    def __init__(self, node: _Node):
        self.node = node


class _Counters:
    def __init__(self):
        self.expanded = 0
        self.generated = 0


# --------------------------------------------------------------- heurística
def heuristic(state: GameState, p: Params) -> float:
    """Ocupadas + estimación de cuántas de las próximas fichas no fusionarán.

    Un "hueco" de color c es una celda vacía vecina de alguna ficha de color c:
    la próxima ficha c puede fusionar ahí. Para cada color distinto entre las
    próximas `lookahead` fichas (solo su primera aparición, porque las
    siguientes pueden fusionar con ella) se suma:
        1                  si c no está en el tablero o no tiene huecos,
        1 / (1 + huecos)   si los tiene (con más huecos es menos probable
                           que otra ficha los bloquee antes).
    ponderado por decay**j según qué tan lejos está la ficha.
    """
    colors = state.colors
    nbrs = neighbors_table(state.n)
    spots = {}
    for i, c in enumerate(colors):
        if c == EMPTY:
            # cada celda vacía cuenta una sola vez por color vecino
            for cn in {colors[nb] for nb in nbrs[i]}:
                if cn != EMPTY:
                    spots[cn] = spots.get(cn, 0) + 1

    penalty = 0.0
    weight = 1.0
    seen_colors = set()
    j0 = state.next_index
    for tile in state.instance.tiles[j0:j0 + p.lookahead]:
        c = tile.color
        if c not in seen_colors:
            seen_colors.add(c)
            penalty += weight / (1 + spots.get(c, 0))
        weight *= p.decay
    return state.occupied + penalty


def ranked_moves(state: GameState, branch: int, rng: random.Random) -> List[int]:
    """Celdas vacías ordenadas por un criterio local barato; devuelve `branch`.

    Orden: 1) más vecinos del mismo color (fusión más grande),
           2) menos colores distintos vecinos (no tapar huecos de otros colores),
           3) menos vecinos vacíos (no fragmentar el espacio libre),
           4) desempate aleatorio derivado de la semilla.
    """
    c = state.current_tile().color
    colors = state.colors
    nbrs = neighbors_table(state.n)
    cand = []
    for i, ci in enumerate(colors):
        if ci != EMPTY:
            continue
        same = empties = 0
        others = set()
        for nb in nbrs[i]:
            cn = colors[nb]
            if cn == EMPTY:
                empties += 1
            elif cn == c:
                same += 1
            else:
                others.add(cn)
        cand.append((-same, len(others), empties, rng.random(), i))
    cand.sort()
    return [x[-1] for x in cand[:branch]]


# -------------------------------------------------------------- beam search
def _beam(instance: Instance, width: int, p: Params, rng: random.Random,
          deadline: float, cnt: _Counters):
    """Una pasada de beam search de ancho `width`.

    Devuelve (mejor nodo terminal, hubo_recorte). Si `hubo_recorte` es False,
    ninguna capa superó el ancho y ampliar W no cambiaría el resultado.
    Lanza _Timeout con el mejor nodo de la capa actual si se acaba el tiempo.
    """
    layer = [_Node(GameState(instance), None, None)]
    best_dead: Optional[_Node] = None
    truncated = False

    while layer:
        if layer[0].state.status() is Status.WON:
            return min(layer, key=lambda nd: nd.state.occupied), truncated

        children = {}
        for node in layer:
            if time.perf_counter() > deadline:
                raise _Timeout(layer[0])
            cnt.expanded += 1
            for mv in ranked_moves(node.state, p.branch, rng):
                child = node.state.after(mv)
                cnt.generated += 1
                if child.status() is Status.LOST:
                    if best_dead is None or child.placed > best_dead.state.placed:
                        best_dead = _Node(child, node, mv)
                    continue
                key = tuple(child.colors)
                if key not in children:
                    children[key] = (heuristic(child, p), rng.random(), _Node(child, node, mv))

        ranked = sorted(children.values(), key=lambda x: (x[0], x[1]))
        if len(ranked) > width:
            truncated = True
        layer = [x[2] for x in ranked[:width]]

    return best_dead, truncated


def _greedy_finish(node: _Node, rng: random.Random, deadline_hard: float) -> _Node:
    """Completa una partida parcial con la mejor jugada local en cada paso."""
    while not node.state.is_terminal() and time.perf_counter() < deadline_hard:
        mv = ranked_moves(node.state, 1, rng)[0]
        node = _Node(node.state.after(mv), node, mv)
    return node


def solve(instance: Instance, seed: int, deadline: float,
          params: Optional[Params] = None) -> AgentResult:
    p = params or Params()
    rng = random.Random(seed)
    cnt = _Counters()
    # Cota inferior de la ocupación final: cada color que aparece en la
    # secuencia deja al menos una ficha en el tablero (la fusión no la borra).
    lower_bound = len({t.color for t in instance.tiles})

    best: Optional[_Node] = None
    width = 1
    widths_done = 0
    while width <= p.max_width:
        try:
            node, truncated = _beam(instance, width, p, rng, deadline, cnt)
        except _Timeout as t:
            # Se usa el tiempo restante del margen para completar voraz.
            node = _greedy_finish(t.node, rng, deadline + 0.05)
            truncated = True
        else:
            widths_done += 1
        if node is not None and (best is None or result_key(node.state) > result_key(best.state)):
            best = node
        if time.perf_counter() > deadline:
            break
        if best.state.status() is Status.WON and best.state.occupied <= lower_bound:
            break  # óptimo demostrado
        if not truncated:
            break  # la búsqueda ya no recorta: ampliar W no cambia nada
        width *= 2

    return AgentResult(
        placements=best.moves(),
        effort=cnt.expanded,
        effort_name="nodos_expandidos",
        extra={"nodos_generados": cnt.generated, "ancho_max": width, "pasadas": widths_done},
    )
