"""Medical knowledge ingestion and document lifecycle manager for Stage-G.

Enforces document lifecycle state machine:
UPLOAD -> VALIDATION -> EXTRACTION -> CLEANING -> INDEXING -> AVAILABLE (or FAILED).
"""

import time
from typing import Any, Mapping, Optional
import uuid

from medicalplab.stage_b.models import ContractError, require, strings
from .audit import AuditService
from .database import DatabaseService
from .models import AuditEventType, DocumentRecord, DocumentStage


VALID_TRANSITIONS: dict[DocumentStage, set[DocumentStage]] = {
    DocumentStage.UPLOAD: {DocumentStage.VALIDATION, DocumentStage.FAILED},
    DocumentStage.VALIDATION: {DocumentStage.EXTRACTION, DocumentStage.FAILED},
    DocumentStage.EXTRACTION: {DocumentStage.CLEANING, DocumentStage.FAILED},
    DocumentStage.CLEANING: {DocumentStage.INDEXING, DocumentStage.FAILED},
    DocumentStage.INDEXING: {DocumentStage.AVAILABLE, DocumentStage.FAILED},
    DocumentStage.AVAILABLE: {DocumentStage.INDEXING, DocumentStage.FAILED},  # Can be re-indexed
    DocumentStage.FAILED: {DocumentStage.UPLOAD, DocumentStage.VALIDATION},  # Can be retried
}


class MedicalKnowledgeManager:
    """Manages clinical guideline document ingestion and lifecycle states."""

    def __init__(self, db: DatabaseService, audit: Optional[AuditService] = None):
        self.db = db
        self.audit = audit

    def upload_document(
        self,
        tenant_id: str,
        owner_id: str,
        title: str,
        file_path: str = "",
        file_size_bytes: int = 1024,
        mime_type: str = "application/pdf",
        filename: str = "",
        source: str = "NICE",
        metadata: Mapping[str, Any] | None = None,
    ) -> DocumentRecord:
        """Register a newly uploaded document in UPLOAD state."""
        strings(tenant_id, owner_id, title)
        doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
        now = time.time()

        meta_pairs: list[tuple[str, str]] = []
        if metadata:
            for k, v in metadata.items():
                meta_pairs.append((str(k), str(v)))

        doc = DocumentRecord(
            doc_id=doc_id,
            tenant_id=tenant_id.strip(),
            owner_id=owner_id.strip(),
            title=title.strip(),
            stage=DocumentStage.UPLOAD,
            version=1,
            file_path=file_path.strip(),
            file_size_bytes=file_size_bytes,
            mime_type=mime_type.strip(),
            status=DocumentStage.UPLOAD,
            filename=filename.strip() if filename else title.strip(),
            source=source.strip(),
            block_count=0,
            created_at=now,
            uploaded_at=now,
            updated_at=now,
            metadata=tuple(meta_pairs),
        )

        self.db.documents.save(doc)

        if self.audit:
            self.audit.record_event(
                tenant_id=tenant_id.strip(),
                actor_id=owner_id.strip(),
                event_type=AuditEventType.DOCUMENT_UPLOAD,
                action=f"Uploaded document: {title}",
                metadata={"doc_id": doc_id, "stage": DocumentStage.UPLOAD.value},
            )

        return doc

    def get_document(self, doc_id: str, tenant_id: str) -> DocumentRecord:
        """Retrieve document enforcing strict tenant boundary."""
        doc = self.db.documents.get_by_id(doc_id.strip())
        require(doc is not None, f"Document '{doc_id}' not found")
        require(
            doc.tenant_id == tenant_id.strip(),
            f"Tenant boundary violation: Document '{doc_id}' does not belong to tenant '{tenant_id}'",
        )
        return doc

    def list_tenant_documents(self, tenant_id: str) -> tuple[DocumentRecord, ...]:
        """List all documents for a tenant."""
        return self.db.documents.list_by_tenant(tenant_id.strip())

    def advance_stage(
        self,
        doc_id: str,
        tenant_id: str,
        next_stage: DocumentStage,
        block_count: int | None = None,
        actor_id: str = "system",
    ) -> DocumentRecord:
        """Advance document lifecycle state with transition validation and audit trail."""
        doc = self.get_document(doc_id, tenant_id)
        require(isinstance(next_stage, DocumentStage), f"Invalid next stage: {next_stage}")

        allowed = VALID_TRANSITIONS.get(doc.stage, set())
        require(
            next_stage in allowed or next_stage == DocumentStage.FAILED,
            f"Invalid document state transition from '{doc.stage.value}' to '{next_stage.value}'",
        )

        new_count = block_count if block_count is not None else doc.block_count
        new_version = doc.version + 1

        updated = DocumentRecord(
            doc_id=doc.doc_id,
            tenant_id=doc.tenant_id,
            owner_id=doc.owner_id,
            title=doc.title,
            stage=next_stage,
            version=new_version,
            file_path=doc.file_path,
            file_size_bytes=doc.file_size_bytes,
            mime_type=doc.mime_type,
            status=next_stage,
            filename=doc.filename,
            source=doc.source,
            block_count=new_count,
            created_at=doc.created_at,
            uploaded_at=doc.uploaded_at,
            updated_at=time.time(),
            metadata=doc.metadata,
        )

        self.db.documents.save(updated)

        if self.audit:
            self.audit.record_event(
                tenant_id=tenant_id.strip(),
                actor_id=actor_id.strip(),
                event_type=AuditEventType.DOCUMENT_UPDATE,
                action=f"Advanced document '{doc.title}' to stage '{next_stage.value}'",
                metadata={"doc_id": doc_id, "new_stage": next_stage.value, "version": str(new_version)},
            )

        return updated

    def transition_status(
        self,
        doc_id: str,
        target_stage: DocumentStage,
        tenant_id: str | None = None,
        block_count: int | None = None,
        actor_id: str = "system",
    ) -> DocumentRecord:
        """Alias for advance_stage."""
        doc = self.db.documents.get_by_id(doc_id.strip())
        require(doc is not None, f"Document '{doc_id}' not found")
        tid = tenant_id if tenant_id else doc.tenant_id
        return self.advance_stage(doc_id, tid, target_stage, block_count=block_count, actor_id=actor_id)
