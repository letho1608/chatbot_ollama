"""RAG module tests: document processing, chunking, embeddings, security check."""

import json
from core.rag import (
    chunk_text, is_allowed_extension, is_security_content,
    extract_text_from_bytes, store_session_document,
    get_session_docs, delete_session_doc, session_retrieve,
    cosine_similarity, get_embedding, session_store
)


class TestExtensions:
    def test_allowed_txt(self):
        assert is_allowed_extension("test.txt") is True

    def test_allowed_pdf(self):
        assert is_allowed_extension("test.pdf") is True

    def test_allowed_docx(self):
        assert is_allowed_extension("test.docx") is True

    def test_blocked_exe(self):
        assert is_allowed_extension("virus.exe") is False

    def test_blocked_html(self):
        assert is_allowed_extension("page.html") is False

    def test_no_extension(self):
        assert is_allowed_extension("Makefile") is False


class TestSecurityContent:
    def test_security_keywords_found(self):
        ok, reason = is_security_content("firewall penetration testing network security analysis")
        assert ok is True

    def test_non_security(self):
        ok, reason = is_security_content("how to bake a cake with sugar and flour and eggs at home")
        assert ok is False

    def test_mixed_content(self):
        ok, reason = is_security_content("Encryption is important for security in modern computing systems")
        assert ok is True


class TestChunking:
    def test_small_text(self):
        chunks = chunk_text("Hello world", chunk_size=500, overlap=80)
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_large_text(self):
        text = "word " * 1000
        chunks = chunk_text(text, chunk_size=500, overlap=80)
        assert len(chunks) > 1

    def test_overlap_content(self):
        text = "Security analysis of malware detection " * 50
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) >= 2


class TestExtraction:
    def test_txt_utf8(self):
        text = extract_text_from_bytes(b"Hello security world", "test.txt")
        assert text == "Hello security world"

    def test_empty_file(self):
        text = extract_text_from_bytes(b"", "empty.txt")
        assert text == ""


class TestSessionStore:
    def test_store_and_retrieve(self, db):
        store_session_document(1, "test.txt", "penetration testing firewall security")
        docs = get_session_docs(1)
        assert len(docs) > 0
        assert docs[0]["filename"] == "test.txt"

    def test_delete_document(self, db):
        store_session_document(1, "delete_me.txt", "security content here")
        docs = get_session_docs(1)
        if docs:
            doc_id = docs[0]["id"]
            ok = delete_session_doc(1, doc_id)
            assert ok is True

    def test_delete_nonexistent(self, db):
        ok = delete_session_doc(1, "nonexistent-id")
        assert ok is False

    def test_retrieve_empty(self):
        results = session_retrieve(999, "firewall")
        assert results == []


class TestCosineSimilarity:
    def test_identical(self):
        sim = cosine_similarity([1, 2, 3], [1, 2, 3])
        assert abs(sim - 1.0) < 0.001

    def test_orthogonal(self):
        sim = cosine_similarity([1, 0, 0], [0, 1, 0])
        assert abs(sim) < 0.001

    def test_zero_vector(self):
        sim = cosine_similarity([0, 0, 0], [1, 0, 0])
        assert sim == 0.0
