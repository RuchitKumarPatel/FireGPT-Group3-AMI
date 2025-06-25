from flask import Flask, request, jsonify, send_from_directory
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
import os

app = Flask(__name__, static_url_path="", static_folder="static")

# Load and split data
loader = TextLoader("wildfire_docs/data.txt")
documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
docs = text_splitter.split_documents(documents)

# Embed and store in FAISS
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = FAISS.from_documents(docs, embeddings)
retriever = db.as_retriever()

# Load local model
llm = LlamaCpp(
    model_path="llama-2-7b-chat.Q4_K_M.gguf",
    temperature=0.7,
    max_tokens=256,
    n_ctx=2048,
    n_batch=512,
    f16_kv=True,
    verbose=True,
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=False
)

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/ask", methods=["POST"])
def ask():
    query = request.json.get("query")
    if not query:
        return jsonify({"error": "No query provided."}), 400
    result = qa_chain.run(query)
    return jsonify({"response": result})

if __name__ == "__main__":
    app.run(debug=True)
