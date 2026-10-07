"""Pruebas de integración: el programa completo, de principio a fin.

Cada prueba corre main.py como un proceso aparte, igual que lo haría el
evaluador, y después revisa la solución con el validador independiente.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import validator
from generador import generate

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXAMPLE = os.path.join(ROOT, "instances", "ejemplo.txt")
AGENTES = ["busqueda", "evolutivo"]
LIMITE = 3.0  # segundos por corrida
# En Windows la consola no usa UTF-8 por defecto y los acentos de los mensajes
# no se podrían leer desde aquí.
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def run_main(*args):
    return subprocess.run([sys.executable, os.path.join(ROOT, "main.py"), *args],
                          cwd=ROOT, env=ENV, capture_output=True, text=True,
                          encoding="utf-8", timeout=LIMITE + 30)


def metricas(stdout):
    """Las líneas `clave=valor` que imprime main.py, como diccionario."""
    out = {}
    for line in stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep and " " not in key:
            out[key] = value
    return out


class TestDePrincipioAFin(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # Instancia pequeña generada: 4x4, 5 colores, 60 fichas.
        self.pequena = os.path.join(self.tmp, "pequena.txt")
        with open(self.pequena, "w", encoding="utf-8") as f:
            f.write(generate(4, 5, 60, seed=7))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def resolver_y_validar(self, instancia, agente, semilla=1):
        """Corre main.py y comprueba con el validador que la solución es legal."""
        salida = os.path.join(self.tmp, f"{agente}_s{semilla}.txt")
        proc = run_main(instancia, "--agente", agente, "--semilla", str(semilla),
                        "--tiempo", str(LIMITE), "--salida", salida)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(os.path.isfile(salida))

        # validate() lanza validator.Invalid si la solución es ilegal o si el
        # resumen del archivo no cuadra con la partida reproducida.
        final = validator.validate(instancia, salida)

        # Lo que main.py informa por salida estándar coincide con el validador.
        out = metricas(proc.stdout)
        for campo in ("colocadas", "ocupadas", "mayor", "estado"):
            self.assertEqual(out[campo], str(final[campo]), campo)
        self.assertLess(float(out["tiempo"]), LIMITE)
        return final, salida

    def test_ejemplo_del_enunciado(self):
        for agente in AGENTES:
            with self.subTest(agente=agente):
                final, _ = self.resolver_y_validar(EXAMPLE, agente)
                self.assertEqual(final["estado"], "victoria")
                self.assertEqual(final["ocupadas"], 3)

    def test_instancia_pequena_generada(self):
        for agente in AGENTES:
            with self.subTest(agente=agente):
                final, _ = self.resolver_y_validar(self.pequena, agente)
                self.assertEqual(final["colocadas"], 60)

    def test_validador_por_linea_de_comandos(self):
        _, salida = self.resolver_y_validar(EXAMPLE, "evolutivo")
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "validator.py"),
                               EXAMPLE, salida],
                              cwd=ROOT, env=ENV, capture_output=True, text=True,
                              encoding="utf-8")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("legal=True", proc.stdout)

    def test_misma_semilla_misma_solucion(self):
        for agente in AGENTES:
            with self.subTest(agente=agente):
                _, a = self.resolver_y_validar(self.pequena, agente, semilla=5)
                with open(a, encoding="utf-8") as f:
                    primera = f.read()
                _, b = self.resolver_y_validar(self.pequena, agente, semilla=5)
                with open(b, encoding="utf-8") as f:
                    self.assertEqual(primera, f.read())

    def test_derrota_tambien_escribe_solucion_legal(self):
        # 1x1 con dos colores distintos: solo cabe la primera ficha.
        derrota = os.path.join(self.tmp, "derrota.txt")
        with open(derrota, "w", encoding="utf-8") as f:
            f.write("1 2\n2\n1 1\n2 1\n")
        for agente in AGENTES:
            with self.subTest(agente=agente):
                final, _ = self.resolver_y_validar(derrota, agente)
                self.assertEqual((final["estado"], final["colocadas"]), ("derrota", 1))

    def test_instancia_mal_formada(self):
        mala = os.path.join(self.tmp, "mala.txt")
        with open(mala, "w", encoding="utf-8") as f:
            f.write("4 3\n2\n1 x\n")
        proc = run_main(mala, "--agente", "busqueda", "--tiempo", "1")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("error", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)


class TestValidadorRechaza(unittest.TestCase):
    """El validador no solo reproduce la partida: rechaza lo que es ilegal."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def validar(self, texto):
        ruta = os.path.join(self.tmp, "sol.txt")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(texto)
        return validator.validate(EXAMPLE, ruta)

    def test_acepta_solucion_del_enunciado(self):
        final = self.validar("0 0 0\n1 1 1\n2 0 1\n3 2 2\n4 0 2\n5 1 2\n"
                             "# colocadas=6 ocupadas=3 mayor=6\n")
        self.assertEqual((final["colocadas"], final["ocupadas"], final["mayor"]), (6, 3, 6))

    def test_rechaza_celda_ocupada(self):
        with self.assertRaisesRegex(validator.Invalid, "ocupada"):
            self.validar("0 0 0\n1 0 0\n")

    def test_rechaza_fuera_del_tablero(self):
        with self.assertRaisesRegex(validator.Invalid, "fuera"):
            self.validar("0 4 0\n")

    def test_rechaza_indices_desordenados(self):
        with self.assertRaisesRegex(validator.Invalid, "orden"):
            self.validar("1 0 0\n")

    def test_rechaza_resumen_que_no_cuadra(self):
        with self.assertRaisesRegex(validator.Invalid, "ocupadas"):
            self.validar("0 0 0\n1 1 1\n2 0 1\n3 2 2\n4 0 2\n5 1 2\n"
                         "# colocadas=6 ocupadas=2 mayor=6\n")


if __name__ == "__main__":
    unittest.main()
