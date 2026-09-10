"""Phase 9 — Undergraduate Renal Curriculum Coverage Matrix.

Builds an independent a priori coverage assessment for the V2 corpus
without reference to benchmark failures (per mission spec §22).

Each topic is classified:
  STRONG   — multiple strong passages, well-indexed
  ADEQUATE — at least one good section found
  THIN     — partial coverage, key aspects missing
  MISSING  — no relevant source

Each source gets a curriculum role:
  UNDERGRADUATE_CORE     — primary learning source
  SUPPORTING             — supplementary detail
  SPECIALIST_SUPPORTING  — specialist depth, not core UG
  LOW_MARGINAL_VALUE     — minimal pedagogical benefit
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "reports" / "renal_v2_curriculum_coverage_matrix.json"
REG_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"

# ============================================================
# CURRICULUM TOPIC MATRIX (from mission spec §22)
# ============================================================
# Format: (topic_id, topic_name, foundational_or_clinical, coverage, primary_docs)
CURRICULUM_TOPICS = [
    # FOUNDATIONAL
    ("kidney_anatomy",              "Kidney anatomy",                    "FOUNDATIONAL", "THIN",     ["DOC-PMC-RENAL-0018"]),
    ("urinary_tract_anatomy",       "Urinary tract anatomy",             "FOUNDATIONAL", "THIN",     []),
    ("nephron_anatomy",             "Nephron anatomy",                   "FOUNDATIONAL", "THIN",     ["DOC-PMC-RENAL-0018"]),
    ("renal_blood_supply",          "Renal blood supply",                "FOUNDATIONAL", "THIN",     ["DOC-PMC-RENAL-0018"]),
    ("renal_circulation",           "Renal circulation",                 "FOUNDATIONAL", "THIN",     ["DOC-PMC-RENAL-0018"]),
    ("filtration_barrier",          "Filtration barrier (glomerular)",   "FOUNDATIONAL", "ADEQUATE", ["DOC-PMC-RENAL-0018", "DOC-PMC-RENAL-0002"]),
    ("glomerular_filtration",       "Glomerular filtration",             "FOUNDATIONAL", "ADEQUATE", ["DOC-PMC-RENAL-0018"]),
    ("gfr",                         "GFR concept and determinants",      "FOUNDATIONAL", "STRONG",   ["DOC-PMC-RENAL-0016", "DOC-PMC-RENAL-0018"]),
    ("gfr_regulation",              "GFR regulation (autoregulation)",   "FOUNDATIONAL", "ADEQUATE", ["DOC-PMC-RENAL-0016", "DOC-PMC-RENAL-0018"]),
    ("afferent_arteriole",          "Afferent arteriole effects on GFR", "FOUNDATIONAL", "ADEQUATE", ["DOC-PMC-RENAL-0016"]),
    ("efferent_arteriole",          "Efferent arteriole effects on GFR", "FOUNDATIONAL", "ADEQUATE", ["DOC-PMC-RENAL-0016"]),
    ("renal_autoregulation",        "Renal autoregulation",              "FOUNDATIONAL", "ADEQUATE", ["DOC-PMC-RENAL-0016"]),
    ("proximal_tubular_transport",  "Proximal tubular transport",        "FOUNDATIONAL", "STRONG",   ["DOC-PMC-RENAL-0004", "DOC-PMC-RENAL-0020", "DOC-PMC-RENAL-0019"]),
    ("sodium_handling",             "Sodium handling (tubular)",         "FOUNDATIONAL", "STRONG",   ["DOC-PMC-RENAL-0004", "DOC-PMC-RENAL-0020"]),
    ("potassium_handling",          "Potassium handling",                "FOUNDATIONAL", "STRONG",   ["DOC-PMC-RENAL-0003", "DOC-PMC-RENAL-0009"]),
    ("glucose_handling",            "Glucose handling / SGLT",           "FOUNDATIONAL", "STRONG",   ["DOC-PMC-RENAL-0019"]),
    ("water_handling",              "Water handling / AQP",              "FOUNDATIONAL", "THIN",     ["DOC-PMC-RENAL-0023"]),
    ("adh_vasopressin",             "ADH / vasopressin mechanism",       "FOUNDATIONAL", "THIN",     ["DOC-PMC-RENAL-0023"]),
    ("countercurrent_multiplier",   "Countercurrent multiplier",         "FOUNDATIONAL", "ADEQUATE", ["DOC-PMC-RENAL-0023"]),
    ("medullary_gradient",          "Medullary concentration gradient",  "FOUNDATIONAL", "ADEQUATE", ["DOC-PMC-RENAL-0023"]),
    ("raas",                        "RAAS physiology",                   "FOUNDATIONAL", "STRONG",   ["DOC-PMC-RENAL-0001", "DOC-PMC-RENAL-0020"]),
    ("acid_base_physiology",        "Acid-base physiology (renal)",      "FOUNDATIONAL", "STRONG",   ["DOC-PMC-RENAL-0004", "DOC-PMC-RENAL-0005", "DOC-PMC-RENAL-0021"]),
    ("renal_endocrine",             "Renal endocrine functions (EPO, calcitriol)", "FOUNDATIONAL", "ADEQUATE", ["DOC-PMC-RENAL-0024"]),
    # CLINICAL
    ("aki",                         "AKI — overview",                    "CLINICAL",     "STRONG",   ["DOC-PMC-RENAL-0006", "DOC-PMC-RENAL-0007"]),
    ("aki_prerenal",                "Pre-renal AKI",                     "CLINICAL",     "ADEQUATE", ["DOC-PMC-RENAL-0006", "DOC-PMC-RENAL-0007"]),
    ("aki_intrinsic",               "Intrinsic renal AKI",               "CLINICAL",     "ADEQUATE", ["DOC-PMC-RENAL-0006", "DOC-PMC-RENAL-0007"]),
    ("aki_postrenal",               "Post-renal AKI",                    "CLINICAL",     "THIN",     ["DOC-PMC-RENAL-0006"]),
    ("aki_rhabdomyolysis",          "AKI due to rhabdomyolysis",         "CLINICAL",     "ADEQUATE", ["DOC-PMC-RENAL-0015"]),
    ("ckd",                         "CKD — definition, staging",         "CLINICAL",     "THIN",     ["DOC-PMC-RENAL-0007"]),
    ("nephrotic_syndrome",          "Nephrotic syndrome",                "CLINICAL",     "ADEQUATE", ["DOC-PMC-RENAL-0008"]),
    ("nephritic_syndrome",          "Nephritic syndrome / GN",           "CLINICAL",     "THIN",     ["DOC-PMC-RENAL-0008"]),
    ("glomerulonephritis",          "Glomerulonephritis",                "CLINICAL",     "THIN",     ["DOC-PMC-RENAL-0008"]),
    ("proteinuria",                 "Proteinuria",                       "CLINICAL",     "ADEQUATE", ["DOC-PMC-RENAL-0008", "DOC-PMC-RENAL-0018"]),
    ("haematuria",                  "Haematuria",                        "CLINICAL",     "ADEQUATE", ["DOC-PMC-RENAL-0025"]),
    ("electrolyte_hyperkalaemia",   "Hyperkalaemia — mechanism & mgt",   "CLINICAL",     "STRONG",   ["DOC-PMC-RENAL-0003", "DOC-PMC-RENAL-0009", "DOC-PMC-RENAL-0010"]),
    ("metabolic_acidosis",          "Metabolic acidosis (renal contribution)", "CLINICAL", "STRONG", ["DOC-PMC-RENAL-0004", "DOC-PMC-RENAL-0005"]),
    ("metabolic_alkalosis",         "Metabolic alkalosis (renal)",       "CLINICAL",     "THIN",     ["DOC-PMC-RENAL-0004"]),
    ("uti",                         "UTI (lower tract)",                 "CLINICAL",     "ADEQUATE", ["DOC-PMC-RENAL-0011", "DOC-PMC-RENAL-0013"]),
    ("pyelonephritis",              "Pyelonephritis / upper UTI",        "CLINICAL",     "THIN",     ["DOC-PMC-RENAL-0011"]),
    ("renal_stones",                "Renal stones / nephrolithiasis",    "CLINICAL",     "STRONG",   ["DOC-PMC-RENAL-0012", "DOC-PMC-RENAL-0013"]),
    ("obstruction_hydronephrosis",  "Urinary obstruction / hydronephrosis", "CLINICAL",  "ADEQUATE", ["DOC-PMC-RENAL-0014"]),
    ("dialysis_basics",             "Dialysis basics",                   "CLINICAL",     "ADEQUATE", ["DOC-PMC-RENAL-0015"]),
    ("rrt_basics",                  "Renal replacement therapy basics",  "CLINICAL",     "ADEQUATE", ["DOC-PMC-RENAL-0015"]),
]

# ============================================================
# SOURCE ROLES (from registry + curriculum assessment)
# ============================================================
SOURCE_ROLES = {
    "DOC-PMC-RENAL-0001": "SUPPORTING",            # RAAS/cardiovascular — specialist
    "DOC-PMC-RENAL-0002": "SPECIALIST_SUPPORTING", # Glomerulus-on-chip — too narrow
    "DOC-PMC-RENAL-0003": "UNDERGRADUATE_CORE",    # Potassium and kidney
    "DOC-PMC-RENAL-0004": "UNDERGRADUATE_CORE",    # Proximal tubule transport
    "DOC-PMC-RENAL-0005": "UNDERGRADUATE_CORE",    # Acid-base exchange
    "DOC-PMC-RENAL-0006": "SUPPORTING",            # Japanese AKI guideline
    "DOC-PMC-RENAL-0007": "UNDERGRADUATE_CORE",    # Evidence-based AKI guideline
    "DOC-PMC-RENAL-0008": "SPECIALIST_SUPPORTING", # IPNA nephrotic — paediatric
    "DOC-PMC-RENAL-0009": "SUPPORTING",            # Hyperkalaemia pathophysiology
    "DOC-PMC-RENAL-0010": "SUPPORTING",            # Hyperkalaemia management
    "DOC-PMC-RENAL-0011": "LOW_MARGINAL_VALUE",    # Recurrent UTI — narrow
    "DOC-PMC-RENAL-0012": "UNDERGRADUATE_CORE",    # Kidney stones urological guidelines
    "DOC-PMC-RENAL-0013": "SUPPORTING",            # Stones + UTI association
    "DOC-PMC-RENAL-0014": "SPECIALIST_SUPPORTING", # Hydronephrosis grading
    "DOC-PMC-RENAL-0015": "SPECIALIST_SUPPORTING", # Rhabdomyolysis + dialysis
    "DOC-PMC-RENAL-0016": "SPECIALIST_SUPPORTING", # GFR in critically ill
    "DOC-PMC-RENAL-0018": "UNDERGRADUATE_CORE",    # Glomerular filtration barrier
    "DOC-PMC-RENAL-0019": "UNDERGRADUATE_CORE",    # Glucose transporters (SGLT)
    "DOC-PMC-RENAL-0020": "SUPPORTING",            # Akt/SGK1 tubular transport
    "DOC-PMC-RENAL-0021": "SUPPORTING",            # AE4 acid-base sensing
    "DOC-PMC-RENAL-0023": "UNDERGRADUATE_CORE",    # Countercurrent / ADH
    "DOC-PMC-RENAL-0024": "UNDERGRADUATE_CORE",    # Renal endocrine (EPO, vitamin D)
    "DOC-PMC-RENAL-0025": "UNDERGRADUATE_CORE",    # Hematuria differential & mgt
}

MISSING_TOPICS = [t for t in CURRICULUM_TOPICS if t[3] == "MISSING"]
THIN_TOPICS = [t for t in CURRICULUM_TOPICS if t[3] == "THIN"]
ADEQUATE_TOPICS = [t for t in CURRICULUM_TOPICS if t[3] == "ADEQUATE"]
STRONG_TOPICS = [t for t in CURRICULUM_TOPICS if t[3] == "STRONG"]


def main() -> None:
    reg = json.loads(REG_PATH.read_text(encoding="utf-8"))
    docs = {d["document_id"]: d for d in reg.get("documents", [])}

    print("UNDERGRADUATE RENAL CURRICULUM COVERAGE MATRIX")
    print("=" * 70)
    print(f"Total topics: {len(CURRICULUM_TOPICS)}")
    print(f"  STRONG:   {len(STRONG_TOPICS)}")
    print(f"  ADEQUATE: {len(ADEQUATE_TOPICS)}")
    print(f"  THIN:     {len(THIN_TOPICS)}")
    print(f"  MISSING:  {len(MISSING_TOPICS)}")
    print()

    print("MISSING TOPICS (priority acquisition candidates):")
    for t_id, t_name, t_type, t_cov, t_docs in MISSING_TOPICS:
        print(f"  [{t_type}] {t_name}")
    print()

    print("THIN TOPICS (secondary acquisition candidates):")
    for t_id, t_name, t_type, t_cov, t_docs in THIN_TOPICS:
        print(f"  [{t_type}] {t_name}  sources={t_docs}")
    print()

    print("SOURCE ROLE SUMMARY:")
    from collections import Counter
    role_counts = Counter(SOURCE_ROLES.values())
    for role, count in sorted(role_counts.items()):
        print(f"  {role:<30} {count}")
    print()

    # Build report
    topics_payload = []
    for t_id, t_name, t_type, t_cov, t_docs in CURRICULUM_TOPICS:
        topics_payload.append({
            "topic_id": t_id,
            "topic_name": t_name,
            "topic_type": t_type,
            "coverage": t_cov,
            "primary_document_ids": t_docs,
        })

    sources_payload = []
    for doc_id, curriculum_role in sorted(SOURCE_ROLES.items()):
        doc = docs.get(doc_id, {})
        sources_payload.append({
            "document_id": doc_id,
            "title": doc.get("title", "?"),
            "educational_classification": doc.get("educational_classification", "?"),
            "curriculum_role_assessment": curriculum_role,
        })

    report = {
        "report_id": "RENAL-V2-CURRICULUM-COVERAGE-MATRIX",
        "n_topics": len(CURRICULUM_TOPICS),
        "coverage_summary": {
            "STRONG": len(STRONG_TOPICS),
            "ADEQUATE": len(ADEQUATE_TOPICS),
            "THIN": len(THIN_TOPICS),
            "MISSING": len(MISSING_TOPICS),
        },
        "missing_topics": [{"id": t[0], "name": t[1], "type": t[2]} for t in MISSING_TOPICS],
        "thin_topics": [{"id": t[0], "name": t[1], "type": t[2], "partial_sources": t[4]} for t in THIN_TOPICS],
        "topics": topics_payload,
        "source_roles": sources_payload,
        "acquisition_justification": (
            "MISSING topics require new open-access PMC sources."
            " THIN topics may benefit from broader review articles."
            " Corpus repair is curriculum-driven, NOT benchmark-failure-driven."
        ),
    }

    OUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Coverage matrix written to: {OUT_PATH}")

    # Acquisition targets
    print("\nACQUISITION PRIORITIES:")
    print("  HIGH PRIORITY (MISSING):")
    for t in MISSING_TOPICS:
        print(f"    - {t[1]} [{t[2]}]")
    print("  MEDIUM PRIORITY (THIN foundational):")
    for t in THIN_TOPICS:
        if t[2] == "FOUNDATIONAL":
            print(f"    - {t[1]}")


if __name__ == "__main__":
    main()
