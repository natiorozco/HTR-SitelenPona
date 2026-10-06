import os
import tempfile
import unittest

from generador import generate, main
from tileup import load_instance, parse_instance


class TestGenerador(unittest.TestCase):
    def test_formato_valido_y_parametros(self):
        inst = parse_instance(generate(5, 7, 120, seed=3))
        self.assertEqual((inst.n, inst.k, inst.m), (5, 7, 120))
        self.assertTrue(all(1 <= t.color <= 7 for t in inst.tiles))
        self.assertTrue(all(1 <= t.value <= 9 for t in inst.tiles))

    def test_misma_semilla_mismo_archivo(self):
        self.assertEqual(generate(4, 3, 50, seed=1), generate(4, 3, 50, seed=1))
        self.assertNotEqual(generate(4, 3, 50, seed=1), generate(4, 3, 50, seed=2))

    def test_valor_max(self):
        inst = parse_instance(generate(3, 2, 200, seed=0, max_value=1))
        self.assertTrue(all(t.value == 1 for t in inst.tiles))

    def test_m_cero(self):
        self.assertEqual(parse_instance(generate(2, 2, 0, seed=0)).m, 0)

    def test_cli_escribe_archivo(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d, "sub", "x.txt")
            self.assertEqual(main(["3", "4", "10", "--semilla", "5", "--salida", ruta]), 0)
            self.assertEqual(load_instance(ruta).m, 10)

    def test_cli_parametros_invalidos(self):
        self.assertNotEqual(main(["0", "4", "10", "--semilla", "1", "--salida", os.devnull]), 0)


if __name__ == "__main__":
    unittest.main()
