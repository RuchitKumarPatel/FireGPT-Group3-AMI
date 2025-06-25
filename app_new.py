from flask import Flask, request, jsonify, send_from_directory
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
import os

app = Flask(__name__, static_url_path="", static_folder="static")

# === Load and split data ===
loader = TextLoader("wildfire_docs/data.txt")
documents = loader.load()

print(f"Loaded {len(documents)} document(s)")
print("Sample document preview:", documents[0].page_content[:300])

text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
docs = text_splitter.split_documents(documents)

print(f"Split into {len(docs)} chunks")
print("Sample chunk preview:", docs[0].page_content[:300])

# === Embed and store in FAISS ===
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = FAISS.from_documents(docs, embeddings)
retriever = db.as_retriever()

# Test retrieval
test_docs = retriever.get_relevant_documents("What aircrafts can I use?")
if test_docs:
    print("Sample retrieved doc for test query:", test_docs[0].page_content[:300])
else:
    print("No documents retrieved for sample query!")

# === Load LlamaCpp model ===
llm = LlamaCpp(
    model_path="llama-2-7b-chat.Q4_K_M.gguf",  # Use full absolute path if needed
    temperature=0.7,
    max_tokens=256,
    n_ctx=2048,
    n_batch=512,
    f16_kv=True,
    verbose=True,
)

# === QA chain with context injection ===
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",  # Ensures source text is directly passed as context
    return_source_documents=True  # Temporary for debugging
)

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/ask", methods=["POST"])
def ask():
    query = request.json.get("query")
    if not query:
        return jsonify({"error": "No query provided."}), 400
    
    result = qa_chain(query)
    print("User query:", query)
    print("Source document preview:", result['source_documents'][0].page_content[:300])

    return jsonify({"response": result["result"]})

if __name__ == "__main__":
    app.run(debug=True)
