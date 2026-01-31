import torch
import torch.nn as nn
import torch.nn.functional as F

class ConvNetSimple(nn.Module):
    def __init__(self, input_channels=1):
        super(ConvNetSimple, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(input_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(32),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(64),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(128),
        )
        
        # We'll use adaptive pooling to ensure the correct output size
        self.adaptive_pool = nn.AdaptiveAvgPool2d((25, 25))
        
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 25 * 25, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        x = self.features(x)
        x = self.adaptive_pool(x)  # Ensure correct dimensions before flattening
        x = self.classifier(x)
        return x
