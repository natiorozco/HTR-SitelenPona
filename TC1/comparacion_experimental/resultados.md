# Resultados de la comparación experimental

Límite de tiempo: 10.0 s por corrida.
Cada configuración tiene 3 instancias (semillas 1, 2 y 3).
Los valores son promedio ± desviación estándar entre las 3 semillas.

## Configuraciones

| N | K | M | Celdas (N²) |
|---|---|---|---|
| 5 | 6 | 150 | 25 |
| 8 | 20 | 400 | 64 |
| 4 | 12 | 150 | 16 |
| 6 | 30 | 300 | 36 |
| 8 | 55 | 500 | 64 |
| 10 | 65 | 800 | 100 |

## Resumen por configuración

| Configuración (N, K, M) | Agente | Victorias | Colocadas | Cota colocadas | Ocupadas | Cota ocupadas | Tiempo (s) | Esfuerzo |
|---|---|---|---|---|---|---|---|---|
| 5×5, K=6, M=150 | busqueda | 3/3 | 150.0 ± 0.0 | 150.0 ± 0.0 | 6.0 ± 0.0 | 6.0 ± 0.0 | 9.00 ± 0.00 | 469075 ± 13917 nodos expandidos |
| 5×5, K=6, M=150 | evolutivo | 3/3 | 150.0 ± 0.0 | 150.0 ± 0.0 | 6.0 ± 0.0 | 6.0 ± 0.0 | 0.05 ± 0.02 | 40 ± 17 evaluaciones aptitud |
| 8×8, K=20, M=400 | busqueda | 0/3 | 125.3 ± 15.9 | 400.0 ± 0.0 | 64.0 ± 0.0 | 20.0 ± 0.0 | 9.00 ± 0.00 | 3313911 ± 114523 nodos expandidos |
| 8×8, K=20, M=400 | evolutivo | 3/3 | 400.0 ± 0.0 | 400.0 ± 0.0 | 20.0 ± 0.0 | 20.0 ± 0.0 | 0.44 ± 0.18 | 80 ± 17 evaluaciones aptitud |
| 4×4, K=12, M=150 | busqueda | 0/3 | 52.0 ± 6.2 | 150.0 ± 0.0 | 16.0 ± 0.0 | 12.0 ± 0.0 | 9.01 ± 0.01 | 4270805 ± 29071 nodos expandidos |
| 4×4, K=12, M=150 | evolutivo | 0/3 | 63.3 ± 13.7 | 150.0 ± 0.0 | 16.0 ± 0.0 | 12.0 ± 0.0 | 9.00 ± 0.00 | 24931 ± 5870 evaluaciones aptitud |
| 6×6, K=30, M=300 | busqueda | 0/3 | 48.0 ± 3.5 | 300.0 ± 0.0 | 36.0 ± 0.0 | 30.0 ± 0.0 | 9.02 ± 0.03 | 4177133 ± 291601 nodos expandidos |
| 6×6, K=30, M=300 | evolutivo | 0/3 | 109.0 ± 18.5 | 300.0 ± 0.0 | 36.0 ± 0.0 | 30.0 ± 0.0 | 9.00 ± 0.00 | 5503 ± 675 evaluaciones aptitud |
| 8×8, K=55, M=500 | busqueda | 0/3 | 75.3 ± 2.9 | 500.0 ± 0.0 | 64.0 ± 0.0 | 55.0 ± 0.0 | 9.00 ± 0.00 | 3688541 ± 201382 nodos expandidos |
| 8×8, K=55, M=500 | evolutivo | 0/3 | 149.7 ± 14.6 | 500.0 ± 0.0 | 64.0 ± 0.0 | 55.0 ± 0.0 | 9.00 ± 0.00 | 2111 ± 245 evaluaciones aptitud |
| 10×10, K=65, M=800 | busqueda | 0/3 | 114.7 ± 5.5 | 800.0 ± 0.0 | 100.0 ± 0.0 | 65.0 ± 0.0 | 9.00 ± 0.00 | 2947053 ± 214778 nodos expandidos |
| 10×10, K=65, M=800 | evolutivo | 0/3 | 454.0 ± 15.6 | 800.0 ± 0.0 | 100.0 ± 0.0 | 65.0 ± 0.0 | 9.01 ± 0.00 | 590 ± 17 evaluaciones aptitud |

## Detalle por instancia

| Instancia | Agente | Estado | Colocadas | Ocupadas | Mayor | Tiempo (s) | Esfuerzo |
|---|---|---|---|---|---|---|---|
| gen_N5_K6_M150_s1 | busqueda | victoria | 150 | 6 | 153 | 9.001 | 463490 nodos expandidos |
| gen_N5_K6_M150_s1 | evolutivo | victoria | 150 | 6 | 153 | 0.078 | 60 evaluaciones aptitud |
| gen_N5_K6_M150_s2 | busqueda | victoria | 150 | 6 | 159 | 9.001 | 484917 nodos expandidos |
| gen_N5_K6_M150_s2 | evolutivo | victoria | 150 | 6 | 159 | 0.037 | 30 evaluaciones aptitud |
| gen_N5_K6_M150_s3 | busqueda | victoria | 150 | 6 | 156 | 9.001 | 458818 nodos expandidos |
| gen_N5_K6_M150_s3 | evolutivo | victoria | 150 | 6 | 156 | 0.034 | 30 evaluaciones aptitud |
| gen_N8_K20_M400_s1 | busqueda | derrota | 134 | 64 | 59 | 9.001 | 3382947 nodos expandidos |
| gen_N8_K20_M400_s1 | evolutivo | victoria | 400 | 20 | 126 | 0.234 | 60 evaluaciones aptitud |
| gen_N8_K20_M400_s2 | busqueda | derrota | 135 | 64 | 43 | 9.001 | 3377071 nodos expandidos |
| gen_N8_K20_M400_s2 | evolutivo | victoria | 400 | 20 | 137 | 0.524 | 90 evaluaciones aptitud |
| gen_N8_K20_M400_s3 | busqueda | derrota | 107 | 64 | 22 | 9.001 | 3181715 nodos expandidos |
| gen_N8_K20_M400_s3 | evolutivo | victoria | 400 | 20 | 138 | 0.576 | 90 evaluaciones aptitud |
| gen_N4_K12_M150_s1 | busqueda | derrota | 45 | 16 | 33 | 9.000 | 4296916 nodos expandidos |
| gen_N4_K12_M150_s1 | evolutivo | derrota | 57 | 16 | 39 | 9.001 | 27827 evaluaciones aptitud |
| gen_N4_K12_M150_s2 | busqueda | derrota | 57 | 16 | 46 | 9.000 | 4239479 nodos expandidos |
| gen_N4_K12_M150_s2 | evolutivo | derrota | 54 | 16 | 49 | 9.001 | 28790 evaluaciones aptitud |
| gen_N4_K12_M150_s3 | busqueda | derrota | 54 | 16 | 38 | 9.025 | 4276020 nodos expandidos |
| gen_N4_K12_M150_s3 | evolutivo | derrota | 79 | 16 | 58 | 9.001 | 18175 evaluaciones aptitud |
| gen_N6_K30_M300_s1 | busqueda | derrota | 50 | 36 | 24 | 9.000 | 4404121 nodos expandidos |
| gen_N6_K30_M300_s1 | evolutivo | derrota | 95 | 36 | 37 | 9.002 | 6121 evaluaciones aptitud |
| gen_N6_K30_M300_s2 | busqueda | derrota | 50 | 36 | 37 | 9.056 | 4279020 nodos expandidos |
| gen_N6_K30_M300_s2 | evolutivo | derrota | 130 | 36 | 56 | 9.001 | 4782 evaluaciones aptitud |
| gen_N6_K30_M300_s3 | busqueda | derrota | 44 | 36 | 16 | 9.000 | 3848259 nodos expandidos |
| gen_N6_K30_M300_s3 | evolutivo | derrota | 102 | 36 | 44 | 9.001 | 5605 evaluaciones aptitud |
| gen_N8_K55_M500_s1 | busqueda | derrota | 72 | 64 | 17 | 9.001 | 3459847 nodos expandidos |
| gen_N8_K55_M500_s1 | evolutivo | derrota | 138 | 64 | 37 | 9.001 | 2313 evaluaciones aptitud |
| gen_N8_K55_M500_s2 | busqueda | derrota | 77 | 64 | 31 | 9.001 | 3839344 nodos expandidos |
| gen_N8_K55_M500_s2 | evolutivo | derrota | 166 | 64 | 34 | 9.001 | 1838 evaluaciones aptitud |
| gen_N8_K55_M500_s3 | busqueda | derrota | 77 | 64 | 18 | 9.001 | 3766433 nodos expandidos |
| gen_N8_K55_M500_s3 | evolutivo | derrota | 145 | 64 | 39 | 9.004 | 2183 evaluaciones aptitud |
| gen_N10_K65_M800_s1 | busqueda | derrota | 109 | 100 | 19 | 9.002 | 2774968 nodos expandidos |
| gen_N10_K65_M800_s1 | evolutivo | derrota | 463 | 100 | 83 | 9.004 | 606 evaluaciones aptitud |
| gen_N10_K65_M800_s2 | busqueda | derrota | 120 | 100 | 23 | 9.002 | 2878436 nodos expandidos |
| gen_N10_K65_M800_s2 | evolutivo | derrota | 436 | 100 | 68 | 9.007 | 590 evaluaciones aptitud |
| gen_N10_K65_M800_s3 | busqueda | derrota | 115 | 100 | 25 | 9.003 | 3187756 nodos expandidos |
| gen_N10_K65_M800_s3 | evolutivo | derrota | 463 | 100 | 71 | 9.008 | 573 evaluaciones aptitud |
