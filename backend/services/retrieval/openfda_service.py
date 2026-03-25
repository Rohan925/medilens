
import requests
import re

BASE_URL = "https://api.fda.gov/drug/label.json"

SYNONYMS = {
    "paracetamol": "acetaminophen",
    "tylenol": "acetaminophen",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "aleve": "naproxen",
    "aspirin": "aspirin", # redundant but safe
}

def format_bullet_points(text_list, max_items=5, is_warning=False):
    """
    Converts a list of text into clean, short bullet points.
    """
    if not text_list:
        return []

    # Flatten list
    flat_list = []
    for item in text_list:
        if isinstance(item, list):
            flat_list.extend(item)
        else:
            flat_list.append(str(item))

    cleaned_items = []

    if is_warning:
        keywords = ["liver", "bleeding", "heart", "stroke", "allergy", "damage", "stomach", "alcohol", "fatal", "risk", "interaction", "pregnant"]
        t = " ".join(flat_list)
        t = re.sub(r'[\r\n\t]+', ' ', t)
        t = re.sub(r'\s+', ' ', t).strip()
        t = re.sub(r'^(?:warnings\s+and\s+cautions|warnings|boxed warning)\s*[:\-]?\s*', '', t, flags=re.IGNORECASE)
        sentences = re.split(r'[.!\•]|(?:\s+-\s+)', t)
        
        final_warnings = []
        for s in sentences:
            s_clean = s.strip()
            if not s_clean or len(s_clean) < 15:
                continue
            s_lower = s_clean.lower()
            if any(k in s_lower for k in keywords):
                s_clean = s_clean[0].upper() + s_clean[1:]
                if s_clean not in final_warnings:
                    final_warnings.append(s_clean)
                    
        if not final_warnings and sentences:
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) >= 15:
                    s_clean = s_clean[0].upper() + s_clean[1:]
                    if s_clean not in final_warnings:
                        final_warnings.append(s_clean)
        
        return final_warnings[:max_items]
    
    else:
        # USES LOGIC: 5-STAGE EXTRACTION PIPELINE
        
        # --- Stage 1: Source Normalization ---
        t = " ".join(flat_list)
        t = re.sub(r'[\r\n\t]+', ' ', t)
        t = re.sub(r'\s+', ' ', t).strip()
        t = t.replace('\u2011', '-').replace('\u2013', '-').replace('\u00a0', ' ').replace('\u2022', '•')
        
        # Remove headers and branding
        t = re.sub(r'(INDICATIONS AND USAGE|1\s+INDICATIONS|USES|For).*?label', '', t, flags=re.IGNORECASE)
        t = re.sub(r'temporarily (relieves|reduces).*?(due to|:)', 'Relief of minor aches and pains due to:', t, flags=re.IGNORECASE)
        t = re.sub(r'\(\s*\d+\s*\)', '', t)
        # Remove definition lines: "Apixaban is a factor Xa inhibitor..."
        t = re.sub(r'[A-Z][a-z]+\s+is a\s+.*?[.](?=\s|$)', '', t)

        # --- Stage 2: Indication Extraction Layer ---
        raw_sentences = re.split(r'[.!\•]|(?:\s+-\s+)', t)
        
        type_a_uses = []
        type_c_buffer = []

        type_a_markers = ["treatment", "prevention", "reduction", "relief", "used for", "management", "indicated", "symptoms"]
        type_b_markers = ["is a", "inhibits", "blocks", "acts on", "binds to"]
        type_c_markers = ["which may lead to", "associated with", "following initial therapy", "due to the"]
        
        for sentence in raw_sentences:
            s = sentence.strip()
            if not s:
                continue
            
            s_lower = s.lower()
            
            is_type_a = any(m in s_lower for m in type_a_markers)
            
            # Type B - Mechanism (Discard)
            if any(m in s_lower for m in type_b_markers) and not is_type_a:
                continue
                
            # Type C - Contextual Risk (Hold to merge)
            is_type_c = any(m in s_lower for m in type_c_markers)
            if is_type_c and not is_type_a:
                type_c_buffer.append(s)
                continue
                
            # Type A - Clinical Action (Keep & Merge)
            if type_a_uses and type_c_buffer:
                merged_c = " ".join(type_c_buffer)
                type_a_uses[-1] = type_a_uses[-1] + " " + merged_c
                
            # Clear buffer even if no type_a_uses existed (edge case protection)
            type_c_buffer = []
                
            type_a_uses.append(s)
            
        # Catch trailing Type C
        if type_a_uses and type_c_buffer:
            merged_c = " ".join(type_c_buffer)
            type_a_uses[-1] = type_a_uses[-1] + " " + merged_c
            
        # --- Stage 3: Indication Consolidation Layer ---
        consolidated = []
        for s in type_a_uses:
            s_clean = s
            # Convert verbose clinical language to short form
            s_clean = re.sub(r'(?:for\s+the\s+)?(reduction|prevention|treatment|management|relief)\s+(?:in\s+the\s+risk\s+of\s+|of\s+)?', r'\1 of ', s_clean, flags=re.IGNORECASE)
            s_clean = re.sub(r'\s+', ' ', s_clean).strip()
            consolidated.append(s_clean)
            
        # --- Stage 4: Standardization Layer ---
        standardized = []
        otc_split_markers = ["due to:", "due to", "associated with"]
        
        for s in consolidated:
            is_otc_list = False
            for marker in otc_split_markers:
                if marker in s.lower():
                    # Find the marker and split AFTER it
                    pattern = re.compile(re.escape(marker), re.IGNORECASE)
                    match = pattern.search(s)
                    if match:
                        symptoms_str = s[match.end():]
                        symptoms = re.split(r',|\s+and\s+', symptoms_str)
                        for pkt in symptoms:
                            pkt = re.sub(r'^[^a-zA-Z]+', '', pkt).strip()
                            if pkt and len(pkt) > 2:
                                pkt = pkt[0].upper() + pkt[1:]
                                standardized.append(pkt)
                        is_otc_list = True
                        break
                    
            if not is_otc_list:
                # Capitalize first
                s = re.sub(r'^[^a-zA-Z]+', '', s).strip()
                if s:
                    s = s[0].upper() + s[1:]
                    standardized.append(s)
                
        # Enforce Rule 1: No sentence > 120 chars
        # Limit to 120 chars, but try not to break words
        truncated = []
        for s in standardized:
            if len(s) > 120:
                s = s[:117] + "..."
            truncated.append(s)
            
        # --- Stage 5: Validation Layer ---
        final = []
        seen = set()
        
        bad_starts = r'^(of|which|that|and|or|when|to|in\s+the|usage|limitations|is\s+indicated)\b'
        
        for s in truncated:
            # 1. No bullet starts with lowercase fragment or blacklisted word
            if re.match(bad_starts, s, flags=re.IGNORECASE):
                continue
                
            # Strip non-alpha
            s = re.sub(r'^[^a-zA-Z]+', '', s).strip()
            if not s:
                continue
                
            s = s[0].upper() + s[1:]
            s_lower = s.lower()
            
            # Remove isolated generic headers
            if s_lower in ["indications and usage", "indications", "is indicated for", "treatment"]:
                continue
                
            # Deduplicate
            is_duplicate = False
            for existing in final:
                if s_lower == existing.lower() or s_lower in existing.lower():
                    is_duplicate = True
                    break
                    
            if not is_duplicate and s_lower not in seen:
                final.append(s)
                seen.add(s_lower)
                
        return final[:max_items]

def fetch_openfda_data(drug_name: str):
    try:
        # Check synonyms
        search_name = SYNONYMS.get(drug_name.lower(), drug_name)
        
        # Prioritize Exact Matches to avoid "Metformin" matching "Zituvimet" (Metformin + Sitagliptin)
        queries = [
            f'openfda.brand_name.exact:"{search_name.upper()}"',
            f'openfda.generic_name.exact:"{search_name.upper()}"',
            f'openfda.substance_name.exact:"{search_name.upper()}"' # New Safe Fallback (Active Ingredient)
        ]
        
        for q in queries:
            params = {
                "search": q,
                "limit": 1
            }
            
            print(f"DEBUG: Querying OpenFDA: {q}")
            response = requests.get(BASE_URL, params=params)
            data = response.json()
            
            if "results" in data:
                result = data["results"][0]
                # Found a match, proceed to extraction
                break
        else:
             # Loop finished without break = No results found
             return None
        
        openfda = result.get("openfda", {})
        openfda = result.get("openfda", {})
        
        # Product Type
        product_types = openfda.get("product_type", [])
        is_prescription = True # Default
        product_type_str = "Unknown"
        
        if product_types:
            pt = product_types[0].upper()
            product_type_str = pt
            if "OTC" in pt:
                is_prescription = False
            elif "PRESCRIPTION" in pt:
                is_prescription = True
        
        # Pharm Class Logic
        pharm_class = "General Health"
        raw_class = ""
        
        # Check if key exists AND list is not empty
        if "pharm_class_epc" in openfda and openfda["pharm_class_epc"]:
            raw_class = openfda["pharm_class_epc"][0]
        elif "pharm_class_cs" in openfda and openfda["pharm_class_cs"]:
            raw_class = openfda["pharm_class_cs"][0]
            
        if raw_class:
            # Remove [EPC], [CS], etc.
            pharm_class = re.sub(r'\s*\[.*?\]', '', raw_class).strip()
        elif product_type_str != "Unknown":
            # Avoid generic "HUMAN PRESCRIPTION DRUG" if possible, but if that's all we have, use it but title case it
            pharm_class = product_type_str.title().replace("Human ", "")
        else:
             pharm_class = "Unclassified"

        # Normalize Fields
        
        # Uses Cleaning
        # Add more aggressive cleaning for "indicated for", etc. is handled in format_bullet_points now?
        # We need to update format_bullet_points first? 
        # Actually I can update the remove_phrases list in format_bullet_points below.
        
        # Uses: Pass completely raw and unfiltered to the LLM
        raw_uses = result.get("indications_and_usage", [])
        if not raw_uses:
            raw_uses = result.get("purpose", [])
             
        uses = raw_uses # Untouched

        # Warnings: Fallback logic, continues using regex parser
        raw_warnings = result.get("warnings", [])
        if not raw_warnings:
             raw_warnings = result.get("warnings_and_cautions", [])
        if not raw_warnings:
             raw_warnings = result.get("boxed_warning", [])
        warnings = format_bullet_points(raw_warnings, max_items=5, is_warning=True)

        return {
            "indications": uses,
            "warnings": warnings,
            "dosage": result.get("dosage_and_administration", []),
            "mechanism_of_action": result.get("mechanism_of_action", []),
            "active_ingredient": result.get("active_ingredient", []),
            "purpose": result.get("purpose", []),
            "source": "OpenFDA",
            "url": f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query={search_name}",
            "product_type": product_type_str,
            "is_prescription": is_prescription,
            "pharm_class": pharm_class,
            "set_id": openfda.get("spl_set_id", [None])[0]
        }

    except Exception as e:
        print(f"DEBUG Error fetching OpenFDA data for {drug_name}: {e}")
        import traceback
        traceback.print_exc()
        return None