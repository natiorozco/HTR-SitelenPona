# Trade-off entre desempeño y costo (macro-F1 en test)

| Modelo | Rol | Semillas | Macro-F1 | Parámetros | s entrenamiento | ms/imagen | Mejor época | Dispositivo |
|---|---|---|---|---|---|---|---|---|
| dummy_estratificada | trivial | 5 | 0.0077 ± 0.0006 | - | - | - | - | - |
| dummy_mayoritaria | trivial | 1 | 0.0001 | - | - | - | - | - |
| pixels_lr | clásica (ablación) | 1 | 0.6812 | - | - | - | - | - |
| hog_lr | clásica | 1 | 0.9015 | - | - | - | - | - |
| cnn_sinaug | propia | 1 | 0.9582 | 846,310 | 43.7 | 0.028 | 35.0 | mps |

Los segundos y ms/imagen solo son comparables entre corridas del mismo dispositivo; las que tienen un valor distinto en Dispositivo corrieron en otro hardware.

Los baselines clásicos (dummy, píxeles + LR, HOG + LR) no son redes neuronales; no tienen parámetros que valga la pena contar, y su costo está en el ajuste del hiperparámetro, no en una corrida repetible. Por eso van con guion en esas columnas.

## Relaciones de costo frente a cnn_sinaug

