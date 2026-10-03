"""Agentes para TileUp. Usan el motor (`tileup`) sin modificar sus reglas.

Contrato de un agente:
    solve(instance, seed, deadline) -> AgentResult
donde `deadline` es un instante de time.perf_counter() a partir del cual el
agente debe dejar de buscar y devolver lo mejor que tenga.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List


@dataclass
class AgentResult:
    placements: List[int]            # índices de celda (fila * N + col), en orden
    effort: int                      # medida de esfuerzo propia del algoritmo
    effort_name: str                 # p. ej. "nodos_expandidos"
    extra: Dict[str, object] = field(default_factory=dict)


def _registry() -> Dict[str, Callable]:
    from . import busqueda
    agents = {"busqueda": busqueda.solve}
    # Para registrar el agente evolutivo:
    #   from . import evolutivo
    #   agents["evolutivo"] = evolutivo.solve
    return agents


AGENTS = _registry()
