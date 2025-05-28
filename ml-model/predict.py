import torch
from model import Predictor

def predict(input_tensor):
    model = Predictor()
    # model.load_state_dict(torch.load('model.pth'))  # Uncomment when trained
    model.eval()
    return model(input_tensor)