import os
import unittest

from tileup import (
    GameState, IllegalMoveError, Instance, InstanceError, Status, Tile,
    format_solution, load_instance, parse_instance, play,
)

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(HERE, "..", "instances", "ejemplo.txt")


def make(n, k, tiles):
    return Instance(n, k, tuple(Tile(c, v) for c, v in tiles))


class TestPlacement(unittest.TestCase):
    def test_colocacion_sin_fusion(self):
        g = GameState(make(3, 2, [(1, 5), (2, 7)]))
        self.assertEqual(g.place_rc(0, 0), 1)
        self.assertEqual(g.place_rc(0, 1), 1)  # vecino de otro color: no fusiona
        self.assertEqual(g.cell(0, 0), (1, 5))
        self.assertEqual(g.cell(0, 1), (2, 7))
        self.assertEqual(g.occupied, 2)

    def test_mismo_color_en_diagonal_no_fusiona(self):
        g = GameState(make(3, 1, [(1, 1), (1, 1)]))
        g.place_rc(0, 0)
        self.assertEqual(g.place_rc(1, 1), 1)
        self.assertEqual(g.occupied, 2)

    def test_fusion_de_dos(self):
        g = GameState(make(3, 2, [(1, 2), (1, 3)]))
        g.place_rc(1, 1)
        self.assertEqual(g.place_rc(1, 2), 2)
        # la ficha resultante queda donde se colocó la última
        self.assertEqual(g.cell(1, 2), (1, 5))
        self.assertEqual(g.cell(1, 1), (0, 0))
        self.assertEqual(g.occupied, 1)

    def test_fusion_componente_de_tres_o_mas(self):
        # Cadena 1-1-1 en L; la cuarta ficha la une toda.
        g = GameState(make(3, 2, [(1, 1), (1, 2), (2, 9), (1, 4)]))
        g.place_rc(0, 0)
        g.place_rc(2, 0)
        g.place_rc(2, 2)           # otro color, no participa
        # (1,0) toca a (0,0) y (2,0): componente de tamaño 3
        self.assertEqual(g.place_rc(1, 0), 3)
        self.assertEqual(g.cell(1, 0), (1, 7))
        self.assertEqual(g.cell(0, 0), (0, 0))
        self.assertEqual(g.cell(2, 0), (0, 0))
        self.assertEqual(g.cell(2, 2), (2, 9))
        self.assertEqual(g.occupied, 2)

    def test_fusion_no_encadena_y_conserva_suma(self):
        # Invariante: tras cada jugada no hay dos fichas adyacentes del mismo
        # color, y la suma de valores en el tablero es la de lo colocado.
        tiles = [(1, 1), (2, 1), (1, 1), (2, 1), (1, 1), (2, 1), (1, 3)]
        g = GameState(make(3, 2, tiles))
        colocado = 0
        for idx, (_, v) in zip([0, 4, 2, 8, 1, 6, 3], tiles):
            g.place(idx)
            colocado += v
            self.assertEqual(sum(g.values), colocado)
            for i, c in enumerate(g.colors):
                if c:
                    for nb in g._nbrs[i]:
                        self.assertNotEqual(g.colors[nb], c)

    def test_celda_ocupada_es_ilegal(self):
        g = GameState(make(2, 2, [(1, 1), (2, 1)]))
        g.place_rc(0, 0)
        with self.assertRaises(IllegalMoveError):
            g.place_rc(0, 0)

    def test_fuera_de_tablero_es_ilegal(self):
        g = GameState(make(2, 2, [(1, 1)]))
        with self.assertRaises(IllegalMoveError):
            g.place_rc(2, 0)
        with self.assertRaises(IllegalMoveError):
            g.place(-1)

    def test_copy_es_independiente(self):
        g = GameState(make(2, 2, [(1, 1), (1, 1)]))
        h = g.after(0)
        self.assertEqual(g.occupied, 0)
        self.assertEqual(h.occupied, 1)
        self.assertNotEqual(g.key(), h.key())


class TestTermination(unittest.TestCase):
    def test_deteccion_de_derrota(self):
        # 2x2, cuatro colores distintos y una quinta ficha pendiente.
        g = GameState(make(2, 4, [(1, 1), (2, 1), (3, 1), (4, 1), (1, 1)]))
        for idx in range(4):
            self.assertEqual(g.status(), Status.IN_PROGRESS)
            g.place(idx)
        self.assertEqual(g.status(), Status.LOST)
        self.assertEqual(g.placed, 4)
        self.assertEqual(g.legal_actions(), [])
        with self.assertRaises(IllegalMoveError):
            g.place(0)

    def test_llenar_con_ultima_ficha_es_victoria(self):
        g = GameState(make(1, 1, [(1, 1)]))
        g.place(0)
        self.assertEqual(g.status(), Status.WON)

    def test_fusion_libera_celdas_y_evita_derrota(self):
        # 2x2 con un solo color: cada ficha fusiona y el tablero nunca se llena.
        g = GameState(make(2, 1, [(1, 1)] * 6))
        for _ in range(6):
            g.place(g.legal_actions()[0])
        self.assertEqual(g.status(), Status.WON)

    def test_victoria(self):
        g = GameState(make(2, 2, [(1, 1)]))
        self.assertEqual(g.status(), Status.IN_PROGRESS)
        g.place(3)
        self.assertEqual(g.status(), Status.WON)
        self.assertIsNone(g.current_tile())

    def test_instancia_vacia_es_victoria(self):
        self.assertEqual(GameState(make(2, 2, [])).status(), Status.WON)

    def test_legal_actions(self):
        g = GameState(make(2, 2, [(1, 1), (2, 1)]))
        self.assertEqual(g.legal_actions(), [0, 1, 2, 3])
        g.place(1)
        self.assertEqual(g.legal_actions(), [0, 2, 3])


class TestEjemploEnunciado(unittest.TestCase):
    def test_ejemplo_del_enunciado(self):
        inst = load_instance(EXAMPLE)
        self.assertEqual((inst.n, inst.k, inst.m), (4, 3, 6))
        moves = [(0, 0), (1, 1), (0, 1), (2, 2), (0, 2), (1, 2)]
        g = play(inst, [r * inst.n + c for r, c in moves])
        self.assertEqual(g.status(), Status.WON)
        self.assertEqual((g.placed, g.occupied, g.max_value), (6, 3, 6))
        expected = ("0 0 0\n1 1 1\n2 0 1\n3 2 2\n4 0 2\n5 1 2\n"
                    "# colocadas=6 ocupadas=3 mayor=6\n")
        self.assertEqual(format_solution(moves, g), expected)


class TestParser(unittest.TestCase):
    def test_comentarios_y_lineas_vacias(self):
        inst = parse_instance("# hola\n\n2 2 # tab\n\n1\n# ficha\n2 5\n")
        self.assertEqual((inst.n, inst.k), (2, 2))
        self.assertEqual(inst.tiles, (Tile(2, 5),))

    def test_errores(self):
        malos = [
            "",                       # vacío
            "2\n1\n1 1\n",            # falta K
            "2 2\n2\n1 1\n",          # faltan fichas
            "2 2\n1\n1 1\n1 1\n",     # sobran fichas
            "2 2\n1\n3 1\n",          # color fuera de rango
            "2 2\n1\n1 0\n",          # valor no positivo
            "2 x\n1\n1 1\n",          # no entero
            "0 2\n0\n",               # N inválido
            "2 2\n-1\n",              # M negativo
        ]
        for text in malos:
            with self.subTest(text=text):
                with self.assertRaises(InstanceError):
                    parse_instance(text)

    def test_archivo_inexistente(self):
        with self.assertRaises(InstanceError):
            load_instance(os.path.join(HERE, "no_existe.txt"))


if __name__ == "__main__":
    unittest.main()
