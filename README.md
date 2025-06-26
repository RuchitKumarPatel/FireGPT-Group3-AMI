## Usage for conda users

```bash
conda create -n ami
conda activate ami
pip install -r requirements.txt
curl -L -o llama-2-7b-chat.Q4_K_M.gguf "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf?download=true"

python3 app_new.py # or app.py
```