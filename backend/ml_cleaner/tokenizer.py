import string

CHARS = string.ascii_lowercase + string.digits + " ."
PAD = "<PAD>"

vocab = [PAD] + list(CHARS)
char2idx = {c: i for i, c in enumerate(vocab)}
idx2char = {i: c for c, i in char2idx.items()}

def encode(text, max_len=100):
    text = text.lower()[:max_len]
    ids = [char2idx.get(c, 0) for c in text]
    return ids + [0] * (max_len - len(ids))

def decode(ids):
    return "".join(idx2char[i] for i in ids if i != 0)
