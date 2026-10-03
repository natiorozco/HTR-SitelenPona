"""Motor del juego TileUp (IC-6200, Tarea Corta 1)."""

from .instance import Instance, InstanceError, Tile, load_instance, parse_instance
from .engine import (
    EMPTY,
    GameState,
    IllegalMoveError,
    Status,
    new_game,
    play,
    result_key,
    summary,
)
from .solution import format_solution, write_solution

__all__ = [
    "Instance", "InstanceError", "Tile", "load_instance", "parse_instance",
    "EMPTY", "GameState", "IllegalMoveError", "Status", "new_game", "play",
    "result_key", "summary", "format_solution", "write_solution",
]
