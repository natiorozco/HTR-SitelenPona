### Reconocimiento de caracteres manuscritos Sitelen Pona: comparación de técnicas de entrenamiento para clasificación multiclase de bajos recursos

Natalia Orozco Delgado - 2024099161 
Fernando Andrés González Robles - 2024201276 
Valeska Brenes Picado - 2021031484


https://github.com/natiorozco/HTR-SitelenPona

## Dataset

Se usa [sitelen pona handwritten SVG samples](https://archive.org/details/sitelen-pona-handwritten-svg-samples), un conjunto público de glifos manuscritos de *sitelen pona* recolectado por la comunidad de Toki Pona  y publicado en Internet Archive bajo licencia [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) (dominio público). Las imágenes están en `Etapa_2/sitelen-pona-handwritten-png-samples/`, una carpeta por palabra.

## Cómo correr la Etapa 2

Todos los comandos se corren desde la raíz del repo.

### Instalación

HCR-Net usa TensorFlow, que necesita Python 3.13 o anterior. Con un entorno de Python 3.13 corre todo:
```
python3.13 -m venv .venv-tf
source .venv-tf/bin/activate
pip install -r requirements.txt
```

### Correr todo

Los resultados reportados en el artículo se obtuvieron así, en una MacBook Pro M4 Pro (PyTorch en la GPU con MPS y TensorFlow en CPU), en unas 5 horas:
```
python Etapa_2/correr_local.py --desde-cero
```
Corre en orden los baselines, la búsqueda de hiperparámetros, las 5 semillas de cada modelo con la configuración elegida, la evaluación, el trade-off y Grad-CAM. Si se interrumpe, correrlo sin `--desde-cero` sigue donde quedó.

Alternativa en Colab: abrir `Etapa_2/correr_etapa2.ipynb` y ejecutar las celdas en orden. Respalda los resultados en Google Drive. No se usó para los resultados reportados por los límites de uso de Colab.

### Correr cada paso por separado

Etapa_2/data/prepare.py (solo si cambia el dataset; correrlo con las versiones de `requirements.txt` y commitear `data/processed/`, porque otra versión de scikit-learn da otra partición):
```
python Etapa_2/data/prepare.py
```

Etapa_2/baselines/dummy.py:
```
python Etapa_2/baselines/dummy.py
```

Etapa_2/baselines/hog_lr.py:
```
python Etapa_2/baselines/hog_lr.py --features pixels
python Etapa_2/baselines/hog_lr.py --features hog
```

Etapa_2/torch_models/train.py, con la configuración elegida en la búsqueda (cambiar `--seed` de 0 a 4):
```
python Etapa_2/torch_models/train.py --model cnn --aug none --lr 0.001 --batch 128 --seed 0
python Etapa_2/torch_models/train.py --model cnn --aug trad --lr 0.001 --batch 128 --seed 0
python Etapa_2/torch_models/train.py --model resnet18 --aug trad --lr 0.001 --batch 64 --freeze-epochs 0 --seed 0
```
Una corrida de la búsqueda de hiperparámetros (no guarda predicciones; la grilla completa está en `correr_local.py`):
```
python Etapa_2/torch_models/train.py --model cnn --aug trad --lr 0.0003 --batch 64 --seed 0 --search
```

Etapa_2/hcrnet/train_hcrnet.py (configuración oficial de HCR-Net; cambiar `--seed` de 0 a 4):
```
python Etapa_2/hcrnet/train_hcrnet.py --aug none --seed 0
python Etapa_2/hcrnet/train_hcrnet.py --aug trad --seed 0
python Etapa_2/hcrnet/train_hcrnet.py --aug trad --elastica --seed 0
```
Prueba rápida (no guarda predicciones):
```
python Etapa_2/hcrnet/train_hcrnet.py --aug trad --epochs1 2 --epochs2 2 --search
```

Etapa_2/evaluate.py (métricas, curvas, confusiones, errores y tabla de referencias en results/ y results/figuras/):
```
python Etapa_2/evaluate.py --split val
python Etapa_2/evaluate.py --split test
```

Etapa_2/tradeoff.py (tabla de costo frente a desempeño; salida en results/tradeoff.md):
```
python Etapa_2/tradeoff.py
```

Etapa_2/xai/gradcam_torch.py y gradcam_tf.py (necesitan los pesos que guardan train.py y train_hcrnet.py; figuras en results/figuras/):
```
python Etapa_2/xai/gradcam_torch.py --model cnn --aug none --seed 0
python Etapa_2/xai/gradcam_torch.py --model cnn --aug trad --seed 0
python Etapa_2/xai/gradcam_torch.py --model resnet18 --aug trad --seed 0
python Etapa_2/xai/gradcam_tf.py --run hcrnet_aug --seed 0
```

### Resultados

Quedan en `Etapa_2/results/`: métricas (`metricas_test.csv`, `metricas_val.csv`), trade-off (`tradeoff.md`), configuración elegida (`configuracion_elegida.json`), predicciones por corrida (`preds/`), registros con configuración, tiempos e historial por época (`logs/`) y figuras (`figuras/`). La salida completa de la corrida está en `Etapa_2/corrida_local.log`. Los pesos de los modelos (`results/modelos/`) no se suben al repositorio.
