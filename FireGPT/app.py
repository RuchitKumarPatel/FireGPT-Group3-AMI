from flask import Flask, request, jsonify, send_from_directory, abort
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
import re
from threading import Lock
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import pdfplumber
import magic  # python-magic for MIME type checking

# config
UPLOAD_FOLDER = 'wildfire_docs/ocr_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

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
text_splitter = CharacterTextSplitter(chunk_size=5000, chunk_overlap=200)
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
                    max_tokens=2048,
                    n_threads=os.cpu_count(),
                    temperature=0.5,
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
    ("system",
     "You are a wildfire response expert. Use the context to generate clear, realistic, and safety-first response plans. "
     "Respond as if advising an incident commander. If a location is mentioned, take it into account. "
     "Always answer using the following sections, even if some are brief or not applicable:\n"
     "1. Situation Overview\n"
     "2. Immediate Actions\n"
     "3. Resource Utilization\n"
     "4. Safety Considerations\n"
     "5. Ongoing Monitoring\n"
     "Format your answer using Markdown. Use clear section headers (##), numbered or bulleted lists, and tables where appropriate (for resources, action steps, or summaries). Make the output easy to read and visually organized."
    ),
    ("human", 
     "Context:\n{context}\n\n"
     "Question: {question}")
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

def to_markdown(text):
    """
    Post-process LLM output to convert section headers and lists to Markdown.
    - Converts section headers (e.g., Situation Overview) to ## headers
    - Converts numbered and bulleted lists to Markdown lists
    - Optionally, you can add more rules for tables if needed
    """
    import re
    # Convert section headers to Markdown (## Header)
    section_headers = [
        'Situation Overview',
        'Immediate Actions',
        'Resource Utilization',
        'Safety Considerations',
        'Ongoing Monitoring',
        'Action Plan for Fire at',
        'Context',
        'Question',
        'Summary',
        'Instructions',
        'Recommendations',
        'Plan',
    ]
    for header in section_headers:
        # Match header at start of line, possibly followed by colon
        text = re.sub(rf'(^|\n)\s*{re.escape(header)}\s*:?\s*\n', rf'\1## {header}\n', text)
    # Convert numbered lists (1. ...)
    text = re.sub(r'(^|\n)\s*(\d+)\.\s+', r'\1\2. ', text)
    # Convert bulleted lists (- ...)
    text = re.sub(r'(^|\n)\s*-\s+', r'\1- ', text)
    # Optionally, add more rules for tables if you can detect them
    return text

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

    # Try to extract and geocode location
    place_name = extract_place_name(query)
    lat, lon = geocode_place(place_name) if place_name else (None, None)

    # Post-process to Markdown
    markdown_result = to_markdown(result)

    return jsonify({
        "response": markdown_result,
        "location": {
            "name": place_name,
            "lat": lat,
            "lon": lon
        } if lat and lon else None,
        "is_html": True
    })


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

        # Post-process to Markdown
        markdown_plan = to_markdown(plan)

        return jsonify({
            "plan": markdown_plan,
            "markers": markers,
            "is_html": True
        })
    except Exception as e:
        print(f"[ERROR] in /plan_action: {e}")
        return jsonify({"error": str(e)}), 500
    
def geocode_place(place_name):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": place_name,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "FireGPT/1.0"
        }

        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            return float(data["lat"]), float(data["lon"])
        return None, None
    except:
        return None, None

def extract_place_name(question):
    # Normalize text
    question = question.strip()

    # Match patterns like: "fire in California", "wildfire near Los Angeles", etc.
    patterns = [
        r'(?:fire|wildfire|incident)?\s*(?:in|at|near|around)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 
        r'(?:in|at|near|around)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:fire|wildfire)?',          
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:fire|wildfire)'                                    
    ]

    for pattern in patterns:
        match = re.search(pattern, question)
        if match:
            return match.group(1).strip()

    return None


def fetch_surroundings(lat, lon, radius=10000):
    try:
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
    except:
        return []


# === Helpers ===
def allowed_file(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in ALLOWED_EXTENSIONS

# OCR function using pytesseract and pdfplumber

def run_ocr(path, ext):
    try:
        if ext == '.pdf':
            # Try direct text extraction with pdfplumber
            text = ''
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + '\n'
            if text.strip():
                return text
            # Fallback to image-based OCR
            images = convert_from_path(path)
            text = ''
            for img in images:
                text += pytesseract.image_to_string(img) + '\n'
            return text
        else:
            img = Image.open(path)
            return pytesseract.image_to_string(img)
    except Exception as e:
        app.logger.error(f"OCR error for {path}: {e}")
        return None

# === Routes ===
@app.route('/upload_doc', methods=['POST'])
def upload_doc():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Unsupported file extension'}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    mime = magic.from_file(path, mime=True)
    if (ext == '.pdf' and mime != 'application/pdf') or (ext != '.pdf' and not mime.startswith('image/')):
        os.remove(path)
        return jsonify({'error': 'MIME mismatch'}), 400

    text = run_ocr(path, ext)
    # Cleanup intermediate images
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if f.startswith(filename + '_page_') and f.endswith('.png'):
            try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))
            except: pass

    if not text or not text.strip():
        os.remove(path)
        return jsonify({'error': 'OCR failed or no text'}), 500

    txt_path = path + '.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    loader = TextLoader(txt_path, encoding='utf-8')
    new_docs = loader.load()
    global vectorstore
    vectorstore.add_documents(new_docs)
    vectorstore.save_local('faiss_index')

    return jsonify({'success': True, 'text': text})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
