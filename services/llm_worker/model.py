import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def load_model(model_name: str="meta-llama/Llama-3.1-8B-Instruct"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        dtype=torch.float16,
        trust_remote_code=True
    )
    return model, tokenizer