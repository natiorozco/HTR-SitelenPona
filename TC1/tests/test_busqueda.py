import os
import random
import time
import unittest

from agents.busqueda import heuristic, Params, solve
from tileup import GameState, Instance, Status, Tile, load_instance, play

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(HERE, "..", "instances", "ejemplo.txt")


def random_instance(n, k, m, seed):
    r = random.Random(seed)
    return Instance(n, k, tuple(Tile(r.randint(1, k), r.randint(1, 9)) for _ in range(m)))


class TestAgenteBusqueda(unittest.TestCase):
    def test_resuelve_ejemplo_optimo(self):
        inst = load_instance(EXAMPLE)
        res = solve(inst, seed=1, deadline=time.perf_counter() + 5)
        g = play(inst, res.placements)  # lanza IllegalMoveError si hay jugadas ilegales
        self.assertEqual(g.status(), Status.WON)
        # 3 colores distintos en la secuencia: 3 es la cota inferior
        self.assertEqual(g.occupied, 3)
        self.assertGreater(res.effort, 0)

    def test_misma_semilla_misma_solucion(self):
        inst = random_instance(5, 6, 120, seed=3)
        a = solve(inst, seed=42, deadline=time.perf_counter() + 30)
        b = solve(inst, seed=42, deadline=time.perf_counter() + 30)
        self.assertEqual(a.placements, b.placements)

    def test_respeta_limite_de_tiempo(self):
        # Instancia difícil (muchos colores): la búsqueda no termina sola.
        inst = random_instance(6, 28, 400, seed=5)
        limite = 0.5
        t0 = time.perf_counter()
        res = solve(inst, seed=1, deadline=t0 + limite)
        elapsed = time.perf_counter() - t0
        self.assertLess(elapsed, limite + 0.2)
        g = play(inst, res.placements)
        self.assertGreater(g.placed, 0)

    def test_derrota_inevitable_entrega_partida_legal(self):
        # 1x1 con dos colores distintos: solo cabe la primera ficha.
        inst = Instance(1, 2, (Tile(1, 1), Tile(2, 1)))
        res = solve(inst, seed=0, deadline=time.perf_counter() + 1)
        g = play(inst, res.placements)
        self.assertEqual((g.placed, g.status()), (1, Status.LOST))

    def test_heuristica_prefiere_hueco_libre(self):
        # Próxima ficha color 1: el estado con hueco junto al 1 es mejor.
        inst = Instance(3, 2, (Tile(1, 1), Tile(2, 1), Tile(1, 1)))
        con_hueco = play(inst, [0, 8])          # 1 en esquina, 2 lejos
        sin_hueco = play(inst, [0, 1])          # el 2 tapa uno de los dos huecos del 1
        self.assertLess(heuristic(con_hueco, Params()), heuristic(sin_hueco, Params()))


if __name__ == "__main__":
    unittest.main()
