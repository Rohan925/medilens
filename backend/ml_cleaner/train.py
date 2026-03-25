import torch
import pandas as pd
from ml_cleaner.model import OCRCleaner
from ml_cleaner.tokenizer import encode, char2idx


df = pd.read_csv("data/train.csv")

X = torch.tensor([encode(x) for x in df["input"]])
Y = torch.tensor([encode(y) for y in df["output"]])

model = OCRCleaner(len(char2idx))
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
loss_fn = torch.nn.CrossEntropyLoss()

for epoch in range(20):
    optimizer.zero_grad()
    out = model(X)
    loss = loss_fn(out.view(-1, len(char2idx)), Y.view(-1))
    loss.backward()
    optimizer.step()
    print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")

torch.save(model.state_dict(), "ocr_cleaner.pt")
