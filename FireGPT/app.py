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
import argparse

app = Flask(__name__)

# === Parse command line arguments ===
parser = argparse.ArgumentParser(description='FireGPT - Wildfire Response RAG System')
parser.add_argument('--dummy', action='store_true', help='Use dummy LLM instead of actual LLaMA model')
args = parser.parse_args()

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

# === Load LLM based on command line argument ===
if args.dummy:
    print("[INFO] Using dummy LLM for UI development...")
    
    # === Dummy LLM for UI development ===
    def dummy_llm(input_text):
        return "This is a placeholder response for UI development. The actual LLM is not loaded."
    
    llm = dummy_llm
else:
    print("[INFO] Loading LLaMA model...")
    try:
        llm = LlamaCpp(
            model_path="llama-2-7b-chat.Q4_K_M.gguf",
            n_ctx=4096,
            n_threads=os.cpu_count(),
            temperature=0.7,
            chat_format="llama-2",
            verbose=True
        )
        print("[INFO] LLaMA model loaded successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to load LLaMA model: {e}")
        print("[INFO] Falling back to dummy LLM...")
        
        def dummy_llm(input_text):
            return f"This is a placeholder response. LLaMA model failed to load: {str(e)}"
        
        llm = dummy_llm

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

@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory("static/css", filename)

@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory("static/js", filename)

@app.route("/ask", methods=["POST"])
def ask():
    query = request.json.get("query")
    if not query:
        return jsonify({"error": "No query provided."}), 400
    
    # Enhanced response for location-based queries
    result = rag_chain.invoke(query)
    
    # Check if query contains location keywords and enhance response
    location_keywords = ['fire', 'wildfire', 'burning', 'location', 'where', 'show me', 'california', 'australia', 'amazon']
    has_location = any(keyword in query.lower() for keyword in location_keywords)
    
    if has_location:
        # Add location context to the response
        enhanced_result = f"{result}\n\nI've marked this location on the map for you. You can see the fire incident marker and get more details by clicking on it."
    else:
        enhanced_result = result
    
    return jsonify({"response": enhanced_result})

if __name__ == "__main__":
    app.run(debug=True)
