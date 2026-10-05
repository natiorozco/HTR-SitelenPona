import os
import random
import time
import unittest

from agents.evolutivo import NUM_FEATURES, _Context, _normalize, decode, solve
from tileup import Instance, Status, Tile, load_instance, play

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(HERE, "..", "instances", "ejemplo.txt")


def random_instance(n, k, m, seed):
    r = random.Random(seed)
    return Instance(n, k, tuple(Tile(r.randint(1, k), r.randint(1, 9)) for _ in range(m)))


class TestAgenteEvolutivo(unittest.TestCase):
    def test_resuelve_ejemplo_optimo(self):
        inst = load_instance(EXAMPLE)
        res = solve(inst, seed=1, deadline=time.perf_counter() + 5)
        g = play(inst, res.placements)  # lanza IllegalMoveError si hay jugadas ilegales
        self.assertEqual(g.status(), Status.WON)
        self.assertEqual(g.occupied, 3)  # cota inferior: 3 colores distintos
        self.assertGreater(res.effort, 0)

    def test_decodificador_coincide_con_motor(self):
        inst = random_instance(5, 18, 150, seed=4)
        ctx = _Context(inst, window=10)
        r = random.Random(0)
        for _ in range(20):
            w = _normalize([r.gauss(0, 1) for _ in range(NUM_FEATURES)])
            moves, occ, _ = decode(ctx, w)
            g = play(inst, moves)
            self.assertEqual((g.placed, g.occupied), (len(moves), occ))

    def test_voraz_fusiona_cuando_puede(self):
        inst = Instance(3, 2, (Tile(1, 1), Tile(1, 1)))
        moves, occ, _ = decode(_Context(inst, window=10), [1.0] + [0.0] * (NUM_FEATURES - 1))
        self.assertEqual(occ, 1)

    def test_misma_semilla_misma_solucion(self):
        inst = random_instance(4, 10, 60, seed=3)
        a = solve(inst, seed=42, deadline=time.perf_counter() + 1)
        b = solve(inst, seed=42, deadline=time.perf_counter() + 1)
        ga, gb = play(inst, a.placements), play(inst, b.placements)
        self.assertEqual((ga.placed, ga.occupied), (gb.placed, gb.occupied))

    def test_respeta_limite_de_tiempo(self):
        inst = random_instance(6, 28, 400, seed=5)
        limite = 0.5
        t0 = time.perf_counter()
        res = solve(inst, seed=1, deadline=t0 + limite)
        self.assertLess(time.perf_counter() - t0, limite + 0.2)
        self.assertGreater(play(inst, res.placements).placed, 0)

    def test_derrota_inevitable_entrega_partida_legal(self):
        inst = Instance(1, 2, (Tile(1, 1), Tile(2, 1)))
        res = solve(inst, seed=0, deadline=time.perf_counter() + 1)
        g = play(inst, res.placements)
        self.assertEqual((g.placed, g.status()), (1, Status.LOST))


if __name__ == "__main__":
    unittest.main()
