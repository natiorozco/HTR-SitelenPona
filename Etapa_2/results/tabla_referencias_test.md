# Comparación contra las referencias (test)

| Referencia | Modelo | Semillas | Top-1 | Top-5 | Macro-F1 | Δ macro-F1 vs HOG + LR |
|---|---|---|---|---|---|---|
| trivial | dummy_estratificada | 5 | 0.99% ± 0.26% | 4.31% ± 0.24% | 0.94% ± 0.24% | -88.65 pp |
| trivial | dummy_mayoritaria | 1 | 0.69% ± 0.00% | 3.55% ± 0.00% | 0.01% ± 0.00% | -89.59 pp |
| clásica (ablación) | pixels_lr | 1 | 67.67% ± 0.00% | 87.92% ± 0.00% | 66.53% ± 0.00% | -23.07 pp |
| clásica | hog_lr | 1 | 89.72% ± 0.00% | 96.50% ± 0.00% | 89.60% ± 0.00% | — |
| literatura | hcrnet_aug | 5 | 96.77% ± 0.21% | 99.14% ± 0.05% | 96.67% ± 0.20% | +7.07 pp |
| literatura | hcrnet_aug_elastica | 5 | 96.68% ± 0.14% | 99.09% ± 0.18% | 96.61% ± 0.11% | +7.01 pp |
| literatura | hcrnet_sinaug | 5 | 96.61% ± 0.15% | 99.16% ± 0.07% | 96.53% ± 0.19% | +6.93 pp |
| propia | cnn_aug | 5 | 96.94% ± 0.07% | 99.26% ± 0.03% | 96.76% ± 0.09% | +7.16 pp |
| propia | cnn_sinaug | 5 | 96.08% ± 0.18% | 98.93% ± 0.09% | 95.93% ± 0.24% | +6.33 pp |
| propia | resnet18_aug | 5 | 97.57% ± 0.29% | 99.39% ± 0.06% | 97.45% ± 0.33% | +7.85 pp |

**Valores publicados (no directamente comparables).** HCR-Net reporta 99.31 % de exactitud en
HWRGurmukhi_1.1 (35 clases, un escritor, 100 muestras por clase) y 96.53 % en HWRGurmukhi_1.3
(35 clases, 100 escritores, una muestra por clase y escritor), con partición aleatoria 80:20 y la
exactitud de la última época. La CNN de Rahman et al. reporta 85.96 % en bengalí (50 clases, ~400
muestras por clase). Aquí hay 132 palabras, 52–133 muestras por clase, partición agrupada por sesión y
selección de época por validación, así que esos números sirven como orden de magnitud, no como
comparación directa. Las cifras publicadas son exactitud top-1, no macro-F1.
