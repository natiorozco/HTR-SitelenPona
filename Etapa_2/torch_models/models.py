"""Modelos en PyTorch: CNN simple desde cero y ResNet18 preentrenada."""

import torch.nn as nn
from torchvision.models import ResNet18_Weights, resnet18


class SimpleCNN(nn.Module):
    """CNN entrenada desde cero, entrada de 32x32"""

    def __init__(self, n_classes, dropout=0.3):
        super().__init__()

        def block(c_in, c_out):
            return nn.Sequential(
                nn.Conv2d(c_in, c_out, 3, padding=1), nn.BatchNorm2d(c_out), nn.ReLU(),
                nn.Conv2d(c_out, c_out, 3, padding=1), nn.BatchNorm2d(c_out), nn.ReLU(),
                nn.MaxPool2d(2),
            )

        
        self.features = nn.Sequential(block(1, 32), block(32, 64), block(64, 128))
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Dropout(dropout),
            nn.Linear(128 * 4 * 4, 256), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(256, n_classes),
        )

    def forward(self, x):
        return self.classifier(self.features(x))

    def head_parameters(self):
        return self.classifier.parameters()


class ResNet18Transfer(nn.Module):
    """ResNet18 preentrenada en ImageNet, con entrada de 64x64."""

    def __init__(self, n_classes, dropout=0.3):
        super().__init__()
        self.net = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
        self.net.fc = nn.Sequential(nn.Dropout(dropout), nn.Linear(self.net.fc.in_features, n_classes))

    def forward(self, x):
        return self.net(x.expand(-1, 3, -1, -1))

    def head_parameters(self):
        return self.net.fc.parameters()


MODELS = {"cnn": (SimpleCNN, 32), "resnet18": (ResNet18Transfer, 64)}
