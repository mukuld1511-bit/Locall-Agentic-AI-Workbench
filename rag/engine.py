"""Local Sovereign RAG Engine with Mandatory Security Access Control Filtering.

Enforces Section 21 RAG Security:
1. Filters candidate documents by calling user's Role & Classification BEFORE retrieval.
   - GRADE_1: Only PUBLIC_INTERNAL documents.
   - GRADE_2: PUBLIC_INTERNAL and ROLE_RESTRICTED documents.
   - GRADE_3 / ADMIN: PUBLIC_INTERNAL, ROLE_RESTRICTED, and CONFIDENTIAL documents.
   - HIGHLY_CONFIDENTIAL: strictly excluded from standard RAG to prevent prompt leaks.
2. Performs keyword + semantic similarity scoring over authorized chunks only.
3. Reranks and returns top-k matching passages.
4. Wraps results in safe XML data envelopes (`<UNTRUSTED_DOCUMENT_EVIDENCE>`).
5. Logs tamper-evident audit records whenever a knowledge document is retrieved.
"""

import math
import re
from typing import Any, Dict, List, Optional
from rag.store import KNOWLEDGE_STORE, KnowledgeDocument
from backend.app.audit.audit_service import AUDIT
from backend.app.security.sanitizer import SANITIZER


ROLE_PERMITTED_CLASSIFICATIONS = {
    "GRADE_1": ["PUBLIC_INTERNAL"],
    "GRADE_2": ["PUBLIC_INTERNAL", "ROLE_RESTRICTED"],
    "GRADE_3": ["PUBLIC_INTERNAL", "ROLE_RESTRICTED", "CONFIDENTIAL"],
    "ADMIN": ["PUBLIC_INTERNAL", "ROLE_RESTRICTED", "CONFIDENTIAL"],
}


class SovereignRAGEngine:
    def __init__(self):
        self.store = KNOWLEDGE_STORE

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def search(
        self,
        query: str,
        role: str = "GRADE_1",
        user_id: Optional[str] = None,
        top_k: int = 3,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Performs secure RAG search with pre-retrieval access control filtering."""
        role_upper = role.upper()
        permitted_classes = ROLE_PERMITTED_CLASSIFICATIONS.get(role_upper, ["PUBLIC_INTERNAL"])
        query_tokens = set(self._tokenize(query))

        candidates = []
        blocked_due_to_security = 0

        # Iterate over all stored documents
        for doc in self.store.documents.values():
            # Mandatory Security Gate: Pre-retrieval filter
            if doc.classification not in permitted_classes:
                blocked_due_to_security += 1
                continue  # Excluded before search scoring

            for chunk_idx, chunk in enumerate(doc.chunks):
                chunk_tokens = self._tokenize(chunk)
                if not chunk_tokens:
                    continue

                # Compute keyword overlap score
                overlap = sum(1 for t in query_tokens if t in chunk_tokens)
                if overlap > 0:
                    score = overlap / (math.sqrt(len(query_tokens) * len(chunk_tokens)) + 1e-5)
                    candidates.append({
                        "doc_id": doc.doc_id,
                        "title": doc.title,
                        "code": doc.code,
                        "classification": doc.classification,
                        "chunk_index": chunk_idx,
                        "text": chunk,
                        "score": round(score, 4),
                    })

        # Sort by relevance score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        top_results = candidates[:top_k]

        # Audit accessed documents
        for res in top_results:
            AUDIT.log_event(
                event_type="RAG_DOCUMENT_ACCESSED",
                action="rag_search",
                status="SUCCESS",
                user_id=user_id,
                role=role_upper,
                resource=f"doc:{res['doc_id']}",
                request_id=request_id,
                details={
                    "code": res["code"],
                    "classification": res["classification"],
                    "score": res["score"],
                },
            )

        # Wrap chunks in untrusted evidence tags
        wrapped_evidence = [
            SANITIZER.wrap_untrusted_data(
                source_name=f"{r['code']} ({r['title']})",
                classification=r["classification"],
                content=r["text"],
            )
            for r in top_results
        ]

        return {
            "success": True,
            "query": query,
            "role": role_upper,
            "results_count": len(top_results),
            "results": top_results,
            "wrapped_evidence": wrapped_evidence,
            "security_metrics": {
                "permitted_classifications": permitted_classes,
                "docs_excluded_by_security_filter": blocked_due_to_security,
            },
        }


RAG_ENGINE = SovereignRAGEngine()
