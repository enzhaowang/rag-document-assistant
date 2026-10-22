"""Split page documents into token-sized chunks with citation metadata.

TODO(P2): split each page separately with
`RecursiveCharacterTextSplitter.from_tiktoken_encoder` (sizes from Settings), detect
section headings, attach the chunk metadata contract from the roadmap (chunk_id,
source, doc_title, doc_type, page, chunk_index, doc_hash, section) and drop tiny chunks.
"""
