# Informe

## Agente de búsqueda

Para el agente de búsqueda usamos una búsqueda en profundidad (DFS). Va probando jugadas hasta el final de la partida y si se equivoca, retrocede y prueba otra. Mientras busca va guardando la mejor partida que ha visto, así que si se acaba el tiempo devuelve esa. Si nunca encuentra una forma de ganar, da la partida en la que logró poner más fichas.

El estado son los colores de las celdas del tablero junto con el número de la siguiente ficha que toca poner. Los sucesores de un estado salen de poner la siguiente ficha en cualquier celda vacía y hacer la fusión si toca. El costo de una jugada es cuánto cambian las celdas ocupadas, poner la ficha suma 1 y cada ficha que se fusiona con ella resta 1. La meta es haber puesto todas las fichas y si hay varias formas de lograrlo es mejor la que deja menos celdas ocupadas.

La heurística es `h = max(0, ocupadas + pendientes − N² − 4 · fusionables)`, donde las pendientes son las fichas que faltan y las fusionables son las que faltan y son de un color que ya salió. Cada ficha que falta ocupa una celda y como mucho se fusiona con 4 vecinas, así que si h > 0 por ese camino es imposible terminar. No es totalmente admisible. Si existe una forma de ganar la encuentra, pero al podar compara las celdas ocupadas en ese momento con las del final de la mejor partida, y las ocupadas todavía podrían bajar después por las fusiones, entonces a veces descarta un camino que podría haber terminado con menos celdas ocupadas. En resumen, no hay garantía de que se tenga la solución con menos celdas ocupadas.

## Agente evolutivo 

Cada individuo es una lista de 8 pesos. Para poner una ficha miramos cada celda vacía y le calculamos 8 features: cuántos vecinos son del mismo color, cuántos vecinos son de otro color que va a salir en las próximas 10 fichas, cuántos son de otro color que no sale pronto, cuántos lados tocan el borde o una ficha de un color que ya no vuelve a salir, cuántas fichas vecinas se quedarían sin espacio libre al lado, qué tan lejos está la celda del centro, cuánto espacio libre le queda a la ficha si su color vuelve a salir pronto, y si hay fusión a cuántas fichas que salen pronto les abre espacio. El puntaje de una celda es la suma de cada feature por su peso, y la ficha va a la celda con el puntaje más alto. Así cualquier individuo juega una partida legal. Los pesos los normalizamos.

Para la aptitud contamos primero cuántas fichas logra poner y después cuántas celdas deja ocupadas, igual que el orden del concurso. La calculamos como `colocadas · (N² + 1) − ocupadas`, para que una ficha más siempre valga más. Y si empatan, gana el que mantuvo el tablero más vacío durante la partida.

La población empieza con 30 individuos, uno al que solo le importa fusionar y 29 con pesos al azar. Para escoger cada padre tomamos 3 al azar y gana el mejor (torneo). Con probabilidad 0.9 cruzamos dos padres, donde cada peso del hijo es un número al azar entre los pesos de los padres con un margen extra de la mitad de la distancia a cada lado. Después viene la mutación, donde a cada peso, con probabilidad 1/8, le sumamos ruido de una distribución normal con σ = 0.2. En cada generación se crean 30 hijos, se juntan con los padres y nos quedamos con los 30 mejores (reemplazo elitista). El algoritmo para cuando se acaba el tiempo o cuando ya puso todas las fichas con una sola celda por color. Todo el azar sale de la semilla.

Datos importantes: torneo de 3, la probabilidad de cruce de 0.9, el margen de 0.5 y la probabilidad de mutación de 1/8, las 10 fichas que cuentan como "pronto". σ y el tamaño de la población se fueron probando con el agente en 36 tableros de práctica con 3 segundos cada uno y sumando las fichas que puestas. Con σ en 0.1, 0.2 y 0.3 salió casi lo mismo, así que dejamos 0.2. Con 30 individuos salió un poco mejor que con 8 o 16, entonces dejamos 30. También vimos que el individuo que solo fusiona, sin evolucionar, pone apenas considerablemente menos fichas, así que la evolución sí está haciendo la diferencia.

## Comparación experimental

Se corrieron los dos agentes sobre 6 configuraciones de N, K y M (5×5 con 6 colores, 8×8 con 20, 4×4 con 12, 6×6 con 30, 8×8 con 55 y 10×10 con 65), con 3 instancias por configuración hechas con el generador (semillas 1, 2 y 3) y 10 segundos por corrida. Usamos 3 instancias distintas y no solo 3 semillas del agente porque la búsqueda es determinista y con una sola instancia daría siempre lo mismo. 

En los tableros con pocos colores comparados con el número de celdas los dos pueden ganar. En 5×5 con 6 colores ambos llegan al óptimo (6 celdas ocupadas, una por color), pero el evolutivo termina en 0.05 segundos, mientras que la búsqueda sigue hasta gastar todo el tiempo. En 8×8 con 20 colores la búsqueda pierde las tres instancias, mientras que el evolutivo las gana con el óptimo. Cuando una ficha no se fusiona, la búsqueda la pone en la primera celda libre, va llenando el tablero en orden y encierra colores, retrocede sobre las últimas jugadas y no alcanza a corregir las primeras.

En los tableros donde el número de colores es muy parecido al de celdas ningún agente gana, porque los colores terminan llenando el tablero, ya es tema de quien dure más. El evolutivo pone más fichas que la búsqueda en 4×4 (63 contra 52), pone casi 2 veces más en 6×6 y 8×8, y casi 4  más en 10×10. La ventaja crece con el tablero porque la búsqueda tiene cada vez más jugadas posibles por revisar y como nunca gana, tampoco poda nada. 

