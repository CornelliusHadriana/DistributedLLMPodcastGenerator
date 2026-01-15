import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

model_name = 'mistralai/Mistral-7B-Instruct'

max_seq_length = 2048
dtype = None

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map='auto',
    load_in_8bit=True,
    max_seq_length=max_seq_length
)

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=['q_proj','v_proj'],
    lora_dropout=0.05,
    bias='none',
    task_type='CAUSAL_LM'
)
model = get_peft_model(model, lora_config)

