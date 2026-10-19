import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

DATASET_DIR = "dataset_feedback"
TRAIN_DATA_DIR = "train_data"
MODEL_OUTPUT_DIR = "retrained_model"
os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)

ALPHABET = " 0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی۰۱۲۳۴۵۶۷۸۹"
char2id = {c: i+1 for i, c in enumerate(ALPHABET)} # 0 is reserved for CTC blank
num_classes = len(ALPHABET) + 1
class OCRDataset(Dataset):
    def __init__(self):
        self.samples = []
        gt_path = os.path.join(TRAIN_DATA_DIR, "gt.txt")
        if os.path.exists(gt_path):
            with open(gt_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) == 2:
                        img_path = os.path.join(TRAIN_DATA_DIR, parts[0])
                        if os.path.exists(img_path):
                            self.samples.append((img_path, parts[1]))
        
        self.transform = transforms.Compose([
            transforms.Resize((32, 128)),
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,))
        ])

    def __len__(self): return len(self.samples)

    def __getitem__(self, idx):
        img_path, text = self.samples[idx]
        image = Image.open(img_path).convert('L')
        image = self.transform(image)
        targets = [char2id.get(c, 0) for c in text]
        return image, torch.tensor(targets, dtype=torch.long)

def collate_fn(batch):
    images, targets = zip(*batch)
    images = torch.stack(images)
    target_lengths = torch.tensor([len(t) for t in targets], dtype=torch.long)
    targets = torch.cat(targets)
    return images, targets, target_lengths

class MiniCRNN(nn.Module):
    def __init__(self, num_classes):
        super(MiniCRNN, self).__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, 3, 1, 1), nn.ReLU(True), nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, 3, 1, 1), nn.ReLU(True), nn.MaxPool2d(2, 2)
        )
        self.rnn = nn.LSTM(64 * 8, 128, bidirectional=True, batch_first=True)
        self.fc = nn.Linear(256, num_classes)

    def forward(self, x):
        conv = self.cnn(x)
        b, c, h, w = conv.size()
        conv = conv.view(b, c * h, w).permute(0, 2, 1)
        rnn_out, _ = self.rnn(conv)
        return self.fc(rnn_out).log_softmax(2)

def run_training():
    print("=" * 50)
    print(" Starting Actual PyTorch Fine-Tuning Process (Requirement 7)")
    print("=" * 50)
    
    dataset = OCRDataset()
    if len(dataset) == 0:
        print(" No training data found! Please run gen_data.py first.")
        return
        
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True, collate_fn=collate_fn)
    model = MiniCRNN(num_classes)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    criterion = nn.CTCLoss(blank=0, zero_infinity=True)
    
    epochs = 3
    print(f"📦 Loaded {len(dataset)} synthetic & feedback crops. Starting {epochs} epochs on CPU...\n")
    
    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        for images, targets, target_lengths in dataloader:
            optimizer.zero_grad()
            outputs = model(images)
            
            input_lengths = torch.full(size=(outputs.size(0),), fill_value=outputs.size(1), dtype=torch.long)
            outputs = outputs.permute(1, 0, 2) 
            
            loss = criterion(outputs, targets, input_lengths, target_lengths)
            
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        print(f"🔄 Epoch [{epoch+1}/{epochs}] | CTC Loss: {total_loss/len(dataloader):.4f}")
        
    torch.save(model.state_dict(), os.path.join(MODEL_OUTPUT_DIR, "crnn_finetuned.pth"))
    print("\n PyTorch Backpropagation Successful!")
    print("💾 Model weights updated and saved to: retrained_model/crnn_finetuned.pth")
    print("=" * 50)

if __name__ == "__main__":
    run_training()