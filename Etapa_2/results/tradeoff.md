# Trade-off entre desempeño y costo (macro-F1 en test)

| Modelo | Rol | Semillas | Macro-F1 | Parámetros | s entrenamiento | ms/imagen | Mejor época | Dispositivo |
|---|---|---|---|---|---|---|---|---|
| dummy_estratificada | trivial | 5 | 0.0094 ± 0.0024 | - | - | - | - | - |
| dummy_mayoritaria | trivial | 1 | 0.0001 | - | - | - | - | - |
| pixels_lr | clásica (ablación) | 1 | 0.6653 | - | - | - | - | - |
| hog_lr | clásica | 1 | 0.8960 | - | - | - | - | - |
| hcrnet_aug | literatura | 5 | 0.9667 ± 0.0020 | 9,804,229 | 831.5 ± 234.7 | 0.667 ± 0.002 | 34.0 ± 10.4 | cpu |
| hcrnet_aug_elastica | literatura | 5 | 0.9661 ± 0.0011 | 9,804,229 | 656.0 ± 147.4 | 0.665 ± 0.001 | 25.8 ± 6.2 | cpu |
| hcrnet_sinaug | literatura | 5 | 0.9653 ± 0.0019 | 9,804,229 | 693.4 ± 20.8 | 0.668 ± 0.000 | 43.6 ± 5.0 | cpu |
| cnn_aug | propia | 5 | 0.9676 ± 0.0009 | 846,053 | 139.3 ± 18.7 | 0.028 ± 0.000 | 42.6 ± 6.9 | mps |
| cnn_sinaug | propia | 5 | 0.9593 ± 0.0024 | 846,053 | 36.6 ± 8.4 | 0.028 ± 0.000 | 32.8 ± 9.4 | mps |
| resnet18_aug | propia | 5 | 0.9745 ± 0.0033 | 11,244,741 | 456.3 ± 91.0 | 0.112 ± 0.000 | 27.2 ± 7.0 | mps |

Los segundos y ms/imagen solo son comparables entre corridas del mismo dispositivo; las que tienen un valor distinto en Dispositivo corrieron en otro hardware.

## Comparabilidad

Se entrenó en más de un dispositivo:
- hcrnet_aug: cpu
- hcrnet_aug_elastica: cpu
- hcrnet_sinaug: cpu
- cnn_aug: mps
- cnn_sinaug: mps
- resnet18_aug: mps

Los baselines clásicos (dummy, píxeles + LR, HOG + LR) no son redes neuronales; no tienen parámetros que valga la pena contar, y su costo está en el ajuste del hiperparámetro, no en una corrida repetible. Por eso van con guion en esas columnas.

## Relaciones de costo frente a cnn_sinaug

- cnn_aug: macro-F1 0.9676 ± 0.0009, 1.0x los parámetros, 3.8x el tiempo de entrenamiento (mps vs mps), 1.0x el ms/imagen, +7.16 pp de macro-F1 frente a hog_lr.
- resnet18_aug: macro-F1 0.9745 ± 0.0033, 13.3x los parámetros, 12.5x el tiempo de entrenamiento (mps vs mps), 4.0x el ms/imagen, +7.85 pp de macro-F1 frente a hog_lr.
- hcrnet_sinaug: macro-F1 0.9653 ± 0.0019, 11.6x los parámetros, tiempo de entrenamiento no comparable (mps vs cpu), 23.9x el ms/imagen, +6.93 pp de macro-F1 frente a hog_lr.
- hcrnet_aug: macro-F1 0.9667 ± 0.0020, 11.6x los parámetros, tiempo de entrenamiento no comparable (mps vs cpu), 23.8x el ms/imagen, +7.07 pp de macro-F1 frente a hog_lr.
