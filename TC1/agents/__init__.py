"""Agentes para TileUp. Usan el motor (`tileup`) sin modificar sus reglas.

Contrato de un agente:
    solve(instance, seed, deadline) -> AgentResult
donde `deadline` es un instante de time.perf_counter() a partir del cual el
agente debe dejar de buscar y devolver lo mejor que tenga.
"""

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List


@dataclass
class AgentResult:
    placements: List[int]            # índices de celda (fila * N + col), en orden
    effort: int                      # medida de esfuerzo propia del algoritmo
    effort_name: str                 # p. ej. "nodos_expandidos"
    extra: Dict[str, object] = field(default_factory=dict)


Result = AgentResult  # nombre que usa search.py


def _registry() -> Dict[str, Callable]:
    from . import evolutivo, search

    def busqueda(instance, seed, deadline):
        remaining = deadline - time.perf_counter()
        return search.solve(instance, time.monotonic() + remaining)

    return {"busqueda": busqueda, "evolutivo": evolutivo.solve}


AGENTS = _registry()
