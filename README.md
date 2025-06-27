# 🔥 FireGPT (Offline Version)

FireGPT is an offline-capable Retrieval-Augmented Generation (RAG) system designed for wildland firefighting knowledge retrieval. This guide helps you run the application **completely locally** without internet access.

---

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/RuchitKumarPatel/FireGPT.git
```

### 2. Navigate to the Repository

```bash
cd FireGPT
```

### 3. Create a Conda Environment

Make sure [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) is installed.

Then create the environment:

```bash
conda env create -f environment.yml
```

### 4. Activate the Conda Environment

```bash
conda activate rag_env
```

### 5. Download the LLaMA Model File

Download the quantized LLaMA model file:

```
[llama-2-7b-chat.Q4_K_M.gguf] (https://drive.google.com/file/d/1UIsEhE8eyYDlUFDFmOGA7MFfjeSNiIlR/view?usp=sharing)
```

Place it into a folder named `FireGPT` at the root of the project:

```bash
FireGPT/llama-2-7b-chat.Q4_K_M.gguf
```

> **Note**: You can download the `.gguf` file from the Google Drive link provided

### 6. Run the Application

```bash
python app.py
```

### 7. Open the Web Interface

After starting the app, open your browser and go to:

```
http://127.0.0.1:5000
```

---

## ✅ Expected Output

You should see the following interface load, allowing you to interact with FireGPT:

![FireGPT Screenshot](https://github.com/user-attachments/assets/1e2cc631-a5c5-41ae-9836-c6116bf8339c)

---

## 📝 Notes

- This application runs fully offline after setup.
- Only local documents are used for retrieval.
- If you encounter PyTorch or model loading issues, ensure you're using a compatible version (`safetensors` or correct `torch` build).
- No telemetry or internet access is required once the model and environment are in place.

---

## 🔐 Licensing

Make sure you comply with:

- Meta's [LLaMA license](https://ai.meta.com/resources/models-and-libraries/llama-downloads/)
- Any document or data licenses used for retrieval

---

## 👷 Maintainer

Developed and maintained by **[Sven Oeder]**  
Feel free to open issues or pull requests!
