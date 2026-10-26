### Reconocimiento de caracteres manuscritos Sitelen Pona: comparación de técnicas de entrenamiento para clasificación multiclase de bajos recursos

Natalia Orozco Delgado - 2024099161 
Fernando Andrés González Robles - 2024201276 


https://github.com/natiorozco/HTR-SitelenPona

## Cómo correr la Etapa 2

Todos los comandos se corren desde la raíz del repo.

Instalación:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Etapa_2/data/prepare.py:
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

Etapa_2/torch_models/train.py:
```
python Etapa_2/torch_models/train.py --model cnn --aug none --seed 0
python Etapa_2/torch_models/train.py --model cnn --aug trad --seed 0
python Etapa_2/torch_models/train.py --model resnet18 --aug trad --freeze-epochs 3 --lr 3e-4 --seed 0
```
Búsqueda de hiperparámetros (no guarda predicciones):
```
python Etapa_2/torch_models/train.py --model cnn --aug trad --lr 1e-2 --search
```

Etapa_2/evaluate.py:
```
python Etapa_2/evaluate.py --split val
python Etapa_2/evaluate.py --split test
```