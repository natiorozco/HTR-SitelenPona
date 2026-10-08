"""Motor del juego TileUp.

Reglas (enunciado, sección 2):
    - Tablero N x N, inicialmente vacío.
    - En cada paso se toma la siguiente ficha de la secuencia y se coloca en
      cualquier celda vacía.
    - Sea p la celda recién ocupada y G la componente conexa (vecindad
      ortogonal) de fichas del mismo color que contiene a p. Si |G| >= 2, se
      retiran todas las fichas de G y en p queda una sola ficha de ese color
      con la suma de los valores. Si |G| = 1 no pasa nada más.
    - La fusión no encadena.
    - Victoria: se colocaron las M fichas.
      Derrota: queda al menos una ficha pendiente y no hay celdas vacías.

El motor no toma decisiones: solo expone el estado, las acciones legales y la
transición. Los agentes viven fuera de este paquete y lo usan como caja negra.

Representación: el tablero es plano, la celda (fila, col) tiene índice
fila * N + col. Una celda vacía tiene color 0 y valor 0.
"""

from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

from .instance import Instance

EMPTY = 0


class Status(Enum):
    IN_PROGRESS = "en_curso"
    WON = "victoria"
    LOST = "derrota"


class IllegalMoveError(Exception):
    """Se intentó una acción que las reglas no permiten."""


# Vecinos ortogonales precalculados por tamaño de tablero.
_NEIGHBORS_CACHE: Dict[int, Tuple[Tuple[int, ...], ...]] = {}


def neighbors_table(n: int) -> Tuple[Tuple[int, ...], ...]:
    table = _NEIGHBORS_CACHE.get(n)
    if table is None:
        rows = []
        for idx in range(n * n):
            r, c = divmod(idx, n)
            nb = []
            if r > 0:
                nb.append(idx - n)
            if r < n - 1:
                nb.append(idx + n)
            if c > 0:
                nb.append(idx - 1)
            if c < n - 1:
                nb.append(idx + 1)
            rows.append(tuple(nb))
        table = tuple(rows)
        _NEIGHBORS_CACHE[n] = table
    return table


class GameState:
    """Estado completo de una partida: tablero + posición en la secuencia.

    `place` modifica el estado en sitio; use `copy()` (barato) o `after()`
    cuando necesite conservar el estado anterior, p. ej. en una búsqueda.
    """

    __slots__ = ("instance", "n", "colors", "values", "next_index", "_empty", "_nbrs")

    def __init__(self, instance: Instance):
        self.instance = instance
        self.n = instance.n
        size = self.n * self.n
        self.colors: List[int] = [EMPTY] * size
        self.values: List[int] = [0] * size
        self.next_index = 0          # índice de la próxima ficha por colocar
        self._empty = size           # cantidad de celdas vacías
        self._nbrs = neighbors_table(self.n)

    # ------------------------------------------------------------------ copia
    def copy(self) -> "GameState":
        s = GameState.__new__(GameState)
        s.instance = self.instance
        s.n = self.n
        s.colors = self.colors[:]
        s.values = self.values[:]
        s.next_index = self.next_index
        s._empty = self._empty
        s._nbrs = self._nbrs
        return s

    # -------------------------------------------------------------- consultas
    @property
    def placed(self) -> int:
        """Cantidad de fichas colocadas hasta ahora."""
        return self.next_index

    @property
    def pending(self) -> int:
        return self.instance.m - self.next_index

    @property
    def empty_cells(self) -> int:
        return self._empty

    @property
    def occupied(self) -> int:
        return self.n * self.n - self._empty

    @property
    def max_value(self) -> int:
        return max(self.values, default=0)

    def current_tile(self):
        """Ficha que se coloca en el siguiente paso, o None si ya no quedan."""
        if self.next_index >= self.instance.m:
            return None
        return self.instance.tiles[self.next_index]

    def status(self) -> Status:
        if self.next_index >= self.instance.m:
            return Status.WON
        if self._empty == 0:
            return Status.LOST
        return Status.IN_PROGRESS

    def is_terminal(self) -> bool:
        return self.status() is not Status.IN_PROGRESS

    def legal_actions(self) -> List[int]:
        """Índices de celdas vacías (vacío si la partida terminó)."""
        if self.is_terminal():
            return []
        return [i for i, c in enumerate(self.colors) if c == EMPTY]

    def cell(self, row: int, col: int) -> Tuple[int, int]:
        """(color, valor) de la celda; (0, 0) si está vacía."""
        i = self.index(row, col)
        return self.colors[i], self.values[i]

    def index(self, row: int, col: int) -> int:
        if not (0 <= row < self.n and 0 <= col < self.n):
            raise IllegalMoveError(f"celda ({row}, {col}) fuera del tablero {self.n}x{self.n}")
        return row * self.n + col

    def coords(self, index: int) -> Tuple[int, int]:
        return divmod(index, self.n)

    def key(self) -> Tuple:
        """Clave hashable del estado (para conjuntos de visitados, memo, etc.)."""
        return (self.next_index, tuple(self.colors), tuple(self.values))

    # ------------------------------------------------------------- transición
    def component(self, index: int) -> List[int]:
        """Componente conexa ortogonal del mismo color que contiene `index`."""
        color = self.colors[index]
        if color == EMPTY:
            return []
        colors, nbrs = self.colors, self._nbrs
        seen = {index}
        stack = [index]
        while stack:
            cur = stack.pop()
            for nb in nbrs[cur]:
                if nb not in seen and colors[nb] == color:
                    seen.add(nb)
                    stack.append(nb)
        return list(seen)

    def place(self, index: int) -> int:
        """Coloca la ficha actual en la celda `index` y aplica la fusión.

        Devuelve el tamaño de la componente fusionada (1 si no hubo fusión).
        Lanza IllegalMoveError si la partida terminó o la celda no es válida.
        """
        if self.is_terminal():
            raise IllegalMoveError(f"la partida ya terminó ({self.status().value})")
        if not 0 <= index < self.n * self.n:
            raise IllegalMoveError(f"índice de celda {index} fuera del tablero")
        if self.colors[index] != EMPTY:
            r, c = self.coords(index)
            raise IllegalMoveError(f"la celda ({r}, {c}) está ocupada")

        tile = self.instance.tiles[self.next_index]
        self.colors[index] = tile.color
        self.values[index] = tile.value
        self._empty -= 1
        self.next_index += 1

        group = self.component(index)
        if len(group) >= 2:
            total = 0
            for g in group:
                total += self.values[g]
                self.colors[g] = EMPTY
                self.values[g] = 0
            self.colors[index] = tile.color
            self.values[index] = total
            self._empty += len(group) - 1
        return len(group)

    def place_rc(self, row: int, col: int) -> int:
        return self.place(self.index(row, col))

    def after(self, index: int) -> "GameState":
        """Versión funcional de `place`: devuelve un estado nuevo."""
        s = self.copy()
        s.place(index)
        return s

    # ---------------------------------------------------------------- display
    def render(self) -> str:
        """Tablero en texto: 'c:v' por celda, '.' si está vacía."""
        cells = [
            "." if self.colors[i] == EMPTY else f"{self.colors[i]}:{self.values[i]}"
            for i in range(self.n * self.n)
        ]
        width = max(len(x) for x in cells)
        rows = []
        for r in range(self.n):
            rows.append(" ".join(x.rjust(width) for x in cells[r * self.n:(r + 1) * self.n]))
        return "\n".join(rows)

    def __repr__(self) -> str:
        return (f"GameState(n={self.n}, colocadas={self.placed}/{self.instance.m}, "
                f"ocupadas={self.occupied}, estado={self.status().value})")


def new_game(instance: Instance) -> GameState:
    return GameState(instance)


def play(instance: Instance, placements: Sequence[int],
         stop_on_terminal: bool = True) -> GameState:
    """Reproduce una lista de índices de celda desde el tablero vacío.

    Si `stop_on_terminal` es True, deja de aplicar jugadas cuando la partida
    termina (útil p. ej. para decodificar individuos del agente evolutivo).
    Lanza IllegalMoveError si una jugada es ilegal.
    """
    state = GameState(instance)
    for idx in placements:
        if stop_on_terminal and state.is_terminal():
            break
        state.place(idx)
    return state


def summary(state: GameState) -> Dict[str, object]:
    return {
        "colocadas": state.placed,
        "ocupadas": state.occupied,
        "mayor": state.max_value,
        "estado": state.status().value,
    }


def result_key(state: GameState) -> Tuple[int, int]:
    """Orden del concurso sin el tiempo: más fichas, luego menos ocupadas.

    Mayor clave = mejor resultado, sirve directamente con max().
    """
    return (state.placed, -state.occupied)
