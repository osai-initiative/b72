"""Inference for neuralese_translator.pt.

The neuralese lang has been dubbed "kalrean".
"""

from __future__ import annotations

import argparse

import torch
import torch.nn as nn

KALREAN_TOKENS = []
ENGLISH_WORDS = []

PAD = "<PAD>"
UNK = "<UNK>"
MAX_INPUT_TOKENS = 32

INPUT_STOI = {PAD: 0, UNK: 1}


class ResidualConvBlock(nn.Module):
    def __init__(self, channels: int, dilation: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(channels, channels, kernel_size=3, padding=dilation, dilation=dilation),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Conv1d(channels, channels, kernel_size=1),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.norm = nn.GroupNorm(1, channels)

    def forward(self, x):
        return self.norm(x + self.net(x))


class NeuraleseTranslator(nn.Module):
    def __init__(self):
        super().__init__()
        embed_dim = 128
        channels = 256
        dropout = 0.10

        self.embedding = nn.Embedding(len(INPUT_STOI), embed_dim, padding_idx=INPUT_STOI[PAD])
        self.input_conv = nn.Conv1d(embed_dim, channels, kernel_size=3, padding=1)
        self.blocks = nn.Sequential(
            ResidualConvBlock(channels, 1, dropout),
            ResidualConvBlock(channels, 2, dropout),
            ResidualConvBlock(channels, 4, dropout),
            ResidualConvBlock(channels, 1, dropout),
        )
        self.head = nn.Sequential(
            nn.Linear(channels * 2, 512),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(512, len(ENGLISH_WORDS)),
        )

    def forward(self, token_ids):
        mask = token_ids.ne(INPUT_STOI[PAD])
        x = self.embedding(token_ids).transpose(1, 2)
        x = self.input_conv(x)
        x = self.blocks(x)

        masked = x.masked_fill(~mask.unsqueeze(1), -1e4)
        max_pool = masked.max(dim=2).values
        weights = mask.unsqueeze(1).float()
        mean_pool = (x * weights).sum(dim=2) / weights.sum(dim=2).clamp_min(1.0)
        return self.head(torch.cat([max_pool, mean_pool], dim=1))


def encode(text: str):
    tokens = text.strip().split()[:MAX_INPUT_TOKENS]
    ids = [INPUT_STOI.get(token, INPUT_STOI[UNK]) for token in tokens]
    ids += [INPUT_STOI[PAD]] * (MAX_INPUT_TOKENS - len(ids))
    return tokens, torch.tensor([ids], dtype=torch.long)


@torch.inference_mode()
def probabilities(model, text: str, device: torch.device):
    _, ids = encode(text)
    logits = model(ids.to(device))[0]
    return torch.sigmoid(logits).cpu()


@torch.inference_mode()
def translate(model, text: str, device: torch.device, threshold: float, max_words: int):
    tokens, _ = encode(text)
    if not tokens:
        return ""

    full_probs = probabilities(model, text, device)
    selected = {
        i for i, p in enumerate(full_probs.tolist())
        if p >= threshold
    }

    if not selected:
        top = torch.topk(full_probs, k=min(max_words, len(ENGLISH_WORDS))).indices.tolist()
        selected = set(top)

    ordered = []
    used = set()
    for token in tokens:
        token_probs = probabilities(model, token, device)
        ranked = torch.argsort(token_probs, descending=True).tolist()
        for i in ranked:
            if i in selected and i not in used:
                ordered.append(i)
                used.add(i)

    remaining = sorted(selected - used, key=lambda i: float(full_probs[i]), reverse=True)
    ordered.extend(remaining)
    ordered = ordered[:max_words]

    return " ".join(ENGLISH_WORDS[i] for i in ordered)


def load_model(weights: str, device: torch.device):
    global KALREAN_TOKENS, ENGLISH_WORDS, INPUT_STOI

    checkpoint = torch.load(weights, map_location="cpu", weights_only=True)
    KALREAN_TOKENS = checkpoint["neuralese_vocab"]
    ENGLISH_WORDS = checkpoint["english_vocab"]
    INPUT_STOI = {
        PAD: 0,
        UNK: 1,
        **{token: i + 2 for i, token in enumerate(KALREAN_TOKENS)},
    }

    model = NeuraleseTranslator().to(device)
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    model.eval()
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("text", nargs="*")
    parser.add_argument("--weights", default="neuralese_translator.pt")
    parser.add_argument("--threshold", type=float, default=0.45)
    parser.add_argument("--max-words", type=int, default=40)
    args = parser.parse_args()

    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    model = load_model(args.weights, device)

    if args.text:
        text = " ".join(args.text)
        print(translate(model, text, device, args.threshold, args.max_words))
        return

    print("Neuralese translator. Type 'exit' to quit.")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text.lower() in {"exit", "quit"}:
            break
        print(translate(model, text, device, args.threshold, args.max_words))


if __name__ == "__main__":
    main()
