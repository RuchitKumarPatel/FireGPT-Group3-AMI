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
import glob
import requests
from threading import Lock

app = Flask(__name__)

# === Parse command line arguments ===
parser = argparse.ArgumentParser(description='FireGPT - Wildfire Response RAG System')
parser.add_argument('--dummy', action='store_true', help='Use dummy LLM instead of actual LLaMA model')
args = parser.parse_args()

llm_lock = Lock()
llm = None
current_model = None

# === Load and split large document ===
print("[INFO] Loading and splitting document...")
loader = TextLoader("wildfire_docs/data.txt", encoding="utf-8")
documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=10000, chunk_overlap=500)
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

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# === LLM Loader ===
def load_llm(model_path=None, use_dummy=False):
    global llm, current_model
    with llm_lock:
        if use_dummy:
            print("[INFO] Using dummy LLM for UI development...")
            def dummy_llm(input_text):
                return "This is a placeholder response for UI development. The actual LLM is not loaded."
            llm = dummy_llm
            current_model = None
        else:
            print(f"[INFO] Loading LLaMA model: {model_path}")
            try:
                llm = LlamaCpp(
                    model_path=model_path,
                    n_ctx=4096,
                    n_threads=os.cpu_count(),
                    temperature=0.7,
                    chat_format="llama-2",
                    verbose=True
                )
                current_model = model_path
                print("[INFO] LLaMA model loaded successfully!")
            except Exception as e:
                print(f"[ERROR] Failed to load LLaMA model: {e}")
                print("[INFO] Falling back to dummy LLM...")
                def dummy_llm(input_text):
                    return f"This is a placeholder response. LLaMA model failed to load: {str(e)}"
                llm = dummy_llm
                current_model = None

# === Initial LLM load ===
if args.dummy:
    load_llm(use_dummy=True)
else:
    # Find first .gguf model in current directory as default
    models = glob.glob("*.gguf")
    default_model = models[0] if models else None
    if default_model:
        load_llm(model_path=default_model)
    else:
        load_llm(use_dummy=True)

# === Prompt template ===
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a wildfire response expert. Use the provided context to answer the user's question."),
    ("human", "Context:\n{context}\n\nQuestion: {question}")
])

def truncate_docs(docs, max_chars=6000):
    return "\n\n".join(doc.page_content for doc in docs)[:max_chars]

def get_rag_chain():
    return (
        RunnableMap({
            "context": retriever | (lambda docs: truncate_docs(docs)),
            "question": RunnablePassthrough()
        })
        | prompt
        | llm
        | StrOutputParser()
    )

# === Model management endpoints ===
@app.route("/models", methods=["GET"])
def list_models():
    models = [os.path.basename(f) for f in glob.glob("*.gguf")]
    return jsonify({"models": models, "current": os.path.basename(current_model) if current_model else None})

@app.route("/set_model", methods=["POST"])
def set_model():
    data = request.json
    model = data.get("model")
    if not model or not os.path.exists(model):
        return jsonify({"error": "Model not found"}), 400
    try:
        load_llm(model_path=model)
        return jsonify({"success": True, "current": os.path.basename(model)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    
    rag_chain = get_rag_chain()
    result = rag_chain.invoke(query)
    
    location_keywords = ['fire', 'wildfire', 'burning', 'location', 'where', 'show me', 'california', 'australia', 'amazon']
    has_location = any(keyword in query.lower() for keyword in location_keywords)
    
    if has_location:
        enhanced_result = f"{result}\n\nI've marked this location on the map for you. You can see the fire incident marker and get more details by clicking on it."
    else:
        enhanced_result = result
    
    return jsonify({"response": enhanced_result})


@app.route("/plan_action", methods=["POST"])
def plan_action():
    data = request.json
    lat = data.get("latitude")
    lon = data.get("longitude")

    if lat is None or lon is None:
        return jsonify({"error": "Latitude and longitude required."}), 400

    # 1. Fetch detailed surroundings information
    surroundings = fetch_surroundings(lat, lon)
    
    # Create a structured report of nearby resources
    resources_report = "Nearby Emergency Resources:\n"
    resource_categories = {
        "Fire Station": [],
        "Police": [],
        "Hospital": [],
        "Water Source": [],
        "Residential Area": [],
        "Forest": []
    }
    
    for loc in surroundings[:30]:  # Limit to 30 closest points
        if "fire" in loc["type"].lower():
            resource_categories["Fire Station"].append(loc)
        elif "police" in loc["type"].lower():
            resource_categories["Police"].append(loc)
        elif "hospital" in loc["type"].lower():
            resource_categories["Hospital"].append(loc)
        elif "water" in loc["type"].lower():
            resource_categories["Water Source"].append(loc)
        elif "residential" in loc["type"].lower():
            resource_categories["Residential Area"].append(loc)
        elif "forest" in loc["type"].lower():
            resource_categories["Forest"].append(loc)
    
    for category, locations in resource_categories.items():
        if locations:
            resources_report += f"\n{category} (Closest {len(locations)}):\n"
            for loc in locations[:10]:  # Show top 10 in each category
                resources_report += f"- {loc['name']} ({loc['type']}) - {loc['distance']:.1f} km away\n"

    # 2. Create a detailed prompt for the RAG chain
        prompt = (
            f"Create a action plan for a fire at {lat}, {lon}.\n"
            f"Surrounding area info:\n{resources_report}\n\n"
        )

    try:
        rag_chain = get_rag_chain()
        plan = rag_chain.invoke(prompt)
        
        # Extract markers for different resource types
        markers = {
            "fire": {"lat": lat, "lon": lon},
            "safe_zones": [{"lat": loc["lat"], "lon": loc["lon"]} for loc in resource_categories["Residential Area"]][:3],
            "crews": [{"lat": loc["lat"], "lon": loc["lon"]} for loc in resource_categories["Fire Station"]],
            "aerial": [],
            "hospitals": [{"lat": loc["lat"], "lon": loc["lon"]} for loc in resource_categories["Hospital"]],
            "water_sources": [{"lat": loc["lat"], "lon": loc["lon"]} for loc in resource_categories["Water Source"]]
        }

        return jsonify({
            "plan": plan,
            "markers": markers
        })
    except Exception as e:
        print(f"[ERROR] in /plan_action: {e}")
        return jsonify({"error": str(e)}), 500


def fetch_surroundings(lat, lon, radius=10000):
    overpass_query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="fire_station"](around:{radius},{lat},{lon});
      node["amenity"="police"](around:{radius},{lat},{lon});
      node["amenity"="hospital"](around:{radius},{lat},{lon});
      node["natural"="water"](around:{radius},{lat},{lon});
      node["highway"="residential"](around:{radius},{lat},{lon});
      way["landuse"="forest"](around:{radius},{lat},{lon});
      way["natural"="water"](around:{radius},{lat},{lon});
    );
    out center;
    """

    url = "https://overpass-api.de/api/interpreter"
    response = requests.post(url, data=overpass_query)
    data = response.json()

    surroundings = []

    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name", "Unnamed location")
        
        location_type = "Unknown"
        if "amenity" in tags:
            location_type = f"{tags['amenity'].replace('_', ' ').title()}"
        elif "natural" in tags:
            location_type = f"{tags['natural'].replace('_', ' ').title()}"
        elif "landuse" in tags:
            location_type = f"{tags['landuse'].replace('_', ' ').title()}"
        elif "highway" in tags:
            location_type = "Road"

        if element["type"] == "node":
            el_lat = element.get("lat")
            el_lon = element.get("lon")
        else:
            center = element.get("center", {})
            el_lat = center.get("lat")
            el_lon = center.get("lon")

        if el_lat is not None and el_lon is not None:
            surroundings.append({
                "name": name,
                "type": location_type,
                "lat": el_lat,
                "lon": el_lon,
                "distance": ((el_lat - lat)**2 + (el_lon - lon)**2)**0.5 * 111.32  # approx km
            })

    # Sort by distance
    surroundings.sort(key=lambda x: x["distance"])
    return surroundings


if __name__ == "__main__":
    app.run(debug=True)