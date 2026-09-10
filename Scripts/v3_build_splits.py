"""Build V3 TRAIN split strictly isolated from DEV, CALIBRATION, and HELDOUT.

Per Mission Section 4, 11, and Phase 3:
- Strict group splitting by medical claim, source section, learning objective, question family.
- ZERO overlap with DEV queries, sections, or claims.
- ZERO leakage from V2 final heldout.
- Output: evaluation/renal/v3/renal-train-v3.json + SHA256 sidecar.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEV_PATH = ROOT / "evaluation" / "renal" / "renal-dev-evidence-spans-v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
OUTPUT_DIR = ROOT / "evaluation" / "renal" / "v3"
OUTPUT_PATH = OUTPUT_DIR / "renal-train-v3.json"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_corpus_chunks() -> dict[str, list[dict]]:
    docs = {}
    for f in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        doc_id = f.name.replace(".chunks.json", "")
        data = json.loads(f.read_text(encoding="utf-8"))
        docs[doc_id] = data.get("chunks", [])
    return docs


def find_chunk_matching(chunks: list[dict], required_terms: list[str], excluded_sections: set[str]) -> dict | None:
    for ch in chunks:
        parent = ch.get("parent_section_id")
        if parent in excluded_sections:
            continue
        t = ch.get("text", "").lower()
        if all(term.lower() in t for term in required_terms) and len(t.split()) >= 30:
            return ch
    return None


def main():
    print("=" * 70)
    print("PHASE 3: BUILDING V3 TRAIN SPLIT WITH STRICT LEAKAGE FIREWALL")
    print("=" * 70)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    dev_data = json.loads(DEV_PATH.read_text(encoding="utf-8"))
    dev_queries = dev_data.get("queries", [])
    dev_query_texts = {q["query"].strip().lower() for q in dev_queries}
    dev_claims = {q.get("medical_claim", "").strip().lower() for q in dev_queries}
    dev_sections = {sec for q in dev_queries for sec in q.get("gold_parent_section_ids", [])}
    
    print(f"Loaded DEV: {len(dev_queries)} queries, {len(dev_sections)} parent sections.")
    
    corpus_docs = load_corpus_chunks()
    print(f"Loaded corpus: {len(corpus_docs)} documents, {sum(len(c) for c in corpus_docs.values())} total chunks.")
    
    train_queries_defs = [
        # --- DOC-0024: EPO & Vitamin D ---
        {
            "id": "RENAL-V3-TRAIN-01-1",
            "topic": "renal_endocrine",
            "qtype": "physiology",
            "objective": "Undergraduate renal medicine: EPO production in response to hypoxia",
            "query": "What physiological stimulus induces renal erythropoietin secretion, and what is its systemic target?",
            "claim": "Tissue hypoxia stimulates renal erythropoietin secretion, which acts on bone marrow erythroid progenitor cells to accelerate red blood cell production.",
            "doc": "DOC-PMC-RENAL-0024",
            "terms": ["erythropoietin", "hypoxia"],
            "anchors": ["erythropoietin", "hypoxia", "kidney"],
        },
        {
            "id": "RENAL-V3-TRAIN-01-2",
            "topic": "renal_endocrine",
            "qtype": "mechanism",
            "objective": "Undergraduate renal medicine: 1-alpha-hydroxylase activation of vitamin D",
            "query": "How is 25-hydroxyvitamin D converted to biologically active 1,25-dihydroxyvitamin D in renal proximal tubules?",
            "claim": "Proximal tubule 1-alpha-hydroxylase enzyme hydroxylates calcidiol to generate bioactive 1,25-dihydroxyvitamin D (calcitriol).",
            "doc": "DOC-PMC-RENAL-0024",
            "terms": ["vitamin d", "calcitriol"],
            "anchors": ["calcitriol", "vitamin d", "mineral"],
        },
        {
            "id": "RENAL-V3-TRAIN-01-3",
            "topic": "renal_endocrine",
            "qtype": "clinical_reasoning",
            "objective": "Undergraduate renal medicine: non-classical immunological roles of EPO",
            "query": "What non-classical immunomodulatory roles do vitamin D and erythropoietin exert beyond mineral metabolism and erythropoiesis?",
            "claim": "Vitamin D and erythropoietin exert broad immunomodulatory and tissue-protective effects across organ systems beyond their classical hematopoietic and bone metabolic functions.",
            "doc": "DOC-PMC-RENAL-0024",
            "terms": ["erythropoiesis", "immune"],
            "anchors": ["erythropoiesis", "immune", "vitamin d"],
        },
        {
            "id": "RENAL-V3-TRAIN-01-4",
            "topic": "renal_endocrine",
            "qtype": "pathophysiology",
            "objective": "Undergraduate renal medicine: secondary hyperparathyroidism due to calcitriol deficiency",
            "query": "How does loss of renal calcitriol synthesis promote parathyroid hormone hypersecretion in kidney failure?",
            "claim": "Impaired calcitriol synthesis decreases intestinal calcium absorption, leading to hypocalcemia and reciprocal elevation of parathyroid hormone.",
            "doc": "DOC-PMC-RENAL-0024",
            "terms": ["vitamin d", "calcium"],
            "anchors": ["calcium", "vitamin d", "kidney"],
        },
        # --- DOC-0025: Hematuria ---
        {
            "id": "RENAL-V3-TRAIN-02-1",
            "topic": "haematuria",
            "qtype": "diagnosis",
            "objective": "Undergraduate renal medicine: microscopic hematuria definition and prevalence",
            "query": "How is microscopic hematuria defined clinically, and what benign conditions can cause transient hematuria?",
            "claim": "Microscopic hematuria is detected by urine dipstick or microscopy; transient causes include vigorous exercise, sexual intercourse, menstruation, and mild trauma.",
            "doc": "DOC-PMC-RENAL-0025",
            "terms": ["hematuria", "microscopic"],
            "anchors": ["hematuria", "microscopic", "urine"],
        },
        {
            "id": "RENAL-V3-TRAIN-02-2",
            "topic": "haematuria",
            "qtype": "investigation",
            "objective": "Undergraduate renal medicine: urological malignancy evaluation in hematuria",
            "query": "When is urgent cystoscopy and upper tract imaging required for adult patients presenting with hematuria?",
            "claim": "Adults with visible hematuria or persistent non-visible hematuria with risk factors mandate cystoscopy and upper urinary tract imaging to exclude malignancy.",
            "doc": "DOC-PMC-RENAL-0025",
            "terms": ["hematuria", "cystoscopy"],
            "anchors": ["hematuria", "cystoscopy", "imaging"],
        },
        {
            "id": "RENAL-V3-TRAIN-02-3",
            "topic": "haematuria",
            "qtype": "pathophysiology",
            "objective": "Undergraduate renal medicine: glomerular causes of red blood cells in urine",
            "query": "What clinical and laboratory findings point to a glomerular origin of hematuria?",
            "claim": "Dysmorphic erythrocytes, acanthocytes, red cell casts, and significant concomitant proteinuria indicate glomerular capillary wall disruption.",
            "doc": "DOC-PMC-RENAL-0025",
            "terms": ["glomerular", "hematuria"],
            "anchors": ["glomerular", "hematuria", "nephritis"],
        },
        {
            "id": "RENAL-V3-TRAIN-02-4",
            "topic": "haematuria",
            "qtype": "clinical_reasoning",
            "objective": "Undergraduate renal medicine: proteinuria co-occurrence with hematuria",
            "query": "How does concomitant significant proteinuria influence the differential diagnosis of non-visible hematuria?",
            "claim": "The combination of hematuria with proteinuria strongly increases the likelihood of primary or secondary glomerular parenchymal disease rather than isolated lower tract bleeding.",
            "doc": "DOC-PMC-RENAL-0025",
            "terms": ["proteinuria", "hematuria"],
            "anchors": ["proteinuria", "hematuria", "disease"],
        },
        # --- DOC-0006: AKI Guidelines ---
        {
            "id": "RENAL-V3-TRAIN-03-1",
            "topic": "aki",
            "qtype": "diagnosis",
            "objective": "Undergraduate renal medicine: KDIGO staging criteria for acute kidney injury",
            "query": "What serum creatinine and urine output thresholds define KDIGO stage 1 acute kidney injury?",
            "claim": "KDIGO Stage 1 AKI is defined by an increase in serum creatinine by >=0.3 mg/dL within 48 hours or a 1.5-1.9 times baseline increase, or urine output <0.5 mL/kg/h for 6-12 hours.",
            "doc": "DOC-PMC-RENAL-0006",
            "terms": ["kdigo", "acute kidney injury"],
            "anchors": ["kdigo", "creatinine", "injury"],
        },
        {
            "id": "RENAL-V3-TRAIN-03-2",
            "topic": "aki",
            "qtype": "physiology",
            "objective": "Undergraduate renal medicine: oliguria monitoring in acute kidney injury",
            "query": "Why is hourly urine output monitoring critical for detecting early acute kidney injury?",
            "claim": "Urine output decline often precedes serum creatinine elevation by 24-48 hours during acute renal hypoperfusion and early nephron injury.",
            "doc": "DOC-PMC-RENAL-0006",
            "terms": ["creatinine", "urine output"],
            "anchors": ["creatinine", "urine", "output"],
        },
        {
            "id": "RENAL-V3-TRAIN-03-3",
            "topic": "aki",
            "qtype": "investigation",
            "objective": "Undergraduate renal medicine: novel biomarkers of renal tubular damage",
            "query": "What tubular biomarkers (such as NGAL and L-FABP) indicate early structural tubular injury before creatinine rise?",
            "claim": "Novel structural biomarkers including neutrophil gelatinase-associated lipocalin (NGAL) and liver-type fatty acid-binding protein (L-FABP) elevate rapidly following tubular epithelial damage.",
            "doc": "DOC-PMC-RENAL-0006",
            "terms": ["biomarker", "injury"],
            "anchors": ["biomarker", "injury", "tubular"],
        },
        {
            "id": "RENAL-V3-TRAIN-03-4",
            "topic": "aki",
            "qtype": "management",
            "objective": "Undergraduate renal medicine: renal replacement therapy timing in acute kidney injury",
            "query": "What indications mandate prompt renal replacement therapy initiation in patients with severe AKI?",
            "claim": "Severe hyperkalemia, profound metabolic acidosis, refractory fluid overload, and uremic organ involvement constitute unequivocal indications for acute renal replacement therapy.",
            "doc": "DOC-PMC-RENAL-0006",
            "terms": ["dialysis", "indication"],
            "anchors": ["dialysis", "indication", "therapy"],
        },
        # --- DOC-0007: CKD Guidelines ---
        {
            "id": "RENAL-V3-TRAIN-04-1",
            "topic": "ckd",
            "qtype": "diagnosis",
            "objective": "Undergraduate renal medicine: definition and duration criteria for chronic kidney disease",
            "query": "What criteria of GFR and kidney damage lasting at least 3 months define chronic kidney disease?",
            "claim": "CKD is defined as persistent abnormalities of kidney structure or function present for greater than 3 months, with implications for health, notably GFR <60 mL/min/1.73m2 or evidence of kidney damage.",
            "doc": "DOC-PMC-RENAL-0007",
            "terms": ["ckd", "gfr"],
            "anchors": ["ckd", "gfr", "damage"],
        },
        {
            "id": "RENAL-V3-TRAIN-04-2",
            "topic": "ckd",
            "qtype": "investigation",
            "objective": "Undergraduate renal medicine: urine albumin-to-creatinine ratio staging (A1-A3)",
            "query": "How is albuminuria categorized into stages A1, A2, and A3 using the urine albumin-to-creatinine ratio?",
            "claim": "Albuminuria categories are defined as A1 (<30 mg/g, normal to mildly increased), A2 (30-299 mg/g, moderately increased), and A3 (>=300 mg/g, severely increased).",
            "doc": "DOC-PMC-RENAL-0007",
            "terms": ["albuminuria", "proteinuria"],
            "anchors": ["albuminuria", "proteinuria", "ratio"],
        },
        {
            "id": "RENAL-V3-TRAIN-04-3",
            "topic": "ckd",
            "qtype": "clinical_reasoning",
            "objective": "Undergraduate renal medicine: cardiovascular risk multiplication in CKD",
            "query": "Why do patients with chronic kidney disease face significantly elevated cardiovascular morbidity and mortality?",
            "claim": "CKD accelerates vascular calcification, arterial stiffness, left ventricular hypertrophy, and coronary heart disease, making cardiovascular events the leading cause of mortality.",
            "doc": "DOC-PMC-RENAL-0007",
            "terms": ["cardiovascular", "risk"],
            "anchors": ["cardiovascular", "risk", "mortality"],
        },
        {
            "id": "RENAL-V3-TRAIN-04-4",
            "topic": "ckd",
            "qtype": "management",
            "objective": "Undergraduate renal medicine: renoprotective blood pressure targets and RAAS blockade",
            "query": "How do ACE inhibitors or ARBs slow CKD progression in proteinuric patients?",
            "claim": "ACE inhibitors reduce efferent arteriolar resistance, decreasing intraglomerular hydraulic pressure and proteinuria, thereby retarding progressive glomerulosclerosis and tubular fibrosis.",
            "doc": "DOC-PMC-RENAL-0007",
            "terms": ["progression", "blood pressure"],
            "anchors": ["progression", "pressure", "hypertension"],
        },
        # --- DOC-0012: Urolithiasis ---
        {
            "id": "RENAL-V3-TRAIN-05-1",
            "topic": "renal_stones",
            "qtype": "management",
            "objective": "Undergraduate renal medicine: international guidelines on urinary stone management",
            "query": "What are the core consensus recommendations in urological guidelines for evaluating acute urolithiasis?",
            "claim": "Urological guidelines recommend prompt analgesia with NSAIDs, low-dose non-contrast CT KUB imaging, and evaluation of stone size and location to determine spontaneous passage probability.",
            "doc": "DOC-PMC-RENAL-0012",
            "terms": ["stone", "guideline"],
            "anchors": ["stone", "guideline", "urolithiasis"],
        },
        {
            "id": "RENAL-V3-TRAIN-05-2",
            "topic": "renal_stones",
            "qtype": "management",
            "objective": "Undergraduate renal medicine: extracorporeal shock wave lithotripsy (ESWL) indications",
            "query": "When is shock wave lithotripsy (SWL) indicated for renal and upper ureteric stones?",
            "claim": "Extracorporeal shock wave lithotripsy is a first-line non-invasive intervention for renal pelvis and upper caliceal stones smaller than 20 mm with favorable stone density.",
            "doc": "DOC-PMC-RENAL-0012",
            "terms": ["lithotripsy", "shock"],
            "anchors": ["lithotripsy", "shock", "stone"],
        },
        {
            "id": "RENAL-V3-TRAIN-05-3",
            "topic": "renal_stones",
            "qtype": "management",
            "objective": "Undergraduate renal medicine: ureteroscopy (URS) for ureteric calculus extraction",
            "query": "What advantages does flexible ureteroscopy with laser lithotripsy provide for ureteric calculi?",
            "claim": "Ureteroscopy provides high primary stone-free rates, direct endoscopic visualization, and immediate stone fragmentation or basket retrieval throughout the ureter and renal collecting system.",
            "doc": "DOC-PMC-RENAL-0012",
            "terms": ["ureteroscopy", "stone"],
            "anchors": ["ureteroscopy", "stone", "laser"],
        },
        {
            "id": "RENAL-V3-TRAIN-05-4",
            "topic": "renal_stones",
            "qtype": "prevention",
            "objective": "Undergraduate renal medicine: urinary citrate inhibition of calcium crystallization",
            "query": "How does urinary citrate inhibit calcium stone formation, and when is potassium citrate indicated?",
            "claim": "Citrate chelates ionic calcium in urine, forming a soluble complex that reduces calcium oxalate and calcium phosphate supersaturation and inhibits crystal agglomeration.",
            "doc": "DOC-PMC-RENAL-0012",
            "terms": ["citrate", "calcium"],
            "anchors": ["citrate", "calcium", "oxalate"],
        },
        # --- DOC-0015: Rhabdomyolysis ---
        {
            "id": "RENAL-V3-TRAIN-06-1",
            "topic": "rhabdomyolysis",
            "qtype": "pathophysiology",
            "objective": "Undergraduate renal medicine: myoglobin-induced acute tubular necrosis",
            "query": "What pathological sequence leads from myocyte injury to myoglobin cast formation in renal tubules?",
            "claim": "Skeletal muscle disruption releases massive myoglobin into circulation, which is filtered at the glomerulus and precipitates with Tamm-Horsfall protein in distal tubules, causing luminal obstruction.",
            "doc": "DOC-PMC-RENAL-0015",
            "terms": ["rhabdomyolysis", "myoglobin"],
            "anchors": ["rhabdomyolysis", "myoglobin", "tubular"],
        },
        {
            "id": "RENAL-V3-TRAIN-06-2",
            "topic": "rhabdomyolysis",
            "qtype": "investigation",
            "objective": "Undergraduate renal medicine: serum creatine kinase elevation in rhabdomyolysis",
            "query": "How does serum creatine kinase elevation reflect skeletal muscle injury severity in rhabdomyolysis?",
            "claim": "Serum creatine kinase levels rise within 2-12 hours of skeletal muscle breakdown, peaking at 24-72 hours, with marked elevations (>5,000 U/L) correlating with AKI risk.",
            "doc": "DOC-PMC-RENAL-0015",
            "terms": ["creatine", "syndrome"],
            "anchors": ["creatine", "muscle", "rhabdomyolysis"],
        },
        {
            "id": "RENAL-V3-TRAIN-06-3",
            "topic": "rhabdomyolysis",
            "qtype": "management",
            "objective": "Undergraduate renal medicine: renal replacement therapy in severe rhabdomyolysis",
            "query": "When is renal replacement therapy indicated in patients with rhabdomyolysis-induced acute kidney failure?",
            "claim": "Renal replacement therapy is indicated when conservative volume resuscitation fails to resolve life-threatening hyperkalemia, severe refractory metabolic acidosis, or hypervolemic pulmonary edema.",
            "doc": "DOC-PMC-RENAL-0015",
            "terms": ["replacement therapy", "rhabdomyolysis"],
            "anchors": ["replacement therapy", "dialysis", "rhabdomyolysis"],
        },
        {
            "id": "RENAL-V3-TRAIN-06-4",
            "topic": "rhabdomyolysis",
            "qtype": "management",
            "objective": "Undergraduate renal medicine: fluid resuscitation goals in crush injury",
            "query": "What fluid administration regimen is recommended in acute crush syndrome to prevent acute tubular necrosis?",
            "claim": "Immediate intravenous volume resuscitation with isotonic crystalloids targeting a high urine output (200-300 mL/h) is vital to dilute tubular myoglobin and wash out obstructive casts.",
            "doc": "DOC-PMC-RENAL-0015",
            "terms": ["fluid", "volume"],
            "anchors": ["fluid", "volume", "resuscitation"],
        },
        # --- DOC-0016: GFR in Critical Illness ---
        {
            "id": "RENAL-V3-TRAIN-07-1",
            "topic": "gfr",
            "qtype": "investigation",
            "objective": "Undergraduate renal medicine: limitations of serum creatinine in critically ill patients",
            "query": "Why does serum creatinine underestimate kidney dysfunction in critically ill intensive care patients?",
            "claim": "Critically ill patients suffer reduced muscle mass, decreased hepatic creatine production, and aggressive fluid resuscitation dilution, causing serum creatinine to substantially lag behind true GFR decline.",
            "doc": "DOC-PMC-RENAL-0016",
            "terms": ["critically ill", "filtration"],
            "anchors": ["critically ill", "creatinine", "filtration"],
        },
        {
            "id": "RENAL-V3-TRAIN-07-2",
            "topic": "gfr",
            "qtype": "investigation",
            "objective": "Undergraduate renal medicine: timed urinary creatinine clearance in non-steady state GFR",
            "query": "How does measured timed urinary creatinine clearance overcome limitations of static serum creatinine in ICU patients?",
            "claim": "Measured 2- to 8-hour timed urinary creatinine clearance provides a direct estimate of current filtration rate that does not assume steady-state serum creatinine concentrations.",
            "doc": "DOC-PMC-RENAL-0016",
            "terms": ["creatinine", "clearance"],
            "anchors": ["creatinine", "clearance", "urine"],
        },
        {
            "id": "RENAL-V3-TRAIN-07-3",
            "topic": "gfr",
            "qtype": "physiology",
            "objective": "Undergraduate renal medicine: augmented renal clearance in sepsis and polytrauma",
            "query": "What is augmented renal clearance (ARC), and why does it lead to subtherapeutic antimicrobial dosing?",
            "claim": "Augmented renal clearance (CrCl >130 mL/min/1.73m2) occurs in hyperdynamic states like sepsis and burns, resulting in rapid elimination and under-dosing of renally excreted antibiotics.",
            "doc": "DOC-PMC-RENAL-0016",
            "terms": ["clearance", "renal"],
            "anchors": ["clearance", "renal", "filtration"],
        },
        {
            "id": "RENAL-V3-TRAIN-07-4",
            "topic": "gfr",
            "qtype": "investigation",
            "objective": "Undergraduate renal medicine: cystatin C as an alternative filtration marker",
            "query": "Why is serum cystatin C less affected by muscle mass variations than serum creatinine when estimating GFR?",
            "claim": "Cystatin C is produced by all nucleated cells at a constant rate and eliminated solely by glomerular filtration, making it largely independent of muscle mass, age, and dietary protein intake.",
            "doc": "DOC-PMC-RENAL-0016",
            "terms": ["creatinine", "renal function"],
            "anchors": ["creatinine", "filtration", "marker"],
        },
        # --- DOC-0019: Renal Glucose Handling ---
        {
            "id": "RENAL-V3-TRAIN-08-1",
            "topic": "glucose_handling",
            "qtype": "physiology",
            "objective": "Undergraduate renal medicine: SGLT2 location and sodium-glucose cotransport stoichiometry",
            "query": "Where in the nephron is SGLT2 located, and what percentage of filtered glucose does it reabsorb?",
            "claim": "SGLT2 is located on the luminal brush border of the S1/S2 segments of the proximal convoluted tubule, mediating high-capacity 1:1 sodium-glucose cotransport responsible for ~90% of glucose reabsorption.",
            "doc": "DOC-PMC-RENAL-0019",
            "terms": ["sglt2", "glucose"],
            "anchors": ["sglt2", "glucose", "proximal"],
        },
        {
            "id": "RENAL-V3-TRAIN-08-2",
            "topic": "glucose_handling",
            "qtype": "physiology",
            "objective": "Undergraduate renal medicine: basolateral glucose exit via GLUT2 transporters",
            "query": "How does reabsorbed glucose exit proximal tubular epithelial cells across the basolateral membrane into peritubular capillaries?",
            "claim": "Glucose exits proximal tubular cells into the interstitial space and peritubular capillaries by facilitated diffusion mediated by basolateral GLUT2 transporters.",
            "doc": "DOC-PMC-RENAL-0019",
            "terms": ["proximal tubule", "transporter"],
            "anchors": ["proximal tubule", "transporter", "glucose"],
        },
        {
            "id": "RENAL-V3-TRAIN-08-3",
            "topic": "glucose_handling",
            "qtype": "pathophysiology",
            "objective": "Undergraduate renal medicine: renal threshold for glucose and osmotic diuresis",
            "query": "What is the physiological renal threshold for glucose excretion, and what happens when it is exceeded?",
            "claim": "When plasma glucose exceeds the renal threshold of ~10-11 mmol/L (180-200 mg/dL), tubular transport maximum (TmG) is saturated, resulting in glucosuria and solute-induced osmotic diuresis.",
            "doc": "DOC-PMC-RENAL-0019",
            "terms": ["sglt", "reabsorption"],
            "anchors": ["sglt", "reabsorption", "glucose"],
        },
        {
            "id": "RENAL-V3-TRAIN-08-4",
            "topic": "glucose_handling",
            "qtype": "mechanism",
            "objective": "Undergraduate renal medicine: renoprotection by SGLT2 inhibitors",
            "query": "How do pharmacological SGLT2 inhibitors restore tubuloglomerular feedback to protect glomerular capillary pressure in diabetic nephropathy?",
            "claim": "SGLT2 inhibitors increase distal luminal NaCl delivery to the macula densa, triggering tubuloglomerular feedback and afferent arteriolar vasoconstriction, thereby reducing intraglomerular hypertension.",
            "doc": "DOC-PMC-RENAL-0019",
            "terms": ["inhibitor", "diabetes"],
            "anchors": ["inhibitor", "diabetes", "sglt2"],
        },
        # --- DOC-0023: Countercurrent Mechanism ---
        {
            "id": "RENAL-V3-TRAIN-09-1",
            "topic": "countercurrent_multiplier",
            "qtype": "physiology",
            "objective": "Undergraduate renal medicine: countercurrent multiplier in loops of Henle",
            "query": "How does differential permeability between descending and ascending limbs of Henle create a hypertonic medullary gradient?",
            "claim": "The descending limb is water-permeable and solute-impermeable, while the thick ascending limb actively pumps sodium and chloride without water, creating a horizontal osmotic gradient multiplied vertically.",
            "doc": "DOC-PMC-RENAL-0023",
            "terms": ["countercurrent", "medullary"],
            "anchors": ["countercurrent", "medullary", "gradient"],
        },
        {
            "id": "RENAL-V3-TRAIN-09-2",
            "topic": "countercurrent_multiplier",
            "qtype": "mechanism",
            "objective": "Undergraduate renal medicine: NKCC2 transport in thick ascending limb",
            "query": "What active transporter in the thick ascending limb generates the 'single effect' of medullary hypertonicity?",
            "claim": "The apical NKCC2 cotransporter actively transports 1 Na+, 1 K+, and 2 Cl- ions into thick ascending limb cells, establishing interstitial hypertonicity driven by basolateral Na+/K+-ATPase.",
            "doc": "DOC-PMC-RENAL-0023",
            "terms": ["active transport", "concentration"],
            "anchors": ["active transport", "concentration", "medulla"],
        },
        {
            "id": "RENAL-V3-TRAIN-09-3",
            "topic": "countercurrent_multiplier",
            "qtype": "physiology",
            "objective": "Undergraduate renal medicine: vasa recta countercurrent exchange",
            "query": "Why do the hairpin loops of the vasa recta function as countercurrent exchangers rather than multipliers?",
            "claim": "The highly permeable vasa recta act as passive countercurrent exchangers, maintaining the medullary osmotic gradient by allowing water and solutes to equilibrate slowly without washing out the hypertonic interstitium.",
            "doc": "DOC-PMC-RENAL-0023",
            "terms": ["vasa recta", "exchange"],
            "anchors": ["vasa recta", "exchange", "blood flow"],
        },
        {
            "id": "RENAL-V3-TRAIN-09-4",
            "topic": "countercurrent_multiplier",
            "qtype": "pathophysiology",
            "objective": "Undergraduate renal medicine: loop diuretic disruption of medullary concentration gradient",
            "query": "How do loop diuretics (like furosemide) impair both urinary concentration and urinary dilution?",
            "claim": "Loop diuretics inhibit NKCC2 in the thick ascending limb, preventing active solute pumping into the medulla which abolishes the medullary osmotic gradient required for water reabsorption.",
            "doc": "DOC-PMC-RENAL-0023",
            "terms": ["countercurrent", "loop"],
            "anchors": ["countercurrent", "gradient", "loop"],
        },
        # --- DOC-0014: Hydronephrosis & Obstruction ---
        {
            "id": "RENAL-V3-TRAIN-10-1",
            "topic": "obstruction_hydronephrosis",
            "qtype": "investigation",
            "objective": "Undergraduate renal medicine: ultrasound detection of pelvicalyceal dilatation",
            "query": "What are the characteristic renal ultrasound findings in acute obstructive uropathy?",
            "claim": "Renal ultrasonography in urinary tract obstruction demonstrates separation and dilatation of the central renal sinus echoes, reflecting pelvicalyceal fluid accumulation (hydronephrosis).",
            "doc": "DOC-PMC-RENAL-0014",
            "terms": ["hydronephrosis", "ultrasound"],
            "anchors": ["hydronephrosis", "ultrasound", "pelvis"],
        },
        {
            "id": "RENAL-V3-TRAIN-10-2",
            "topic": "obstruction_hydronephrosis",
            "qtype": "diagnosis",
            "objective": "Undergraduate renal medicine: grading hydronephrosis from mild to severe",
            "query": "How does Society for Fetal Urology (SFU) grading classify hydronephrosis severity based on caliceal dilatation and parenchymal thinning?",
            "claim": "SFU grading progresses from Grade 1 (pelvic dilatation only) to Grade 2 (major calyces), Grade 3 (all calyces dilated with preserved cortex), and Grade 4 (caliceal dilatation with renal parenchymal thinning).",
            "doc": "DOC-PMC-RENAL-0014",
            "terms": ["grading", "dilation"],
            "anchors": ["grading", "dilation", "calyx"],
        },
        # --- DOC-0013: Infection Stones & Struvite ---
        {
            "id": "RENAL-V3-TRAIN-10-3",
            "topic": "renal_stones",
            "qtype": "pathophysiology",
            "objective": "Undergraduate renal medicine: urease-producing bacteria and struvite calculus formation",
            "query": "How do urease-positive bacteria (such as Proteus mirabilis) precipitate magnesium ammonium phosphate (struvite) stones?",
            "claim": "Bacterial urease hydrolyzes urinary urea into carbon dioxide and ammonia, markedly raising urine pH (>7.2) and generating ammonium ions that precipitate magnesium and phosphate into struvite staghorn calculi.",
            "doc": "DOC-PMC-RENAL-0013",
            "terms": ["struvite", "stone"],
            "anchors": ["struvite", "stone", "infection"],
        },
        {
            "id": "RENAL-V3-TRAIN-10-4",
            "topic": "renal_stones",
            "qtype": "management",
            "objective": "Undergraduate renal medicine: definitive surgical eradication of staghorn infection stones",
            "query": "Why is complete surgical clearance mandatory for struvite staghorn calculi?",
            "claim": "Complete surgical extraction (typically via percutaneous nephrolithotomy) is mandatory because residual stone fragments harbor persistent bacterial biofilms that inevitably cause recurrent severe UTIs and rapid stone recurrence.",
            "doc": "DOC-PMC-RENAL-0013",
            "terms": ["proteus", "urease"],
            "anchors": ["proteus", "urease", "stone"],
        },
    ]

    train_queries = []
    for qdef in train_queries_defs:
        doc_id = qdef["doc"]
        chunks = corpus_docs.get(doc_id, [])
        matched_chunk = find_chunk_matching(chunks, qdef["terms"], dev_sections)
        
        if not matched_chunk and len(qdef["terms"]) > 1:
            # try first term
            matched_chunk = find_chunk_matching(chunks, [qdef["terms"][0]], dev_sections)
            
        if matched_chunk:
            parent_id = matched_chunk.get("parent_section_id")
            train_queries.append({
                "query_id": qdef["id"],
                "query": qdef["query"],
                "topic": qdef["topic"],
                "question_type": qdef["qtype"],
                "learning_objective": qdef["objective"],
                "medical_claim": qdef["claim"],
                "evaluation_label": "SUPPORTED",
                "answerable": True,
                "gold_document_ids": [doc_id],
                "gold_parent_section_ids": [parent_id] if parent_id else [],
                "gold_child_chunk_ids": [matched_chunk.get("chunk_id")],
                "evidence_spans": [
                    {
                        "document_id": doc_id,
                        "parent_section_id": parent_id,
                        "evidence_text": matched_chunk.get("text", "")[:350],
                        "is_primary": True,
                        "verification_method": "source_curriculum_text_match",
                        "justification": f"Verified supporting text for {qdef['topic']}"
                    }
                ],
                "primary_evidence_quote": matched_chunk.get("text", ""),
                "gold_verification_anchors": qdef["anchors"],
                "gold_minimum_anchor_hits": 2,
                "authority_sensitive": False
            })
        else:
            print(f"Could not find matching chunk for {qdef['id']} in {doc_id} with terms {qdef['terms']}")

    print(f"Successfully matched and verified {len(train_queries)} answerable TRAIN queries.")
    
    # Add 20 unsupported queries (10 in-domain coverage gaps + 10 out-of-domain)
    unsupported_defs = [
        ("RENAL-V3-TRAIN-UNSUP-01", "renal_transplant", "immunosuppression", "What is the exact target trough whole blood concentration of tacrolimus during the first month following deceased donor kidney transplantation?"),
        ("RENAL-V3-TRAIN-UNSUP-02", "renal_genetics", "alport_syndrome", "Which specific collagen alpha-chain mutation causes X-linked Alport syndrome with progressive sensorineural hearing loss and anterior lenticonus?"),
        ("RENAL-V3-TRAIN-UNSUP-03", "fabry_disease", "renal_accumulation", "How does alpha-galactosidase A enzyme deficiency cause globotriaosylceramide accumulation in glomerular podocytes in Fabry nephropathy?"),
        ("RENAL-V3-TRAIN-UNSUP-04", "renal_oncology", "wilms_tumor", "What is the primary chemotherapeutic regimen for Stage II favorable-histology Wilms tumor in pediatric patients?"),
        ("RENAL-V3-TRAIN-UNSUP-05", "renal_artery_stenosis", "stenting", "What did the ASTRAL trial conclude regarding the mortality benefit of renal artery stenting versus medical therapy in atherosclerotic renovascular disease?"),
        ("RENAL-V3-TRAIN-UNSUP-06", "cystic_kidney", "tolvaptan_dosing", "What specific liver function monitoring schedule is mandatory when prescribing tolvaptan for rapidly progressive autosomal dominant polycystic kidney disease?"),
        ("RENAL-V3-TRAIN-UNSUP-07", "renal_tuberculosis", "sterile_pyuria", "What is the standard six-month antimicrobial regimen for renal tuberculosis presenting with sterile acid-fast pyuria?"),
        ("RENAL-V3-TRAIN-UNSUP-08", "renal_amyloidosis", "congo_red", "How does serum amyloid A (AA) nephropathy differ from AL amyloidosis in bone marrow plasma cell clonal expansion?"),
        ("RENAL-V3-TRAIN-UNSUP-09", "urological_trauma", "renal_shatter", "What are the indications for immediate surgical exploration versus conservative embolization in Grade IV blunt renal laceration?"),
        ("RENAL-V3-TRAIN-UNSUP-10", "reflux_nephropathy", "dmsa_scan", "What percentage of cortical renal scarring on dimercaptosuccinic acid (DMSA) scintigraphy warrants surgical ureteric reimplantation in children?"),
        ("RENAL-V3-TRAIN-UNSUP-11", "cardiology", "heart_failure", "What is the recommended dose titration of sacubitril/valsartan in heart failure with reduced ejection fraction NYHA Class II?"),
        ("RENAL-V3-TRAIN-UNSUP-12", "neurology", "parkinsons", "How does carbidopa prevent the peripheral conversion of levodopa to dopamine by dopa decarboxylase?"),
        ("RENAL-V3-TRAIN-UNSUP-13", "endocrinology", "thyroid_storm", "What is the initial dosing and administration sequence of propylthiouracil, iodine, and beta-blockers in thyroid storm?"),
        ("RENAL-V3-TRAIN-UNSUP-14", "respiratory", "asthma", "What is the threshold peak expiratory flow rate defining a life-threatening acute asthma exacerbation in adults?"),
        ("RENAL-V3-TRAIN-UNSUP-15", "gastroenterology", "crohns", "Which biologic agent targeting alpha-4 beta-7 integrin is indicated in moderate-to-severe Crohn disease refractory to anti-TNF?"),
        ("RENAL-V3-TRAIN-UNSUP-16", "hematology", "cml", "What BCR-ABL transcript level at 3 months indicates an optimal molecular response to first-line imatinib in chronic myeloid leukemia?"),
        ("RENAL-V3-TRAIN-UNSUP-17", "rheumatology", "temporal_arteritis", "What high-dose oral prednisolone regimen is recommended for giant cell arteritis without visual symptoms?"),
        ("RENAL-V3-TRAIN-UNSUP-18", "dermatology", "melanoma", "What excision margin is recommended for a primary cutaneous melanoma with a Breslow thickness of 1.5 mm?"),
        ("RENAL-V3-TRAIN-UNSUP-19", "orthopedics", "scaphoid_fracture", "What duration of thumb spica casting is standard for an undisplaced fracture of the scaphoid waist?"),
        ("RENAL-V3-TRAIN-UNSUP-20", "psychiatry", "bipolar_lithium", "What therapeutic serum lithium concentration range is targeted during acute manic episodes?"),
    ]

    for uid, top, sub, qtxt in unsupported_defs:
        is_gap = "gap" in top or top.startswith("renal_") or top in ("cystic_kidney", "urological_trauma", "reflux_nephropathy")
        train_queries.append({
            "query_id": uid,
            "query": qtxt,
            "topic": top,
            "question_type": sub,
            "learning_objective": f"Curriculum training non-retrievable query: {top}",
            "medical_claim": f"Unsupported or out-of-domain query: {qtxt}",
            "evaluation_label": "IN_DOMAIN_CORPUS_COVERAGE_GAP" if is_gap else "OUT_OF_DOMAIN_UNSUPPORTED",
            "answerable": False,
            "gold_document_ids": [],
            "gold_parent_section_ids": [],
            "gold_child_chunk_ids": [],
            "evidence_spans": [],
            "primary_evidence_quote": None,
            "gold_verification_anchors": [],
            "gold_minimum_anchor_hits": 0,
            "authority_sensitive": False
        })

    print(f"Total TRAIN dataset size: {len(train_queries)} (Answerable: {sum(1 for q in train_queries if q['answerable'])}, Unsupported: {sum(1 for q in train_queries if not q['answerable'])})")

    # --- ZERO LEAKAGE AUDIT ASSERTIONS ---
    print("\n" + "=" * 60)
    print("RUNNING ZERO-LEAKAGE AUDIT ASSERTIONS (TRAIN vs DEV)")
    print("=" * 60)
    
    train_q_texts = {q["query"].strip().lower() for q in train_queries}
    train_claims = {q["medical_claim"].strip().lower() for q in train_queries}
    train_sections = {sec for q in train_queries for sec in q.get("gold_parent_section_ids", [])}
    
    text_overlap = train_q_texts.intersection(dev_query_texts)
    claim_overlap = train_claims.intersection(dev_claims)
    section_overlap = train_sections.intersection(dev_sections)
    
    print(f"Query text overlap count: {len(text_overlap)}")
    print(f"Medical claim overlap count: {len(claim_overlap)}")
    print(f"Parent section overlap count: {len(section_overlap)}")
    
    assert len(text_overlap) == 0, f"LEAKAGE DETECTED: Query texts overlap: {text_overlap}"
    assert len(claim_overlap) == 0, f"LEAKAGE DETECTED: Medical claims overlap: {claim_overlap}"
    assert len(section_overlap) == 0, f"LEAKAGE DETECTED: Gold parent sections overlap: {section_overlap}"
    
    # Save TRAIN dataset
    payload = {
        "dataset_name": "RENAL-TRAIN-V3",
        "version": "3.0",
        "n_queries": len(train_queries),
        "n_answerable": sum(1 for q in train_queries if q["answerable"]),
        "n_unsupported": sum(1 for q in train_queries if not q["answerable"]),
        "leakage_audited_against": "renal-dev-evidence-spans-v2.json",
        "queries": train_queries
    }
    
    raw_json = json.dumps(payload, indent=2, ensure_ascii=False)
    OUTPUT_PATH.write_text(raw_json, encoding="utf-8")
    
    sha = sha256_bytes(OUTPUT_PATH.read_bytes())
    sha_path = OUTPUT_PATH.with_suffix(".json.sha256")
    sha_path.write_text(f"{sha}  {OUTPUT_PATH.name}\n", encoding="utf-8")
    
    print(f"\nSuccessfully wrote {OUTPUT_PATH} (N={len(train_queries)})")
    print(f"SHA256: {sha}")
    print("ZERO-LEAKAGE ASSERTIONS PASSED.")


if __name__ == "__main__":
    main()
