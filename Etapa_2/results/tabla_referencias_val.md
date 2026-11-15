# Comparación contra las referencias (val)

| Referencia | Modelo | Semillas | Top-1 | Top-5 | Macro-F1 | Δ macro-F1 vs HOG + LR |
|---|---|---|---|---|---|---|
| trivial | dummy_estratificada | 5 | 0.74% ± 0.18% | 3.60% ± 0.22% | 0.72% ± 0.19% | -87.36 pp |
| trivial | dummy_mayoritaria | 1 | 1.20% ± 0.00% | 4.81% ± 0.00% | 0.02% ± 0.00% | -88.07 pp |
| clásica (ablación) | pixels_lr | 1 | 65.94% ± 0.00% | 86.71% ± 0.00% | 64.91% ± 0.00% | -23.18 pp |
| clásica | hog_lr | 1 | 88.57% ± 0.00% | 96.72% ± 0.00% | 88.08% ± 0.00% | — |
| literatura | hcrnet_aug | 5 | 95.49% ± 0.23% | 98.34% ± 0.08% | 95.40% ± 0.22% | +7.32 pp |
| literatura | hcrnet_aug_elastica | 5 | 95.45% ± 0.26% | 98.38% ± 0.13% | 95.34% ± 0.27% | +7.26 pp |
| literatura | hcrnet_sinaug | 5 | 95.40% ± 0.22% | 98.12% ± 0.15% | 95.30% ± 0.24% | +7.22 pp |
| propia | cnn_aug | 5 | 95.52% ± 0.26% | 98.12% ± 0.13% | 95.43% ± 0.26% | +7.35 pp |
| propia | cnn_sinaug | 5 | 94.67% ± 0.26% | 97.71% ± 0.14% | 94.60% ± 0.31% | +6.52 pp |
| propia | resnet18_aug | 5 | 96.00% ± 0.14% | 98.15% ± 0.16% | 95.96% ± 0.12% | +7.88 pp |

**Valores publicados (no directamente comparables).** HCR-Net reporta 99.31 % de exactitud en
HWRGurmukhi_1.1 (35 clases, un escritor, 100 muestras por clase) y 96.53 % en HWRGurmukhi_1.3
(35 clases, 100 escritores, una muestra por clase y escritor), con partición aleatoria 80:20 y la
exactitud de la última época. La CNN de Rahman et al. reporta 85.96 % en bengalí (50 clases, ~400
muestras por clase). Aquí hay 132 palabras, 52–133 muestras por clase, partición agrupada por sesión y
selección de época por validación, así que esos números sirven como orden de magnitud, no como
comparación directa. Las cifras publicadas son exactitud top-1, no macro-F1.
