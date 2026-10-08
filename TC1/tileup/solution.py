"""Escritura del archivo de solución.

Una línea por colocación, en orden: `indice_ficha fila columna` (base cero).
Última línea: `# colocadas=X ocupadas=Y mayor=Z`.

La lectura/verificación de soluciones corresponde al validador, que debe ser
independiente; por eso aquí solo se escribe.
"""

from typing import Iterable, Tuple

from .engine import GameState


def format_solution(moves: Iterable[Tuple[int, int]], final_state: GameState) -> str:
    """`moves` son pares (fila, columna) en el orden en que se colocaron."""
    lines = [f"{i} {r} {c}" for i, (r, c) in enumerate(moves)]
    lines.append(
        f"# colocadas={final_state.placed} ocupadas={final_state.occupied} "
        f"mayor={final_state.max_value}"
    )
    return "\n".join(lines) + "\n"


def write_solution(path: str, moves: Iterable[Tuple[int, int]], final_state: GameState) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(format_solution(moves, final_state))
