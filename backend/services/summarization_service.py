def generate_medical_summary(data: dict):
    name = data["drug_name"]
    fda = data.get("openfda")
    pubchem = data.get("pubchem")

    summary_parts = []

    if fda and fda.get("indications"):
        summary_parts.append(f"{name.capitalize()} is indicated for {fda['indications'][0][:300]}")

    if pubchem and pubchem.get("molecular_formula"):
        summary_parts.append(
            f"It has a molecular formula of {pubchem['molecular_formula']} "
            f"and molecular weight of {pubchem['molecular_weight']}."
        )

    if fda and fda.get("warnings"):
        summary_parts.append(f"Important warnings include: {fda['warnings'][0][:250]}")

    return " ".join(summary_parts)
