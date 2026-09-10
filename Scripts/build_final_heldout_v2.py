"""Phase 16 & 17 — Build and SHA-freeze Independently Sampled FINAL HELDOUT per Mission §36 & §37.

Creates evaluation/renal/renal-heldout-v2-final.json and writes its SHA256 sidecar immediately.
Marked: FINAL_FROZEN_UNSEEN.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
OUT_PATH = ROOT / "evaluation" / "renal" / "renal-heldout-v2-final.json"

# Load chunks to verify evidence presence
chunks_map = {}
for f in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    for ch in json.loads(f.read_text(encoding="utf-8"))["chunks"]:
        chunks_map[ch["chunk_id"]] = ch

CONCEPTS = [
    {
        "topic": "RAAS",
        "doc_id": "DOC-PMC-RENAL-0001",
        "auth": False,
        "queries": [
            ("mechanism", ["aldosterone", "principal", "sodium"], "How does aldosterone increase sodium reabsorption in the principal cells of the collecting duct?"),
            ("physiology", ["hemodynamic", "perfusion", "filtration"], "What hemodynamic changes occur in the renal microcirculation when angiotensin II levels rise?"),
            ("clinical_reasoning", ["heart failure", "fluid", "retention"], "In congestive heart failure, how does chronic activation of RAAS contribute to fluid retention?"),
            ("comparison", ["efferent", "afferent", "resistance"], "What is the difference between afferent and efferent arteriolar resistance changes mediated by angiotensin II?"),
        ]
    },
    {
        "topic": "filtration_barrier",
        "doc_id": "DOC-PMC-RENAL-0018",
        "auth": False,
        "queries": [
            ("mechanism", ["endothelial", "fenestrations", "permeability"], "What role do endothelial fenestrations play in determining the permeability of the glomerular capillary wall?"),
            ("physiology", ["size", "charge", "selectivity"], "How do size and charge selectivity collaborate in the renal filtration barrier?"),
            ("clinical_reasoning", ["slit diaphragm", "proteinuria", "damage"], "Why does damage to the glomerular slit diaphragm result in severe selective proteinuria?"),
            ("investigation", ["ultrastructure", "barrier", "glomerulus"], "What ultrastructural changes are seen in the glomerular filtration barrier in nephrotic syndrome?"),
        ]
    },
    {
        "topic": "potassium_handling",
        "doc_id": "DOC-PMC-RENAL-0003",
        "auth": False,
        "queries": [
            ("mechanism", ["aldosterone", "principal", "potassium"], "How does aldosterone stimulate potassium excretion via the apical membrane of principal cells?"),
            ("physiology", ["alkalosis", "excretion", "potassium"], "Why does metabolic alkalosis enhance urinary potassium excretion?"),
            ("clinical_reasoning", ["thick ascending", "Henle", "potassium"], "Which transport mechanisms reabsorb potassium in the thick ascending limb of the loop of Henle?"),
            ("comparison", ["proximal", "distal", "potassium"], "How does potassium handling in the proximal tubule differ from that in the late distal tubule and collecting duct?"),
        ]
    },
    {
        "topic": "proximal_transport",
        "doc_id": "DOC-PMC-RENAL-0004",
        "auth": False,
        "queries": [
            ("mechanism", ["ATPase", "gradient", "basolateral"], "How does basolateral Na+/K+-ATPase generate the electrochemical gradient for proximal tubular reabsorption?"),
            ("physiology", ["isosmotic", "reabsorption", "plasma"], "Why is fluid reabsorption in the proximal tubule isosmotic with plasma?"),
            ("clinical_reasoning", ["proton", "acid-base", "impaired"], "What consequence does impaired proximal tubular proton secretion have on systemic acid-base balance?"),
            ("definition", ["solute", "uptake", "proximal"], "Which apical transporters mediate solute uptake in the early proximal tubule?"),
        ]
    },
    {
        "topic": "acid_base",
        "doc_id": "DOC-PMC-RENAL-0005",
        "auth": False,
        "queries": [
            ("mechanism", ["carbonic anhydrase", "bicarbonate", "reabsorption"], "How does carbonic anhydrase contribute to proximal bicarbonate reabsorption?"),
            ("physiology", ["type B", "intercalated", "bicarbonate"], "Under what circumstances do type B intercalated cells secrete bicarbonate into urine?"),
            ("clinical_reasoning", ["hypovolaemia", "contraction alkalosis", "kidney"], "Why does severe hypovolaemia lead to contraction alkalosis in the kidney?"),
            ("comparison", ["proximal", "distal", "secretion"], "How does proximal bicarbonate reabsorption differ from distal proton secretion?"),
        ]
    },
    {
        "topic": "aki_definition",
        "doc_id": "DOC-PMC-RENAL-0006",
        "auth": True,
        "queries": [
            ("clinical_reasoning", ["risk factors", "hospital-acquired", "AKI"], "What are the common clinical risk factors for developing hospital-acquired acute kidney injury?"),
            ("definition", ["time window", "creatinine", "0.3"], "What time window is specified in the KDIGO guidelines for an increase in serum creatinine of 0.3 mg/dL?"),
            ("investigation", ["urine output", "monitoring", "detection"], "How does urine output monitoring assist in identifying developing AKI before serum creatinine rises?"),
            ("comparison", ["prerenal", "intrinsic", "fractional excretion"], "How does the fractional excretion of sodium distinguish prerenal azotemia from acute tubular necrosis?"),
        ]
    },
    {
        "topic": "ckd_management",
        "doc_id": "DOC-PMC-RENAL-0007",
        "auth": True,
        "queries": [
            ("clinical_reasoning", ["blood pressure", "target", "proteinuria"], "What are the recommended blood pressure targets in chronic kidney disease patients with significant proteinuria?"),
            ("physiology", ["hyperparathyroidism", "phosphate", "fibroblast"], "How does phosphate retention contribute to secondary hyperparathyroidism in advancing CKD?"),
            ("mechanism", ["SGLT2", "hyperfiltration", "nephroprotection"], "How do SGLT2 inhibitors reduce intraglomerular pressure and slow CKD progression?"),
            ("investigation", ["albuminuria", "ACR", "staging"], "Why is urinary albumin-to-creatinine ratio preferred over total protein measurement in CKD staging?"),
        ]
    },
    {
        "topic": "nephrotic_syndrome",
        "doc_id": "DOC-PMC-RENAL-0008",
        "auth": True,
        "queries": [
            ("clinical_reasoning", ["oedema", "hypoalbuminaemia", "oncotic"], "What is the physiological mechanism of oedema formation in nephrotic syndrome according to the underfill and overfill theories?"),
            ("investigation", ["biopsy", "indications", "steroid resistant"], "What are the primary clinical indications for performing a renal biopsy in suspected nephrotic syndrome?"),
            ("mechanism", ["hypercoagulability", "antithrombin", "thrombosis"], "Why are patients with severe nephrotic syndrome at increased risk of deep vein thrombosis and renal vein thrombosis?"),
            ("comparison", ["minimal change", "FSGS", "electron microscopy"], "How do minimal change disease and focal segmental glomerulosclerosis differ on renal biopsy and response to corticosteroids?"),
        ]
    },
    {
        "topic": "hyperkalaemia_patho",
        "doc_id": "DOC-PMC-RENAL-0009",
        "auth": False,
        "queries": [
            ("clinical_reasoning", ["ECG", "peaked T", "conduction"], "What sequence of electrocardiographic changes occurs as serum potassium concentrations rise above 6.5 mmol/L?"),
            ("mechanism", ["insulin", "Na+/K+-ATPase", "cellular"], "How does insulin promote cellular uptake of potassium in acute hyperkalaemia?"),
            ("physiology", ["acidosis", "transcellular", "exchange"], "How does acute metabolic acidosis cause transcellular potassium shift into the extracellular fluid?"),
            ("comparison", ["tissue breakdown", "pseudohyperkalaemia", "haemolysis"], "What is the difference between pseudohyperkalaemia caused by in vitro haemolysis and genuine hyperkalaemia?"),
        ]
    },
    {
        "topic": "hyperkalaemia_management",
        "doc_id": "DOC-PMC-RENAL-0010",
        "auth": True,
        "queries": [
            ("clinical_reasoning", ["calcium gluconate", "membrane", "stabilisation"], "What is the physiological rationale for administering intravenous calcium gluconate in severe hyperkalaemia?"),
            ("mechanism", ["salbutamol", "beta-2", "intracellular"], "How do nebulised beta-2 adrenergic agonists promote intracellular potassium shifting?"),
            ("investigation", ["monitoring", "potassium", "recurrence"], "Why must serum potassium be remeasured 2 to 4 hours after insulin and glucose administration?"),
            ("comparison", ["patiromer", "zirconium", "onset"], "How do newer potassium binders patiromer and sodium zirconium cyclosilicate compare in onset and mechanism?"),
        ]
    },
    {
        "topic": "uti_pathology",
        "doc_id": "DOC-PMC-RENAL-0011",
        "auth": False,
        "queries": [
            ("physiology", ["urothelium", "umbrella cells", "adherence"], "How do uropathogenic Escherichia coli adhere to and invade superficial bladder umbrella cells?"),
            ("clinical_reasoning", ["biofilm", "catheter", "recurrent"], "Why do catheter-associated urinary tract infections frequently become chronic and resistant to standard antibiotics?"),
            ("investigation", ["dipstick", "nitrite", "leukocyte esterase"], "What does the combination of positive leukocyte esterase and nitrite on urine dipstick indicate?"),
            ("comparison", ["cystitis", "pyelonephritis", "systemic symptoms"], "What clinical features distinguish upper urinary tract infection (pyelonephritis) from lower tract cystitis?"),
        ]
    },
    {
        "topic": "renal_stones",
        "doc_id": "DOC-PMC-RENAL-0012",
        "auth": True,
        "queries": [
            ("clinical_reasoning", ["tamsulosin", "alpha-blocker", "passage"], "What is the role of medical expulsive therapy with alpha-1 blockers for distal ureteric stones?"),
            ("mechanism", ["hypocitraturia", "calcium", "crystallisation"], "How does urinary citrate act as an endogenous inhibitor of calcium stone formation?"),
            ("investigation", ["stone analysis", "24-hour urine", "prevention"], "Which metabolic abnormalities should be evaluated with 24-hour urine collection in recurrent stone formers?"),
            ("comparison", ["calcium oxalate", "uric acid", "radiopacity"], "How do calcium oxalate stones differ from uric acid stones on plain abdominal radiography and CT?"),
        ]
    },
    {
        "topic": "stones_uti_synergy",
        "doc_id": "DOC-PMC-RENAL-0013",
        "auth": False,
        "queries": [
            ("mechanism", ["urease", "Proteus", "struvite"], "How does bacterial urease production by Proteus mirabilis lead to magnesium ammonium phosphate (struvite) stone formation?"),
            ("clinical_reasoning", ["obstructing stone", "infection", "emergency"], "Why is an infected, obstructed kidney a medical and surgical emergency requiring immediate decompression?"),
            ("investigation", ["urine culture", "pH", "alkaline"], "Why does persistent alkaline urine (pH > 7.5) raise suspicion for infection stones?"),
            ("comparison", ["nephrostomy", "stent", "decompression"], "What are the relative advantages of percutaneous nephrostomy versus retrograde ureteric stenting in acute septic obstruction?"),
        ]
    },
    {
        "topic": "hydronephrosis",
        "doc_id": "DOC-PMC-RENAL-0014",
        "auth": False,
        "queries": [
            ("investigation", ["ultrasound", "pelvicalyceal", "dilatation"], "How does renal ultrasonography detect and grade pelvicalyceal dilatation in suspected hydronephrosis?"),
            ("clinical_reasoning", ["false negative", "dehydration", "retroperitoneal fibrosis"], "In what clinical situations can significant urinary obstruction present with minimal or absent pelvicalyceal dilatation?"),
            ("physiology", ["intrapelvic pressure", "atrophy", "tubular"], "What pathological changes occur in the renal parenchyma after prolonged high intrapelvic pressure?"),
            ("comparison", ["acute obstruction", "chronic hydronephrosis", "parenchymal thickness"], "How does renal cortical thickness on ultrasound help differentiate acute obstruction from chronic irreversible hydronephrosis?"),
        ]
    },
    {
        "topic": "rhabdomyolysis_rrt",
        "doc_id": "DOC-PMC-RENAL-0015",
        "auth": False,
        "queries": [
            ("mechanism", ["myoglobin", "tubular obstruction", "nephrotoxicity"], "How does myoglobin cause renal tubular damage and vasoconstriction in rhabdomyolysis?"),
            ("investigation", ["creatine kinase", "urine dipstick", "haem"], "Why does urine dipstick show a positive result for blood in the absence of red blood cells on microscopy in rhabdomyolysis?"),
            ("clinical_reasoning", ["intravenous fluids", "bicarbonate", "alkalinisation"], "What is the rationale and monitoring protocol for aggressive volume resuscitation in acute rhabdomyolysis?"),
            ("definition", ["indications", "RRT", "refractory"], "What are the absolute emergency indications for initiating renal replacement therapy in acute kidney injury?"),
        ]
    },
    {
        "topic": "gfr_measurement",
        "doc_id": "DOC-PMC-RENAL-0016",
        "auth": False,
        "queries": [
            ("comparison", ["cystatin C", "creatinine", "muscle mass"], "Why is serum cystatin C less dependent on muscle mass and diet than serum creatinine?"),
            ("physiology", ["inulin", "gold standard", "filtration"], "Why is inulin clearance considered the ideal physiological gold standard for determining true GFR?"),
            ("clinical_reasoning", ["unstable creatinine", "kinetic eGFR", "ICU"], "Why do steady-state GFR estimating equations fail during rapidly evolving acute kidney injury in the ICU?"),
            ("investigation", ["creatinine clearance", "overestimation", "tubular secretion"], "Why does creatinine clearance systematically overestimate true GFR, especially at low filtration rates?"),
        ]
    },
    {
        "topic": "glucose_handling",
        "doc_id": "DOC-PMC-RENAL-0019",
        "auth": False,
        "queries": [
            ("mechanism", ["SGLT2", "SGLT1", "proximal tubule"], "What percentage of filtered glucose is reabsorbed by SGLT2 versus SGLT1 along the proximal tubule?"),
            ("physiology", ["renal threshold", "glycosuria", "transport maximum"], "What is the normal renal threshold for glucose, and what happens when plasma glucose exceeds transport maximum?"),
            ("clinical_reasoning", ["SGLT2 inhibitors", "osmotic diuresis", "euglycaemic DKA"], "Why can SGLT2 inhibitors cause euglycaemic diabetic ketoacidosis despite lowering blood glucose?"),
            ("comparison", ["apical", "basolateral", "GLUT2"], "How is apical sodium-glucose cotransport coupled to basolateral facilitated glucose exit via GLUT2?"),
        ]
    },
    {
        "topic": "tubular_signaling",
        "doc_id": "DOC-PMC-RENAL-0020",
        "auth": False,
        "queries": [
            ("mechanism", ["SGK1", "ENaC", "phosphorylation"], "How does serum- and glucocorticoid-regulated kinase 1 (SGK1) increase apical ENaC abundance in principal cells?"),
            ("physiology", ["Akt", "insulin", "sodium reabsorption"], "What role does the PI3K/Akt pathway play in mediating insulin-stimulated tubular sodium reabsorption?"),
            ("clinical_reasoning", ["Liddle syndrome", "ENaC", "hypertension"], "Why does a gain-of-function mutation in ENaC lead to pseudohyperaldosteronism with low renin and low aldosterone?"),
            ("comparison", ["aldosterone", "insulin", "distal nephron"], "How do aldosterone and insulin collaborate to regulate sodium reabsorption in the distal convoluted tubule and collecting duct?"),
        ]
    },
    {
        "topic": "acid_base_sensing",
        "doc_id": "DOC-PMC-RENAL-0021",
        "auth": False,
        "queries": [
            ("mechanism", ["AE4", "bicarbonate sensor", "intercalated"], "How does the anion exchanger AE4 contribute to bicarbonate sensing in beta-intercalated cells?"),
            ("physiology", ["pendrin", "chloride-bicarbonate", "metabolic alkalosis"], "What is the function of apical pendrin in correcting systemic metabolic alkalosis?"),
            ("clinical_reasoning", ["type 2 RTA", "proximal", "Fanconi"], "What clinical features characterize proximal (type 2) renal tubular acidosis, and how does it relate to generalized Fanconi syndrome?"),
            ("investigation", ["urine anion gap", "ammonium", "distal RTA"], "How does a positive urine anion gap assist in the diagnosis of distal (type 1) renal tubular acidosis?"),
        ]
    },
    {
        "topic": "countercurrent_mechanism",
        "doc_id": "DOC-PMC-RENAL-0023",
        "auth": False,
        "queries": [
            ("mechanism", ["NKCC2", "thick ascending limb", "hypertonicity"], "How does active NaCl reabsorption by the apical NKCC2 cotransporter in the thick ascending limb drive medullary hypertonicity?"),
            ("physiology", ["urea recycling", "inner medulla", "osmocenter"], "What role does urea recycling via UT-A1 and UT-A3 transporters play in generating the inner medullary osmotic gradient?"),
            ("clinical_reasoning", ["loop diuretics", "furosemide", "urine concentration"], "Why do loop diuretics abolish the kidney's ability to excrete either a concentrated or a maximally dilute urine?"),
            ("comparison", ["descending limb", "thick ascending limb", "water permeability"], "How do the water permeability and active transport properties of the thin descending limb differ from the thick ascending limb?"),
        ]
    },
    {
        "topic": "renal_endocrine",
        "doc_id": "DOC-PMC-RENAL-0024",
        "auth": False,
        "queries": [
            ("mechanism", ["erythropoietin", "hypoxia", "interstitial cells"], "How does renal hypoxia stimulate erythropoietin production in peritubular interstitial cells?"),
            ("physiology", ["1-alpha-hydroxylase", "calcitriol", "vitamin D"], "What is the role of proximal tubular 1-alpha-hydroxylase in activating 25-hydroxyvitamin D into calcitriol?"),
            ("clinical_reasoning", ["normocytic anemia", "EPO deficiency", "CKD"], "Why do patients with progressive chronic kidney disease characteristically develop normochromic normocytic anemia?"),
            ("comparison", ["endocrine", "exocrine", "kidney functions"], "What are the distinct systemic functions of renal-derived erythropoietin, calcitriol, and renin?"),
        ]
    },
    {
        "topic": "haematuria",
        "doc_id": "DOC-PMC-RENAL-0025",
        "auth": True,
        "queries": [
            ("clinical_reasoning", ["dysmorphic RBCs", "casts", "glomerular"], "How do dysmorphic red blood cells and red cell casts distinguish glomerular from lower urinary tract haematuria?"),
            ("definition", ["microscopic haematuria", "RBC per HPF", "criteria"], "What is the standard clinical threshold definition for significant microscopic haematuria on automated microscopy?"),
            ("investigation", ["cystoscopy", "CT urogram", "malignancy workup"], "Which high-risk patients with unexplained visible haematuria require urgent dual investigation with flexible cystoscopy and CT urogram?"),
            ("comparison", ["glomerular", "urological", "haematuria"], "What key clinical and urinalysis findings differentiate glomerular haematuria from urological tract bleeding?"),
        ]
    },
]

OUTSIDE = [
    "What are the diagnostic electrocardiographic criteria for acute ST-elevation myocardial infarction?",
    "How does left ventricular ejection fraction guide medical therapy in heart failure with reduced ejection fraction?",
    "What are the key clinical differences between Crohn's disease and ulcerative colitis on colonoscopy?",
    "How do proton pump inhibitors decrease gastric acid secretion in gastroesophageal reflux disease?",
    "What are the diagnostic criteria for diabetic ketoacidosis including blood glucose, ketones, and arterial pH?",
    "How does thyroxine replacement therapy normalize elevated thyroid-stimulating hormone in primary hypothyroidism?",
    "What are the clinical hallmarks and emergency treatment protocol for status epilepticus?",
    "How does secondary hyperaldosteronism differ from primary hyperaldosteronism (Conn syndrome) in plasma renin activity?",
    "What are the primary radiological features of tension pneumothorax on chest radiograph?",
    "How does unfractionated heparin inhibit the coagulation cascade compared to low molecular weight heparin?",
    "What are the indications and target INR ranges for warfarin in mechanical heart valves?",
    "How does insulin aspart differ from insulin glargine in onset and duration of pharmacokinetic action?",
]

def find_evidence_chunks(doc_id: str, anchors: list[str]) -> tuple[list[str], list[str], str]:
    pool = [c for c in chunks_map.values() if c["document_id"] == doc_id and c.get("retrieval_role") != "EXCLUDED_FROM_SEARCH"]
    if not pool:
        pool = [c for c in chunks_map.values() if c["document_id"] == doc_id]
        
    def score(item):
        t = item["text"].lower()
        return (sum(1 for a in anchors if a.lower() in t), len(item["text"]))
        
    ranked = sorted(pool, key=score, reverse=True)
    if not ranked:
        return [], [], ""
    best = ranked[0]
    p_id = best.get("parent_section_id") or f"{doc_id}-P{int(best.get('source_block_index', 1)):04d}"
    matched = [a for a in anchors if a.lower() in best["text"].lower()]
    return [p_id], matched, best["text"]


queries = []
n_concepts = len(CONCEPTS)

for idx, c in enumerate(CONCEPTS, 1):
    topic = c["topic"]
    doc_id = c["doc_id"]
    auth = c["auth"]
    
    for qidx, (qtype, anchors, qtext) in enumerate(c["queries"], 1):
        parents, matched, quote = find_evidence_chunks(doc_id, anchors)
        is_answerable = len(matched) >= 2
        
        evidence_spans = []
        if is_answerable and quote:
            evidence_spans.append({
                "document_id": doc_id,
                "parent_section_id": parents[0] if parents else None,
                "evidence_text": quote[:500],
                "matched_anchors": matched,
                "verification_method": "source_two_anchor_exact_text",
            })
            
        qid = f"RENAL-V2-HO-FINAL-{idx:02d}-{qidx}"
        claim = f"Factual medical answer regarding {topic}: {qtext}"
        
        queries.append({
            "query_id": qid,
            "query": qtext,
            "topic": topic,
            "question_type": qtype,
            "learning_objective": f"Undergraduate renal medicine: understand {topic} ({qtype})",
            "medical_claim": claim,
            "evaluation_label": "SUPPORTED" if is_answerable else "IN_DOMAIN_CORPUS_COVERAGE_GAP",
            "answerable": is_answerable,
            "gold_document_ids": [doc_id] if is_answerable else [],
            "gold_parent_section_ids": parents if is_answerable else [],
            "evidence_spans": evidence_spans,
            "primary_evidence_quote": quote if is_answerable else None,
            "gold_verification_anchors": anchors,
            "gold_minimum_anchor_hits": 2,
            "authority_sensitive": auth,
            "source_mapping_rule": (
                "A chunk is relevant if it contains any verified evidence span, "
                "or belongs to gold_parent_section_ids and contains at least 2 verification anchors."
            ),
        })

# Add 12 unsupported queries
for uidx, uq in enumerate(OUTSIDE, 1):
    qid = f"RENAL-V2-HO-FINAL-U-{uidx:02d}"
    queries.append({
        "query_id": qid,
        "query": uq,
        "topic": "out_of_domain",
        "question_type": "unsupported",
        "learning_objective": "Recognize out-of-domain medical queries where safe abstention is required",
        "medical_claim": None,
        "evaluation_label": "OUT_OF_DOMAIN_UNSUPPORTED",
        "answerable": False,
        "gold_document_ids": [],
        "gold_parent_section_ids": [],
        "evidence_spans": [],
        "primary_evidence_quote": None,
        "gold_verification_anchors": [],
        "gold_minimum_anchor_hits": 2,
        "authority_sensitive": False,
        "source_mapping_rule": "No passage is relevant (unsupported / out-of-domain query)",
    })

payload = {
    "dataset_id": "RENAL-HELDOUT-V2-FINAL",
    "status": "FINAL_FROZEN_UNSEEN",
    "n_total_queries": len(queries),
    "n_answerable": sum(1 for q in queries if q["answerable"]),
    "n_unsupported": sum(1 for q in queries if not q["answerable"]),
    "n_concepts": n_concepts,
    "queries": queries,
}

OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
sha = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()
OUT_PATH.with_suffix(".json.sha256").write_text(f"{sha}  {OUT_PATH.name}\n", encoding="utf-8")

print(f"Generated Final Heldout Dataset:")
print(f"  Path: {OUT_PATH.name}")
print(f"  Status: FINAL_FROZEN_UNSEEN")
print(f"  Total queries: {len(queries)}")
print(f"  Answerable: {payload['n_answerable']}")
print(f"  Unsupported: {payload['n_unsupported']}")
print(f"  SHA256: {sha}")
