"""Regression tests for PMC acquisition provenance persistence."""

import json

import pytest

from Scripts import download_pmc_xml


@pytest.mark.parametrize("wrapped", [False, True])
def test_record_download_provenance_preserves_manifest_shape(tmp_path, monkeypatch, wrapped):
    document = {
        "document_id": "DOC-PMC-TEST-0001",
        "sha256": None,
        "retrieved_at": None,
        "ingestion_status": "candidate",
    }
    payload = {"documents": [document]} if wrapped else [document]
    manifest_path = tmp_path / "document_manifest.json"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(download_pmc_xml, "MANIFEST_PATH", manifest_path)

    digest = "a" * 64
    retrieved_at = "2026-09-09T03:21:35.524578+00:00"
    download_pmc_xml.record_download_provenance(
        "DOC-PMC-TEST-0001",
        digest,
        retrieved_at,
    )

    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert isinstance(saved, dict) is wrapped
    saved_documents = saved["documents"] if wrapped else saved
    assert saved_documents[0]["sha256"] == digest
    assert saved_documents[0]["retrieved_at"] == retrieved_at
    assert saved_documents[0]["ingestion_status"] == "downloaded"


def test_record_download_provenance_rejects_unknown_document(tmp_path, monkeypatch):
    manifest_path = tmp_path / "document_manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(download_pmc_xml, "MANIFEST_PATH", manifest_path)

    with pytest.raises(ValueError, match="Document not found"):
        download_pmc_xml.record_download_provenance(
            "DOC-PMC-MISSING",
            "b" * 64,
            "2026-09-09T03:21:35+00:00",
        )
