"""Lectura de instancias de TileUp.

Formato (texto plano):
    - Se ignoran las líneas en blanco y las que empiezan con '#'.
    - Todo lo que sigue a un '#' dentro de una línea también es comentario.
    - Línea 1: N K
    - Línea 2: M
    - Siguientes M líneas: color valor
"""

from dataclasses import dataclass
from typing import List, Tuple


class InstanceError(Exception):
    """Instancia mal formada. El mensaje es legible para el usuario."""


@dataclass(frozen=True)
class Tile:
    color: int
    value: int


@dataclass(frozen=True)
class Instance:
    n: int                   # el tablero es n x n
    k: int                   # cantidad de colores (1..k)
    tiles: Tuple[Tile, ...]  # secuencia fija, en orden de colocación

    @property
    def m(self) -> int:
        return len(self.tiles)


def _meaningful_lines(text: str) -> List[Tuple[int, List[str]]]:
    """Devuelve (número de línea, tokens) quitando comentarios y líneas vacías."""
    out = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if line:
            out.append((lineno, line.split()))
    return out


def _ints(lineno: int, tokens: List[str], expected: int, what: str) -> List[int]:
    if len(tokens) != expected:
        raise InstanceError(
            f"línea {lineno}: se esperaban {expected} entero(s) ({what}), "
            f"se encontraron {len(tokens)}: {' '.join(tokens)!r}"
        )
    try:
        return [int(t) for t in tokens]
    except ValueError:
        raise InstanceError(
            f"línea {lineno}: valor no entero en {what}: {' '.join(tokens)!r}"
        ) from None


def parse_instance(text: str) -> Instance:
    lines = _meaningful_lines(text)
    if len(lines) < 2:
        raise InstanceError("la instancia debe tener al menos la línea 'N K' y la línea 'M'")

    lineno, toks = lines[0]
    n, k = _ints(lineno, toks, 2, "N K")
    if n < 1:
        raise InstanceError(f"línea {lineno}: N debe ser >= 1 (se leyó {n})")
    if k < 1:
        raise InstanceError(f"línea {lineno}: K debe ser >= 1 (se leyó {k})")

    lineno, toks = lines[1]
    (m,) = _ints(lineno, toks, 1, "M")
    if m < 0:
        raise InstanceError(f"línea {lineno}: M no puede ser negativo (se leyó {m})")

    tile_lines = lines[2:]
    if len(tile_lines) != m:
        raise InstanceError(
            f"se declararon M={m} fichas pero hay {len(tile_lines)} línea(s) de fichas"
        )

    tiles = []
    for lineno, toks in tile_lines:
        c, v = _ints(lineno, toks, 2, "color valor")
        if not 1 <= c <= k:
            raise InstanceError(f"línea {lineno}: color {c} fuera del rango 1..{k}")
        if v < 1:
            raise InstanceError(f"línea {lineno}: el valor debe ser positivo (se leyó {v})")
        tiles.append(Tile(c, v))

    return Instance(n, k, tuple(tiles))


def load_instance(path: str) -> Instance:
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        raise InstanceError(f"no se pudo leer la instancia '{path}': {e.strerror}") from None
    except UnicodeDecodeError:
        raise InstanceError(f"la instancia '{path}' no es texto UTF-8 válido") from None
    return parse_instance(text)
