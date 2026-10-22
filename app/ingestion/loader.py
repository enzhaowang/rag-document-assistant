"""Load PDFs into per-page documents with cleaned text.

TODO(P2): extract text per page with PyMuPDF, strip repeated headers/footers, fix
hyphenated line breaks, collapse whitespace, skip blank pages, and skip unreadable or
encrypted files with a log entry instead of failing the whole run.
"""
