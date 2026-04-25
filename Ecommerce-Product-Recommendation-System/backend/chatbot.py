# Import Library
import csv
import os
import re
import numpy as np
from collections import Counter
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi

# Load environment variables from .env
load_dotenv()


class Document:
    """Minimal Document type for retrieval (compatible with our usage)."""

    def __init__(self, page_content: str, metadata: dict):
        self.page_content = page_content
        self.metadata = metadata

# Access the OpenAI API key
openai_api_key = os.getenv("MY_OPENAI_KEY")
USE_OPENAI = bool(openai_api_key and "dummy" not in openai_api_key)

# SentenceTransformer model settings
SENTENCE_TRANSFORMER_MODEL_PATH = os.getenv("SENTENCE_TRANSFORMER_MODEL_PATH", "").strip()
SENTENCE_TRANSFORMER_MODEL_NAME = os.getenv(
    "SENTENCE_TRANSFORMER_MODEL_NAME",
    "paraphrase-multilingual-MiniLM-L12-v2",
).strip()

# ---------------------------------------------------------------------------
# Data Loading – 1 product = 1 Document
# ---------------------------------------------------------------------------
records_list = []
with open('../amazon.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row.get('product_name', '')
        features = row.get('product_features', '')
        # Support both dataset column name variations
        price = row.get('price(INR)') or row.get('price', 'N/A')
        rating = row.get('rating', '0')
        discount = row.get('discount(%)', '0')

        # Richer text for better embedding + BM25 matching
        combined_desc = (
            f"Product: {name} | "
            f"Features: {features} | "
            f"Category: Electronics | "
            f"Price: ₹{price} | "
            f"Rating: {rating}⭐ | "
            f"Discount: {discount}%"
        )
        row['combined_info'] = combined_desc
        row['price'] = price if price != 'N/A' else '0'
        row['rating'] = rating
        row['discount'] = discount
        row['category'] = "Electronics"
        records_list.append(row)

docs = [Document(page_content=r['combined_info'], metadata=r) for r in records_list]

# ---------------------------------------------------------------------------
# BM25 – keyword retrieval (always available)
# ---------------------------------------------------------------------------
def tokenize_for_bm25(text: str):
    return re.findall(r'\w+', text.lower())

tokenized_corpus = [tokenize_for_bm25(doc.page_content) for doc in docs]
bm25 = BM25Okapi(tokenized_corpus)

# ---------------------------------------------------------------------------
# Multilingual Embedding Model (HuggingFace – no API key required)
# Uses paraphrase-multilingual-MiniLM-L12-v2 which supports 50+ languages.
# ---------------------------------------------------------------------------
print("[chatbot] Loading multilingual embedding model …")
MULTILINGUAL_LOAD_ERROR = None
_st_model = None
_corpus_embeddings = None
MULTILINGUAL_READY = False

try:
    from sentence_transformers import SentenceTransformer

    # Require local model files (no internet download). If you set
    # `SENTENCE_TRANSFORMER_MODEL_PATH`, we load directly from that folder.
    # Otherwise we rely on the HuggingFace local cache only.
    if SENTENCE_TRANSFORMER_MODEL_PATH:
        if not os.path.isdir(SENTENCE_TRANSFORMER_MODEL_PATH):
            raise FileNotFoundError(
                f"`SENTENCE_TRANSFORMER_MODEL_PATH` does not exist: {SENTENCE_TRANSFORMER_MODEL_PATH}"
            )
        _st_model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL_PATH)
    else:
        _st_model = SentenceTransformer(
            SENTENCE_TRANSFORMER_MODEL_NAME,
            model_kwargs={"local_files_only": True},
        )

    # Pre-compute corpus embeddings once for fast similarity search
    _corpus_texts = [doc.page_content for doc in docs]
    _corpus_embeddings = _st_model.encode(
        _corpus_texts,
        batch_size=64,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    MULTILINGUAL_READY = True
    print(f"[chatbot] Multilingual model loaded – {len(docs)} product embeddings ready.")
except Exception as e:
    MULTILINGUAL_LOAD_ERROR = str(e)
    MULTILINGUAL_READY = False
    print(f"[chatbot] WARNING: Could not load multilingual model (local-only): {MULTILINGUAL_LOAD_ERROR}")

# ---------------------------------------------------------------------------
# OpenAI / LLM setup (optional – used only if a real API key is provided)
# ---------------------------------------------------------------------------
llm = None
if USE_OPENAI:
    try:
        from langchain_openai import ChatOpenAI as ChatOpenAINew
        llm = ChatOpenAINew(openai_api_key=openai_api_key,
                            model_name='gpt-3.5-turbo', temperature=0)
    except Exception:
        try:
            from langchain.chat_models import ChatOpenAI
            llm = ChatOpenAI(openai_api_key=openai_api_key,
                             model_name='gpt-3.5-turbo', temperature=0)
        except Exception:
            llm = None

# ---------------------------------------------------------------------------
# Multilingual semantic search using SentenceTransformers
# ---------------------------------------------------------------------------
def semantic_search_multilingual(query: str, top_k: int = 15):
    """Return (doc, score) pairs using cosine similarity on multilingual embeddings."""
    if not MULTILINGUAL_READY:
        return []
    q_emb = _st_model.encode([query], normalize_embeddings=True, convert_to_numpy=True)[0]
    scores = (_corpus_embeddings @ q_emb).tolist()  # dot product = cosine (normalized)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [(docs[i], scores[i]) for i in top_indices]

# ---------------------------------------------------------------------------
# Hybrid Search: BM25 (0.3 weight) + Multilingual Semantic (0.7 weight)
# ---------------------------------------------------------------------------
def hybrid_search(query: str, top_k: int = 5, min_rating: float = 0.0, max_price: float = float('inf'), language: str = "English"):
    # Prevent silent degradation for non-English. If multilingual semantic
    # matching is unavailable, return no results rather than pretending BM25
    # is reliable across languages.
    if not MULTILINGUAL_READY and language != "English":
        return []

    # 1. BM25 keyword retrieval
    query_tokens = tokenize_for_bm25(query)
    bm25_scores = bm25.get_scores(query_tokens)
    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0

    # 2. Multilingual semantic retrieval
    semantic_results = semantic_search_multilingual(query, top_k=top_k * 10) # Get more candidates for filtering
    max_semantic = max(s for _, s in semantic_results) if semantic_results else 1.0

    # 3. Combine with hard filters (Rating and Price)
    combined: dict = {}

    # BM25 contribution: Helpful for specific keywords (brand, specs)
    bm25_weight = 0.3 if MULTILINGUAL_READY else 1.0
    for idx, score in enumerate(bm25_scores):
        if score > 0:
            doc = docs[idx]
            try:
                r = float(doc.metadata.get('rating', 0))
                p = float(str(doc.metadata.get('price', '0')).replace(',', ''))
            except (ValueError, TypeError):
                r, p = 0.0, 0.0
            
            # Apply hard filters
            if r >= min_rating and p <= max_price:
                norm = (score / max_bm25) * bm25_weight
                combined[doc.page_content] = {'doc': doc, 'score': norm}

    # Semantic contribution (0.7 weight when embeddings are available)
    for doc, score in semantic_results:
        try:
            r = float(doc.metadata.get('rating', 0))
            p = float(str(doc.metadata.get('price', '0')).replace(',', ''))
        except (ValueError, TypeError):
            r, p = 0.0, 0.0
            
        # Apply hard filters
        if r >= min_rating and p <= max_price:
            norm_sem = (score / max_semantic) * 0.7
            if doc.page_content in combined:
                combined[doc.page_content]['score'] += norm_sem
            else:
                combined[doc.page_content] = {'doc': doc, 'score': norm_sem}

    sorted_results = sorted(combined.values(), key=lambda x: x['score'], reverse=True)
    return [item['doc'] for item in sorted_results[:top_k]]

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
HEADERS = {
    "English":   "### 🛍️ Recommended Products",
    "Spanish":   "### 🛍️ Productos Recomendados",
    "French":    "### 🛍️ Produits Recommandés",
    "German":    "### 🛍️ Empfohlene Produkte",
    "Hindi":     "### 🛍️ अनुशंसित उत्पाद",
    "Bengali":   "### 🛍️ প্রস্তাবিত পণ্য",
    "Marathi":   "### 🛍️ शिफारस केलेले उत्पादन",
    "Telugu":    "### 🛍️ సిఫార్సు చేయబడిన ఉత్పత్తులు",
    "Tamil":     "### 🛍️ பரிந்துரைக்கப்பட்ட தயாரிப்புகள்",
    "Gujarati":  "### 🛍️ ભલામણ કરેલ ઉત્પાદનો",
    "Kannada":   "### 🛍️ ಶಿಫಾರಸು ಮಾಡಿದ ಉತ್ಪನ್ನಗಳು",
    "Malayalam": "### 🛍️ ശുപാർശ ചെയ്യുന്ന ഉൽപ്പന്നങ്ങൾ",
    "Punjabi":   "### 🛍️ ਸਿਫਾਰਸ਼ ਕੀਤੇ ਉਤਪਾਦ",
    "Arabic":    "### 🛍️ المنتجات الموصى بها",
}

LANG_DETECT_CODE_TO_HEADER = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "hi": "Hindi",
    "bn": "Bengali",
    "mr": "Marathi",
    "te": "Telugu",
    "ta": "Tamil",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ar": "Arabic",
}


def detect_language_from_text(text: str) -> str:
    """Detect language and map it to one of HEADERS keys.

    If detection isn't available, default to "English".
    """
    try:
        from langdetect import detect
    except Exception:
        return "English"

    if not text or not text.strip():
        return "English"

    try:
        code = detect(text)
        return LANG_DETECT_CODE_TO_HEADER.get(code, "English")
    except Exception:
        return "English"

def format_as_table(result_docs):
    if not result_docs:
        return "❌ No matching products found. Try different keywords."
    table = "| # | Product Name | Key Features | Price | Rating |\n"
    table += "|---|---|---|---|---|\n"
    for i, d in enumerate(result_docs, 1):
        name = d.metadata.get('product_name', 'N/A')
        features = d.metadata.get('product_features', 'N/A')
        price = d.metadata.get('price', 'N/A')
        rating = d.metadata.get('rating', 'N/A')
        name = name[:55] + "…" if len(name) > 55 else name
        features = features[:90] + "…" if len(features) > 90 else features
        table += f"| {i} | {name} | {features} | ₹{price} | {rating}⭐ |\n"
    return table

# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------
def extract_constraints(query):
    """Extract numeric constraints like min_rating and max_price from natural language query."""
    min_rating = 0.0
    max_price = float('inf')
    cleaned_query = query
    
    # 1. Rating patterns
    rating_patterns = [
        r"(?:rating|stars|rate|score|calificación|note|Bewertung|रेटिंग|రేటింగ్|ரேட்டிங்)\s*(?:above|over|>|more than|higher than|>=|at least|superior a|plus de|mehr als|से ज्यादा|కంటే ఎక్కువ|விட அதிகமாக)?\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(?:stars?|star rating|rating|calificación|note|Bewertung|रेटिंग|రేటింగ్|ரேட்டிங்)",
        r"(?:above|over|>|more than|higher than|>=|at least|superior a|plus de|mehr als|से ज्यादा|కంటే ఎక్కువ|விட அதிகமாக)\s*(\d+(?:\.\d+)?)\s*(?:rating|stars?|calificación|note|Bewertung|रेटिंग|రేటింగ్|ரேட்டிங்)?"
    ]
    
    for pattern in rating_patterns:
        match = re.search(pattern, cleaned_query, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                if 0 <= val <= 5:
                    min_rating = val
                    cleaned_query = cleaned_query.replace(match.group(0), "").strip()
                    break
            except ValueError: continue

    # 2. Price patterns: Handles "under 50000", "below 20k", "less than 1000", etc.
    price_patterns = [
        r"(?:under|below|<|less than|max|maximum|budget|upto|up to|within)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\s*[kK])?)",
        r"(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\s*[kK])?)\s*(?:or less|max|maximum|budget|under|below)"
    ]

    def parse_price(p_str):
        p_str = p_str.lower().replace(",", "").replace(" ", "")
        if 'k' in p_str:
            return float(p_str.replace('k', '')) * 1000
        return float(p_str)

    for pattern in price_patterns:
        match = re.search(pattern, cleaned_query, re.IGNORECASE)
        if match:
            try:
                val = parse_price(match.group(1))
                if val > 0:
                    max_price = val
                    cleaned_query = cleaned_query.replace(match.group(0), "").strip()
                    break
            except Exception: continue

    # Cleanup trailing prepositions
    cleaned_query = re.sub(r'\s+(?:at|with|for|in|of|under|on|से|के लिए|తో|తోటి|உடன்)\s*$', '', cleaned_query, flags=re.IGNORECASE)
    cleaned_query = cleaned_query.replace("  ", " ").strip()
                
    return min_rating, max_price, cleaned_query

def run_manual(department, category, brand, price,

def run_manual(department, category, brand, price,
               top_k=5, min_rating=0.0, language="English"):
    """Search via structured fields (manual mode)."""
    resolved_language = language
    if language == "Auto":
        resolved_language = detect_language_from_text(f"{department} {category} {brand} {price}")

    query = f"{department} {category} {brand} electronics"
    matched_docs = hybrid_search(
        query,
        top_k=top_k,
        min_rating=min_rating,
        language=resolved_language,
    )

    header = HEADERS.get(resolved_language, HEADERS["English"])

    # Deterministic output: always derived from retrieved products.
    warning = ""
    if resolved_language != "English" and not MULTILINGUAL_READY:
        warning = (
            f"\n\n⚠️ Multilingual semantic model unavailable. "
            f"Non-English matching is disabled locally. ({MULTILINGUAL_LOAD_ERROR})\n"
        )

    response = f"{header}\n\n{warning}"
    response += format_as_table(matched_docs)
    return response, [d.metadata for d in matched_docs]


def run_chatbot(query, top_k=5, min_rating=0.0, language="English"):
    """Search via natural-language chatbot query (cross-lingual)."""
    resolved_language = language
    if language == "Auto":
        resolved_language = detect_language_from_text(query)

    # 1. Extract constraints from query (e.g. "rating above 4", "under 50000")
    extracted_min_rating, extracted_max_price, cleaned_query = extract_constraints(query)
    
    # Use extracted constraints if found, otherwise use defaults
    final_min_rating = max(min_rating, extracted_min_rating)
    final_max_price = extracted_max_price

    # 2. Search using hybrid system
    matched_docs = hybrid_search(
        cleaned_query,
        top_k=top_k,
        min_rating=final_min_rating,
        max_price=final_max_price,
        language=resolved_language,
    )
    header = HEADERS.get(resolved_language, HEADERS["English"])

    # Deterministic output: always derived from retrieved products.
    warning = ""
    if resolved_language != "English" and not MULTILINGUAL_READY:
        warning = (
            f"\n\n⚠️ Multilingual semantic model unavailable. "
            f"Non-English matching is disabled locally. ({MULTILINGUAL_LOAD_ERROR})\n"
        )

    response = f"{header}\n\n{warning}"
    response += format_as_table(matched_docs)
    return response, [d.metadata for d in matched_docs]
