"""Entrena HCR-Net (Chauhan et al., 2024) en TensorFlow/Keras, adaptado de la implementación oficial
(github.com/jmdvinodjmd/HCR-Net, licencia MIT) al protocolo común del proyecto.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import keras
import numpy as np
import tensorflow as tf
from keras import layers
# el mismo ImageDataGenerator del código oficial; Keras 3.12+ ya no lo expone en keras.preprocessing
from keras.src.legacy.preprocessing.image import ImageDataGenerator
from scipy.ndimage import gaussian_filter, map_coordinates
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import PROCESSED_DIR, RESULTS_DIR, load_data, subclass_to_word, write_log, write_preds

SIZE = 32
VGG_LAYERS = 12  # block1_conv1 ... block4_conv2 (layers[:-6] en el código oficial)
WARMUP_FASE2 = 5  # el calendario oficial de la fase 2 empieza con 5 épocas a lr 1e-7
MODELS_DIR = RESULTS_DIR / "modelos"


def lr_fase1(epoch):
    return 1e-4 if epoch < 5 else 5e-5


def lr_fase2(epochs2):
    """Generaliza decayed_learning_rate_tuned{20,30,50,...} de learning_rate.py."""
    def schedule(epoch):
        if epoch < WARMUP_FASE2:
            return 1e-7
        return 5e-6 if epoch < epochs2 - 5 else 1e-6
    return schedule


def elastic(alpha, sigma, p, rng):
    """Distorsión elástica equivalente a v2.ElasticTransform de train.py (desplazamiento = alpha/2 px)."""
    def transform(x):
        if rng.random() >= p:
            return x
        h, w = x.shape[:2]
        dy = gaussian_filter(rng.uniform(-1, 1, (h, w)), sigma) * alpha / 2
        dx = gaussian_filter(rng.uniform(-1, 1, (h, w)), sigma) * alpha / 2
        i, j = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
        return map_coordinates(x[..., 0], [i + dy, j + dx], order=1, cval=0)[..., None]
    return transform


def build_augmentation(aug, elastica, seed):
    """Rangos de HCR-Net, iguales a los de train.py. Sin volteos."""
    if aug == "none":
        return ImageDataGenerator()
    extra = {"preprocessing_function": elastic(SIZE / 2, SIZE / 8, 0.5, np.random.default_rng(seed))}
    return ImageDataGenerator(rotation_range=10, width_shift_range=0.05, height_shift_range=0.05,
                              zoom_range=0.05, shear_range=0.5, fill_mode="constant", cval=0,
                              **(extra if elastica else {}))


def build_model(n_classes, mean, std, dropout):
    """VGG16 de ImageNet hasta block4_conv2 + la cabeza densa de HCR-Net.

    La normalización y la réplica del gris a 3 canales van dentro del modelo, así recibe la imagen en [0, 1].
    """
    vgg = keras.applications.VGG16(include_top=False, weights="imagenet", input_shape=(SIZE, SIZE, 3))
    vgg_layers = vgg.layers[1:VGG_LAYERS + 1]
    inputs = keras.Input((SIZE, SIZE, 1))
    x = layers.Normalization(mean=mean, variance=std ** 2)(inputs)
    x = layers.Concatenate()([x, x, x])
    for layer in vgg_layers:
        x = layer(x)
    x = layers.BatchNormalization()(x)
    x = layers.Flatten()(x)
    for _ in range(2):
        x = layers.Dense(512, activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(dropout)(x)
    outputs = layers.Dense(n_classes, activation="softmax")(x)
    return keras.Model(inputs, outputs, name="hcrnet"), vgg_layers


class MejorMacroF1(keras.callbacks.Callback):
    """Early stopping por macro-F1 de validación por palabra; guarda los pesos de la mejor época."""

    def __init__(self, X_val, y_val, words_val, M, words, patience):
        super().__init__()
        self.X_val, self.y_val, self.words_val = X_val, y_val, words_val
        self.M, self.words, self.patience = M, words, patience
        self.history, self.best = [], {"f1": -1.0, "epoch": 0, "weights": None}
        self.epoch, self.fase, self.inicio_paciencia = 0, 1, 0

    def on_epoch_end(self, epoch, logs=None):
        self.epoch += 1
        proba = self.model.predict(self.X_val, batch_size=256, verbose=0)
        val_loss = float(-np.log(proba[np.arange(len(self.y_val)), self.y_val] + 1e-12).mean())
        val_pred = self.words[(proba @ self.M).argmax(1)]
        val_acc = float((val_pred == self.words_val).mean())
        val_f1 = f1_score(self.words_val, val_pred, average="macro")
        lr = float(keras.ops.convert_to_numpy(self.model.optimizer.learning_rate))
        self.history.append({"epoca": self.epoch, "fase": self.fase, "train_loss": logs["loss"],
                             "train_acc": logs["accuracy"], "val_loss": val_loss, "val_acc": val_acc,
                             "val_macro_f1": val_f1, "lr": lr})
        print(f"época {self.epoch:3d} (fase {self.fase})  train loss {logs['loss']:.3f} "
              f"acc {logs['accuracy']:.3f}  val loss {val_loss:.3f} acc {val_acc:.3f} macro-F1 {val_f1:.3f}")

        if val_f1 > self.best["f1"]:
            self.best = {"f1": val_f1, "epoch": self.epoch, "weights": self.model.get_weights()}
        elif self.epoch - max(self.best["epoch"], self.inicio_paciencia) >= self.patience:
            print(f"early stopping (fase {self.fase}): sin mejora desde la época {self.best['epoch']}")
            self.model.stop_training = True


def get_device():
    gpus = tf.config.list_physical_devices("GPU")
    if not gpus:
        return "cpu"
    return f"gpu ({tf.config.experimental.get_device_details(gpus[0]).get('device_name', 'desconocida')})"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aug", choices=["none", "trad"], default="none")
    parser.add_argument("--elastica", action="store_true",
                        help="agrega la distorsión elástica de train.py (Keras no la trae)")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs1", type=int, help="máximo de épocas de la fase 1 (30 sin aumento, 10 con)")
    parser.add_argument("--epochs2", type=int, help="máximo de épocas de la fase 2 (20 sin aumento, 50 con)")
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--dropout", type=float, default=0.35)
    parser.add_argument("--patience", type=int, default=8, help="épocas sin mejorar val macro-F1")
    parser.add_argument("--search", action="store_true",
                        help="para la búsqueda de hiperparámetros: guarda el log pero no predicciones")
    args = parser.parse_args()
    if args.elastica and args.aug == "none":
        parser.error("--elastica requiere --aug trad")
    args.epochs1 = args.epochs1 or (10 if args.aug == "trad" else 30)
    args.epochs2 = args.epochs2 or (50 if args.aug == "trad" else 20)

    keras.utils.set_random_seed(args.seed)
    tf.config.experimental.enable_op_determinism()
    device = get_device()
    name = "hcrnet_" + ("sinaug" if args.aug == "none" else "aug_elastica" if args.elastica else "aug")

    X, meta = load_data(SIZE)
    X = X[..., None].astype("float32") / 255
    with open(PROCESSED_DIR / f"norm_stats{SIZE}.json") as f:
        stats = json.load(f)
    subclases = np.array(sorted(set(meta["subclase"])))
    y = np.searchsorted(subclases, meta["subclase"])
    M, words = subclass_to_word(subclases)
    train, val = meta["split"] == "train", meta["split"] == "val"

    train_flow = build_augmentation(args.aug, args.elastica, args.seed).flow(
        X[train], y[train], batch_size=args.batch, shuffle=True, seed=args.seed)
    model, vgg_layers = build_model(len(subclases), stats["mean"], stats["std"], args.dropout)
    tracker = MejorMacroF1(X[val], y[val], meta["clase"][val], M, words, args.patience)

    def run_fase(trainable, epochs, schedule):
        for layer in vgg_layers:
            layer.trainable = trainable
        model.compile(optimizer=keras.optimizers.RMSprop(), loss="sparse_categorical_crossentropy",
                      metrics=["accuracy"])
        model.fit(train_flow, epochs=epochs, verbose=0,
                  callbacks=[keras.callbacks.LearningRateScheduler(schedule), tracker])

    start = time.perf_counter()
    run_fase(False, args.epochs1, lr_fase1)
    epocas_fase1 = tracker.epoch
    # la fase 2 sigue desde la última época de la fase 1, como en el código oficial
    tracker.fase, tracker.inicio_paciencia = 2, tracker.epoch + WARMUP_FASE2
    run_fase(True, args.epochs2, lr_fase2(args.epochs2))
    train_seconds = time.perf_counter() - start
    # mismo criterio que torch: parámetros entrenables, sin las estadísticas de BatchNorm
    n_params = int(sum(np.prod(w.shape) for w in model.trainable_weights))

    best = tracker.best
    model.set_weights(best["weights"])
    start = time.perf_counter()
    proba = model.predict(X, batch_size=256, verbose=0)
    ms_per_image = (time.perf_counter() - start) / len(y) * 1000

    run = f"{name}_seed{args.seed}"
    log = {"modelo": name, "semilla": args.seed, "config": vars(args), "dispositivo": device,
           "versiones": {"tensorflow": tf.__version__, "keras": keras.__version__},
           "parametros": n_params, "segundos_entrenamiento": round(train_seconds, 1),
           "ms_inferencia_por_imagen": round(ms_per_image, 3), "epocas_fase1": epocas_fase1,
           "mejor_epoca": best["epoch"], "mejor_val_macro_f1": round(best["f1"], 4),
           "historial": tracker.history}
    if args.search:
        tag = f"e{args.epochs1}+{args.epochs2}_b{args.batch}_d{args.dropout}"
        write_log(f"busqueda/{run}_{tag}", log)
    else:
        write_log(run, log)
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        model.save(MODELS_DIR / f"{run}.keras")
        path = write_preds(name, args.seed, meta["id"], meta["split"], meta["clase"], proba, subclases)
        print(f"-> {path.name}")
    print(f"mejor época {best['epoch']}, val macro-F1 {best['f1']:.4f}, {train_seconds:.0f} s en {device}")


if __name__ == "__main__":
    main()
