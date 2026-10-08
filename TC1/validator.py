"""Validador independiente de soluciones de TileUp.

    python3 validator.py <instancia> <solución>

Reproduce la partida paso a paso y dice si la solución es legal. Informa por
terminal la cantidad de fichas colocadas y las celdas ocupadas al final.

Códigos de salida:
    0  la solución es legal
    1  la solución es ilegal, o algún archivo está mal formado
    2  uso incorrecto
"""

import sys
from typing import Dict, List, Sequence, Tuple

SUMMARY_FIELDS = ("colocadas", "ocupadas", "mayor")


class Invalid(Exception):
    """La solución no cumple las reglas, o un archivo está mal formado."""


# ----------------------------------------------------------------- lectura
def _read_text(path: str, what: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        raise Invalid(f"no se pudo leer {what} '{path}': {e.strerror}") from None
    except UnicodeDecodeError:
        raise Invalid(f"{what} '{path}' no es texto UTF-8 válido") from None


def _content_lines(text: str) -> List[Tuple[int, List[str]]]:
    """(número de línea, tokens) sin comentarios ni líneas en blanco.

    Se ignoran las líneas en blanco y todo lo que sigue a un '#', como en el
    formato de la instancia.
    """
    out = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        body = raw.split("#", 1)[0].strip()
        if body:
            out.append((lineno, body.split()))
    return out


# ----------------------------------------------------------------- instancia
def read_instance(path: str) -> Tuple[int, int, List[Tuple[int, int]]]:
    """Devuelve (N, K, [(color, valor), ...]) con las fichas en orden de colocación.

    Solo se rechaza lo que impide replayear la partida: archivos ilegibles, líneas
    que no son los enteros que pide el formato, un tablero de lado cero y una
    cantidad de fichas que no corresponde con el M declarado.
    """
    lines = _content_lines(_read_text(path, "la instancia"))
    if not lines:
        raise Invalid("la instancia está vacía")

    def want(pos: int, count: int, what: str) -> List[int]:
        if pos >= len(lines):
            raise Invalid(f"instancia incompleta: falta la línea de {what}")
        lineno, tokens = lines[pos]
        if len(tokens) != count:
            raise Invalid(f"línea {lineno}: se esperaban {count} entero(s) "
                          f"({what}) y hay {len(tokens)}")
        try:
            return [int(t) for t in tokens]
        except ValueError:
            raise Invalid(f"línea {lineno}: valor no entero en {what}") from None

    n, k = want(0, 2, "N K")
    if n < 1:
        raise Invalid(f"línea {lines[0][0]}: N debe ser >= 1 (se leyó {n})")
    (m,) = want(1, 1, "M")
    if len(lines) - 2 != m:
        raise Invalid(f"se declararon M={m} fichas pero hay {len(lines) - 2} línea(s) de fichas")

    tiles = []
    for pos in range(2, 2 + m):
        c, v = want(pos, 2, "color valor")
        tiles.append((c, v))
    return n, k, tiles


# ------------------------------------------------------------------ solución
def _parse_summary(raw: str, lineno: int) -> Dict[str, int]:
    """Lee las métricas declaradas en una línea de comentario.

    Solo se leen los tres campos que define el enunciado (colocadas, ocupadas,
    mayor). Cualquier otra clave se ignora, para que un agente que agregue
    métricas al resumen no quede fuera por eso.
    """
    out: Dict[str, int] = {}
    for part in raw.strip().lstrip("#").split():
        key, sep, value = part.partition("=")
        if not sep or key.strip() not in SUMMARY_FIELDS:
            continue
        key = key.strip()
        try:
            out[key] = int(value)
        except ValueError:
            raise Invalid(f"línea {lineno}: '{part}' no declara un entero") from None
    return out


def read_solution(path: str) -> Tuple[List[Tuple[int, int, int]], Dict[str, int]]:
    """Devuelve (jugadas, resumen declarado). Jugada = (índice, fila, columna).

    Se lee lo que haya: las líneas de comentario se ignoran, salvo por las
    métricas que declaran, y las jugadas se toman en el orden del archivo. El
    resumen es opcional y no tiene que ser la última línea; si está, se contrasta
    con la partida reproducida.
    """
    text = _read_text(path, "la solución")

    moves: List[Tuple[int, int, int]] = []
    declared: Dict[str, int] = {}
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            declared.update(_parse_summary(stripped, lineno))
            continue
        tokens = stripped.split()
        if len(tokens) != 3:
            raise Invalid(f"línea {lineno}: se esperaban 3 enteros "
                          "(índice fila columna) y hay {len(tokens)}")
        try:
            moves.append((int(tokens[0]), int(tokens[1]), int(tokens[2])))
        except ValueError:
            raise Invalid(f"línea {lineno}: valor no entero") from None

    return moves, declared


# --------------------------------------------------------------------- reglas
def replay(n: int, tiles: Sequence[Tuple[int, int]],
           moves: Sequence[Tuple[int, int, int]]) -> Dict[str, object]:
    """Aplica las reglas de TileUp desde el tablero vacío.

    Devuelve las métricas del final. Levanta Invalid en cuanto una jugada no
    cumple las reglas.
    """
    size = n * n
    color = [0] * size
    value = [0] * size
    occupied = 0
    pending = len(tiles)

    for expected, (index, row, col) in enumerate(moves):
        if pending == 0:
            raise Invalid(f"la solución propone más jugadas que fichas tiene la "
                          f"secuencia (M={len(tiles)}); la jugada {index} sobra")
        if index != expected:
            raise Invalid(f"las jugadas deben ir en orden y sin repetir: esperaba el "
                          f"índice {expected} y llegó {index}")
        if not (0 <= row < n and 0 <= col < n):
            raise Invalid(f"jugada {index}: la celda ({row}, {col}) está fuera "
                          f"del tablero {n}x{n}")
        if occupied == size:
            raise Invalid(f"jugada {index}: la partida ya terminó en derrota "
                          f"(tablero {n}x{n} lleno) y quedan {pending} ficha(s) "
                          f"pendiente(s), así que no hay jugada legal")
        p = row * n + col
        if color[p] != 0:
            raise Invalid(f"jugada {index}: la celda ({row}, {col}) ya está ocupada")

        c, v = tiles[expected]
        color[p], value[p] = c, v
        occupied += 1
        pending -= 1

        # G: componente conexa de fichas del mismo color que contiene p.
        group, stack = {p}, [p]
        while stack:
            q = stack.pop()
            f, c2 = divmod(q, n)
            for rf, rc in ((f - 1, c2), (f + 1, c2), (f, c2 - 1), (f, c2 + 1)):
                if not (0 <= rf < n and 0 <= rc < n):
                    continue
                j = rf * n + rc
                if j not in group and color[j] == c:
                    group.add(j)
                    stack.append(j)

        if len(group) >= 2:
            # |G| >= 2: se retiran las fichas de G y en p queda una del mismo
            # color con la suma de los valores. La fusión no encadena.
            total = sum(value[g] for g in group)
            for g in group:
                color[g] = value[g] = 0
            color[p], value[p] = c, total
            occupied -= len(group) - 1

    if pending == 0:
        estado = "victoria"
    elif occupied == size:
        estado = "derrota"        # queda al menos una ficha pendiente, tablero lleno
    else:
        estado = "en_curso"       # solución parcial: se agotó el tiempo del agente

    return {"colocadas": len(tiles) - pending,
            "ocupadas": occupied,
            "mayor": max(value),
            "estado": estado,
            "tablero": [tuple(color[i * n:(i + 1) * n]) for i in range(n)],
            "valores": [tuple(value[i * n:(i + 1) * n]) for i in range(n)]}


# ------------------------------------------------------------------- programa
def validate(instance_path: str, solution_path: str) -> Dict[str, object]:
    """Valida y devuelve las métricas de la partida reproducida.

    Levanta Invalid si alguna colocación viola las reglas, si la solución declara
    métricas que no cuadran o si algún archivo no se puede leer o replayear.
    """
    n, _k, tiles = read_instance(instance_path)
    moves, declared = read_solution(solution_path)
    metrics = replay(n, tiles, moves)

    for field, value in declared.items():
        if value != metrics[field]:
            raise Invalid(f"el resumen declara {field}={value} pero la partida "
                          f"termina con {field}={metrics[field]}")
    metrics["resumen"] = declared
    return metrics


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("uso: python3 validator.py <instancia> <solución>", file=sys.stderr)
        return 2

    instance, solution = argv
    try:
        metrics = validate(instance, solution)
    except Invalid as e:
        print(f"ILLEGAL {solution}: {e}", file=sys.stderr)
        return 1

    print(f"legal=True instancia={instance} solucion={solution}")
    print(f"estado={metrics['estado']}")
    for field in SUMMARY_FIELDS:
        print(f"{field}={metrics[field]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())