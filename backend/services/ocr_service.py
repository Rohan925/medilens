import easyocr
import rapidfuzz
from rapidfuzz import process, fuzz
import logging
import re
import cv2
import numpy as np
import os
import httpx
import asyncio
from services.medicine_service import get_medicine_data
from core.llm_client import llm_client
import json

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize EasyOCR Reader (loads model into memory)
# 'en' for English
reader = easyocr.Reader(['en'])

# Common medicines list for fuzzy matching (fallback/enhancement)
COMMON_MEDICINES = [
    "Paracetamol", "Ibuprofen", "Aspirin", "Metformin", "Atorvastatin", 
    "Omeprazole", "Amoxicillin", "Lisinopril", "Levothyroxine", "Amlodipine",
    "Metoprolol", "Losartan", "Albuterol", "Gabapentin", "Hydrochlorothiazide",
    "Cetirizine", "Loratadine", "Fexofenadine", "Diphenhydramine", "Doxycycline",
    "Azithromycin", "Ciprofloxacin", "Pantoprazole", "Simvastatin", "Rosuvastatin",
    "Prednisone", "Insulin", "Montelukast", "Escitalopram", "Sertraline"
]

# STOPWORDS for OCR filtering
STOPWORDS = {
    "tablet", "tablets", "capsule", "capsules", "syrup", "suspension", "injection",
    "cream", "gel", "ointment", "drops", "solution", "pain", "relief", "extra",
    "strength", "mg", "ml", "g", "mcg", "store", "batch", "expiry", "mfg", "price",
    "india", "ltd", "pvt", "pharmaceuticals", "pharma", "labs", "laboratories",
    "dosage", "physician", "keep", "reach", "children", "cool", "dry", "place",
    "anti", "inflammatory", "analgesic", "antipyretic", "antibiotic", "contains",
    "film", "coated", "dispersible", "usp", "ip", "bp", "net", "content", "mrp",
    "incl", "taxes", "regd", "trade", "mark", "marketed", "manufactured",
    "photolibrary", "alamy", "stock", "photo", "images", "getty"
}

async def check_pubchem_cid(name):
    """
    Checks if a name has a valid CID in PubChem.
    Returns CID if valid, None otherwise.
    """
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/cids/JSON"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                if "IdentifierList" in data and "CID" in data["IdentifierList"]:
                    return data["IdentifierList"]["CID"][0]
    except Exception as e:
        logger.error(f"PubChem CID check failed for '{name}': {e}")
    return None

async def pubchem_spell_check(name):
    """
    Uses PubChem Autocomplete API to find the correct drug name.
    1. Calls Autocomplete with the typo.
    2. Tokenizes all suggestion results.
    3. Returns the most frequent token that is a valid drug part (heuristic).
    4. STRICT: Verifies the suggestion is actually similar to the input name.
    """
    # Use Autocomplete instead of formal spell check (which is flaky/requires specific POST)
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound/{name}/json?limit=10"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                suggestions = data.get("dictionary_terms", {}).get("compound", [])
                
                if not suggestions:
                    return None
                    
                # Frequency Analysis of tokens in suggestions
                token_counts = {}
                for sugg in suggestions:
                    # Split by space and common punctuation
                    tokens = re.split(r'[\s\-\(\)\[\]]+', sugg)
                    for t in tokens:
                        t_clean = t.lower()
                        if len(t_clean) > 3: # Ignore short bits
                            token_counts[t_clean] = token_counts.get(t_clean, 0) + 1
                
                if not token_counts:
                    return None
                    
                # Get most frequent token
                best_token = max(token_counts, key=token_counts.get).title()
                
                # STRICT SIMILARITY CHECK
                # Prevent "photolibrary" -> "Phosphate"
                # Ratio must be decent (> 60?)
                sim_score = fuzz.ratio(name.lower(), best_token.lower())
                
                if sim_score < 60:
                    logger.info(f"Rejected autocorrect: '{name}' -> '{best_token}' (Similarity: {sim_score} < 60)")
                    return None
                
                return best_token

    except Exception as e:
        logger.error(f"PubChem Autocomplete check failed for '{name}': {e}")
    return None

def extract_candidates(text):
    """
    Extracts potential drug name candidates from text.
    Filters: len > 4, alpha only, not in stopwords.
    Returns unique list sorted by length (descending).
    """
    words = text.split()
    candidates = []
    seen = set()
    
    for word in words:
        clean_word = re.sub(r'[^a-z]', '', word.lower())
        if (len(clean_word) > 4 and 
            clean_word not in STOPWORDS and 
            clean_word not in seen):
            candidates.append(clean_word)
            seen.add(clean_word)
    
    # Sort by length (descending) to prioritize specific names over generic words
    return sorted(candidates, key=len, reverse=True)

def preprocess_image(image_path):
    """
    Preprocesses the image to improve OCR accuracy using OpenCV.
    Simplified: Grayscale only. Upscaling only for small images.
    Avoids aggressive thresholding which ruins camera photos.
    """
    try:
        # Read image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Could not read image at {image_path}")
            return None

        # 1. Resize (Upscaling) - Only if image is small (e.g. < 1000px width)
        height, width = img.shape[:2]
        if width < 1000:
            img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # 2. Convert to Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. Denoise slightly
        # gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21) # Removed: Too slow for CPU

        return gray
        
    except Exception as e:
        logger.error(f"Error in image preprocessing: {e}")
        return None

def clean_text(text):
    """
    Cleans OCR text: Lowercase, remove special chars, remove single letters, deduplicate.
    """
    if not text:
        return ""

    # 1. Convert to Lowercase
    text = text.lower()

    # 2. Remove specific patterns (Batch, Exp, dates, strengths)
    text = re.sub(r'(?i)batch\s*:?\s*[a-z0-9]+', '', text)
    text = re.sub(r'(?i)exp\s*:?\s*[\d/-]+', '', text)
    text = re.sub(r'(?i)mfg\s*:?\s*[\d/-]+', '', text)
    text = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '', text)
    text = re.sub(r'\b\d+\s*(mg|ml|g|mcg)\b', '', text)
    text = re.sub(r'\b\d+\b', '', text) # Pure numbers

    # 3. Remove Special Characters (Keep only a-z and spaces)
    text = re.sub(r'[^a-z\s]', ' ', text)

    # 4. Remove Single Letter Words
    text = re.sub(r'\b[a-z]\b', ' ', text)

    # 5. Remove Duplicates & Collapse Spaces
    words = text.split()
    seen = set()
    deduped_words = []
    for word in words:
        if word not in seen:
            seen.add(word)
            deduped_words.append(word)
    
    return " ".join(deduped_words)

def extract_best_candidate(text):
    """
    Extracts the best potential medicine name from text using heuristics:
    1. Longest uppercase word (often brand names).
    2. Longest word overall if no uppercase.
    Ignores STOPWORDS.
    """
    words = text.split()
    if not words:
        return "Unknown"

    # Filter out stopwords from the start
    valid_words = [w for w in words if w.lower() not in STOPWORDS and len(w) > 3]

    if not valid_words:
        return "Unknown"

    # Heuristic 1: Longest Uppercase Word (3+ chars)
    uppercase_words = [w for w in valid_words if w.isupper()]
    if uppercase_words:
        return max(uppercase_words, key=len)

    # Heuristic 2: Longest Word (likely the name)
    return max(valid_words, key=len)

def fuzzy_match_medicine(text, threshold=80):
    """
    Attempts to find a known medicine in the text using fuzzy matching.
    """
    try:
        if not text:
            return None, 0
            
        # Extract the best match from the list
        match = process.extractOne(text, COMMON_MEDICINES, scorer=fuzz.token_set_ratio)
        
        if match:
            candidate, score, _ = match
            if score >= threshold:
                logger.info(f"Fuzzy match found: {candidate} (Score: {score})")
                return candidate, score
    except Exception as e:
        logger.error(f"Fuzzy match error: {e}")
    return None, 0

async def process_image(path):
    confidence_score = 0.0
    detected_name = "Unknown"
    is_strict_fallback = False

    try:
        logger.info(f"Processing image at: {path}")

        # 1. Preprocess Image
        processed_img = preprocess_image(path)
        img_source = processed_img if processed_img is not None else path

        # 2. Perform OCR
        # detail=1 returns [bbox, text, confidence]
        result = reader.readtext(img_source, detail=1)
        
        # Aggregate text and average confidence
        raw_text_parts = []
        total_ocr_conf = 0.0
        count = 0
        
        for (bbox, text, prob) in result:
            # 5. Confidence Filtering (> 0.3) - Lowered from 0.5 to catch more
            if prob > 0.3:
                raw_text_parts.append(text)
                total_ocr_conf += prob
                count += 1
            else:
                logger.debug(f"Ignored low confidence text: '{text}' ({prob:.2f})")
            
        raw_text = " ".join(raw_text_parts)
        avg_ocr_conf = (total_ocr_conf / count) if count > 0 else 0.0
        
        logger.info(f"Raw OCR Text: {raw_text[:100]}... (Avg Conf: {avg_ocr_conf:.2f})")
        
        # Fallback: If no text found, try Raw Image with aggressive parameters
        if not raw_text.strip():
            logger.warning("First pass yielded no text. Retrying with raw image...")
            result = reader.readtext(path, detail=1) # Let EasyOCR handle it
            
            raw_text_parts = []
            total_ocr_conf = 0.0
            count = 0
            for (bbox, text, prob) in result:
                if prob > 0.3:
                    raw_text_parts.append(text)
                    total_ocr_conf += prob
                    count += 1
            
            raw_text = " ".join(raw_text_parts)
            avg_ocr_conf = (total_ocr_conf / count) if count > 0 else 0.0
            logger.info(f"Retry OCR Text: {raw_text[:100]}... (Avg Conf: {avg_ocr_conf:.2f})")

        if not raw_text.strip():
            logger.warning("OCR returned empty text after retry.")
            return {
                "medicine": "Unknown",
                "success": False,
                "confidence": 0,
                "summary": None,
                "error": "No text detected"
            }

        # 3. Text Cleaning
        cleaned_text = clean_text(raw_text)
        logger.info(f"Cleaned Text: {cleaned_text[:100]}...")

        # 4. Strategy: PubChem Validation -> Fuzzy Match -> Heuristic -> LLM
        
        # A. PubChem Extraction & Validation (Dynamic)
        candidates = extract_candidates(cleaned_text)
        logger.info(f"Candidates for PubChem: {candidates}")
        
        pubchem_found = False
        
        # Check top 3 candidates to avoid rate limits/latency
        for cand in candidates[:3]:
            # 1. Direct PubChem Check
            cid = await check_pubchem_cid(cand)
            if cid:
                detected_name = cand.title()
                confidence_score = avg_ocr_conf + 0.3 # High confidence for valid chemical
                logger.info(f"PubChem Direct Match: {detected_name} (CID: {cid})")
                pubchem_found = True
                break
            
            # 2. PubChem Autocomplete Correction (Remote Only - No Local List)
            corrected = await pubchem_spell_check(cand)
            if corrected:
                if corrected.lower() == cand.lower(): continue # No change
                
                # Verify the corrected name has a CID (it should, coming from PubChem)
                cid_corr = await check_pubchem_cid(corrected)
                if cid_corr:
                    detected_name = corrected.title()
                    confidence_score = avg_ocr_conf + 0.25
                    logger.info(f"PubChem Autocomplete Corrected: {cand} -> {detected_name} (CID: {cid_corr})")
                    pubchem_found = True
                    break
        
        if pubchem_found:
             # Already set detected_name
             pass
        else:
             # B. Fuzzy Match (Fallback - Full Text)
            match_name, match_score = fuzzy_match_medicine(cleaned_text)
            
            if match_name:
                detected_name = match_name
                # Boost confidence for fuzzy match
                confidence_score = (avg_ocr_conf * 0.4) + (match_score / 200.0)
            else:
                # C. Heuristic Extraction (Longest Uppercase / Longest Word)
                # Ensure we don't pick a stopword like "inflammatory"
                heuristic_name = extract_best_candidate(cleaned_text)
                
                # Filter heuristics against STOPWORDS
                if heuristic_name.lower() in STOPWORDS:
                    logger.info(f"Heuristic skipped stopword: {heuristic_name}")
                    heuristic_name = "Unknown"

                logger.info(f"Heuristic Match: {heuristic_name}")
                
                if heuristic_name != "Unknown":
                    # Try PubChem on Heuristic result as last ditch
                    cid_heur = await check_pubchem_cid(heuristic_name)
                    if cid_heur:
                         detected_name = heuristic_name
                         confidence_score = avg_ocr_conf + 0.2
                         logger.info(f"Heuristic validated via PubChem: {detected_name}")
                    else:
                        detected_name = heuristic_name
                        confidence_score = avg_ocr_conf
                else:
                     # D. Fallback to LLM
                    logger.info("No match found. Using LLM for extraction.")
                    prompt_name = f"Extract the single most prominent medicine name from this OCR text. Return ONLY the name. If no medicine is found, return 'Unknown'.\n\nText:\n{raw_text}"
                    detected_name_llm = await llm_client.generate_answer(prompt_name)
                    detected_name = detected_name_llm.strip().split('\n')[0].replace('"', '').replace("'", "")
                    
                    if detected_name.lower() != "unknown" and len(detected_name) > 2:
                        confidence_score = avg_ocr_conf
                    else:
                        detected_name = "Unknown"
                        confidence_score = 0.0

        logger.info(f"Final Detected Name: {detected_name} (Conf: {confidence_score:.2f})")

        if detected_name == "Unknown":
             return {
                "medicine": "Unknown",
                "success": False,
                "confidence": 0.0,
                "summary": None,
                "error": "Could not identify medicine name"
            }

        # 5. Fetch Medicine Data (Multi-Source Validation implicitly via get_medicine_data)
        base_data = await get_medicine_data(detected_name)
        
        # 6. Cross-Validation & Structure Data
        cat_from_db = base_data.get("category")
        rx_from_db = base_data.get("prescription_required")
        summary_text = base_data.get("summary", "")
        
        # Check if we got valid data back
        if cat_from_db and cat_from_db not in ["Consult Professional", "General Health", "Unknown"]:
             # Validation Success: The name exists in our DB/OpenFDA
             confidence_score = min(confidence_score + 0.2, 1.0) # Boost confidence
        elif confidence_score < 0.4:
            # Low confidence and no strong DB match
            is_strict_fallback = True

        # Construct structured_data directly from base_data (which comes from medicine_service)
        # medicine_service already returns structured warnings/summary
        structured_data = {
            "uses": base_data.get("uses", []), # Populated from OpenFDA via medicine_service
            "warnings": base_data.get("warnings", []),
            "category": cat_from_db if cat_from_db else "General Health",
            "prescription_status": base_data.get("prescription_status", "Unknown") # Correct Key
        }
        
        # If strict fallback, override
        if is_strict_fallback:
            structured_data["category"] = "Classification: Low Confidence"
            structured_data["prescription_status"] = "Unknown"
            structured_data["warnings"] = ["Low confidence in scan. Please verify medicine name manually."]

        # Return result
        return {
            "medicine": base_data.get("name", detected_name),
            "success": not is_strict_fallback,
            "confidence": round(confidence_score * 100, 2), # Return as percentage
            "summary": structured_data,
            "citations": base_data.get("citations", []),
            "is_strict_fallback": is_strict_fallback
        }

    except Exception as e:
        logger.error(f"OCR CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            "medicine": "Error",
            "success": False,
            "confidence": 0,
            "summary": None,
            "error": str(e)
        }
