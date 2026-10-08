# TileUp: agentes de búsqueda y evolutivos

IC-6200 Inteligencia Artificial, Tarea Corta 1.

Integrantes: Natalia Orozco Delgado, Fernando Andrés González Robles y Valeska Brenes.

Este proyecto incluye el motor del juego TileUp, un agente de búsqueda (DFS con poda), un agente evolutivo (algoritmo genético sobre pesos), un validador independiente, un generador de instancias y los guiones de la comparación experimental y de la batería de escalabilidad.

La formulación de los agentes y el análisis de resultados están en el informe: [agents/informe.md](agents/informe.md). La declaración de uso de IA está en [declaracionIA.md](declaracionIA.md).

## Requisitos

- Python 3.10 o superior (probado con 3.10.4).
- Nada más. Solo se usa la biblioteca estándar, así que no hay que instalar dependencias, compilar ni crear un entorno virtual.

En Linux y macOS, use `python3` donde este documento dice `python` si `python` no apunta a Python 3.

## Inicio rápido

Todos los comandos se ejecutan desde la carpeta `TC1`:

```bash
git clone https://github.com/natiorozco/HTR-SitelenPona.git
cd HTR-SitelenPona/TC1

# Resolver una instancia con cada agente
python main.py instances/ejemplo.txt --agente busqueda  --semilla 1 --tiempo 10
python main.py instances/ejemplo.txt --agente evolutivo --semilla 1 --tiempo 10

# Validar las soluciones que se acaban de escribir
python validator.py instances/ejemplo.txt soluciones/ejemplo_busqueda_s1.txt
python validator.py instances/ejemplo.txt soluciones/ejemplo_evolutivo_s1.txt

# Correr todas las pruebas (unitarias y de integración)
python -m unittest -v
```

## Ejecutar un agente

```
python main.py <instancia> --agente {busqueda,evolutivo} [--semilla S] [--tiempo T] [--salida RUTA]
```

| Opción | Alias | Significado | Por defecto |
|---|---|---|---|
| `<instancia>` | | Ruta del archivo de instancia | (obligatorio) |
| `--agente` | `--agent` | `busqueda` o `evolutivo` | (obligatorio) |
| `--semilla` | `--seed` | Entero del que sale todo el azar | `0` |
| `--tiempo` | `--time` | Límite total en segundos, incluida la lectura y la escritura | `10` |
| `--salida` | `--output` | Archivo de solución | `soluciones/<instancia>_<agente>_s<semilla>.txt` |

El programa no pide nada de forma interactiva. Al terminar escribe el archivo de solución, también cuando la partida termina en derrota, y muestra las métricas por salida estándar:

```
agente=evolutivo semilla=1 instancia=instances/ejemplo.txt
estado=victoria
colocadas=6
ocupadas=3
mayor=6
tiempo=0.032
evaluaciones_aptitud=30
generaciones=0
pesos=1.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000
solucion=soluciones/ejemplo_evolutivo_s1.txt
```

- `estado` toma uno de estos valores: `victoria` (se colocaron las M fichas), `derrota` (el tablero quedó lleno con fichas pendientes) o `en_curso` (el tiempo se agotó antes de terminar).
- `colocadas`, `ocupadas` y `mayor` son la cantidad de fichas colocadas, las celdas ocupadas al final y el valor de la ficha mayor.
- `tiempo` es el tiempo total en segundos.
- La medida de esfuerzo es `nodos_expandidos` en la búsqueda y `evaluaciones_aptitud` en el evolutivo. Cada agente agrega además sus propios datos: `completo` indica si la búsqueda recorrió todo el espacio, y el evolutivo informa `generaciones` y los `pesos` del mejor individuo.

**Límite de tiempo.** El agente recibe el límite menos un margen (10 % del límite, entre 0.05 s y 1 s) para que reproducir y escribir la solución no haga pasar el programa del límite. Si se acaba el tiempo, el agente entrega la mejor solución que haya encontrado hasta ese momento.

**Determinismo.** Con la misma instancia, el mismo agente y la misma semilla, la solución es idéntica. La búsqueda es determinista por construcción. El evolutivo saca todo su azar de `random.Random(semilla)`. La única excepción es un límite de tiempo muy justo: en ese caso, cuántas generaciones alcanza a correr el evolutivo depende de la velocidad de la máquina.

**Códigos de salida.**

| Código | Significado |
|---|---|
| 0 | Se escribió la solución |
| 1 | Instancia mal formada o ilegible, o no se pudo escribir la solución. Se muestra un mensaje legible en stderr, sin traza de Python |
| 2 | Argumentos inválidos (por ejemplo, `--tiempo` no positivo o un agente desconocido) |
| 3 | Error interno: el agente propuso una jugada ilegal. El motor reproduce siempre la solución antes de escribirla |

## Validar una solución

```
python validator.py <instancia> <solución>
```

El validador reproduce la partida paso a paso desde el tablero vacío, con su propia implementación de las reglas: no importa el motor ni los agentes. Comprueba que los índices vayan en orden y sin repetirse, que cada celda esté dentro del tablero y vacía, que no se juegue después de una derrota y que el resumen `# colocadas=… ocupadas=… mayor=…`, si viene, coincida con la partida reproducida.

```
legal=True instancia=instances/ejemplo.txt solucion=soluciones/ejemplo_busqueda_s1.txt
estado=victoria
colocadas=6
ocupadas=3
mayor=6
```

Sale con 0 si la solución es legal. Si es ilegal, o algún archivo está mal formado, sale con 1 y muestra `ILLEGAL <solución>: <motivo>` en stderr. Si el uso es incorrecto, sale con 2.

## Pruebas

```bash
python -m unittest -v
```

El comando corre las 45 pruebas de la carpeta [tests/](tests/) y tarda alrededor de 25 segundos.

| Archivo | Qué cubre |
|---|---|
| `test_engine.py` | Pruebas unitarias del motor de forma aislada: colocación sin fusión, fusión de dos fichas, fusión de una componente de tres o más, que la fusión no encadena y conserva la suma, detección de derrota y de victoria, jugadas ilegales y lectura de instancias mal formadas |
| `test_busqueda.py` | Agente de búsqueda: óptimo en el ejemplo, repetibilidad, límite de tiempo y derrota inevitable |
| `test_evolutivo.py` | Agente evolutivo: óptimo en el ejemplo, que el decodificador coincida con el motor, misma semilla con misma solución, límite de tiempo y derrota |
| `test_generador.py` | Generador de instancias: formato, semilla y CLI |
| `test_integracion.py` | Pruebas de integración de principio a fin: corren `main.py` como proceso aparte sobre el ejemplo del enunciado y una instancia pequeña generada, y comprueban con el validador que la solución es legal y que las métricas de stdout coinciden. También verifican el determinismo por semilla, que la derrota escriba una solución legal, que una instancia mal formada dé error sin traza y que el validador rechace jugadas ilegales y resúmenes falsos |

## Formatos

### Instancia

Es un archivo de texto. Las líneas en blanco y todo lo que sigue a un `#` se ignoran. El resto contiene, en este orden: una línea `N K` (lado del tablero y cantidad de colores), una línea `M` (cantidad de fichas) y M líneas `color valor`, en el orden de colocación.

```
# TileUp -- instancia de ejemplo
4 3   # tablero 4x4, 3 colores
6     # 6 fichas en la secuencia
1 2
2 1
1 3
3 1
1 1
2 4
```

### Solución

Tiene una línea por colocación con `índice fila columna` (todos empiezan en cero), en el orden de la secuencia. La última línea es el resumen.

```
0 0 0
1 1 1
2 0 1
3 2 2
4 0 2
5 1 2
# colocadas=6 ocupadas=3 mayor=6
```

## Generar instancias

```
python generador.py N K M --semilla S [--valor-max V] [--salida RUTA]
```

Cada color se elige de forma uniforme en 1..K y cada valor en 1..V (por defecto, V = 9). Con los mismos parámetros y la misma semilla, el archivo es idéntico byte a byte. Si no se indica `--salida`, el archivo se escribe en `instances/gen_N<N>_K<K>_M<M>_s<S>.txt`.

```bash
python generador.py 6 10 200 --semilla 4
python main.py instances/gen_N6_K10_M200_s4.txt --agente evolutivo --semilla 1 --tiempo 5
```

## Formulación de los agentes

En esta sección se resume la formulación. La justificación completa y la discusión están en [agents/informe.md](agents/informe.md).

### Agente de búsqueda: DFS con poda ([agents/search.py](agents/search.py))

- **Estado:** `(colores de las N² celdas, i)`, donde `i` es el índice de la siguiente ficha. Los valores no se guardan porque no influyen en ninguna decisión: solo afectan a `mayor`.
- **Operador de sucesión:** colocar la ficha `i` en cualquier celda vacía y aplicar la fusión con el motor. El factor de ramificación es la cantidad de celdas vacías. Los hijos se ordenan primero por los que más fichas fusionan y después por el índice de la celda.
- **Costo de una acción:** el cambio en las celdas ocupadas, es decir, `1 − (|G| − 1)`. El costo acumulado es la cantidad de celdas ocupadas, así que minimizarlo equivale a dejar el tablero más despejado.
- **Prueba de meta:** `i == M`. Entre las metas encontradas se queda la de menos celdas ocupadas.
- **Heurística:** `h = max(0, ocupadas + pendientes − N² − 4 · fusionables)`, donde *fusionables* es la cantidad de fichas pendientes cuyo color ya apareció antes en la secuencia. Una ficha libera como máximo 4 celdas, una por cada vecino ortogonal. Cuando el agente ya tiene una victoria, poda los estados con `ocupadas + h ≥ mejor`. Además, descarta los estados repetidos con una tabla de visitados.
- **Admisibilidad:** no se garantiza. Al podar se comparan las celdas ocupadas *ahora* con las del final de la mejor victoria, y las ocupadas todavía pueden bajar por fusiones posteriores. Por eso se puede descartar un camino que terminaría con menos celdas. Lo que se pierde es la garantía de devolver la victoria con menos celdas ocupadas. Si el espacio se recorre completo (`completo=True`), sí se garantiza encontrar una victoria cuando existe, porque la poda solo se activa después de la primera victoria.
- **Sin victoria:** devuelve la partida parcial más profunda (más fichas colocadas y, entre ellas, menos celdas ocupadas).
- **Esfuerzo:** `nodos_expandidos`.

### Agente evolutivo: algoritmo genético sobre pesos ([agents/evolutivo.py](agents/evolutivo.py))

- **Individuo:** un vector de 8 pesos normalizados. Para decodificarlo se juega una partida voraz. En cada paso se calculan 8 características para cada celda vacía: vecinos del mismo color, vecinos de otro color que sale pronto, vecinos de otro color que sale tarde, lados contra el borde o contra fichas que ya no vuelven, vecinos que quedarían encerrados, distancia al centro, espacio que queda si el color vuelve pronto y espacio que libera una fusión. La ficha va a la celda con mayor puntaje (producto punto entre características y pesos). Así, todo individuo produce una partida legal.
- **Aptitud:** `colocadas · (N² + 1) − ocupadas`, de modo que una ficha más siempre vale más que cualquier diferencia en celdas ocupadas, igual que el orden del concurso. Si hay empate, gana el individuo que mantuvo el tablero más vacío durante toda la partida.
- **Población inicial:** 30 individuos: uno voraz que solo busca fusionar y 29 con pesos gaussianos al azar.
- **Selección:** torneo de tamaño 3.
- **Variación:** cruce aritmético extendido (BLX-α con α = 0.5) con probabilidad 0.9, y mutación gaussiana con σ = 0.2 aplicada a cada peso con probabilidad 1/8.
- **Reemplazo:** elitista (μ + λ). Se juntan los 30 padres con los 30 hijos y se conservan los 30 mejores.
- **Criterio de paro:** que se agote el tiempo o que el mejor individuo alcance la cota óptima (todas las fichas colocadas con una sola celda por color).
- **Esfuerzo:** `evaluaciones_aptitud`.

| Parámetro | Valor | Cómo se fijó |
|---|---|---|
| Tamaño de población | 30 | Se comparó con 8 y 16 en 36 tableros de práctica, con 3 s cada uno. Con 30 se colocaron más fichas en total |
| σ de la mutación | 0.2 | Se probaron 0.1, 0.2 y 0.3 en los mismos tableros. La diferencia fue mínima y se dejó 0.2 |
| Torneo | 3 | Valor estándar, no ajustado |
| Probabilidad de cruce | 0.9 | Valor estándar, no ajustado |
| α del cruce | 0.5 | Valor estándar de BLX-α, no ajustado |
| Probabilidad de mutación por gen | 1/8 | 1 / cantidad de genes (valor estándar) |
| Ventana "pronto" | 10 fichas | Elegida a mano |

## Experimentos

### Comparación experimental

Usa 6 configuraciones de N, K y M con 3 instancias cada una (semillas 1, 2 y 3), corre ambos agentes y da 10 s a cada corrida. Las instancias, las soluciones y los resultados ya están en el repositorio, en [comparacion_experimental/](comparacion_experimental/).

```bash
python comparacion_experimental/generar.py                  # regenera las instancias
python comparacion_experimental/correr.py --tiempo 10       # corre los 36 casos y escribe resultados.csv
python comparacion_experimental/resumen.py                  # escribe resultados.md
```

`correr.py` corre 4 casos en paralelo por defecto (`--paralelo 4`). Para que los tiempos sean comparables, use `--paralelo 1`.

Para verificar con el validador cualquier resultado del informe:

```bash
python validator.py comparacion_experimental/instancias/gen_N8_K20_M400_s1.txt \
                    comparacion_experimental/soluciones/gen_N8_K20_M400_s1_evolutivo.txt
```

### Batería de escalabilidad

Recorre N ∈ {4, 5, 6} y K ∈ {4, 12, 24}, con M = 200 y 3 semillas, y da 5 s por corrida. Genera tablas y gráficas SVG en [experimentos/resultados/](experimentos/resultados/).

```bash
python experimentos/bateria.py                     # corre todo (unos 5 minutos)
python experimentos/bateria.py --solo-resumen      # rehace tablas y gráficas desde el CSV
python experimentos/bateria.py --N 4 5 --K 4 8 --M 100 --semillas 1 2 3 --tiempo 2
```

## Jugar a mano

```bash
python jugar.py instances/ejemplo.txt
```

En cada turno se escribe `fila columna` (desde cero), o `q` para salir. Sirve para probar el motor.

## Estructura

```
TC1/
├── main.py                  punto de entrada único (CLI)
├── validator.py             validador independiente (no importa tileup ni agents)
├── generador.py             generador de instancias
├── jugar.py                 juego interactivo para probar el motor
├── tileup/                  motor del juego
│   ├── instance.py          lectura de instancias
│   ├── engine.py            estado, colocación, fusión, victoria y derrota
│   └── solution.py          escritura de soluciones
├── agents/
│   ├── search.py            agente de búsqueda
│   ├── evolutivo.py         agente evolutivo
│   └── informe.md           informe
├── tests/                   pruebas unitarias y de integración
├── instances/               instancias de ejemplo
├── comparacion_experimental/  instancias, soluciones y resultados de la comparación
└── experimentos/            batería de escalabilidad, resultados y gráficas
```
