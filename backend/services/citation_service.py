def extract_citations(data: dict):
    citations = []

    if data.get("openfda"):
        citations.append({
            "source": "OpenFDA",
            "url": data["openfda"]["url"]
        })

    if data.get("pubchem"):
        citations.append({
            "source": "PubChem",
            "url": data["pubchem"]["url"]
        })

    return citations
