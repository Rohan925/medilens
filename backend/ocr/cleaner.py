import re

def rule_clean(text: str) -> str:
    text = text.lower()

    # fix joined dosage
    text = re.sub(r'(\d+)\s*mg', r'\1 mg', text)

    # tablets500mg → tablets 500 mg
    text = re.sub(r'tablets\s*(\d+)\s*mg', r'tablets \1 mg', text)

    # handle "20tablets" → "tablets"
    text = re.sub(r'\d+\s*tablets?', 'tablets', text)

    # remove marketing / noise text
    text = re.sub(r'for\s*pain\s*and\s*fever', ' ', text)
    text = re.sub(r'forpainandfever', ' ', text)

    # remove stray single letters (like trailing "i")
    text = re.sub(r'\b[a-z]\b', ' ', text)

    # cleanup
    text = re.sub(r'\s+', ' ', text).strip()

    return text
