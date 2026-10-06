"""Generador de instancias de TileUp.

Uso:
    python generador.py N K M --semilla S [--valor-max V] [--salida ruta]

Produce un archivo en el formato de la especificación: comentarios con '#',
una línea "N K", una línea "M" y M líneas "color valor". Cada color se elige
uniformemente en 1..K y cada valor uniformemente en 1..V. Con los mismos
parámetros y la misma semilla el archivo es idéntico byte a byte.
"""

import argparse
import os
import random
import sys


def generate(n: int, k: int, m: int, seed: int, max_value: int = 9) -> str:
    """Devuelve el texto de la instancia."""
    rng = random.Random(seed)
    lines = [
        "# TileUp -- instancia generada",
        f"# N={n} K={k} M={m} semilla={seed} valor_max={max_value}",
        f"{n} {k}",
        f"{m}",
    ]
    for _ in range(m):
        lines.append(f"{rng.randint(1, k)} {rng.randint(1, max_value)}")
    return "\n".join(lines) + "\n"


def default_path(n: int, k: int, m: int, seed: int) -> str:
    return os.path.join("instances", f"gen_N{n}_K{k}_M{m}_s{seed}.txt")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generador de instancias de TileUp")
    ap.add_argument("N", type=int, help="lado del tablero (N x N)")
    ap.add_argument("K", type=int, help="cantidad de colores")
    ap.add_argument("M", type=int, help="cantidad de fichas en la secuencia")
    ap.add_argument("--semilla", type=int, required=True)
    ap.add_argument("--valor-max", type=int, default=9,
                    help="los valores se eligen en 1..valor-max (por defecto 9)")
    ap.add_argument("--salida", default=None,
                    help="ruta del archivo (por defecto instances/gen_N<N>_K<K>_M<M>_s<semilla>.txt)")
    args = ap.parse_args(argv)

    errores = []
    if args.N < 1:
        errores.append("N debe ser >= 1")
    if args.K < 1:
        errores.append("K debe ser >= 1")
    if args.M < 0:
        errores.append("M no puede ser negativo")
    if args.valor_max < 1:
        errores.append("--valor-max debe ser >= 1")
    if errores:
        for e in errores:
            print(f"error: {e}", file=sys.stderr)
        return 2

    salida = args.salida or default_path(args.N, args.K, args.M, args.semilla)
    try:
        carpeta = os.path.dirname(salida)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(salida, "w", encoding="utf-8", newline="\n") as f:
            f.write(generate(args.N, args.K, args.M, args.semilla, args.valor_max))
    except OSError as e:
        print(f"error: no se pudo escribir '{salida}': {e.strerror}", file=sys.stderr)
        return 1

    print(salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
