"""Content for the fictional Lumora Home Systems sample knowledge base.

Each document is plain data (see `model.py`); `scripts/generate_sample_pdfs.py`
renders them to PDF and verifies where every embedded fact ends up.
"""

from scripts.sample_docs.faqs import FAQS
from scripts.sample_docs.model import SampleDoc
from scripts.sample_docs.policy import WARRANTY_POLICY
from scripts.sample_docs.product_guides import PRODUCT_GUIDES
from scripts.sample_docs.sops import SOPS

ALL_DOCS: tuple[SampleDoc, ...] = (*PRODUCT_GUIDES, *SOPS, *FAQS, WARRANTY_POLICY)

__all__ = ["ALL_DOCS"]
