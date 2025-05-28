import torch
import torch.nn as nn

class Predictor(nn.Module):
    def __init__(self):
        super(Predictor, self).__init__()
        self.fc = nn.Linear(10, 1)

    def forward(self, x):
        return torch.sigmoid(self.fc(x))