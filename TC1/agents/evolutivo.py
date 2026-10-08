"""Algoritmo genético

Tenemos una lista de pesos, entonces a cada celda de opción (las vacías)
les calculamos unos features, los multiplicamos por los pesos generados
y ponemos la ficha en la celda con el mejor puntaje

El criterio es primero las fichas colocadas y después las celdas que quedan vacías
y se seleccionan las mejores a las cuales se les hace una mezcla de los padres
y una mutación gaussiana (distribución normal y al azar)

Nos quedamos con los mejores entre padres e hijos y paramos cuando se acaba el tiempo o cuando ya no se puede mejorar.

"""

import math
import random
import time
from dataclasses import dataclass
from typing import List, NamedTuple, Optional, Tuple

from tileup import Instance
from tileup.engine import EMPTY, neighbors_table

from . import AgentResult

WALL = 255  # ficha de un color que ya no vuelve a salir

FEATURES = (
    "mismo_color",          # cuántos vecinos son del mismo color
    "otro_pronto",          # vecinos de otro color que va a salir pronto
    "otro_tarde",           # vecinos de otro color que no sale pronto
    "borde_o_pared",        # lados que tocan el borde del tablero o una pared
    "ultimo_hueco",         # fichas vecinas que se quedarían encerradas
    "dist_centro",          # qué tan lejos está la celda del centro
    "deja_huecos",          # si el color vuelve pronto, cuánto espacio le queda
    "libera_huecos",        # si se fusiona, a cuántas fichas les abre espacio
)
NUM_FEATURES = len(FEATURES)


@dataclass
class Params:
    population: int = 30       # cuántos individuos hay en la población
    tournament: int = 3        # cuántos compiten en cada torneo
    p_cross: float = 0.9       # probabilidad de cruzar dos padres
    sigma: float = 0.2         # qué tan grande es la mutación
    window: int = 10           # cuántas fichas hacia adelante cuentan como "pronto"


class Individual(NamedTuple):
    fitness: Tuple[int, int]   
    weights: List[float]
    moves: List[int]           


class _Context:

    def __init__(self, instance: Instance, window: int):
        side = instance.n
        self.num_cells = side * side
        self.neighbors = neighbors_table(side)
        self.colors = [tile.color for tile in instance.tiles]
        self.num_tiles = len(self.colors)
        # is_last[i] dice si la ficha i es la última de su color
        last_index = {}
        for index, color in enumerate(self.colors):
            last_index[color] = index
        self.is_last = [last_index[color] == index for index, color in enumerate(self.colors)]
        self.window = window
        # cuántos lados de cada celda dan al borde
        self.border_sides = [4 - len(self.neighbors[cell]) for cell in range(self.num_cells)]
        # distancia de cada celda al centro
        center = (side - 1) / 2
        max_distance = max(1e-9, math.hypot(center, center))
        self.center_distance = [
            math.hypot(cell // side - center, cell % side - center) / max_distance
            for cell in range(self.num_cells)
        ]


def _normalize(weights: List[float]) -> List[float]:
    length = math.sqrt(sum(weight * weight for weight in weights)) or 1.0
    return [weight / length for weight in weights]


def features(context: _Context, board: bytearray, cell: int, color: int, upcoming_colors: set) -> Tuple:
    """Calcula los features de poner una ficha de color `color` en la celda `cell`
    """
    same_color = other_soon = other_later = trapped = freed_spaces = empty_neighbors = 0
    edge_or_wall = context.border_sides[cell]
    for neighbor in context.neighbors[cell]:
        neighbor_color = board[neighbor]
        if neighbor_color == EMPTY:
            empty_neighbors += 1
        elif neighbor_color == color:
            # mismo color: se fusiona y la anterior queda vacía
            # se ve a cuántas fichas que salen pronto les sirve ese espacio nuevo
            same_color += 1
            freed_spaces += sum(1 for around in context.neighbors[neighbor]
                                if board[around] != color and board[around] in upcoming_colors)
        elif neighbor_color == WALL:
            edge_or_wall += 1
        else:
            # otro color
            if neighbor_color in upcoming_colors:
                other_soon += 1
            else:
                other_later += 1
            # si cell es el único espacio vacío al lado
            if sum(1 for around in context.neighbors[neighbor] if board[around] == EMPTY) == 1:
                trapped += 1
    # el espacio libre alrededor solo importa si el color vuelve a salir
    space_left = empty_neighbors if color in upcoming_colors else 0
    return (same_color, other_soon, other_later, edge_or_wall, trapped,
            context.center_distance[cell], space_left, freed_spaces)


def _place(context: _Context, board: bytearray, cell: int, color: int, is_last: bool) -> int:
    """Pone la ficha de color en la celda y hace la fusión """
    merged = 0
    for neighbor in context.neighbors[cell]:
        if board[neighbor] == color:
            board[neighbor] = EMPTY
            merged += 1
    board[cell] = color
    if is_last:
        # este color ya no sale más, entonces sus fichas son como paredes
        for other_cell in range(context.num_cells):
            if board[other_cell] == color:
                board[other_cell] = WALL
    return merged


def decode(context: _Context, weights: List[float]) -> Tuple[List[int], int, int]:
    """Juega una partida completa usando los pesos.

    Devuelve las jugadas, las celdas ocupadas al final y la suma de las
    ocupadas en cada paso.
    """
    board = bytearray(context.num_cells)
    occupied = occupied_sum = 0
    moves = []
    for index, color in enumerate(context.colors):
        if occupied == context.num_cells:
            break  # tablero lleno y todavía quedan fichas (ya perdimos)
        upcoming_colors = set(context.colors[index + 1:index + 1 + context.window])

        def score(cell):
            cell_features = features(context, board, cell, color, upcoming_colors)
            return sum(weight * value for weight, value in zip(weights, cell_features))

        empty_cells = (cell for cell in range(context.num_cells) if board[cell] == EMPTY)
        best_cell = max(empty_cells, key=score)
        occupied += 1 - _place(context, board, best_cell, color, context.is_last[index])
        occupied_sum += occupied
        moves.append(best_cell)
    return moves, occupied, occupied_sum


class _Timeout(Exception):
    pass


def solve(instance: Instance, seed: int, deadline: float, params: Optional[Params] = None) -> AgentResult:
    params = params or Params()
    context = _Context(instance, params.window)
    rng = random.Random(seed)
    evaluations = 0
    
    best_possible = context.num_tiles * (context.num_cells + 1) - len(set(context.colors))

    def evaluate(weights):
        nonlocal evaluations
        moves, occupied, occupied_sum = decode(context, weights)
        evaluations += 1
        # una ficha más siempre vale más que tener menos celdas ocupadas
        score = len(moves) * (context.num_cells + 1) - occupied
        return Individual((score, -occupied_sum), weights, moves)

    def evaluate_in_time(weights):
        if time.perf_counter() > deadline:
            raise _Timeout
        return evaluate(weights)

    def random_weights():
        return _normalize([rng.gauss(0, 1) for _ in range(NUM_FEATURES)])

    def tournament(population):
        # escogemos algunos al azar y gana el que tenga mejor aptitud
        contestants = rng.sample(population, min(params.tournament, len(population)))
        return max(contestants, key=lambda individual: individual.fitness)

    def crossover(weights_a, weights_b):
        child = []
        for weight_a, weight_b in zip(weights_a, weights_b):
            margin = 0.5 * abs(weight_a - weight_b)
            low, high = min(weight_a, weight_b) - margin, max(weight_a, weight_b) + margin
            child.append(rng.uniform(low, high))
        return child

    def mutate(weights):
        return [weight + rng.gauss(0, params.sigma) if rng.random() < 1 / NUM_FEATURES else weight
                for weight in weights]

    greedy_weights = [1.0] + [0.0] * (NUM_FEATURES - 1)
    population = [evaluate(greedy_weights)]
    generations = 0
    try:
        population += [evaluate_in_time(random_weights()) for _ in range(params.population - 1)]
        population.sort(key=lambda individual: individual.fitness, reverse=True)
        while population[0].fitness[0] < best_possible:
            children = []
            for _ in range(params.population):
                parent_a, parent_b = tournament(population), tournament(population)
                if rng.random() < params.p_cross:
                    child_weights = crossover(parent_a.weights, parent_b.weights)
                else:
                    child_weights = list(parent_a.weights)
                children.append(evaluate_in_time(_normalize(mutate(child_weights))))
            # juntamos padres e hijos y nos quedamos con los mejores
            population = sorted(population + children,
                                key=lambda individual: individual.fitness,
                                reverse=True)[:params.population]
            generations += 1
    except _Timeout:
        pass
    best = population[0]

    return AgentResult(
        placements=best.moves,
        effort=evaluations,
        effort_name="evaluaciones_aptitud",
        extra={"generaciones": generations,
               "pesos": " ".join(f"{weight:.3f}" for weight in best.weights)},
    )
