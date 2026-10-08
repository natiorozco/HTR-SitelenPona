import os
import random
import time
import unittest

from agents import AGENTS
from tileup import Instance, Status, Tile, load_instance, play

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(HERE, "..", "instances", "ejemplo.txt")

# Se prueba a través del registro, igual que lo llama main.py.
solve = AGENTS["busqueda"]


def random_instance(n, k, m, seed):
    r = random.Random(seed)
    return Instance(n, k, tuple(Tile(r.randint(1, k), r.randint(1, 9)) for _ in range(m)))


class TestAgenteBusqueda(unittest.TestCase):
    def test_resuelve_ejemplo_optimo(self):
        inst = load_instance(EXAMPLE)
        res = solve(inst, 1, time.perf_counter() + 5)
        g = play(inst, res.placements)  # lanza IllegalMoveError si hay jugadas ilegales
        self.assertEqual(g.status(), Status.WON)
        self.assertEqual(g.occupied, 3)  # cota inferior: 3 colores distintos
        self.assertGreater(res.effort, 0)

    def test_mismo_resultado_al_repetir(self):
        inst = random_instance(4, 5, 40, seed=3)
        a = solve(inst, 42, time.perf_counter() + 5)
        b = solve(inst, 42, time.perf_counter() + 5)
        self.assertEqual(a.placements, b.placements)

    def test_respeta_limite_de_tiempo(self):
        inst = random_instance(6, 28, 400, seed=5)
        limite = 0.5
        t0 = time.perf_counter()
        res = solve(inst, 1, t0 + limite)
        self.assertLess(time.perf_counter() - t0, limite + 0.2)
        self.assertGreater(play(inst, res.placements).placed, 0)

    def test_derrota_inevitable_entrega_partida_legal(self):
        # 1x1 con dos colores distintos: solo cabe la primera ficha.
        inst = Instance(1, 2, (Tile(1, 1), Tile(2, 1)))
        res = solve(inst, 0, time.perf_counter() + 1)
        g = play(inst, res.placements)
        self.assertEqual((g.placed, g.status()), (1, Status.LOST))


if __name__ == "__main__":
    unittest.main()
