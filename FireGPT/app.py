from flask import Flask, request, jsonify, send_from_directory
from langchain_community.llms import LlamaCpp
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableMap, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os

app = Flask(__name__)

# === Load and split large document ===
print("[INFO] Loading and splitting document...")
loader = TextLoader("wildfire_docs/data.txt", encoding="utf-8")
documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
docs = text_splitter.split_documents(documents)

# === Create/load FAISS vectorstore ===
print("[INFO] Creating/loading vectorstore...")
embeddings = HuggingFaceEmbeddings(model_name="local_models/all-MiniLM-L6-v2")

if os.path.exists("faiss_index"):
    vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    print("[INFO] FAISS index loaded from disk.")
else:
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local("faiss_index")
    print("[INFO] FAISS index created and saved.")

# ✅ Limit retrieval to top 3 chunks only
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# === Load local LLaMA 2 model ===
print("[INFO] Loading LLaMA model...")
llm = LlamaCpp(
    model_path="llama-2-7b-chat.Q4_K_M.gguf",
    n_ctx=4096,
    n_threads=os.cpu_count(),
    temperature=0.7,
    chat_format="llama-2",
    verbose=True
)

# === Prompt template ===
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a wildfire response expert. Use the provided context to answer the user's question."),
    ("human", "Context:\n{context}\n\nQuestion: {question}")
])

# === Limit final context length to 6000 characters ===
def truncate_docs(docs, max_chars=6000):
    return "\n\n".join(doc.page_content for doc in docs)[:max_chars]

# === RAG chain with truncation ===
rag_chain = (
    RunnableMap({
        "context": retriever | (lambda docs: truncate_docs(docs)),
        "question": RunnablePassthrough()
    })
    | prompt
    | llm
    | StrOutputParser()
)

# === Routes ===
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/ask", methods=["POST"])
def ask():
    query = request.json.get("query")
    if not query:
        return jsonify({"error": "No query provided."}), 400
    result = rag_chain.invoke(query)
    return jsonify({"response": result})

if __name__ == "__main__":
    app.run(debug=True)
