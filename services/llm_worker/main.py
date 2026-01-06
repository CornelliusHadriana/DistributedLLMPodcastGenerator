from model import load_model
from worker import worker_loop

model, tokenizer = load_model()
worker_loop(model, tokenizer)