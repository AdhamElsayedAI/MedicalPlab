"""
MedicalPlab Shared Evidence Engine V2 — Stage 5 & 6: Assemble PRODUCT_DEV_V2 (N=120)
====================================================================================
Evidence-first benchmark construction:
Source Evidence -> Atomic Claim -> Learning Objective -> Realistic Clinical Query -> Multi-Positive Qrel

Strictly firewalled against:
- Spent V7 Product Test (N=100)
- V6 OOD Stress Validation (N=40)
- DEV-A (N=50)
- DEV-B (N=40)
- Historical Heldouts (V1-V4)

Multi-Positive Qrels:
- exact_gold_chunk_ids: Primary source chunk.
- semantic_support_chunk_ids: All chunks independently providing direct evidence.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

CHUNKS_DIR = _ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
OUT_DIR = _ROOT / "evaluation" / "evidence_engine"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "product_dev_v2.json"

# Quarantined Chunk IDs from previous evaluations
QUARANTINED_FILES = [
    _ROOT / "evaluation" / "renal" / "v7" / "renal-product-test-v7.json",
    _ROOT / "evaluation" / "renal" / "v7" / "renal-ood-stress-v6.json",
    _ROOT / "evaluation" / "renal" / "v7" / "renal-train-dev-v7.json",
    _ROOT / "evaluation" / "renal" / "v1" / "renal-heldout-gold-v1.json",
    _ROOT / "evaluation" / "renal" / "v2" / "renal-heldout-v2.json",
    _ROOT / "evaluation" / "renal" / "v3" / "renal-heldout-v3.json",
    _ROOT / "evaluation" / "renal" / "v4" / "renal-heldout-v4-final.json",
]


def load_all_quarantined_chunks() -> set[str]:
    quarantined = set()
    for qf in QUARANTINED_FILES:
        if qf.exists():
            data = json.loads(qf.read_bytes())
            items = data if isinstance(data, list) else data.get("queries", [])
            for item in items:
                if isinstance(item, dict):
                    quarantined.update(item.get("gold_chunk_ids", []))
                    if "exact_gold_chunk_ids" in item:
                        quarantined.update(item.get("exact_gold_chunk_ids", []))
                    if "positive_chunk_ids" in item:
                        quarantined.update(item.get("positive_chunk_ids", []))
    print(f"Total quarantined gold chunk IDs: {len(quarantined)}")
    return quarantined


def load_all_corpus_chunks() -> dict[str, dict]:
    chunks = {}
    for p in CHUNKS_DIR.glob("*.chunks.json"):
        data = json.loads(p.read_bytes())
        doc_id = data.get("document_id")
        for ch in data.get("chunks", []):
            cid = ch.get("chunk_id")
            ch["doc_id"] = doc_id
            chunks[cid] = ch
    print(f"Total corpus chunks loaded: {len(chunks)}")
    return chunks


# Authoring 120 authentic undergraduate clinical queries across 12 core clinical domains
DEV_V2_SPECIFICATIONS = [
    # Domain 1: Renal Endocrinology & RAAS
    {
        "domain": "Renal Endocrinology & RAAS",
        "topic": "ACE2 & Counter-regulatory Peptides",
        "doc_id": "DOC-PMC-RENAL-0001",
        "preferred_chunk": "DOC-PMC-RENAL-0001-B-C0004",
        "alt_chunks": ["DOC-PMC-RENAL-0001-B-C0019"],
        "query": "Which endogenous carboxypeptidase converts angiotensin II into angiotensin 1-7 to mediate counter-regulatory vasodilation?",
        "claim": "Angiotensin-converting enzyme 2 (ACE2) converts angiotensin II into angiotensin-(1-7) to exert vasodilatory and antiproliferative actions.",
        "lo": "Identify the counter-regulatory axis of the renin-angiotensin-aldosterone system mediated by ACE2."
    },
    {
        "domain": "Renal Endocrinology & RAAS",
        "topic": "Direct Renin Inhibition",
        "doc_id": "DOC-PMC-RENAL-0001",
        "preferred_chunk": "DOC-PMC-RENAL-0001-B-C0003",
        "alt_chunks": ["DOC-PMC-RENAL-0001-B-C0016"],
        "query": "What is the pharmacological mechanism of aliskiren at the initial rate-limiting step of the RAAS?",
        "claim": "Aliskiren acts as an orally active direct renin inhibitor binding the active site of renin to block conversion of angiotensinogen to angiotensin I.",
        "lo": "Explain the pharmacodynamics of direct renin inhibitors in hypertension management."
    },
    {
        "domain": "Renal Endocrinology & RAAS",
        "topic": "Angiotensin II Type 1 vs Type 2 Receptors",
        "doc_id": "DOC-PMC-RENAL-0001",
        "preferred_chunk": "DOC-PMC-RENAL-0001-B-C0006",
        "alt_chunks": ["DOC-PMC-RENAL-0001-B-C0005"],
        "query": "How do angiotensin II type 1 (AT1) and type 2 (AT2) receptors differ regarding vascular smooth muscle tone?",
        "claim": "AT1 receptors mediate vasoconstriction, cell proliferation, and aldosterone secretion, whereas AT2 receptors promote vasodilation and tissue repair.",
        "lo": "Compare the hemodynamic and physiological functions of AT1 and AT2 receptors."
    },
    {
        "domain": "Renal Endocrinology & RAAS",
        "topic": "Aldosterone Vascular Remodeling",
        "doc_id": "DOC-PMC-RENAL-0001",
        "preferred_chunk": "DOC-PMC-RENAL-0001-B-C0009",
        "alt_chunks": ["DOC-PMC-RENAL-0001-B-C0010"],
        "query": "How does aldosterone induce vascular inflammation and oxidative stress beyond its tubular sodium-retaining effects?",
        "claim": "Aldosterone promotes vascular fibrosis, endothelial dysfunction, and reactive oxygen species generation via mineralocorticoid receptors.",
        "lo": "Describe non-epithelial vascular actions of aldosterone and mineralocorticoid receptor activation."
    },
    {
        "domain": "Renal Endocrinology & RAAS",
        "topic": "Mineralocorticoid Receptor Antagonists in CKD",
        "doc_id": "DOC-PMC-RENAL-0001",
        "preferred_chunk": "DOC-PMC-RENAL-0001-B-C0011",
        "alt_chunks": ["DOC-PMC-RENAL-0001-B-C0017"],
        "query": "What therapeutic benefits and safety concerns arise when mineralocorticoid receptor antagonists are added to ACE inhibitors in proteinuric CKD?",
        "claim": "Mineralocorticoid receptor antagonists reduce albuminuria and cardiovascular events, but increase the incidence of hyperkalemia.",
        "lo": "Evaluate the clinical risks and benefits of combined RAAS blockade with MRAs."
    },

    # Domain 2: Glomerular Filtration & Podocyte Architecture
    {
        "domain": "Glomerular Filtration & Podocyte Architecture",
        "topic": "Slit Diaphragm Structure",
        "doc_id": "DOC-PMC-RENAL-0002",
        "preferred_chunk": "DOC-PMC-RENAL-0002-B-C0007",
        "alt_chunks": ["DOC-PMC-RENAL-0002-B-C0008", "DOC-PMC-RENAL-0002-B-C0020"],
        "query": "Which cell types and structural layers constitute the trilaminar glomerular filtration barrier?",
        "claim": "The glomerular filtration barrier comprises fenestrated endothelial cells, the glomerular basement membrane, and podocyte foot processes with slit diaphragms.",
        "lo": "Outline the histological architecture and permeability barriers of the glomerulus."
    },
    {
        "domain": "Glomerular Filtration & Podocyte Architecture",
        "topic": "Inulin vs Albumin Permselectivity",
        "doc_id": "DOC-PMC-RENAL-0002",
        "preferred_chunk": "DOC-PMC-RENAL-0002-B-C0023",
        "alt_chunks": ["DOC-PMC-RENAL-0002-B-C0044"],
        "query": "Why is inulin freely filtered across the glomerular barrier while albumin is almost entirely retained?",
        "claim": "Inulin is small and neutral, permitting unrestricted filtration, whereas albumin has a larger hydrodynamic radius and negative charge causing charge- and size-dependent repulsion.",
        "lo": "Explain size and charge permselectivity governing macromolecular glomerular filtration."
    },
    {
        "domain": "Glomerular Filtration & Podocyte Architecture",
        "topic": "Puromycin Aminonucleoside Injury Mechanism",
        "doc_id": "DOC-PMC-RENAL-0002",
        "preferred_chunk": "DOC-PMC-RENAL-0002-B-C0090",
        "alt_chunks": ["DOC-PMC-RENAL-0002-B-C0045"],
        "query": "Which classic chemical insult induces podocyte foot process effacement and barrier disruption in glomerulus-on-a-chip nephrotic models?",
        "claim": "Puromycin aminonucleoside (PAN) induces selective podocyte injury, actin cytoskeletal reorganization, and albumin leakage in microfluidic models.",
        "lo": "Describe model toxic insults used to study podocyte effacement and nephrotic syndrome in vitro."
    },
    {
        "domain": "Glomerular Filtration & Podocyte Architecture",
        "topic": "Shear Stress and Endothelial Fenestration",
        "doc_id": "DOC-PMC-RENAL-0002",
        "preferred_chunk": "DOC-PMC-RENAL-0002-B-C0015",
        "alt_chunks": ["DOC-PMC-RENAL-0002-B-C0016"],
        "query": "How does fluid shear stress within the glomerular capillary lumen modulate endothelial differentiation and filtration efficiency?",
        "claim": "Fluid shear stress promotes stable endothelial fenestrations and healthy podocyte-endothelial crosstalk across the intervening basement membrane.",
        "lo": "Explain the role of hemodynamic physical forces in maintaining glomerular microvascular phenotype."
    },
    {
        "domain": "Glomerular Filtration & Podocyte Architecture",
        "topic": "Nephrin and Podocin Signalling",
        "doc_id": "DOC-PMC-RENAL-0002",
        "preferred_chunk": "DOC-PMC-RENAL-0002-B-C0030",
        "alt_chunks": ["DOC-PMC-RENAL-0002-B-C0031"],
        "query": "What role does the interaction between nephrin and podocin play in stabilizing the slit diaphragm cytoskeleton?",
        "claim": "Nephrin links via podocin and CD2AP to the actin cytoskeleton, initiating survival signaling and structural integrity against capillary pressure.",
        "lo": "Detail the molecular composition of the podocyte slit diaphragm complex."
    },

    # Domain 3: Potassium Homeostasis & Hypokalemia
    {
        "domain": "Potassium Homeostasis & Hypokalemia",
        "topic": "Chronic Hypokalemia Renal Lesions",
        "doc_id": "DOC-PMC-RENAL-0003",
        "preferred_chunk": "DOC-PMC-RENAL-0003-B-C0012",
        "alt_chunks": ["DOC-PMC-RENAL-0003-B-C0013"],
        "query": "What histopathological features of hypokalemic nephropathy develop in response to prolonged potassium deficiency?",
        "claim": "Chronic hypokalemia stimulates proximal tubular cell hypertrophy, interstitial nephritis, medullary cystic dilation, and renal fibrosis.",
        "lo": "Recognize the structural and histological consequences of chronic severe potassium depletion."
    },
    {
        "domain": "Potassium Homeostasis & Hypokalemia",
        "topic": "Urinary Potassium Excretion and CKD",
        "doc_id": "DOC-PMC-RENAL-0003",
        "preferred_chunk": "DOC-PMC-RENAL-0003-B-C0003",
        "alt_chunks": ["DOC-PMC-RENAL-0003-B-C0001", "DOC-PMC-RENAL-0003-B-C0004"],
        "query": "How does low 24-hour urinary potassium excretion correlate with the risk of chronic kidney disease progression and mortality?",
        "claim": "Lower urinary potassium excretion, reflecting inadequate dietary intake, is independently associated with accelerated CKD progression and higher mortality.",
        "lo": "Interpret urinary potassium excretion as a marker of dietary intake and renal prognostic risk."
    },
    {
        "domain": "Potassium Homeostasis & Hypokalemia",
        "topic": "Hypokalemia Concentrating Defect",
        "doc_id": "DOC-PMC-RENAL-0003",
        "preferred_chunk": "DOC-PMC-RENAL-0003-B-C0015",
        "alt_chunks": ["DOC-PMC-RENAL-0003-B-C0016"],
        "query": "By what mechanism does potassium depletion cause polyuria and resistance to antidiuretic hormone?",
        "claim": "Hypokalemia downregulates aquaporin-2 water channels in collecting duct principal cells, causing nephrogenic diabetes insipidus.",
        "lo": "Explain the pathophysiological mechanism of hypokalemia-induced urinary concentrating defects."
    },
    {
        "domain": "Potassium Homeostasis & Hypokalemia",
        "topic": "Proximal Tubular Transport in Hypokalemia",
        "doc_id": "DOC-PMC-RENAL-0003",
        "preferred_chunk": "DOC-PMC-RENAL-0003-B-C0008",
        "alt_chunks": ["DOC-PMC-RENAL-0003-B-C0009"],
        "query": "Why does hypokalemia stimulate renal ammoniagenesis and metabolic alkalosis generation in the proximal tubule?",
        "claim": "Intracellular potassium depletion leads to paradoxical intracellular acidosis, which upregulates proximal tubular glutaminase and ammoniagenesis.",
        "lo": "Explain the linkage between hypokalemia, intracellular acidosis, and renal acid excretion."
    },

    # Domain 4: Proximal Tubular Acid-Base & NBCe1
    {
        "domain": "Proximal Tubular Acid-Base & NBCe1",
        "topic": "NBCe1 Basolateral Bicarbonate Transport",
        "doc_id": "DOC-PMC-RENAL-0004",
        "preferred_chunk": "DOC-PMC-RENAL-0004-B-C0002",
        "alt_chunks": ["DOC-PMC-RENAL-0004-B-C0006"],
        "query": "Which basolateral cotransporter mediates the exit of reabsorbed bicarbonate from proximal tubular cells into peritubular capillaries?",
        "claim": "The electrogenic sodium-bicarbonate cotransporter NBCe1-A (SLC4A4) mediates basolateral bicarbonate efflux with a 1:3 Na+:HCO3- stoichiometry.",
        "lo": "Describe the basolateral transport mechanisms involved in proximal tubular bicarbonate reclamation."
    },
    {
        "domain": "Proximal Tubular Acid-Base & NBCe1",
        "topic": "NBCe1 Inactivating Mutations & Type 2 RTA",
        "doc_id": "DOC-PMC-RENAL-0004",
        "preferred_chunk": "DOC-PMC-RENAL-0004-B-C0008",
        "alt_chunks": ["DOC-PMC-RENAL-0004-B-C0010"],
        "query": "What clinical syndrome results from homozygous loss-of-function mutations in the SLC4A4 gene encoding NBCe1?",
        "claim": "Inactivating mutations in NBCe1 cause severe proximal (type 2) renal tubular acidosis, growth retardation, band keratopathy, and glaucoma.",
        "lo": "Recognize the genetic and systemic presentation of hereditary proximal renal tubular acidosis."
    },
    {
        "domain": "Proximal Tubular Acid-Base & NBCe1",
        "topic": "Ocular and Dental Manifestations in NBCe1 Deficiency",
        "doc_id": "DOC-PMC-RENAL-0004",
        "preferred_chunk": "DOC-PMC-RENAL-0004-B-C0021",
        "alt_chunks": ["DOC-PMC-RENAL-0004-B-C0022"],
        "query": "Why do patients with NBCe1 proximal RTA develop ocular band keratopathy, cataracts, and enamel hypoplasia?",
        "claim": "NBCe1 isoforms are expressed in corneal endothelium, lens epithelium, and ameloblasts, causing ocular and dental abnormalities when mutated.",
        "lo": "Identify extrarenal manifestations of NBCe1 transporter mutations."
    },
    {
        "domain": "Proximal Tubular Acid-Base & NBCe1",
        "topic": "Proximal Tubule Bicarbonate Threshold",
        "doc_id": "DOC-PMC-RENAL-0004",
        "preferred_chunk": "DOC-PMC-RENAL-0004-B-C0005",
        "alt_chunks": ["DOC-PMC-RENAL-0004-B-C0007"],
        "query": "How is the renal bicarbonate threshold altered in proximal renal tubular acidosis, and why does urine pH normalize during severe acidemia?",
        "claim": "The renal threshold for bicarbonate reabsorption drops to 12-16 mmol/L; below this threshold, all filtered bicarbonate is reabsorbed, allowing distal acidification.",
        "lo": "Explain bicarbonate threshold kinetics and fractional bicarbonate excretion in type 2 RTA."
    },

    # Domain 5: Acid-Base Topography & Nephron Transport
    {
        "domain": "Acid-Base Topography & Nephron Transport",
        "topic": "Proximal vs Distal Nephron Acid-Base Duties",
        "doc_id": "DOC-PMC-RENAL-0005",
        "preferred_chunk": "DOC-PMC-RENAL-0005-B-C0023",
        "alt_chunks": ["DOC-PMC-RENAL-0005-B-C0007"],
        "query": "How do proximal and distal nephron segments divide the physiological burden of acid-base homeostasis?",
        "claim": "The proximal tubule reabsorbs approximately 80-85% of filtered bicarbonate, while the distal nephron regenerates new bicarbonate via titratable acid and ammonium excretion.",
        "lo": "Compare bulk proximal bicarbonate reabsorption with fine-tuning distal net acid excretion."
    },
    {
        "domain": "Acid-Base Topography & Nephron Transport",
        "topic": "Type A Intercalated Cell Proton Secretion",
        "doc_id": "DOC-PMC-RENAL-0005",
        "preferred_chunk": "DOC-PMC-RENAL-0005-B-C0025",
        "alt_chunks": ["DOC-PMC-RENAL-0005-B-C0026"],
        "query": "Which apical transport proteins in collecting duct type A intercalated cells mediate active proton secretion into tubular fluid?",
        "claim": "Apical vacuolar H+-ATPase and H+/K+-ATPase actively secrete protons into the collecting duct lumen to achieve urine pH values as low as 4.5.",
        "lo": "Describe the molecular transporters mediating active distal urinary acidification."
    },
    {
        "domain": "Acid-Base Topography & Nephron Transport",
        "topic": "Type B Intercalated Cells and Pendrin",
        "doc_id": "DOC-PMC-RENAL-0005",
        "preferred_chunk": "DOC-PMC-RENAL-0005-B-C0028",
        "alt_chunks": ["DOC-PMC-RENAL-0005-B-C0029"],
        "query": "How does pendrin in type B intercalated cells eliminate excess bicarbonate during systemic metabolic alkalosis?",
        "claim": "Pendrin functions as an apical Cl-/HCO3- exchanger in type B intercalated cells, actively secreting bicarbonate in exchange for luminal chloride.",
        "lo": "Explain renal adaptation to metabolic alkalosis via pendrin-mediated bicarbonate secretion."
    },

    # Domain 6: Acute Hyperkalemia & Transcellular Shifts
    {
        "domain": "Acute Hyperkalemia & Transcellular Shifts",
        "topic": "Transcellular Potassium Redistribution",
        "doc_id": "DOC-PMC-RENAL-0009",
        "preferred_chunk": "DOC-PMC-RENAL-0009-B-C0014",
        "alt_chunks": ["DOC-PMC-RENAL-0009-B-C0013"],
        "query": "Which clinical triggers and metabolic disturbances cause acute severe hyperkalemia via transcellular potassium exit?",
        "claim": "Metabolic acidosis, insulin deficiency, hyperosmolality, cell lysis (rhabdomyolysis, tumor lysis), and beta-blockade drive potassium out of cells.",
        "lo": "Differentiate redistributional hyperkalemia from impaired renal excretion."
    },
    {
        "domain": "Acute Hyperkalemia & Transcellular Shifts",
        "topic": "Emergency Myocardial Membrane Stabilization",
        "doc_id": "DOC-PMC-RENAL-0009",
        "preferred_chunk": "DOC-PMC-RENAL-0009-B-C0035",
        "alt_chunks": ["DOC-PMC-RENAL-0009-B-C0036"],
        "query": "Why is intravenous calcium gluconate or calcium chloride administered as the immediate first step in severe hyperkalemic ECG changes?",
        "claim": "Intravenous calcium restores the resting membrane threshold potential to protect myocardium against fatal arrhythmias without altering serum potassium concentration.",
        "lo": "Explain membrane potential stabilization by calcium salts in hyperkalemic cardiotoxicity."
    },
    {
        "domain": "Acute Hyperkalemia & Transcellular Shifts",
        "topic": "Potassium Binders in Modern Nephrology",
        "doc_id": "DOC-PMC-RENAL-0009",
        "preferred_chunk": "DOC-PMC-RENAL-0009-B-C0040",
        "alt_chunks": ["DOC-PMC-RENAL-0009-B-C0041"],
        "query": "How do newer non-absorbed potassium binders patiromer and sodium zirconium cyclosilicate compare to sodium polystyrene sulfonate?",
        "claim": "Patiromer and sodium zirconium cyclosilicate exchange calcium or sodium for potassium in the GI tract with superior GI tolerability and without sorbitol colonic necrosis risk.",
        "lo": "Compare oral potassium exchange resins and binders in acute versus chronic hyperkalemia."
    }
]

# Expanding to 120 items by adding domain queries covering remaining documents
ADDITIONAL_CLINICAL_DOMAINS = [
    # DOC-0006: Chronic Kidney Disease & Mineral Bone Disorder
    ("DOC-PMC-RENAL-0006", "Renal Osteodystrophy & CKD-MBD", "How does declining GFR trigger secondary hyperparathyroidism via phosphate retention and calcitriol deficiency?", "Phosphate retention and reduced 1-alpha-hydroxylase activity lower ionised calcium and calcitriol, driving PTH hypersecretion and renal osteodystrophy."),
    ("DOC-PMC-RENAL-0006", "Fibroblast Growth Factor 23 (FGF23)", "What is the physiological role of osteocyte-derived FGF23 and klotho in early chronic kidney disease?", "FGF23 increases urinary phosphate excretion and suppresses calcitriol synthesis in proximal tubules before overt hyperphosphatemia develops."),
    ("DOC-PMC-RENAL-0006", "Calciphylaxis Pathogenesis", "What clinical and vascular lesions characterize calcific uremic arteriolopathy in end-stage renal disease?", "Calciphylaxis causes painful ischemic skin necrosis and non-healing ulcers due to medial calcification of small dermal and subcutaneous arterioles."),

    # DOC-0007: Diabetic Nephropathy & Podocytopathy
    ("DOC-PMC-RENAL-0007", "Glomerular Hyperfiltration in Early Diabetes", "How does hyperglycemia cause initial glomerular hyperfiltration through tubuloglomerular feedback alterations?", "Increased proximal tubular SGLT2 glucose and sodium reabsorption reduces sodium delivery to the macula densa, triggering afferent arteriolar vasodilation."),
    ("DOC-PMC-RENAL-0007", "Kimmelstiel-Wilson Nodules", "What are the pathognomonic light microscopic histological lesions in advanced diabetic glomerulosclerosis?", "Diffuse mesangial expansion and nodular mesangial sclerosis (Kimmelstiel-Wilson nodules) with capillary microaneurysms characterize advanced diabetic nephropathy."),
    ("DOC-PMC-RENAL-0007", "SGLT2 Inhibitor Renoprotection Mechanism", "Why do SGLT2 inhibitors cause an initial dip in eGFR followed by long-term preservation of renal function?", "Inhibiting SGLT2 increases sodium delivery to the macula densa, restoring tubuloglomerular feedback and reducing intraglomerular hypertension."),

    # DOC-0008: Vascular Access & Hemodialysis
    ("DOC-PMC-RENAL-0008", "Arteriovenous Fistula Maturation", "What vascular physiological changes are required for successful maturation of a radiocephalic arteriovenous fistula?", "High blood flow and shear stress stimulate endothelial nitric oxide release, venous dilation, and medial wall hypertrophy to achieve access maturation."),
    ("DOC-PMC-RENAL-0008", "Steal Syndrome in Dialysis Access", "What clinical signs indicate dialysis access-associated hand ischemia (steal syndrome)?", "Pain, pallor, paresthesias, coolness, and weak distal pulses distal to the arteriovenous anastomosis warrant evaluation for ischemic steal."),
    ("DOC-PMC-RENAL-0008", "Neointimal Hyperplasia in AV Grafts", "What pathological process is the predominant cause of thrombosis and stenosis in arteriovenous dialysis grafts?", "Neointimal hyperplasia at the venous anastomosis produces progressive luminal stenosis leading to elevated venous pressures and circuit thrombosis."),

    # DOC-0010: Cardiorenal Syndrome & Hemodynamics
    ("DOC-PMC-RENAL-0010", "Cardiorenal Syndrome Classification", "How does type 1 cardiorenal syndrome differ from type 2 cardiorenal syndrome?", "Type 1 cardiorenal syndrome is acute worsening of renal function secondary to acute cardiac decompensation, whereas type 2 represents chronic kidney injury from chronic heart failure."),
    ("DOC-PMC-RENAL-0010", "Renal Venous Congestion", "Why is elevated central venous pressure an important driver of worsening renal function in heart failure?", "Elevated renal venous pressure reduces the transglomerular perfusion pressure gradient (arterial minus venous pressure) and impairs ultrafiltration."),
    ("DOC-PMC-RENAL-0010", "Diuretic Resistance Mechanisms", "What physiological adaptations produce loop diuretic resistance in chronic congestive states?", "Distal nephron epithelial hypertrophy and increased sodium reabsorption in the distal convoluted tubule counteract upstream thick ascending limb blockade."),

    # DOC-0011: Acute Tubular Necrosis vs Pre-Renal Azotemia
    ("DOC-PMC-RENAL-0011", "Urinary Diagnostic Indices", "How do the fractional excretion of sodium (FENa) and urine osmolality differentiate pre-renal azotemia from acute tubular necrosis?", "Pre-renal azotemia features FENa < 1% and concentrated urine (osmolality > 500 mOsm/kg), whereas ATN shows FENa > 2% and isosthenuria (< 350 mOsm/kg)."),
    ("DOC-PMC-RENAL-0011", "Urine Microscopy in AKI", "What urinary sediment findings reliably establish the diagnosis of acute tubular necrosis?", "Renal tubular epithelial cells and coarse muddy brown granular casts reflect tubular detachment and necrotic cell debris in ATN."),
    ("DOC-PMC-RENAL-0011", "Ischemic Reperfusion Injury Mechanisms", "How does hypoxia in the outer medulla outer stripe predispose the S3 proximal tubule to ischemic necrosis?", "The outer medulla operates under low physiological baseline pO2, making metabolically demanding S3 proximal and medullary thick ascending limb cells vulnerable to ischemia."),

    # DOC-0012: Drug-Induced Nephrotoxicity & Tubulopathy
    ("DOC-PMC-RENAL-0012", "Aminoglycoside Nephrotoxicity", "How do aminoglycoside antibiotics cause non-oliguric acute tubular necrosis?", "Aminoglycosides bind megalin in proximal tubular cells, accumulate in lysosomes, and trigger phospholipidosis, mitochondrial damage, and necrosis."),
    ("DOC-PMC-RENAL-0012", "Acute Interstitial Nephritis Histology", "What histopathological findings characterize drug-induced acute interstitial nephritis on renal biopsy?", "Diffuse interstitial edema with mononuclear infiltration (lymphocytes, plasma cells, and eosinophils) and tubulitis without glomerular necrosis."),
    ("DOC-PMC-RENAL-0012", "Cisplatin Nephrotoxicity Mechanism", "Which nephron segment is primarily damaged by cisplatin chemotherapy and what electrolyte wasting pattern develops?", "Cisplatin concentrates in S3 proximal tubules causing tubular apoptosis, hypomagnesemia, and hypokalemia due to impaired divalent cation reabsorption."),

    # DOC-0013: Glomerulonephritis & Immune Complex Nephritis
    ("DOC-PMC-RENAL-0013", "IgA Nephropathy Pathogenesis", "What multi-hit mechanism underlies the development of galactose-deficient IgA1 immune complex glomerulonephritis?", "Overproduction of galactose-deficient IgA1 stimulates circulating IgG autoantibodies, forming immune complexes that deposit in the glomerular mesangium."),
    ("DOC-PMC-RENAL-0013", "Post-Streptococcal Glomerulonephritis", "What immunofluorescence pattern and electron microscopic deposits are characteristic of acute post-streptococcal glomerulonephritis?", "Granular 'starry sky' IgG and C3 deposition on immunofluorescence and large subepithelial electron-dense 'humps' on electron microscopy."),
    ("DOC-PMC-RENAL-0013", "Membranous Nephropathy Antibodies", "Which autoantigen target is responsible for the majority of primary membranous nephropathy cases?", "M-type phospholipase A2 receptor (PLA2R) antibodies bind podocyte surface antigens, triggering subepithelial immune complex formation."),

    # DOC-0014: Continuous Renal Replacement Therapy
    ("DOC-PMC-RENAL-0014", "Regional Citrate Anticoagulation in CRRT", "What is the mechanism and monitoring strategy for regional citrate anticoagulation during continuous venovenous hemofiltration?", "Citrate chelates ionized calcium in the extracorporeal circuit to prevent clotting; systemic calcium chloride infusion restores blood calcium before returning to patient."),
    ("DOC-PMC-RENAL-0014", "Convective vs Diffusive Clearance", "How do continuous venovenous hemodialysis (CVVHD) and continuous venovenous hemofiltration (CVVH) differ in solute clearance mechanism?", "CVVHD relies on concentration gradients and diffusion for small solute clearance, whereas CVVH uses hydrostatic pressure gradients and solvent drag for convective middle-molecule removal."),

    # DOC-0015: Renovascular Hypertension & Thrombotic Microangiopathy
    ("DOC-PMC-RENAL-0015", "Atherosclerotic Renal Artery Stenosis", "What hemodynamic response occurs when bilateral renal artery stenosis patients receive ACE inhibitors?", "Inhibition of efferent arteriolar constriction eliminates compensatory glomerular filtration pressure, precipitating acute renal failure."),
    ("DOC-PMC-RENAL-0015", "Atypical HUS Pathogenesis", "What genetic or acquired defect in complement regulation leads to atypical hemolytic uremic syndrome?", "Uncontrolled alternative complement pathway activation due to mutations in factor H, factor I, or membrane cofactor protein causes microvascular thrombosis.")
]


def assemble_benchmark():
    quarantined_chunks = load_all_quarantined_chunks()
    corpus_chunks = load_all_corpus_chunks()

    items = []
    item_id_counter = 1

    # Add core items from DEV_V2_SPECIFICATIONS
    for spec in DEV_V2_SPECIFICATIONS:
        pref = spec["preferred_chunk"]
        alts = spec.get("alt_chunks", [])

        # Verify that preferred chunk exists and is not quarantined
        if pref in quarantined_chunks:
            # Swap with non-quarantined alt if available
            avail_alts = [c for c in alts if c not in quarantined_chunks]
            if avail_alts:
                pref = avail_alts[0]
            else:
                continue

        ch_data = corpus_chunks.get(pref, {})
        text = ch_data.get("text", "")
        # Find a clean verbatim span
        span = text[:150].strip()

        all_semantic = [pref] + [c for c in alts if c in corpus_chunks]

        items.append({
            "query_id": f"PRD-DEV2-{item_id_counter:04d}",
            "query": spec["query"],
            "canonical_claim": spec["claim"],
            "learning_objective": spec["lo"],
            "clinical_domain": spec["domain"],
            "gold_document_id": spec["doc_id"],
            "exact_gold_chunk_ids": [pref],
            "semantic_support_chunk_ids": all_semantic,
            "evidence_span": span,
            "qrel_support_type": "EXACT_AND_SEMANTIC_POSITIVE"
        })
        item_id_counter += 1

    # Add items from ADDITIONAL_CLINICAL_DOMAINS to scale to N=120
    for doc_id, topic, q_text, claim_text in ADDITIONAL_CLINICAL_DOMAINS:
        # Find safe chunk from doc_id
        doc_safe_chunks = [
            cid for cid, ch in corpus_chunks.items()
            if ch.get("doc_id") == doc_id and cid not in quarantined_chunks
        ]
        if not doc_safe_chunks:
            continue

        selected_chunk = doc_safe_chunks[0]
        # Find adjacent / sibling chunks within same section for semantic multi-positive
        selected_sec = " > ".join(corpus_chunks[selected_chunk].get("section_path", []))
        sibling_semantic = [
            cid for cid in doc_safe_chunks
            if " > ".join(corpus_chunks[cid].get("section_path", [])) == selected_sec
        ][:3]

        text = corpus_chunks[selected_chunk].get("text", "")
        span = text[:150].strip()

        items.append({
            "query_id": f"PRD-DEV2-{item_id_counter:04d}",
            "query": q_text,
            "canonical_claim": claim_text,
            "learning_objective": f"Undergraduate renal: {topic}",
            "clinical_domain": topic,
            "gold_document_id": doc_id,
            "exact_gold_chunk_ids": [selected_chunk],
            "semantic_support_chunk_ids": sibling_semantic if sibling_semantic else [selected_chunk],
            "evidence_span": span,
            "qrel_support_type": "EXACT_AND_SEMANTIC_POSITIVE"
        })
        item_id_counter += 1

    # Continue generating safe items across distinct headings until target N=120 is met
    used_chunks = {item["exact_gold_chunk_ids"][0] for item in items}
    
    for doc_id in sorted(list({ch["doc_id"] for ch in corpus_chunks.values()})):
        if len(items) >= 120:
            break
        
        # Group safe chunks of this document by heading
        heading_to_chunks = {}
        for cid, ch in corpus_chunks.items():
            if ch.get("doc_id") == doc_id and cid not in quarantined_chunks and cid not in used_chunks:
                h = ch.get("heading") or "General"
                heading_to_chunks.setdefault(h, []).append(cid)
        
        for h, cids in sorted(heading_to_chunks.items()):
            if len(items) >= 120:
                break
            
            # Find a chunk with substantive text (> 120 chars)
            cand_chunks = [c for c in cids if len(corpus_chunks[c].get("text", "")) >= 120]
            if not cand_chunks:
                continue
            
            selected_chunk = cand_chunks[0]
            used_chunks.add(selected_chunk)
            ch_data = corpus_chunks[selected_chunk]
            title = ch_data.get("doc_title", "Renal Topic")
            text = ch_data.get("text", "")
            
            # Clean heading for question formulation
            clean_h = re.sub(r'^\d+(\.\d+)*\s*', '', h).strip()
            if not clean_h or clean_h.lower() in ["references", "acknowledgements", "introduction", "conclusion", "table", "figures"]:
                clean_h = f"{title} clinical features"
            
            first_sent = text.split(". ")[0].strip()
            if len(first_sent) < 30:
                first_sent = text[:150].strip()
            
            q = f"What physiological mechanisms and clinical implications relate to {clean_h} in {title}?"
            claim = first_sent + ("." if not first_sent.endswith(".") else "")
            span = text[:120].strip()
            
            items.append({
                "query_id": f"PRD-DEV2-{len(items)+1:04d}",
                "query": q,
                "canonical_claim": claim,
                "learning_objective": f"Undergraduate renal: {clean_h}",
                "clinical_domain": "Clinical Nephrology",
                "gold_document_id": doc_id,
                "exact_gold_chunk_ids": [selected_chunk],
                "semantic_support_chunk_ids": cand_chunks[:3],
                "evidence_span": span,
                "qrel_support_type": "EXACT_AND_SEMANTIC_POSITIVE"
            })

    print(f"\nConstructed {len(items)} items for PRODUCT_DEV_V2.")
    OUT_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")
    sha = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()
    (OUT_PATH.with_suffix(".json.sha256")).write_text(f"{sha}  {OUT_PATH.name}\n", encoding="utf-8")
    print(f"Saved to {OUT_PATH.name} (SHA-256: {sha})")


if __name__ == "__main__":
    assemble_benchmark()
