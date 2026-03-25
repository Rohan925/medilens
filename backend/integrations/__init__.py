# backend/integrations/__init__.py

#from .openfda_client import fetch_openfda_drug_info
#from .drugbank_client import fetch_drugbank_drug_info
from .pubchem_client import fetch_pubchem_compound_info

__all__ = [
    #"fetch_openfda_drug_info",
    "fetch_drugbank_drug_info",
    "fetch_pubchem_compound_info",
]