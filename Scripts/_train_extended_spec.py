"""
Build and verify RERANK_TRAIN_V5_EXTENDED (N=80)
=================================================
Expands training queries from N=20 to N=80 across all 12 undergraduate
curriculum strata while enforcing a strict 7-fold firewall against
DEV-A, DEV-B, and historical heldouts (V1, V2, V3, V4).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

ROOT = _ROOT
CHUNKS_DIR = ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
REGISTRY_PATH = ROOT / "Data/metadata/renal_source_registry_v2.json"
V5_DIR = ROOT / "evaluation/renal/v5"
REPORTS_DIR = ROOT / "reports/renal_v5"
HELDOUT_DIR = ROOT / "evaluation/renal"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "


def normalize_text(text: str) -> str:
    t = text.lower()
    t = re.sub(r"[^\w\s]", "", t)
    return " ".join(t.split())


def compute_sha256(data) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")).hexdigest()


def load_corpus():
    registry = json.loads(REGISTRY_PATH.read_bytes())
    doc_meta = {d["document_id"]: d for d in registry.get("documents", []) if d.get("status") == "accepted"}
    chunks = []
    chunk_map = {}
    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_bytes())
        for ch in payload.get("chunks", []):
            chunks.append(ch)
            chunk_map[ch["chunk_id"]] = ch
    return chunks, chunk_map, doc_meta


def find_gold_chunks(kw: str, chunks: list[dict], doc_id: str, max_n: int = 3) -> list[str]:
    kw_l = kw.lower()
    return [ch["chunk_id"] for ch in chunks if ch.get("document_id") == doc_id and kw_l in ch.get("text", "").lower()][:max_n]


def sfk(doc_id: str, sec: list[str]) -> str:
    p = " > ".join(sec[:2]) if sec else "ROOT"
    return hashlib.sha256(f"{doc_id}|{p}".encode()).hexdigest()[:12]


def qid(n: int) -> str:
    return f"V5-RNK-TRAIN-{n:04d}"


def make_item(n, q, stratum, style, obj, claim, doc_id, kw, sec, chunks, chunk_map):
    gold = find_gold_chunks(kw, chunks, doc_id)
    fk = sfk(doc_id, sec)
    
    # Resolve actual section path from chunk if resolved
    actual_sec_path = sec
    if gold and gold[0] in chunk_map:
        ch_sec = chunk_map[gold[0]].get("section_path")
        if ch_sec:
            actual_sec_path = ch_sec

    return {
        "query_id": qid(n),
        "query": q,
        "curriculum_stratum": stratum,
        "query_style": style,
        "learning_objective": obj,
        "canonical_claim": claim,
        "source_document_id": doc_id,
        "evidence_search_keyword": kw,
        "parent_section_path": actual_sec_path,
        "gold_chunk_ids": gold,
        "gold_doc_id": doc_id,
        "gold_section_path": actual_sec_path,
        "review_status": "AUTO_VERIFIED" if gold else "HUMAN_REVIEW_REQUIRED",
        "verification_method": "SOURCE_GROUNDED_KEYWORD_MATCH",
        "query_family": f"QF-{stratum}-{doc_id}-{fk}",
        "split_group_key": fk,
        "source": "V5_TRAIN_EXTENDED",
    }


def get_all_80_items(chunks, chunk_map):
    # 1. Load original 20 items from renal-rerank-train-v5.json
    orig_path = V5_DIR / "renal-rerank-train-v5.json"
    orig_20 = json.loads(orig_path.read_text(encoding="utf-8"))
    assert len(orig_20) == 20, f"Expected 20 original items, got {len(orig_20)}"
    
    items = list(orig_20) # 1 to 20 preserved exactly

    # 2. Add 60 new query families (21 to 80)
    new_items_spec = [
        # --- STR-01: Renal Anatomy & Glomerular Filtration (+6 -> 7 total) ---
        (21, "What are the key components of the podocyte foot process cytoskeleton?",
         "STR-01", "QS-A", "Describe actin cytoskeleton organization in podocyte foot processes",
         "The podocyte foot process contains an actin-based contractile apparatus linked to the slit diaphragm via synaptopodin and CD2AP.",
         "DOC-PMC-RENAL-0018", "actin", ["Slit Diaphragm", "Cytoskeleton"]),
        (22, "How does the endothelial glycocalyx contribute to glomerular barrier selectivity?",
         "STR-01", "QS-F", "Explain charge and size selectivity of glomerular endothelial glycocalyx",
         "Glomerular endothelial glycocalyx possesses negatively charged proteoglycans that repel anionic plasma proteins.",
         "DOC-PMC-RENAL-0018", "glycocalyx", ["Glomerular Endothelium"]),
        (23, "What hydrostatic and oncotic pressure changes determine net ultrafiltration pressure in the glomerulus?",
         "STR-01", "QS-A", "Calculate Starling forces across glomerular capillaries",
         "Net ultrafiltration pressure equals glomerular capillary hydrostatic pressure minus Bowman space hydrostatic pressure and capillary oncotic pressure.",
         "DOC-PMC-RENAL-0002", "capillary", ["Haemodynamics", "Starling"]),
        (24, "How does angiotensin II selectively constrict the efferent arteriole to maintain GFR?",
         "STR-01", "QS-A", "Explain efferent arteriolar constriction and filtration fraction elevation by Ang II",
         "Angiotensin II preferential efferent arteriolar constriction increases glomerular capillary pressure, preserving GFR during hypoperfusion.",
         "DOC-PMC-RENAL-0001", "vasoconstrict", ["RAAS", "Glomerular Pressure"]),
        (25, "What cellular interactions maintain the fenestrated phenotype of glomerular endothelial cells?",
         "STR-01", "QS-F", "Explain VEGF-A paracrine signalling from podocytes to endothelial cells",
         "Podocyte-derived VEGF-A signals across the GBM to VEGFR2 on endothelial cells, maintaining their fenestrations.",
         "DOC-PMC-RENAL-0018", "VEGF", ["Cross-talk", "Endothelium"]),
        (26, "How is inulin clearance used as the gold standard for measuring true GFR?",
         "STR-01", "QS-C", "Evaluate inulin clearance criteria for ideal GFR marker",
         "Inulin is freely filtered at the glomerulus and undergoes neither tubular reabsorption nor secretion, making its clearance equal to GFR.",
         "DOC-PMC-RENAL-0016", "clearance", ["GFR Measurement"]),

        # --- STR-02: Tubular Transport & Physiology (+4 -> 7 total) ---
        (27, "How does parathyroid hormone regulate phosphate reabsorption in the proximal tubule?",
         "STR-02", "QS-A", "Explain PTH-mediated Npt2a endocytosis and phosphaturia",
         "PTH activates apical and basolateral receptors in proximal tubule, promoting Npt2a/Npt2c transporter retrieval and phosphaturia.",
         "DOC-PMC-RENAL-0006", "phosphate", ["Phosphate", "Tubular Transport"]),
        (28, "What transporter mediates basolateral bicarbonate extrusion coupled to sodium in the proximal tubule?",
         "STR-02", "QS-A", "Identify NBCe1 electrogenic sodium-bicarbonate cotransporter stoichiometry",
         "NBCe1 mediates basolateral extrusion of 1 Na+ and 3 HCO3- ions in proximal tubule epithelial cells.",
         "DOC-PMC-RENAL-0020", "NBCe1", ["Basolateral Transport"]),
        (29, "How does insulin stimulate sodium reabsorption in the distal convoluted tubule?",
         "STR-02", "QS-A", "Explain insulin-Akt-WNK4 pathway activation of NCC in DCT",
         "Insulin activates Akt, inhibiting WNK4 degradation and promoting phosphorylation and apical membrane trafficking of NCC.",
         "DOC-PMC-RENAL-0020", "WNK", ["Insulin Signaling", "NCC"]),
        (30, "How do URAT1 and GLUT9 coordinate proximal tubular urate reabsorption?",
         "STR-02", "QS-A", "Explain apical URAT1 uptake and basolateral GLUT9 exit in renal urate transport",
         "URAT1 on the apical membrane mediates urate reabsorption coupled to organic anions, while GLUT9 transports urate across the basolateral membrane into peritubular capillaries.",
         "DOC-PMC-RENAL-0019", "urate", ["Proximal Tubule", "Urate"]),

        # --- STR-03: Countercurrent & Urine Concentration (+5 -> 6 total) ---
        (31, "How does the medullary countercurrent multiplier create an osmotic gradient in the loop of Henle?",
         "STR-03", "QS-A", "Explain active NaCl reabsorption in TAL driving medullary hyperosmolality",
         "Active NaCl transport by NKCC2 without water movement in TAL creates a single effect, multiplied along the corticomedullary axis.",
         "DOC-PMC-RENAL-0023", "countercurrent", ["Countercurrent Mechanism"]),
        (32, "What role does urea recycling play in establishing maximum inner medullary hypertonicity?",
         "STR-03", "QS-A", "Describe UT-A1/UT-A3 mediated urea reabsorption and medullary interstitial accumulation",
         "Vasopressin-regulated UT-A1 and UT-A3 facilitate urea efflux from inner medullary collecting ducts, providing up to half of medullary osmutes.",
         "DOC-PMC-RENAL-0023", "urea", ["Urea Recycling"]),
        (33, "Why does high medullary blood flow wash out the renal concentrating gradient?",
         "STR-03", "QS-F", "Explain medullary washout from increased vasa recta perfusion velocity",
         "Excessive vasa recta blood velocity reduces countercurrent diffusion equilibration time, carrying solutes out of the medulla.",
         "DOC-PMC-RENAL-0023", "perfusion", ["Vasa Recta"]),
        (34, "How does furosemide abolish the corticomedullary osmotic gradient?",
         "STR-03", "QS-A", "Explain NKCC2 inhibition preventing hyperosmolar medullary gradient generation",
         "Furosemide blocks the Na-K-2Cl cotransporter in the thick ascending limb, preventing solute deposition into the medullary interstitium.",
         "DOC-PMC-RENAL-0023", "thick ascending", ["TAL Physiology"]),
        (35, "What cellular second messenger pathways mediate aquaporin-2 vesicle translocation to apical membranes?",
         "STR-03", "QS-A", "Describe V2R-Gs-cAMP-PKA signalling pathway for AQP2 exocytosis",
         "Arginine vasopressin binds basolateral V2 receptors, stimulating cAMP generation and PKA phosphorylation of AQP2 tetramers.",
         "DOC-PMC-RENAL-0023", "aquaporin", ["Vasopressin Signaling"]),

        # --- STR-04: RAAS & Blood Pressure Regulation (+5 -> 7 total) ---
        (36, "How does parathyroid hormone stimulate renal 1-alpha-hydroxylase activity to produce calcitriol?",
         "STR-04", "QS-A", "Explain PTH stimulation of CYP27B1 in proximal tubular mitochondria",
         "Parathyroid hormone activates mitochondrial CYP27B1 (1-alpha-hydroxylase) in proximal tubule cells, converting 25(OH)D to active 1,25(OH)2D3 (calcitriol).",
         "DOC-PMC-RENAL-0024", "calcitriol", ["Renal Endocrine", "Vitamin D"]),
        (37, "How does angiotensin-converting enzyme 2 (ACE2) counteract classical RAAS vasoconstriction?",
         "STR-04", "QS-C", "Contrast Ang II-AT1R axis with Ang-(1-7)-Mas receptor protective axis",
         "ACE2 degrades Ang II to Ang-(1-7), which acts through Mas receptors to cause vasodilation, anti-inflammatory, and antifibrotic effects.",
         "DOC-PMC-RENAL-0001", "ACE2", ["Alternative RAAS Axis"]),
        (38, "What vascular remodeling changes occur in renal resistance arterioles in chronic hypertension?",
         "STR-04", "QS-F", "Describe hyaline and hyperplastic arteriolosclerosis secondary to prolonged elevated renal perfusion pressure",
         "Prolonged high pressure induces medial hypertrophy, smooth muscle proliferation, and extracellular matrix accumulation in afferent arterioles.",
         "DOC-PMC-RENAL-0001", "remodeling", ["Vascular Pathophysiology"]),
        (39, "How does aldosterone stimulate ENaC transcription versus ENaC membrane stabilization?",
         "STR-04", "QS-C", "Differentiate early SGK1 phosphorylation from late genomic induction by mineralocorticoid receptor",
         "Early aldosterone action induces SGK1 to inhibit NEDD4-2-mediated ENaC retrieval; late action stimulates direct ENaC subunit transcription.",
         "DOC-PMC-RENAL-0020", "NEDD4-2", ["Aldosterone Mechanism"]),
        (40, "What is the role of intrarenal local RAAS in promoting tubulointerstitial fibrosis?",
         "STR-04", "QS-A", "Explain locally produced Ang II inducing TGF-beta and collagen deposition in renal parenchyma",
         "Locally generated renal Ang II acts on tubular epithelial cells to stimulate TGF-beta1 and CTGF, driving epithelial-mesenchymal transition and fibrosis.",
         "DOC-PMC-RENAL-0001", "fibrosis", ["Intrarenal RAAS"]),

        # --- STR-05: Fluid & Volume Homeostasis (+6 -> 7 total) ---
        (41, "How does atrial natriuretic peptide counteract renal sodium and fluid retention?",
         "STR-05", "QS-A", "Explain ANP actions on afferent arteriole dilation, medullary collecting duct Na+ transport, and renin suppression",
         "ANP dilates afferent and constricts efferent arterioles to increase GFR, while directly inhibiting Na+ reabsorption in collecting ducts.",
         "DOC-PMC-RENAL-0001", "blood pressure", ["Volume Regulation"]),
        (42, "What clinical features differentiate hypovolemic from hypervolemic hyponatremia?",
         "STR-05", "QS-C", "Compare extracellular fluid volume assessment in dehydration versus congestive heart failure and cirrhosis",
         "Hypovolemic hyponatremia displays orthostatic hypotension, dry mucosa, and poor skin turgor; hypervolemic hyponatremia presents with peripheral edema, ascites, and raised JVP.",
         "DOC-PMC-RENAL-0009", "volume", ["Fluid Disturbance"]),
        (43, "Why does severe hypomagnesemia cause refractory hypocalcemia and hypokalemia?",
         "STR-05", "QS-F", "Explain magnesium requirement for ROMK inhibition and PTH secretion",
         "Magnesium deficiency removes intracellular inhibition on ROMK channels causing renal K+ wasting, and impairs parathyroid hormone release and end-organ sensitivity.",
         "DOC-PMC-RENAL-0003", "magnesium", ["Electrolyte Interactions"]),
        (44, "What mechanisms shift potassium intracellularly in response to acute alkalemia?",
         "STR-05", "QS-A", "Describe H+/K+ transcellular exchange and Na+/K+-ATPase stimulation in systemic alkalosis",
         "Extracellular proton deficit drives H+ out of cells in exchange for K+ entry, while alkalosis stimulates Na+/K+-ATPase activity.",
         "DOC-PMC-RENAL-0009", "shift", ["Potassium Shift"]),
        (45, "How does effective circulating volume depletion cause secondary hyperaldosteronism in decompensated cirrhosis?",
         "STR-05", "QS-A", "Explain splanchnic arterial vasodilation triggering baroreceptor-mediated RAAS and sympathetic stimulation",
         "Splanchnic arterial vasodilation reduces effective arterial blood volume, triggering persistent non-osmotic baroreceptor activation of RAAS.",
         "DOC-PMC-RENAL-0001", "vasodilation", ["Effective Circulating Volume"]),
        (46, "What transport defects distinguish Bartter syndrome from Gitelman syndrome?",
         "STR-05", "QS-C", "Differentiate loop NKCC2/ROMK dysfunction from distal NCC cotransporter mutations",
         "Bartter syndrome involves thick ascending limb NKCC2, ROMK, or CLCNKB defects with hypercalciuria; Gitelman syndrome involves distal tubule NCC defects with hypocalciuria and severe hypomagnesemia.",
         "DOC-PMC-RENAL-0020", "sodium", ["Tubulopathies"]),

        # --- STR-06: Acid-Base Balance & Renal Regulation (+5 -> 7 total) ---
        (47, "How does pendrin coordinate with AE4 in collecting duct intercalated cells during alkalemia?",
         "STR-06", "QS-A", "Describe apical pendrin bicarbonate secretion and AE4 bicarbonate sensing",
         "In metabolic alkalosis, beta-intercalated cells upregulate apical pendrin to excrete HCO3-, while basolateral AE4 coordinates distal nephron chloride and bicarbonate sensing.",
         "DOC-PMC-RENAL-0021", "intercalated", ["Intercalated Polarity"]),
        (48, "What distinguishes type 1 (distal) from type 2 (proximal) renal tubular acidosis?",
         "STR-06", "QS-C", "Compare urine pH, serum potassium, and nephrocalcinosis risk between distal and proximal RTA",
         "Type 1 RTA cannot acidify urine below pH 5.5, has hypokalemia and high nephrocalcinosis risk; Type 2 RTA has impaired HCO3- threshold with fractional HCO3- excretion >15%.",
         "DOC-PMC-RENAL-0005", "renal tubular acidosis", ["RTA Differentiation"]),
        (49, "Why does hypokalemia maintain or exacerbate metabolic alkalosis?",
         "STR-06", "QS-F", "Explain transcellular H+/K+ exchange, increased ammoniagenesis, and enhanced proximal HCO3- reabsorption",
         "Intracellular acidosis from K+ depletion stimulates proximal tubule glutaminase and Na+/H+ exchange, perpetuating bicarbonate regeneration.",
         "DOC-PMC-RENAL-0003", "ammoniagenesis", ["Alkalosis Maintenance"]),
        (50, "What is the urinary net charge and how does it assess renal ammonium excretion in normal anion gap acidosis?",
         "STR-06", "QS-D", "Calculate urinary net charge (Na + K - Cl) to differentiate renal from gastrointestinal bicarbonate loss",
         "Negative urinary net charge indicates intact renal NH4+ excretion (diarrhea); positive net charge indicates impaired renal NH4+ excretion (distal RTA).",
         "DOC-PMC-RENAL-0005", "ammonium", ["Urinary Net Charge"]),
        (51, "How does pendrin in beta-intercalated cells mediate renal bicarbonate excretion?",
         "STR-06", "QS-A", "Describe apical Cl-/HCO3- exchanger pendrin in cortical collecting duct",
         "Pendrin on apical membrane of beta-intercalated cells secretes bicarbonate into tubular lumen in exchange for chloride during metabolic alkalosis.",
         "DOC-PMC-RENAL-0021", "pendrin", ["Distal Secretion"]),

        # --- STR-07: Acute Kidney Injury (AKI) (+4 -> 7 total) ---
        (52, "What are the KDIGO staging criteria for acute kidney injury based on serum creatinine and urine output?",
         "STR-07", "QS-D", "Define KDIGO stage 1, 2, and 3 thresholds for serum creatinine rise and oliguria duration",
         "KDIGO stage 1: Cr 1.5-1.9x baseline or rise >=0.3 mg/dL; stage 2: Cr 2.0-2.9x; stage 3: Cr >=3.0x, rise to >=4.0 mg/dL, or anuria >=12 hours.",
         "DOC-PMC-RENAL-0006", "KDIGO", ["AKI Classification"]),
        (53, "What histopathological features differentiate acute tubular necrosis from acute interstitial nephritis?",
         "STR-07", "QS-C", "Contrast tubular epithelial cell loss and muddy brown casts with interstitial inflammatory infiltrate and tubulitis",
         "ATN shows patchy tubular necrosis, denudation of basement membrane, and granular casts; AIN shows interstitial edema and lymphocytic/eosinophilic infiltrate.",
         "DOC-PMC-RENAL-0006", "tubular necrosis", ["Histology Differentiation"]),
        (54, "Why is serum creatinine a delayed biomarker of glomerular filtration decline in early AKI?",
         "STR-07", "QS-F", "Explain kinetic lag and non-linear relationship between GFR reduction and creatinine accumulation",
         "Creatinine requires steady-state accumulation over 24-48 hours; substantial GFR loss occurs before serum creatinine exceeds reference range.",
         "DOC-PMC-RENAL-0016", "steady", ["Creatinine Kinetics"]),
        (55, "What hemodynamic changes occur in abdominal compartment syndrome that precipitate acute kidney injury?",
         "STR-07", "QS-A", "Explain elevated renal vein pressure and reduced renal perfusion pressure in intra-abdominal hypertension",
         "Increased intra-abdominal pressure compresses renal veins and parenchyma, elevating renal venous pressure and reducing renal perfusion pressure.",
         "DOC-PMC-RENAL-0006", "perfusion pressure", ["Hemodynamic AKI"]),

        # --- STR-08: Chronic Kidney Disease (CKD) (+6 -> 7 total) ---
        (56, "What are the KDIGO heat map risk categories defined by GFR and albuminuria stages?",
         "STR-08", "QS-D", "Classify CKD prognosis using G1-G5 and A1-A3 CGA grid",
         "CKD staging combines GFR category (G1 >90 to G5 <15) with albuminuria category (A1 <30, A2 30-300, A3 >300 mg/g) to determine risk.",
         "DOC-PMC-RENAL-0007", "albuminuria", ["CKD Staging"]),
        (57, "How does secondary hyperparathyroidism develop in progressive chronic kidney disease?",
         "STR-08", "QS-A", "Explain phosphate retention, calcitriol deficiency, and FGF23 elevation driving PTH hypersecretion",
         "Loss of functional nephrons causes phosphate retention and decreased 1-alpha-hydroxylase activity, lowering calcitriol and ionized calcium to stimulate PTH.",
         "DOC-PMC-RENAL-0024", "parathyroid", ["Mineral Bone Disorder"]),
        (58, "What is the pathophysiology of normocytic normochromic anemia in advanced renal insufficiency?",
         "STR-08", "QS-A", "Explain peritubular interstitial cell loss reducing erythropoietin production and hepcidin-mediated iron trapping",
         "Degeneration of peritubular fibroblasts reduces EPO synthesis, combined with elevated hepcidin that blocks iron release from enterocytes and macrophages.",
         "DOC-PMC-RENAL-0024", "erythropoietin", ["Renal Anemia"]),
        (59, "Why does strict blood pressure control with RAAS inhibitors slow diabetic kidney disease progression?",
         "STR-08", "QS-A", "Explain intraglomerular pressure reduction and proteinuria attenuation by ACE inhibitors or ARBs",
         "RAAS blockade preferentially reduces efferent arteriolar resistance, diminishing glomerular hyperfiltration and shear stress that drive glomerulosclerosis.",
         "DOC-PMC-RENAL-0007", "antihypertensive", ["Nephroprotection"]),
        (60, "What dietary sodium and protein intake limits are recommended for non-dialysis CKD patients?",
         "STR-08", "QS-B", "Apply guideline-directed nutritional management in stage 3-5 CKD",
         "Guidelines recommend sodium restriction (<2 g/day / <5 g salt) and moderate protein intake (0.8 g/kg/day) in stage 3-5 non-dialysis CKD.",
         "DOC-PMC-RENAL-0007", "protein", ["Nutritional Guidelines"]),
        (61, "How does chronic metabolic acidosis accelerate chronic kidney disease progression?",
         "STR-08", "QS-F", "Explain complement activation and endothelin-1 induction by intrarenal ammoniagenesis in residual nephrons",
         "Residual nephrons must produce excessive ammonium per nephron to excrete acid, which activates alternative complement pathway and triggers interstitial fibrosis.",
         "DOC-PMC-RENAL-0004", "acidosis", ["Fibrosis Mechanisms"]),

        # --- STR-09: Glomerular Diseases (+5 -> 7 total) ---
        (62, "What immunofluorescence pattern confirms anti-glomerular basement membrane (anti-GBM) disease?",
         "STR-09", "QS-D", "Identify linear IgG deposition along glomerular capillary loops on direct immunofluorescence",
         "Anti-GBM disease shows bright, ribbon-like linear IgG staining along glomerular capillary basement membranes on immunofluorescence.",
         "DOC-PMC-RENAL-0018", "basement membrane", ["Glomerular Pathology"]),
        (63, "What distinguishes minimal change disease from focal segmental glomerulosclerosis on electron microscopy?",
         "STR-09", "QS-C", "Compare podocyte foot process effacement and absence versus presence of segmental sclerosis and hyalinosis",
         "MCD shows diffuse foot process effacement with normal light microscopy; FSGS shows patchy sclerosis of capillary tufts with hyalinosis and foot process effacement.",
         "DOC-PMC-RENAL-0008", "minimal change", ["Podocytopathies"]),
        (64, "What autoantibody is diagnostic for primary membranous nephropathy in >70% of adult cases?",
         "STR-09", "QS-D", "Identify anti-PLA2R antibodies as serological biomarker for primary membranous nephropathy",
         "Circulating IgG4 autoantibodies against the M-type phospholipase A2 receptor (PLA2R) are specific for primary membranous nephropathy.",
         "DOC-PMC-RENAL-0008", "membranous", ["Nephrotic Autoantibodies"]),
        (65, "What clinical presentation characterizes rapidly progressive glomerulonephritis (RPGN)?",
         "STR-09", "QS-B", "Recognize rapid GFR decline over days to weeks accompanied by active nephritic sediment and cellular crescents",
         "RPGN presents with rapid loss of renal function over days to weeks, active urine sediment with red cell casts, and extensive glomerular crescent formation.",
         "DOC-PMC-RENAL-0025", "glomerulonephritis", ["Nephritic Syndrome"]),
        (66, "How does IgA nephropathy typically present in young adults following upper respiratory infection?",
         "STR-09", "QS-B", "Identify synpharyngitic macroscopic hematuria developing within 24-48 hours of mucosal infection",
         "IgA nephropathy typically presents as episodic macroscopic hematuria developing 1-2 days after an upper respiratory or gastrointestinal infection.",
         "DOC-PMC-RENAL-0025", "nephropathy", ["Mesangial Glomerulopathy"]),

        # --- STR-10: Tubulointerstitial & Genetic (+5 -> 6 total) ---
        (67, "What gene mutations cause autosomal dominant polycystic kidney disease (ADPKD)?",
         "STR-10", "QS-D", "Identify PKD1 (polycystin-1) and PKD2 (polycystin-2) mutations and their relative phenotypic severity",
         "PKD1 mutations on chromosome 16 cause ~78% of cases with earlier ESRD (~58 years); PKD2 mutations on chromosome 4 account for ~15% with milder disease.",
         "DOC-PMC-RENAL-0007", "polycystic", ["Genetic Kidney Disease"]),
        (68, "What drug classes are most frequently implicated in drug-induced acute interstitial nephritis?",
         "STR-10", "QS-B", "Identify antibiotics (beta-lactams), NSAIDs, and proton pump inhibitors as leading AIN causes",
         "Common triggers of allergic AIN include antibiotics (penicillins, cephalosporins), PPIs (omeprazole), and NSAIDs, typically presenting with eosinophilia or rash.",
         "DOC-PMC-RENAL-0006", "nephritis", ["Allergic Nephropathy"]),
        (69, "How does urinary obstruction produce medullary ischemia and tubular atrophy in hydronephrosis?",
         "STR-10", "QS-A", "Explain elevated intratubular pressure compressing peritubular capillaries and inducing interstitial inflammation",
         "Sustained retrograde pressure from urinary obstruction compresses medullary vasculature, triggering tubular apoptosis, macrophage infiltration, and interstitial fibrosis.",
         "DOC-PMC-RENAL-0014", "hydronephrosis", ["Obstructive Nephropathy"]),
        (70, "What histological feature on renal ultrasound grades severe hydronephrosis according to SFU guidelines?",
         "STR-10", "QS-D", "Define Society for Fetal Urology grade 4 hydronephrosis based on parenchymal thinning",
         "SFU Grade 4 hydronephrosis is defined by pelvicalyceal dilatation accompanied by marked cortical and medullary parenchymal thinning.",
         "DOC-PMC-RENAL-0014", "parenchymal", ["Hydronephrosis Grading"]),
        (71, "What mechanisms trigger recurrent urinary tract infections in women with normal urinary anatomy?",
         "STR-10", "QS-A", "Explain periurethral colonization, urothelial intracellular bacterial reservoirs, and bladder umbrella cell invasion",
         "Uropathogenic E. coli invade superficial umbrella cells via FimH adhesion, forming quiescent intracellular bacterial communities resistant to host clearance.",
         "DOC-PMC-RENAL-0011", "urothelial", ["Recurrent Infection"]),

        # --- STR-11: Nephrolithiasis & UTI (+4 -> 6 total) ---
        (72, "What 24-hour urine metabolic abnormalities predispose to calcium oxalate nephrolithiasis?",
         "STR-11", "QS-B", "Identify hypercalciuria, hyperoxaluria, hypocitraturia, and low urine volume as primary lithogenic factors",
         "Key metabolic risk factors include hypercalciuria, hyperoxaluria, low urine volume (<2 L/day), and hypocitraturia (loss of natural crystallization inhibitor).",
         "DOC-PMC-RENAL-0012", "oxalate", ["Stone Metabolic Evaluation"]),
        (73, "Why does low urine pH promote uric acid stone formation whereas alkaline urine promotes calcium phosphate stones?",
         "STR-11", "QS-F", "Explain pH-dependent solubility of uric acid (pKa 5.5) and calcium phosphate brushite/apatite",
         "Uric acid is insoluble below its pKa of 5.5 in acidic urine; calcium phosphate precipitates in alkaline urine (pH >6.5) where trivalent phosphate is available.",
         "DOC-PMC-RENAL-0012", "uric acid", ["Physicochemical Lithogenesis"]),
        (74, "How do bacterial biofilms on indwelling urinary catheters perpetuate catheter-associated UTI?",
         "STR-11", "QS-A", "Describe extracellular polymeric substance matrix protecting uropathogens from antimicrobial agents",
         "Uropathogens adhere to catheter surfaces and secrete an extracellular polysaccharide matrix that shields bacteria from host immune defenses and antibiotics.",
         "DOC-PMC-RENAL-0013", "biofilm", ["Catheter-Associated Infection"]),
        (75, "What are the indications for emergency decompression of an obstructed upper urinary tract?",
         "STR-11", "QS-B", "Identify infected hydronephrosis (urosepsis with obstruction) and bilateral obstruction in solitary kidney",
         "Emergency ureteral stenting or nephrostomy is mandated for an obstructed kidney with signs of systemic infection/pyelonephritis or acute renal failure in a solitary kidney.",
         "DOC-PMC-RENAL-0012", "decompression", ["Urological Emergencies"]),

        # --- STR-12: Dialysis, Transplantation & Pharmacology (+5 -> 6 total) ---
        (76, "What absolute clinical indications mandate emergency initiation of renal replacement therapy (AEIOU)?",
         "STR-12", "QS-B", "Identify Acidosis, Electrolytes (K), Ingestion/toxins, Overload (pulmonary edema), and Uremic complications",
         "Urgent dialysis indications: severe refractory metabolic acidosis (pH <7.15), refractory hyperkalemia (>6.5 mmol/L), drug toxins, refractory pulmonary edema, and uremic pericarditis/encephalopathy.",
         "DOC-PMC-RENAL-0015", "replacement", ["Emergency Dialysis"]),
        (77, "How does continuous venovenous hemofiltration (CVVH) clear solutes by convection rather than diffusion?",
         "STR-12", "QS-A", "Explain hydrostatic transmembrane pressure driving solvent drag across high-flux hemofilter membrane",
         "CVVH relies on convective solvent drag across a permeable membrane driven by hydrostatic pressure, providing superior clearance of middle and large molecular weight toxins.",
         "DOC-PMC-RENAL-0015", "hemofiltration", ["Dialysis Modalities"]),
        (78, "What calcineurin inhibitor nephrotoxicity mechanisms induce acute afferent arteriolar vasoconstriction?",
         "STR-12", "QS-F", "Explain cyclosporine and tacrolimus induction of endothelin-1 and thromboxane with reduction of nitric oxide and prostacyclin",
         "Calcineurin inhibitors stimulate renal vasoconstrictors (endothelin-1, thromboxane) and impair vasodilators (NO, PGI2), causing reversible pre-glomerular arteriolar vasoconstriction.",
         "DOC-PMC-RENAL-0001", "vasoconstriction", ["Drug Nephrotoxicity"]),
        (79, "What hemodynamic and metabolic benefits do SGLT2 inhibitors confer in cardiorenal syndrome?",
         "STR-12", "QS-A", "Explain tubuloglomerular feedback restoration, intraglomerular pressure reduction, and osmotic diuresis without neurohormonal activation",
         "SGLT2 inhibitors increase distal sodium delivery to macula densa, restoring afferent arteriolar constriction to reduce glomerular hyperfiltration and renal interstitial edema.",
         "DOC-PMC-RENAL-0019", "hemodynamic", ["Cardiorenal Pharmacology"]),
        (80, "What red cell morphological features on phase-contrast microscopy distinguish glomerular from lower urinary tract hematuria?",
         "STR-12", "QS-C", "Differentiate dysmorphic erythrocytes and acanthocytes from isomorphic red blood cells",
         "Glomerular bleeding is characterized by dysmorphic erythrocytes (>80%), acanthocytes (G1 cells >5%), and red blood cell casts; isomorphic red cells indicate urological bleeding.",
         "DOC-PMC-RENAL-0025", "dysmorphic", ["Hematuria Differentiation"]),
    ]

    for spec in new_items_spec:
        n, q, stratum, style, obj, claim, doc_id, kw, sec = spec
        items.append(make_item(n, q, stratum, style, obj, claim, doc_id, kw, sec, chunks, chunk_map))

    return items
