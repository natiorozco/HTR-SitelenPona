"""Para las instancias de la comparación experimental

Se usa el generador previo para crear una instancia por cada configuración y semilla.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))   # para importar generador.py, el general

from generador import default_path, generate  

# (N, K, M): tablero N x N, K colores, M fichas
CONFIGS = [
    (5, 6, 150),     
    (8, 20, 400),   
    (4, 12, 150),    
    (6, 30, 300),   
    (8, 55, 500),    
    (10, 65, 800),   
]
SEEDS = [1, 2, 3]

OUT_DIR = os.path.join(HERE, "instancias")


def instance_name(n, k, m, seed):
    return os.path.basename(default_path(int(n), int(k), int(m), int(seed)))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for n, k, m in CONFIGS:
        for seed in SEEDS:
            path = os.path.join(OUT_DIR, instance_name(n, k, m, seed))
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(generate(n, k, m, seed))
    print(f"{len(CONFIGS) * len(SEEDS)} instancias en {OUT_DIR}")


if __name__ == "__main__":
    main()
