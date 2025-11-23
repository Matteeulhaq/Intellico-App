from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Paths and names
local_model_path = "./models/adapters/gemma-2b"  # folder where your trained LoRA adapter is
base_model_name = "google/gemma-2b-it"           # base model
hub_repo_name = "matteeulhaq/Intellico_Gemma-2b"    # change to your HF username/repo name

# 1️⃣ Load base model
print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(base_model_name)

# 2️⃣ Load LoRA adapter
print("Loading LoRA adapter...")
adapter_model = PeftModel.from_pretrained(base_model, local_model_path)

# 3️⃣ Push adapter to HuggingFace Hub
print(f"Pushing adapter to HuggingFace Hub: {hub_repo_name} ...")
adapter_model.push_to_hub(hub_repo_name, use_auth_token=True)

# 4️⃣ Push tokenizer too
print("Pushing tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(local_model_path)
tokenizer.push_to_hub(hub_repo_name, use_auth_token=True)

print("Done! Your model is now on HuggingFace Hub.")
