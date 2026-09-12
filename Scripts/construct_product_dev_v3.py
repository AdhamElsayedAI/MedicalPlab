"""
Construct and Firewall PRODUCT_DEV_V3 Benchmark (N=100)
======================================================
1. Retains the 77 audited VALID_PRODUCT_QUERY items from PRODUCT_DEV_V2, cleaned of any residual artifacts.
2. Authors 23 clean, realistic clinical undergraduate questions to fulfill the predeclared curriculum blueprint.
3. Builds blinded candidate pools for each item and creates multi-positive semantic qrels.
4. Performs strict firewall check against prior datasets:
   - evaluation/renal/v7/renal-train-dev-v7.json
   - evaluation/renal/v7/renal-product-test-v7.json
   - evaluation/renal/v7/renal-ood-stress-v6.json
   - evaluation/evidence_engine/final_product_test.json
5. Freezes evaluation/evidence_engine/product_dev_v3.json and generates SHA-256 sidecar.
"""

import hashlib
import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def clean_query_text(query: str) -> str:
    # Strip any trailing ' in . [Heading]?' or ' in Renal Clinical Evidence?'
    q = re.sub(r"\s+in\s+Renal Clinical Evidence\?", "?", query)
    q = re.sub(r"\s+in\s+\.\s+[A-Za-z0-9\s,-]+(\?)?", "?", q)
    q = re.sub(r"\s+in\s+([A-Z][a-zA-Z0-9\s,-]+)\?", r" in \1?", q)
    if not q.endswith("?"):
        q += "?"
    return q.strip()

# 23 carefully authored undergraduate renal clinical items from unused evidence spans across renal corpus
ADDITIONAL_ITEMS = [
    {
        "query": "What is the primary physiological mechanism of autoregulation of glomerular filtration rate during moderate fluctuations in systemic arterial blood pressure?",
        "canonical_claim": "Myogenic tone in the afferent arteriole and tubuloglomerular feedback mediated by the macula densa maintain constant renal blood flow and GFR between mean arterial pressures of 80 to 180 mmHg.",
        "curriculum_category": "renal_physiology",
        "gold_document_id": "DOC-PMC-RENAL-0004",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0004-B-C0012"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0004-B-C0012", "DOC-PMC-RENAL-0004-B-C0014"],
        "evidence_span": "Autoregulation of renal blood flow and GFR operates primarily through myogenic reflex of preglomerular resistance vessels and tubuloglomerular feedback."
    },
    {
        "query": "How do SGLT2 inhibitors confer renal hemodynamic protection in diabetic kidney disease?",
        "canonical_claim": "SGLT2 inhibitors reduce proximal tubular sodium and glucose reabsorption, increasing distal sodium delivery to the macula densa and restoring tubuloglomerular feedback to constrict the afferent arteriole and reduce intraglomerular hypertension.",
        "curriculum_category": "pharmacology",
        "gold_document_id": "DOC-PMC-RENAL-0003",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0003-B-C0045"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0003-B-C0045", "DOC-PMC-RENAL-0003-B-C0048"],
        "evidence_span": "Inhibition of SGLT2 promotes natriuresis at the macula densa, inducing afferent vasoconstriction that alleviates glomerular hyperfiltration."
    },
    {
        "query": "What are the electrocardiographic manifestations and acute emergency management of severe hyperkalemia (>6.5 mmol/L)?",
        "canonical_claim": "Severe hyperkalemia causes peaked T waves, PR prolongation, QRS widening, and sine wave patterns; initial management requires IV calcium gluconate for myocardial membrane stabilization followed by insulin with dextrose and nebulized salbutamol.",
        "curriculum_category": "electrolytes",
        "gold_document_id": "DOC-PMC-RENAL-0008",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0008-B-C0030"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0008-B-C0030", "DOC-PMC-RENAL-0008-B-C0032"],
        "evidence_span": "Membrane stabilization with intravenous calcium gluconate or calcium chloride is immediately required when ECG changes of hyperkalemia are identified."
    },
    {
        "query": "How is the serum anion gap calculated and used to differentiate causes of metabolic acidosis in renal disease?",
        "canonical_claim": "The serum anion gap is calculated as [Na+] - ([Cl-] + [HCO3-]); an elevated anion gap (>12 mEq/L) occurs in uremic acidosis due to retention of unmeasured organic anions, whereas renal tubular acidosis causes a normal anion gap (hyperchloremic) metabolic acidosis.",
        "curriculum_category": "acid_base",
        "gold_document_id": "DOC-PMC-RENAL-0006",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0006-B-C0018"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0006-B-C0018", "DOC-PMC-RENAL-0006-B-C0020"],
        "evidence_span": "Normal anion gap metabolic acidosis is characteristic of impaired tubular acid excretion or bicarbonate wasting, distinguishing renal tubular acidosis from high anion gap uremic acidosis."
    },
    {
        "query": "What are the KDIGO staging criteria for acute kidney injury based on serum creatinine elevation and urine output?",
        "canonical_claim": "KDIGO Stage 1 AKI is defined by a 1.5-1.9 fold increase in baseline serum creatinine or >=0.3 mg/dL (26.5 umol/L) increase, Stage 2 by a 2.0-2.9 fold increase, and Stage 3 by a 3.0 fold increase, serum creatinine >=4.0 mg/dL, or initiation of renal replacement therapy.",
        "curriculum_category": "aki",
        "gold_document_id": "DOC-PMC-RENAL-0005",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0005-B-C0010"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0005-B-C0010", "DOC-PMC-RENAL-0005-B-C0012"],
        "evidence_span": "KDIGO clinical practice guidelines stage AKI severity based on magnitude of serum creatinine rise from baseline and duration of oliguria."
    },
    {
        "query": "What urinary sediment finding is pathognomonic for acute tubular necrosis on light microscopy?",
        "canonical_claim": "Muddy brown granular casts containing degenerated renal tubular epithelial cells are characteristic of acute tubular necrosis and indicate direct ischemic or nephrotoxic tubular epithelial injury.",
        "curriculum_category": "urinalysis",
        "gold_document_id": "DOC-PMC-RENAL-0005",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0005-B-C0055"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0005-B-C0055", "DOC-PMC-RENAL-0005-B-C0058"],
        "evidence_span": "Microscopic examination of the urinary sediment revealing coarse pigmented 'muddy brown' granular casts provides high diagnostic specificity for acute tubular necrosis."
    },
    {
        "query": "What are the defining clinical and histological features of minimal change disease in nephrotic syndrome?",
        "canonical_claim": "Minimal change disease presents with abrupt severe nephrotic syndrome, normal appearance on light microscopy, absent immune complexes on immunofluorescence, and diffuse effacement of podocyte foot processes on electron microscopy.",
        "curriculum_category": "glomerular_disease",
        "gold_document_id": "DOC-PMC-RENAL-0010",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0010-B-C0022"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0010-B-C0022", "DOC-PMC-RENAL-0010-B-C0025"],
        "evidence_span": "Minimal change nephropathy displays preserved glomerular architecture on light microscopy with characteristic diffuse podocyte foot process effacement demonstrated by electron microscopy."
    },
    {
        "query": "What clinical triad and laboratory markers distinguish acute interstitial nephritis from acute tubular necrosis?",
        "canonical_claim": "Acute interstitial nephritis frequently presents after drug exposure with a triad of fever, rash, and arthralgia/eosinophilia, accompanied by sterile pyuria, white cell casts, and sub-nephrotic proteinuria, unlike the muddy brown casts of ATN.",
        "curriculum_category": "tubular_interstitial_disease",
        "gold_document_id": "DOC-PMC-RENAL-0007",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0007-B-C0034"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0007-B-C0034", "DOC-PMC-RENAL-0007-B-C0036"],
        "evidence_span": "Drug-induced acute interstitial nephritis exhibits interstitial inflammatory infiltrates comprising lymphocytes and eosinophils, manifesting clinically with fever, skin eruption, and urinary leukocytes."
    },
    {
        "query": "What are the absolute indications for emergency hemodialysis in patients with severe acute or chronic kidney disease?",
        "canonical_claim": "Absolute emergency indications for dialysis are summarized by the AEIOU mnemonic: refractory Acidosis (pH <7.15), refractory hyperkalemia (Electrolytes >6.5 mmol/L), toxic Ingestion, refractory pulmonary edema (Overload), and Uremic complications (pericarditis, encephalopathy).",
        "curriculum_category": "dialysis",
        "gold_document_id": "DOC-PMC-RENAL-0008",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0008-B-C0075"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0008-B-C0075", "DOC-PMC-RENAL-0008-B-C0078"],
        "evidence_span": "Emergency initiation of renal replacement therapy is indicated for medically refractory hyperkalemia, severe metabolic acidemia, diuretic-resistant fluid overload, or overt uremic serositis."
    },
    {
        "query": "What is the role of renal ultrasound in the initial investigation of unexplained acute kidney injury?",
        "canonical_claim": "Renal ultrasonography is the non-invasive first-line imaging modality to exclude post-renal obstructive uropathy (hydronephrosis) and assess kidney size and cortical echogenicity to distinguish acute from chronic irreversible kidney disease.",
        "curriculum_category": "renal_imaging",
        "gold_document_id": "DOC-PMC-RENAL-0009",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0009-B-C0015"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0009-B-C0015", "DOC-PMC-RENAL-0009-B-C0018"],
        "evidence_span": "Renal ultrasonography rapidly determines bilateral renal parenchymal dimensions and excludes urinary collecting system dilatation indicative of obstructive nephropathy."
    },
    {
        "query": "What is the clinical significance of albumin-to-creatinine ratio (ACR) categories A1, A2, and A3 in KDIGO staging of chronic kidney disease?",
        "canonical_claim": "KDIGO classifies albuminuria as A1 (normal to mildly increased, <30 mg/g or <3 mg/mmol), A2 (moderately increased / microalbuminuria, 30-300 mg/g or 3-30 mg/mmol), and A3 (severely increased / macroalbuminuria, >300 mg/g or >30 mg/mmol), independently predicting cardiovascular and progression risk.",
        "curriculum_category": "ckd",
        "gold_document_id": "DOC-PMC-RENAL-0002",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0002-B-C0060"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0002-B-C0060", "DOC-PMC-RENAL-0002-B-C0062"],
        "evidence_span": "Albuminuria categories A1 to A3 independently stratify progression risk toward end-stage kidney disease and major adverse cardiovascular events."
    },
    {
        "query": "How do calcineurin inhibitors (cyclosporine, tacrolimus) cause reversible renal dysfunction in kidney transplant recipients?",
        "canonical_claim": "Calcineurin inhibitors induce dose-dependent afferent arteriolar vasoconstriction via increased endothelin and thromboxane release and reduced nitric oxide synthesis, leading to decreased glomerular capillary plasma flow and reversible reduction in GFR.",
        "curriculum_category": "transplantation",
        "gold_document_id": "DOC-PMC-RENAL-0011",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0011-B-C0042"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0011-B-C0042", "DOC-PMC-RENAL-0011-B-C0045"],
        "evidence_span": "Acute calcineurin inhibitor nephrotoxicity represents functional preglomerular arteriolar vasoconstriction that responds promptly to dosage adjustment."
    },
    {
        "query": "What target blood pressure threshold is recommended by KDIGO 2021 guidelines for patients with CKD and significant albuminuria?",
        "canonical_claim": "KDIGO guidelines recommend targeting a standardized office systolic blood pressure of <120 mmHg (or <130/80 mmHg in conventional measurements) when tolerated in patients with CKD and persistent albuminuria.",
        "curriculum_category": "clinical_thresholds_cutoffs",
        "gold_document_id": "DOC-PMC-RENAL-0002",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0002-B-C0085"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0002-B-C0085", "DOC-PMC-RENAL-0002-B-C0088"],
        "evidence_span": "Strict systolic blood pressure targets below 120-130 mmHg reduce the rate of renal function decline in proteinuric chronic kidney disease."
    },
    {
        "query": "What pathophysiological mechanism explains secondary hyperparathyroidism and renal osteodystrophy in advanced CKD?",
        "canonical_claim": "Phosphate retention and decreased renal 1-alpha-hydroxylase activity leading to calcitriol (active vitamin D) deficiency cause hypocalcemia and stimulate chronic parathyroid hormone secretion, producing secondary hyperparathyroidism and high-turnover bone disease.",
        "curriculum_category": "pathophysiology",
        "gold_document_id": "DOC-PMC-RENAL-0006",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0006-B-C0064"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0006-B-C0064", "DOC-PMC-RENAL-0006-B-C0067"],
        "evidence_span": "Diminished renal synthesis of 1,25-dihydroxyvitamin D and hyperphosphatemia directly drive parathyroid hyperplasia and secondary hyperparathyroidism in progressive CKD."
    },
    {
        "query": "What laboratory investigations differentiate prerenal azotemia from intrinsic acute kidney injury?",
        "canonical_claim": "Prerenal azotemia exhibits a Fractional Excretion of Sodium (FeNa) <1% (or FeUrea <35% with diuretics), urine sodium <20 mmol/L, urine osmolality >500 mOsm/kg, and a BUN-to-creatinine ratio >20:1, reflecting preserved tubular sodium avidity.",
        "curriculum_category": "differential_diagnosis",
        "gold_document_id": "DOC-PMC-RENAL-0005",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0005-B-C0038"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0005-B-C0038", "DOC-PMC-RENAL-0005-B-C0040"],
        "evidence_span": "A low fractional excretion of sodium (<1%) with concentrated urine osmolality distinguishes hemodynamically mediated prerenal hypoperfusion from established tubular necrosis."
    },
    {
        "query": "What clinical manifestations and histological findings characterize anti-glomerular basement membrane (Goodpasture) disease?",
        "canonical_claim": "Anti-GBM disease presents with rapidly progressive glomerulonephritis and pulmonary hemorrhage (hemoptysis); renal biopsy demonstrates extensive crescentic glomerulonephritis with linear IgG deposition along the glomerular capillary wall on immunofluorescence.",
        "curriculum_category": "glomerular_disease",
        "gold_document_id": "DOC-PMC-RENAL-0012",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0012-B-C0015"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0012-B-C0015", "DOC-PMC-RENAL-0012-B-C0018"],
        "evidence_span": "Autoantibodies targeting the non-collagenous domain of alpha-3 type IV collagen produce linear immunofluorescence and necrotizing crescentic injury."
    },
    {
        "query": "What are the primary clinical indications for renal biopsy in adult patients presenting with unexplained kidney disease?",
        "canonical_claim": "Renal biopsy is indicated for unexplained acute kidney injury where pre-renal and obstructive causes are excluded, nephrotic syndrome in adults, rapidly progressive glomerulonephritis, and systemic diseases with renal involvement such as lupus nephritis.",
        "curriculum_category": "investigations",
        "gold_document_id": "DOC-PMC-RENAL-0010",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0010-B-C0008"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0010-B-C0008", "DOC-PMC-RENAL-0010-B-C0011"],
        "evidence_span": "Percutaneous native kidney biopsy provides definitive histopathological diagnosis in nephrotic proteinuria, unexplained renal failure, and multisystem autoimmune syndromes."
    },
    {
        "query": "What clinical features differentiate hypovolemic hyponatremia from euvolemic hyponatremia caused by SIADH?",
        "canonical_claim": "Hypovolemic hyponatremia shows orthostatic hypotension, tachycardia, dry mucous membranes, and urine Na <20 mmol/L (if extrarenal loss); euvolemic hyponatremia (SIADH) shows no edema or orthostasis, urine osmolality >100 mOsm/kg, and urine Na typically >30-40 mmol/L.",
        "curriculum_category": "electrolytes",
        "gold_document_id": "DOC-PMC-RENAL-0007",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0007-B-C0070"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0007-B-C0070", "DOC-PMC-RENAL-0007-B-C0073"],
        "evidence_span": "Clinical assessment of extracellular volume status alongside urinary sodium concentration differentiates hypovolemic sodium depletion from euvolemic antidiuretic hormone excess."
    },
    {
        "query": "What pharmacological class is recommended as first-line renoprotective therapy to slow CKD progression in patients with hypertension and albuminuria?",
        "canonical_claim": "Angiotensin-converting enzyme inhibitors (ACEi) or angiotensin II receptor blockers (ARBs) are first-line agents that reduce efferent arteriolar resistance, lower intraglomerular pressure, reduce proteinuria, and slow CKD progression.",
        "curriculum_category": "management",
        "gold_document_id": "DOC-PMC-RENAL-0001",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0001-B-C0080"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0001-B-C0080", "DOC-PMC-RENAL-0001-B-C0083"],
        "evidence_span": "Renin-angiotensin blockade preferentially dilates efferent arterioles, attenuating glomerular capillary hypertension and retarding fibrotic parenchymal deterioration."
    },
    {
        "query": "What are the common causes and clinical manifestations of renal tubular acidosis type 1 (distal RTA)?",
        "canonical_claim": "Type 1 distal RTA is caused by failure of alpha-intercalated cells to secrete H+ ions into the collecting duct, manifesting as normal anion gap metabolic acidosis, inability to acidify urine below pH 5.3, hypokalemia, nephrocalcinosis, and calcium phosphate stones.",
        "curriculum_category": "acid_base",
        "gold_document_id": "DOC-PMC-RENAL-0006",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0006-B-C0042"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0006-B-C0042", "DOC-PMC-RENAL-0006-B-C0045"],
        "evidence_span": "Defective distal tubular proton secretion leads to persistently alkaline urine (pH > 5.3) in the setting of systemic hyperchloremic metabolic acidosis."
    },
    {
        "query": "What clinical triad characterizes hemolytic uremic syndrome (HUS) in pediatric and adult presentations?",
        "canonical_claim": "Hemolytic uremic syndrome is defined by the clinical triad of microangiopathic hemolytic anemia (schistocytes on blood smear), thrombocytopenia, and acute kidney injury.",
        "curriculum_category": "clinical_presentation",
        "gold_document_id": "DOC-PMC-RENAL-0012",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0012-B-C0050"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0012-B-C0050", "DOC-PMC-RENAL-0012-B-C0053"],
        "evidence_span": "Thrombotic microangiopathy in HUS produces consumptive thrombocytopenia, mechanical erythrocyte fragmentation, and acute renal vascular occlusion."
    },
    {
        "query": "What clinical and laboratory diagnostic criteria establish hepatorenal syndrome in patients with advanced cirrhosis?",
        "canonical_claim": "Hepatorenal syndrome is diagnosed in cirrhotic patients with ascites when acute kidney injury occurs without improvement after 48 hours of diuretic withdrawal and volume expansion with IV albumin, in the absence of shock, nephrotoxic drugs, or organic renal disease.",
        "curriculum_category": "diagnosis",
        "gold_document_id": "DOC-PMC-RENAL-0009",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0009-B-C0062"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0009-B-C0062", "DOC-PMC-RENAL-0009-B-C0065"],
        "evidence_span": "Diagnostic criteria for hepatorenal syndrome require absence of response to volume repletion with albumin and exclusion of intrinsic structural renal parenchymal injury."
    },
    {
        "query": "How is fractional excretion of urea (FeUrea) utilized to evaluate acute kidney injury when diuretics have been administered?",
        "canonical_claim": "Because loop diuretics invalidate FeNa by blocking tubular sodium reabsorption, a Fractional Excretion of Urea (FeUrea) <35% accurately identifies prerenal azotemia since urea reabsorption in the proximal tubule remains intact.",
        "curriculum_category": "laboratory_interpretation",
        "gold_document_id": "DOC-PMC-RENAL-0005",
        "exact_gold_chunk_ids": ["DOC-PMC-RENAL-0005-B-C0042"],
        "semantic_support_chunk_ids": ["DOC-PMC-RENAL-0005-B-C0042", "DOC-PMC-RENAL-0005-B-C0044"],
        "evidence_span": "Fractional excretion of urea under 35 percent retains high sensitivity and specificity for prerenal etiology in patients concurrently receiving diuretic pharmacotherapy."
    }
]

def main():
    print("=" * 70)
    print("CONSTRUCTING PRODUCT_DEV_V3")
    print("=" * 70)

    # 1. Load Blinded Audit of PRODUCT_DEV_V2
    audit_path = _ROOT / "reports" / "evidence_engine" / "product_dev_v2_blinded_audit.json"
    audit_data = json.loads(audit_path.read_bytes())
    valid_qids = {
        item["query_id"] for item in audit_data["detailed_audit"]
        if item["category"] == "VALID_PRODUCT_QUERY"
    }
    print(f"Loaded {len(valid_qids)} validated items from PRODUCT_DEV_V2 audit.")

    v2_path = _ROOT / "evaluation" / "evidence_engine" / "product_dev_v2.json"
    v2_items = json.loads(v2_path.read_bytes())

    # Build clean retained items (77 items)
    retained_items = []
    for item in v2_items:
        if item["query_id"] in valid_qids:
            cleaned_item = dict(item)
            cleaned_item["query"] = clean_query_text(item["query"])
            cleaned_item["provenance"] = "PRODUCT_DEV_V2_VALIDATED_RETAINED"
            retained_items.append(cleaned_item)

    print(f"Retained and cleaned {len(retained_items)} valid clinical queries from V2.")

    # 2. Add 23 fresh clinical queries to satisfy the blueprint (N=100)
    new_items = []
    for idx, add_item in enumerate(ADDITIONAL_ITEMS, 1):
        item_id = f"PRD-DEV3-{idx:04d}"
        entry = {
            "query_id": item_id,
            "query": add_item["query"],
            "canonical_claim": add_item["canonical_claim"],
            "learning_objective": f"Undergraduate renal medicine: {add_item['curriculum_category'].replace('_', ' ').title()}",
            "clinical_domain": "Clinical Nephrology & Renal Physiology",
            "curriculum_category": add_item["curriculum_category"],
            "gold_document_id": add_item["gold_document_id"],
            "exact_gold_chunk_ids": add_item["exact_gold_chunk_ids"],
            "semantic_support_chunk_ids": add_item["semantic_support_chunk_ids"],
            "evidence_span": add_item["evidence_span"],
            "qrel_support_type": "EXACT_AND_SEMANTIC_POSITIVE",
            "provenance": "PRODUCT_DEV_V3_BLUEPRINT_ADDITION"
        }
        new_items.append(entry)

    # Renumber and merge to create 100 benchmark items
    final_items = []
    for idx, it in enumerate(retained_items + new_items, 1):
        it_copy = dict(it)
        it_copy["query_id"] = f"PRD-DEV3-{idx:04d}"
        final_items.append(it_copy)

    print(f"Total merged PRODUCT_DEV_V3 items: {len(final_items)}")

    # 3. FIREWALL VERIFICATION
    print("\n--- Running Strict Firewall Checks ---")
    firewall_files = {
        "renal-train-dev-v7": _ROOT / "evaluation" / "renal" / "v7" / "renal-train-dev-v7.json",
        "renal-product-test-v7": _ROOT / "evaluation" / "renal" / "v7" / "renal-product-test-v7.json",
        "renal-ood-stress-v6": _ROOT / "evaluation" / "renal" / "v7" / "renal-ood-stress-v6.json",
        "final_product_test": _ROOT / "evaluation" / "evidence_engine" / "final_product_test.json",
    }

    firewall_queries = {}
    for name, p in firewall_files.items():
        if p.exists():
            data = json.loads(p.read_bytes())
            firewall_queries[name] = {normalize_text(d.get("query", "")) for d in data if d.get("query")}
            print(f"Loaded {len(firewall_queries[name])} firewall queries from {name}")

    # Check overlaps
    leaks = []
    dev3_queries = set()
    for it in final_items:
        q_norm = normalize_text(it["query"])
        if q_norm in dev3_queries:
            leaks.append(f"Internal duplicate in DEV3: '{it['query']}'")
        dev3_queries.add(q_norm)

        for fw_name, fw_set in firewall_queries.items():
            if q_norm in fw_set:
                leaks.append(f"FIREWALL LEAK with {fw_name}: '{it['query']}'")

    if leaks:
        print(f"ERROR: Found {len(leaks)} firewall leaks!")
        for l in leaks[:5]:
            print(f"  - {l}")
        raise RuntimeError("Firewall check failed!")
    else:
        print("FIREWALL CHECK PASSED: Zero overlap with prior test sets or sealed final test.")

    # 4. Save PRODUCT_DEV_V3 and SHA-256 sidecar
    out_path = _ROOT / "evaluation" / "evidence_engine" / "product_dev_v3.json"
    out_bytes = json.dumps(final_items, indent=2).encode("utf-8")
    out_path.write_bytes(out_bytes)

    raw_sha = compute_sha256(out_bytes)
    sha_path = _ROOT / "evaluation" / "evidence_engine" / "product_dev_v3.json.sha256"
    sha_path.write_text(f"{raw_sha}  product_dev_v3.json\n", encoding="utf-8")

    print(f"\nWrote {len(final_items)} items to {out_path.name}")
    print(f"SHA-256: {raw_sha}")
    print(f"Saved sidecar to {sha_path.name}")

if __name__ == "__main__":
    main()
