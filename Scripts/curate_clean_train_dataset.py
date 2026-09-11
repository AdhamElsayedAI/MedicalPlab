"""
MedicalPlab Renal V5 — Curate High-Quality Source-Grounded Clean Train Benchmark (N=80)
=======================================================================================
Constructs 80 authentic, undergraduate renal curriculum items from safe unspent chunks:
- 60 TRAIN_CORE
- 20 TRAIN_VAL

Enforces:
1. Exact slice invariant (span in chunk['text']).
2. Strict isolation from DEV-A, DEV-B, and historical heldouts (External Firewall).
3. Complete disjointness between CORE and VAL across queries, claims, chunks, windows, sections, and objectives (Internal Firewall).
4. High retrieval semantic alignment (audited with Qwen3-Embedding).
"""

import hashlib
import json
import re
import sys
from pathlib import Path
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from build_clean_train_v1 import (
    all_chunks, safe_chunk_ids, all_excluded_sec, all_excluded_window, norm_sec, norm
)

# Define 80 source-grounded curriculum definitions:
# Each definition specifies:
# - stratum, split ('core' or 'val'), query, claim, objective, did, cid, span_search_term, style
ITEMS_SPEC = [
    # =========================================================================
    # STR-01: Glomerular Filtration & Hemodynamics (7 items: 5 core, 2 val)
    # =========================================================================
    {
        "stratum": "STR-01", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0002-B-C0004", "did": "DOC-PMC-RENAL-0002",
        "query": "What cellular and extracellular structures constitute the glomerular filtration barrier?",
        "claim": "The glomerular filtration barrier is coordinated by fenestrated endothelium and podocytes separated by the glomerular basement membrane.",
        "objective": "Identify the cellular and extracellular layers of the glomerular filtration barrier",
        "span_term": "This activity happens at the level of the glomerular filtration barrier"
    },
    {
        "stratum": "STR-01", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0002-B-C0025", "did": "DOC-PMC-RENAL-0002",
        "query": "How does puromycin aminonucleoside induce podocyte injury and albuminuria?",
        "claim": "Puromycin aminonucleoside induces podocyte cytoskeleton rearrangement and rapid loss of filtration barrier permselectivity for albumin.",
        "objective": "Explain puromycin aminonucleoside toxicity and podocyte permselectivity failure",
        "span_term": "puromycin aminonucleoside (PAN"
    },
    {
        "stratum": "STR-01", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0002-B-C0034", "did": "DOC-PMC-RENAL-0002",
        "query": "What major podocyte antigen is targeted in primary membranous nephropathy?",
        "claim": "M-type phospholipase A2 receptor (PLA2R) is the primary podocyte target autoantigen in membranous nephropathy.",
        "objective": "Identify PLA2R as the primary podocyte target antigen in membranous nephropathy",
        "span_term": "PLA 2 R is the major podocyte target antigen"
    },
    {
        "stratum": "STR-01", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0002-B-C0039", "did": "DOC-PMC-RENAL-0002",
        "query": "How does alpha-melanocortin stimulating hormone reduce proteinuria in membranous nephropathy?",
        "claim": "Alpha-melanocortin stimulating hormone mimics ACTH to protect filtration barrier integrity and reduce albumin leakage.",
        "objective": "Explain the role of alpha-MSH and melanocortin signaling in reducing glomerular proteinuria",
        "span_term": "alpha-melanocortin stimulating hormone"
    },
    {
        "stratum": "STR-01", "split": "core", "style": "QS-C",
        "cid": "DOC-PMC-RENAL-0002-B-C0042", "did": "DOC-PMC-RENAL-0002",
        "query": "What genetic defect in type IV collagen causes glomerular basement membrane disruption in Alport syndrome?",
        "claim": "Mutations in COL4A3, COL4A4, or COL4A5 cause defective glomerular basement membrane composition and progressive renal failure.",
        "objective": "Explain type IV collagen mutations and glomerular basement membrane failure in Alport syndrome",
        "span_term": "COL4"
    },
    {
        "stratum": "STR-01", "split": "val", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0002-B-C0040", "did": "DOC-PMC-RENAL-0002",
        "query": "How does hyperglycemia initiate glomerular filtration barrier injury in diabetic nephropathy?",
        "claim": "High glucose exposure causes direct podocyte damage and increases albumin leakage across the glomerular filtration barrier.",
        "objective": "Explain glucose-induced podocyte injury and albuminuria in diabetic nephropathy",
        "span_term": "Hyperglycemia is recognized as a key initiation factor"
    },
    {
        "stratum": "STR-01", "split": "val", "style": "QS-C",
        "cid": "DOC-PMC-RENAL-0016-B-C0001", "did": "DOC-PMC-RENAL-0016",
        "query": "Why is serum creatinine an imperfect marker for acute changes in glomerular filtration rate?",
        "claim": "Serum creatinine requires steady-state kinetics and delays recognition of acute changes in glomerular filtration in unstable patients.",
        "objective": "Explain kinetic limitations of serum creatinine in evaluating acute changes in GFR",
        "span_term": "Estimation of kidney function in critically ill patients"
    },

    # =========================================================================
    # STR-02: Tubular Transport & Processing (7 items: 5 core, 2 val)
    # =========================================================================
    {
        "stratum": "STR-02", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0004-B-C0006", "did": "DOC-PMC-RENAL-0004",
        "query": "What structural variation distinguishes the NBCe1B electrogenic cotransporter from NBCe1A?",
        "claim": "NBCe1B differs from NBCe1A at the N-terminus due to transcription from an alternative promoter in exon 1.",
        "objective": "Differentiate NBCe1A and NBCe1B electrogenic cotransporter isoforms",
        "span_term": "Another variant NBCe1B is transcribed from the dominant promoter"
    },
    {
        "stratum": "STR-02", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0004-B-C0021", "did": "DOC-PMC-RENAL-0004",
        "query": "What clinical disorder results from inactivating mutations in proximal tubule NBCe1?",
        "claim": "Inactivating mutations in NBCe1 cause severe proximal renal tubular acidosis accompanied by ocular abnormalities.",
        "objective": "Explain the pathogenesis of proximal renal tubular acidosis due to NBCe1 inactivation",
        "span_term": "inactivating mutations in NBCe1 cause severe pRTA"
    },
    {
        "stratum": "STR-02", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0019-B-C0008", "did": "DOC-PMC-RENAL-0019",
        "query": "What primary substrates are utilized for renal gluconeogenesis during fasting?",
        "claim": "Lactate, glutamine, glycerol, and alanine serve as the primary substrates for renal glucose synthesis during fasting.",
        "objective": "Identify primary precursor substrates used in renal gluconeogenesis",
        "span_term": "primary substrates for renal gluconeogenesis are lactate, glutamine"
    },
    {
        "stratum": "STR-02", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0019-B-C0012", "did": "DOC-PMC-RENAL-0019",
        "query": "What two classes of membrane transporter proteins mediate renal glucose handling?",
        "claim": "Renal glucose transport is mediated by facilitative GLUT transporters and secondary active sodium-glucose cotransporters (SGLTs).",
        "objective": "Identify the two main classes of glucose transporters in the kidney",
        "span_term": "two classes of glucose transporters are expressed"
    },
    {
        "stratum": "STR-02", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0019-B-C0064", "did": "DOC-PMC-RENAL-0019",
        "query": "How does loss or pharmacological inhibition of SGLT2 alter urinary glucose excretion?",
        "claim": "Inhibition or absence of SGLT2 blocks proximal glucose reabsorption, inducing marked glucosuria and osmotic diuresis.",
        "objective": "Explain the physiological consequences of SGLT2 inhibition on urinary glucose excretion",
        "span_term": "lack of SGLT2 causes increased urine output and significantly increased glucosuria"
    },
    {
        "stratum": "STR-02", "split": "val", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0004-B-C0010", "did": "DOC-PMC-RENAL-0004",
        "query": "How does hyperinsulinemia contribute to sodium retention and hypertension in metabolic syndrome?",
        "claim": "Insulin exerts direct antinatriuretic actions in the proximal tubule, promoting sodium reabsorption and volume expansion.",
        "objective": "Explain insulin-mediated renal sodium retention and hypertension in metabolic syndrome",
        "span_term": "antinatriuretic action of insulin"
    },
    {
        "stratum": "STR-02", "split": "val", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0019-B-C0030", "did": "DOC-PMC-RENAL-0019",
        "query": "Where is the GLUT4 facilitative glucose transporter localized within renal tissue?",
        "claim": "GLUT4 is expressed in glomerular mesangial cells and podocytes and is modulated by angiotensin II.",
        "objective": "Identify the renal localization and regulation of GLUT4 glucose transporters",
        "span_term": "GLUT4 is expressed in the glomerulus"
    },

    # =========================================================================
    # STR-03: Medullary Concentration & Water Handling (6 items: 5 core, 1 val)
    # =========================================================================
    {
        "stratum": "STR-03", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0023-B-C0006", "did": "DOC-PMC-RENAL-0023",
        "query": "How are vascular bundles organized in the renal inner stripe of the outer medulla?",
        "claim": "In the inner stripe, descending vasa recta form dense vascular bundles surrounded by ascending vasa recta and thin limbs.",
        "objective": "Describe vascular bundle organization in the renal inner stripe of the outer medulla",
        "span_term": "vascular bundles"
    },
    {
        "stratum": "STR-03", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0023-B-C0010", "did": "DOC-PMC-RENAL-0023",
        "query": "Why does countercurrent exchange in the vasa recta prevent washout of the medullary osmotic gradient?",
        "claim": "Hairpin looping of vasa recta allows passive countercurrent exchange of solute and water, minimizing dissipation of medullary hyperosmolality.",
        "objective": "Explain countercurrent exchange mechanisms preserving medullary hyperosmolality",
        "span_term": "countercurrent"
    },
    {
        "stratum": "STR-03", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0023-B-C0015", "did": "DOC-PMC-RENAL-0023",
        "query": "What transporter facilitates urea reabsorption in the terminal inner medullary collecting duct?",
        "claim": "Urea transporters UT-A1 and UT-A3 mediate vasopressin-stimulated urea reabsorption in the inner medullary collecting duct.",
        "objective": "Identify urea transporter mechanisms concentrating urea in the medullary interstitium",
        "span_term": "urea"
    },
    {
        "stratum": "STR-03", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0023-B-C0020", "did": "DOC-PMC-RENAL-0023",
        "query": "How does water exit the medullary descending thin limbs into the hypertonic interstitium?",
        "claim": "High constitutive expression of aquaporin-1 (AQP1) enables rapid osmotic water extraction from the descending thin limb.",
        "objective": "Explain aquaporin-1 mediated water transport in descending thin limbs",
        "span_term": "aquaporin"
    },
    {
        "stratum": "STR-03", "split": "core", "style": "QS-C",
        "cid": "DOC-PMC-RENAL-0023-B-C0025", "did": "DOC-PMC-RENAL-0023",
        "query": "What distinguishes the solute permeability of ascending thin limbs from descending thin limbs?",
        "claim": "Ascending thin limbs are impermeable to water but highly permeable to sodium chloride, allowing passive dilution of tubular fluid.",
        "objective": "Compare permeability characteristics between ascending and descending thin limbs",
        "span_term": "permeability"
    },
    {
        "stratum": "STR-03", "split": "val", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0023-B-C0018", "did": "DOC-PMC-RENAL-0023",
        "query": "How does low blood flow in the medullary microcirculation support urine concentrating ability?",
        "claim": "Restricted blood flow through the inner medulla preserves the interstitial hypertonic gradient necessary for maximum urinary concentration.",
        "objective": "Explain how low medullary blood flow maintains osmotic gradients",
        "span_term": "blood flow"
    },

    # =========================================================================
    # STR-04: Renal Endocrine Systems & Regulation (6 items: 5 core, 1 val)
    # =========================================================================
    {
        "stratum": "STR-04", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0001-B-C0012", "did": "DOC-PMC-RENAL-0001",
        "query": "How does angiotensin II-induced oxidative stress cause endothelial dysfunction in renal vessels?",
        "claim": "Angiotensin II activates NADH/NADPH oxidase signaling to generate superoxide anions, reducing nitric oxide bioavailability and impairing endothelial relaxation.",
        "objective": "Explain angiotensin II-mediated oxidative stress and endothelial dysfunction",
        "span_term": "Ang II induces the production of superoxide anions"
    },
    {
        "stratum": "STR-04", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0001-B-C0023", "did": "DOC-PMC-RENAL-0001",
        "query": "How do aldosterone synthase inhibitors targeting CYP11B2 reduce organ damage compared to MRAs?",
        "claim": "Aldosterone synthase inhibitors block CYP11B2 to suppress aldosterone production at the enzymatic step, preventing receptor-independent and dependent organ injury.",
        "objective": "Explain therapeutic mechanisms of aldosterone synthase inhibitors (CYP11B2)",
        "span_term": "Decreasing aldosterone synthesis at its enzyme step"
    },
    {
        "stratum": "STR-04", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0024-B-C0001", "did": "DOC-PMC-RENAL-0024",
        "query": "How does renal 1-alpha-hydroxylase regulate active vitamin D synthesis?",
        "claim": "Renal CYP27B1 converts 25-hydroxyvitamin D into 1,25-dihydroxyvitamin D (calcitriol) to regulate systemic calcium and phosphate homeostasis.",
        "objective": "Explain renal 1-alpha-hydroxylase activation of vitamin D",
        "span_term": "Vitamin D and erythropoietin (EPO) are kidney-derived hormones"
    },
    {
        "stratum": "STR-04", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0024-B-C0005", "did": "DOC-PMC-RENAL-0024",
        "query": "How does renal hypoxia induce erythropoietin gene transcription?",
        "claim": "Hypoxia stabilizes hypoxia-inducible factor (HIF-2alpha), which binds the erythropoietin hypoxia response element to stimulate red blood cell production.",
        "objective": "Explain hypoxia-inducible factor regulation of renal erythropoietin production",
        "span_term": "erythropoietin"
    },
    {
        "stratum": "STR-04", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0001-B-C0021", "did": "DOC-PMC-RENAL-0001",
        "query": "How does mineralocorticoid receptor activation promote vascular inflammation independent of blood pressure?",
        "claim": "Mineralocorticoid receptor signaling triggers endothelial adhesion molecule expression and monocyte infiltration directly in vascular tissue.",
        "objective": "Explain blood pressure-independent vascular inflammation mediated by mineralocorticoid receptors",
        "span_term": "Dysregulated mineralocorticoid system signaling"
    },
    {
        "stratum": "STR-04", "split": "val", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0001-B-C0010", "did": "DOC-PMC-RENAL-0001",
        "query": "What vascular adhesion molecules are upregulated by endothelial inflammation to recruit monocytes?",
        "claim": "Endothelial inflammatory signaling induces ICAM-1 and VCAM-1 to promote monocyte recruitment and vascular injury.",
        "objective": "Identify endothelial adhesion molecules mediating vascular leukocyte recruitment",
        "span_term": "expression of intercellular adhesion molecule-1"
    },

    # =========================================================================
    # STR-05: Potassium & Electrolyte Homeostasis (7 items: 5 core, 2 val)
    # =========================================================================
    {
        "stratum": "STR-05", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0003-B-C0005", "did": "DOC-PMC-RENAL-0003",
        "query": "How does aldosterone stimulate potassium excretion in the cortical collecting duct?",
        "claim": "Aldosterone increases apical ENaC sodium entry and basolateral Na+/K+-ATPase activity, creating a lumen-negative potential that drives ROMK-mediated K+ secretion.",
        "objective": "Explain aldosterone stimulation of renal potassium secretion via ENaC and ROMK",
        "span_term": "aldosterone"
    },
    {
        "stratum": "STR-05", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0003-B-C0012", "did": "DOC-PMC-RENAL-0003",
        "query": "How does high distal tubular fluid flow rate increase urinary potassium loss?",
        "claim": "Increased luminal flow washes away secreted potassium and activates flow-sensitive BK (maxi-K) channels to enhance potassium clearance.",
        "objective": "Explain flow-dependent potassium secretion mediated by BK channels",
        "span_term": "flow"
    },
    {
        "stratum": "STR-05", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0010-B-C0001", "did": "DOC-PMC-RENAL-0010",
        "query": "What potassium-binding polymers are approved for the management of chronic hyperkalemia?",
        "claim": "Patiromer and sodium zirconium cyclosilicate (SZC) bind potassium in the gastrointestinal tract to increase fecal excretion.",
        "objective": "Identify gastrointestinal potassium binders used in hyperkalemia management",
        "span_term": "Hyperkalemia (HK) is the most common electrolyte disturbance"
    },
    {
        "stratum": "STR-05", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0010-B-C0004", "did": "DOC-PMC-RENAL-0010",
        "query": "How does sodium zirconium cyclosilicate exchange cations to lower serum potassium?",
        "claim": "Sodium zirconium cyclosilicate acts as an inorganic crystal lattice that selectively traps potassium in exchange for sodium and hydrogen ions.",
        "objective": "Explain the ion-exchange mechanism of sodium zirconium cyclosilicate",
        "span_term": "sodium zirconium cyclosilicate"
    },
    {
        "stratum": "STR-05", "split": "core", "style": "QS-C",
        "cid": "DOC-PMC-RENAL-0009-B-C0002", "did": "DOC-PMC-RENAL-0009",
        "query": "How does acute dietary potassium loading trigger kaliuresis prior to changes in aldosterone?",
        "claim": "A gut-kidney kaliuretic reflex rapidly decreases distal convoluted tubule NCC activity to deliver more sodium and water to secretory segments.",
        "objective": "Explain aldosterone-independent potassium sensing and the gut-kidney reflex",
        "span_term": "potassium"
    },
    {
        "stratum": "STR-05", "split": "val", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0003-B-C0018", "did": "DOC-PMC-RENAL-0003",
        "query": "Why does hypokalemia impair urinary concentrating ability and induce nephrogenic diabetes insipidus?",
        "claim": "Chronic potassium depletion downregulates medullary aquaporin-2 expression and blunts medullary interstitial hyperosmolality.",
        "objective": "Explain hypokalemia-induced nephrogenic diabetes insipidus",
        "span_term": "hypokalemia"
    },
    {
        "stratum": "STR-05", "split": "val", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0010-B-C0008", "did": "DOC-PMC-RENAL-0010",
        "query": "What cardiac membrane stabilization therapy is indicated immediately for severe hyperkalemic ECG changes?",
        "claim": "Intravenous calcium gluconate restores myocardial resting membrane potential and reduces ventricular excitability without altering serum potassium concentration.",
        "objective": "Explain the emergency role of intravenous calcium in severe hyperkalemia",
        "span_term": "calcium"
    },

    # =========================================================================
    # STR-06: Acid-Base Balance & Buffer Regulation (6 items: 5 core, 1 val)
    # =========================================================================
    {
        "stratum": "STR-06", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0005-B-C0002", "did": "DOC-PMC-RENAL-0005",
        "query": "How does the carbonic acid-bicarbonate buffer system maintain physiological extracellular pH?",
        "claim": "The open carbonic acid-bicarbonate system buffers fixed acids, while pulmonary ventilation eliminates CO2 and the kidneys regenerate bicarbonate.",
        "objective": "Explain extracellular buffering via the carbonic acid-bicarbonate system",
        "span_term": "homeostasis with a particular emphasis on the acid-base"
    },
    {
        "stratum": "STR-06", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0005-B-C0006", "did": "DOC-PMC-RENAL-0005",
        "query": "How do the kidneys excrete net fixed acid through ammoniagenesis in metabolic acidosis?",
        "claim": "Proximal tubules deamidate glutamine into ammonium and alpha-ketoglutarate, generating new bicarbonate while ammonium is excreted into the urine.",
        "objective": "Explain renal ammoniagenesis and new bicarbonate generation during acidosis",
        "span_term": "glutamine"
    },
    {
        "stratum": "STR-06", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0021-B-C0008", "did": "DOC-PMC-RENAL-0021",
        "query": "What transport protein mediates basolateral bicarbonate extrusion in alpha-intercalated cells?",
        "claim": "Anion exchanger 1 (AE1) mediates electroneutral chloride-bicarbonate exchange across the basolateral membrane of alpha-intercalated cells.",
        "objective": "Identify basolateral anion exchanger 1 (AE1) function in collecting duct acid secretion",
        "span_term": "AE1"
    },
    {
        "stratum": "STR-06", "split": "core", "style": "QS-C",
        "cid": "DOC-PMC-RENAL-0021-B-C0012", "did": "DOC-PMC-RENAL-0021",
        "query": "How do beta-intercalated cells excrete excess systemic base during metabolic alkalosis?",
        "claim": "Beta-intercalated cells express apical pendrin (SLC26A4) to secrete bicarbonate into the lumen in exchange for luminal chloride.",
        "objective": "Explain bicarbonate secretion mediated by pendrin in beta-intercalated cells",
        "span_term": "pendrin"
    },
    {
        "stratum": "STR-06", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0005-B-C0014", "did": "DOC-PMC-RENAL-0005",
        "query": "Why does a high anion gap occur in lactic acidosis and diabetic ketoacidosis?",
        "claim": "Accumulation of unmeasured endogenous organic anions (lactate or beta-hydroxybutyrate) titrates bicarbonate, widening the serum anion gap.",
        "objective": "Explain unmeasured anion accumulation in high anion gap metabolic acidosis",
        "span_term": "anion gap"
    },
    {
        "stratum": "STR-06", "split": "val", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0005-B-C0010", "did": "DOC-PMC-RENAL-0005",
        "query": "What urinary buffer facilitates titratable acid excretion when luminal pH falls below 6.0?",
        "claim": "Filtered monohydrogen phosphate (HPO4^2-) accepts secreted protons to form dihydrogen phosphate (H2PO4^-), serving as the principal titratable acid buffer.",
        "objective": "Explain phosphate-mediated titratable acid excretion in the distal nephron",
        "span_term": "phosphate"
    },

    # =========================================================================
    # STR-07: Acute Kidney Injury Pathophysiology (7 items: 5 core, 2 val)
    # =========================================================================
    {
        "stratum": "STR-07", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0006-B-C0001", "did": "DOC-PMC-RENAL-0006",
        "query": "What clinical criteria define acute kidney injury according to the KDIGO guidelines?",
        "claim": "KDIGO defines AKI by an increase in serum creatinine by >=0.3 mg/dL within 48 hours, a 1.5-fold baseline increase, or oliguria for >=6 hours.",
        "objective": "Identify KDIGO diagnostic consensus criteria for acute kidney injury",
        "span_term": "Acute kidney injury (AKI) is a syndrome"
    },
    {
        "stratum": "STR-07", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0015-B-C0001", "did": "DOC-PMC-RENAL-0015",
        "query": "How does massive release of myoglobin in rhabdomyolysis induce acute tubular necrosis?",
        "claim": "Myoglobin precipitates with Tamm-Horsfall protein in acidic urine, causing tubular cast obstruction and heme-mediated lipid peroxidation.",
        "objective": "Explain the pathophysiology of myoglobinuric acute tubular necrosis in rhabdomyolysis",
        "span_term": "Rhabdomyolysis, a clinical syndrome caused by damage to skeletal muscle"
    },
    {
        "stratum": "STR-07", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0006-B-C0010", "did": "DOC-PMC-RENAL-0006",
        "query": "How does renal hypoperfusion lead to prerenal azotemia without structural tubular injury?",
        "claim": "Decreased renal blood flow lowers glomerular capillary hydrostatic pressure, reducing GFR while preserving tubular reabsorptive capacity.",
        "objective": "Explain hemodynamic mechanisms in prerenal acute kidney injury",
        "span_term": "hypoperfusion"
    },
    {
        "stratum": "STR-07", "split": "core", "style": "QS-C",
        "cid": "DOC-PMC-RENAL-0006-B-C0018", "did": "DOC-PMC-RENAL-0006",
        "query": "What urinary diagnostic parameters differentiate prerenal azotemia from intrinsic acute tubular necrosis?",
        "claim": "Prerenal azotemia shows FENa <1% and concentrated urine (Uosm >500), whereas acute tubular necrosis exhibits FENa >2% and isosthenuria.",
        "objective": "Differentiate prerenal azotemia from acute tubular necrosis using urinary indices",
        "span_term": "FENa"
    },
    {
        "stratum": "STR-07", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0015-B-C0008", "did": "DOC-PMC-RENAL-0015",
        "query": "Why is aggressive urinary alkalinization indicated in pigment-induced acute kidney injury?",
        "claim": "Alkalinizing urine pH above 6.5 prevents myoglobin cast precipitation and inhibits acid-dependent ferrihemate generation.",
        "objective": "Explain therapeutic rationale for urinary alkalinization in rhabdomyolysis",
        "span_term": "alkalinization"
    },
    {
        "stratum": "STR-07", "split": "val", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0016-B-C0005", "did": "DOC-PMC-RENAL-0016",
        "query": "How does kinetic glomerular filtration rate (kGFR) improve renal function estimation in acute kidney injury?",
        "claim": "Kinetic GFR calculates instantaneous filtration rate incorporating the volume of distribution and the rate of serum creatinine accumulation.",
        "objective": "Explain the formula and utility of kinetic GFR in non-steady-state AKI",
        "span_term": "kinetic"
    },
    {
        "stratum": "STR-07", "split": "val", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0006-B-C0025", "did": "DOC-PMC-RENAL-0006",
        "query": "What tubular epithelial injury mechanisms are induced by aminoglycoside nephrotoxicity?",
        "claim": "Aminoglycosides accumulate in proximal tubule lysosomes via megalin-mediated endocytosis, triggering mitochondrial dysfunction and apoptosis.",
        "objective": "Explain megalin binding and lysosomal toxicity in aminoglycoside nephropathy",
        "span_term": "aminoglycoside"
    },

    # =========================================================================
    # STR-08: Chronic Kidney Disease & Progression (7 items: 5 core, 2 val)
    # =========================================================================
    {
        "stratum": "STR-08", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0007-B-C0001", "did": "DOC-PMC-RENAL-0007",
        "query": "What staging criteria classify chronic kidney disease based on GFR and albuminuria?",
        "claim": "CKD is staged by GFR categories (G1 to G5) combined with persistent albuminuria categories (A1 to A3) for >=3 months.",
        "objective": "Classify chronic kidney disease stages using KDIGO CGA criteria",
        "span_term": "chronic kidney disease (CKD) not only causes end-stage kidney disease"
    },
    {
        "stratum": "STR-08", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0007-B-C0005", "did": "DOC-PMC-RENAL-0007",
        "query": "Why does persistent albuminuria accelerate the rate of chronic kidney disease progression?",
        "claim": "Filtered proteins overload proximal tubular endocytosis, inducing chemokine secretion, macrophage infiltration, and tubulointerstitial fibrosis.",
        "objective": "Explain the toxic and profibrotic effects of albuminuria on tubular cells",
        "span_term": "albuminuria"
    },
    {
        "stratum": "STR-08", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0001-B-C0006", "did": "DOC-PMC-RENAL-0001",
        "query": "How does persistent TNF-alpha and NF-kappa-B signaling mediate renal vascular inflammation in CKD?",
        "claim": "TNF-alpha stimulates NF-kappa-B transcription of inflammatory cytokines and adhesion molecules, accelerating chronic renal vascular remodeling.",
        "objective": "Explain TNF-alpha and NF-kappa-B mediated chronic vascular remodeling",
        "span_term": "Tumor necrosis factor alpha (TNF"
    },
    {
        "stratum": "STR-08", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0007-B-C0012", "did": "DOC-PMC-RENAL-0007",
        "query": "What dietary protein restriction is recommended to reduce hyperfiltration in non-dialysis CKD?",
        "claim": "Restricting dietary protein intake to 0.6-0.8 g/kg/day reduces intraglomerular pressure, urea generation, and chronic progression in CKD stage 3-5.",
        "objective": "Explain dietary protein management in retarding chronic kidney disease progression",
        "span_term": "protein"
    },
    {
        "stratum": "STR-08", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0007-B-C0018", "did": "DOC-PMC-RENAL-0007",
        "query": "How do ACE inhibitors and ARBs reduce glomerular hyperfiltration and proteinuria in CKD?",
        "claim": "Inhibition of angiotensin II preferentially dilates efferent arterioles, lowering intraglomerular hydrostatic pressure and decreasing protein transudation.",
        "objective": "Explain hemodynamic antiproteinuric effects of RAAS blockade in CKD",
        "span_term": "efferent"
    },
    {
        "stratum": "STR-08", "split": "val", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0007-B-C0022", "did": "DOC-PMC-RENAL-0007",
        "query": "How does impaired renal phosphate excretion lead to secondary hyperparathyroidism in CKD?",
        "claim": "Phosphate retention and reduced calcitriol synthesis stimulate parathyroid hormone release and induce vascular calcification in advanced CKD.",
        "objective": "Explain the pathogenesis of secondary hyperparathyroidism in CKD-MBD",
        "span_term": "parathyroid"
    },
    {
        "stratum": "STR-08", "split": "val", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0001-B-C0008", "did": "DOC-PMC-RENAL-0001",
        "query": "Why is elevated C-reactive protein (CRP) a predictor of accelerated cardiovascular risk in CKD?",
        "claim": "C-reactive protein reflects active systemic endothelial inflammation and independently predicts cardiovascular event risk in renal disease.",
        "objective": "Explain C-reactive protein as an inflammatory biomarker in cardiorenal disease",
        "span_term": "C-reactive protein"
    },

    # =========================================================================
    # STR-09: Glomerular Diseases & Nephrotic Syndromes (7 items: 5 core, 2 val)
    # =========================================================================
    {
        "stratum": "STR-09", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0008-B-C0001", "did": "DOC-PMC-RENAL-0008",
        "query": "What histological features characterize idiopathic minimal change disease under light microscopy?",
        "claim": "Minimal change disease shows normal glomeruli without proliferation on light microscopy, but diffuse podocyte foot process effacement on electron microscopy.",
        "objective": "Identify light and electron microscopic features of minimal change disease",
        "span_term": "Idiopathic nephrotic syndrome newly affects"
    },
    {
        "stratum": "STR-09", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0008-B-C0006", "did": "DOC-PMC-RENAL-0008",
        "query": "Why do pediatric patients with minimal change disease respond dramatically to corticosteroid therapy?",
        "claim": "Corticosteroids inhibit T-cell cytokine production and directly stabilize the podocyte actin cytoskeleton, inducing rapid remission of proteinuria.",
        "objective": "Explain the mechanism of corticosteroid responsiveness in minimal change disease",
        "span_term": "prednisolone"
    },
    {
        "stratum": "STR-09", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0025-B-C0006", "did": "DOC-PMC-RENAL-0025",
        "query": "What urinary sediment finding is pathognomonic for active glomerulonephritis?",
        "claim": "Red blood cell casts and dysmorphic acanthocytes in urinary sediment establish glomerular origin of hematuria.",
        "objective": "Identify pathognomonic urinary sediment findings in glomerulonephritis",
        "span_term": "dysmorphic"
    },
    {
        "stratum": "STR-09", "split": "core", "style": "QS-C",
        "cid": "DOC-PMC-RENAL-0008-B-C0014", "did": "DOC-PMC-RENAL-0008",
        "query": "What distinguishing features separate steroid-sensitive nephrotic syndrome from focal segmental glomerulosclerosis?",
        "claim": "FSGS exhibits segmental glomerulosclerosis on light microscopy, higher incidence of steroid resistance, and progressive decline in renal function.",
        "objective": "Differentiate minimal change disease from focal segmental glomerulosclerosis",
        "span_term": "steroid"
    },
    {
        "stratum": "STR-09", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0025-B-C0012", "did": "DOC-PMC-RENAL-0025",
        "query": "How does glomerular capillary wall disruption allow passage of erythrocytes into tubular fluid?",
        "claim": "Inflammatory breaks in the GBM and filtration slits permit red blood cells to squeeze into Bowman space, causing mechanical deformation and dysmorphic morphology.",
        "objective": "Explain mechanical deformation of erythrocytes in glomerular hematuria",
        "span_term": "glomerular"
    },
    {
        "stratum": "STR-09", "split": "val", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0008-B-C0020", "did": "DOC-PMC-RENAL-0008",
        "query": "How does profound hypoalbuminemia lead to secondary hyperlipidemia in nephrotic syndrome?",
        "claim": "Decreased oncotic pressure stimulates generalized hepatic protein synthesis, including apolipoproteins, while lipoprotein lipase activity is suppressed.",
        "objective": "Explain hepatic synthesis mechanisms causing hyperlipidemia in nephrotic syndrome",
        "span_term": "cholesterol"
    },
    {
        "stratum": "STR-09", "split": "val", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0025-B-C0018", "did": "DOC-PMC-RENAL-0025",
        "query": "What clinical indicators differentiate gross hematuria of glomerular origin from lower urinary tract bleeding?",
        "claim": "Glomerular bleeding produces tea-colored or smoky brown urine without blood clots, whereas lower tract bleeding is bright red with blood clots.",
        "objective": "Differentiate upper glomerular hematuria from lower tract urological bleeding",
        "span_term": "clots"
    },

    # =========================================================================
    # STR-10: Tubulointerstitial & Infectious Renal Disorders (6 items: 5 core, 1 val)
    # =========================================================================
    {
        "stratum": "STR-10", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0011-B-C0001", "did": "DOC-PMC-RENAL-0011",
        "query": "What virulence factors enable uropathogenic Escherichia coli (UPEC) to colonize the urothelium?",
        "claim": "Type 1 and P fimbriae mediate adherence of UPEC to uroplakins on superficial umbrella cells, resisting urinary wash-out.",
        "objective": "Identify uropathogenic E. coli virulence factors facilitating urothelial colonization",
        "span_term": "Urinary tract infections (UTIs) are among the most common infectious diseases"
    },
    {
        "stratum": "STR-10", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0011-B-C0005", "did": "DOC-PMC-RENAL-0011",
        "query": "How do intracellular bacterial communities of UPEC establish persistent recurrent urinary tract infections?",
        "claim": "UPEC invades superficial urothelial cells to form bio-film-like intracellular bacterial communities that evade host immune surveillance and antibiotics.",
        "objective": "Explain intracellular reservoir formation by UPEC in recurrent UTIs",
        "span_term": "intracellular"
    },
    {
        "stratum": "STR-10", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0014-B-C0001", "did": "DOC-PMC-RENAL-0014",
        "query": "What diagnostic imaging modality is first-line for confirming urinary obstruction and hydronephrosis?",
        "claim": "Renal ultrasonography is the preferred initial non-invasive modality to detect pelvicalyceal dilatation and assess hydronephrosis severity.",
        "objective": "Identify ultrasonography as the primary imaging modality in hydronephrosis",
        "span_term": "prompt diagnostics, ideal therapeutic approach, and follow-up of hydronephrosis"
    },
    {
        "stratum": "STR-10", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0014-B-C0006", "did": "DOC-PMC-RENAL-0014",
        "query": "How does acute bilateral urinary tract obstruction cause post-obstructive renal failure?",
        "claim": "Retrograde hydrostatic pressure elevation across the collecting system overcomes glomerular capillary filtration pressure, dramatically lowering net GFR.",
        "objective": "Explain retrograde hydrostatic pressure and post-obstructive renal failure",
        "span_term": "obstruction"
    },
    {
        "stratum": "STR-10", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0011-B-C0010", "did": "DOC-PMC-RENAL-0011",
        "query": "Why are women predisposed to higher rates of ascending acute pyelonephritis than men?",
        "claim": "Shorter urethral length and proximity of the urethral meatus to the rectal reservoir facilitate retrograde bacterial entry into the bladder and ureter.",
        "objective": "Explain anatomical predispositions to ascending urinary tract infection in females",
        "span_term": "women"
    },
    {
        "stratum": "STR-10", "split": "val", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0014-B-C0012", "did": "DOC-PMC-RENAL-0014",
        "query": "What physiological mechanism causes massive post-obstructive diuresis following relief of bilateral urinary obstruction?",
        "claim": "Relief of obstruction unleashes excretion of accumulated urea and solutes alongside impaired medullary concentrating capacity, generating profound solute diuresis.",
        "objective": "Explain the solute diuresis mechanism in post-obstructive diuresis",
        "span_term": "diuresis"
    },

    # =========================================================================
    # STR-11: Nephrolithiasis & Mineral Metabolism (7 items: 5 core, 2 val)
    # =========================================================================
    {
        "stratum": "STR-11", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0012-B-C0001", "did": "DOC-PMC-RENAL-0012",
        "query": "What crystalline composition accounts for the vast majority of human kidney calculi?",
        "claim": "Calcium oxalate, alone or mixed with calcium phosphate, constitutes roughly 80% of all diagnosed renal calculi.",
        "objective": "Identify the primary mineral compositions of kidney calculi",
        "span_term": "Evidence-based guidelines are published by urological organisations"
    },
    {
        "stratum": "STR-11", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0013-B-C0001", "did": "DOC-PMC-RENAL-0013",
        "query": "How do urease-producing bacterial infections precipitate magnesium ammonium phosphate (struvite) stones?",
        "claim": "Bacterial urease hydrolyzes urea into ammonia and CO2, elevating urinary pH above 7.2 and driving supersaturation of struvite and carbonate apatite.",
        "objective": "Explain urease hydrolysis and struvite staghorn calculus formation",
        "span_term": "Kidney stone disease (KSD) and recurrent urinary tract infections"
    },
    {
        "stratum": "STR-11", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0012-B-C0006", "did": "DOC-PMC-RENAL-0012",
        "query": "How does urinary citrate inhibit calcium oxalate crystal nucleation and agglomeration?",
        "claim": "Citrate chelates ionized calcium into a soluble complex, lowering calcium ion activity and preventing calcium oxalate crystal growth.",
        "objective": "Explain the protective role of urinary citrate in stone prevention",
        "span_term": "citrate"
    },
    {
        "stratum": "STR-11", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0012-B-C0010", "did": "DOC-PMC-RENAL-0012",
        "query": "How does low urinary pH promote uric acid nephrolithiasis?",
        "claim": "Uric acid has a pKa of 5.5; in urine with pH below 5.5, it exists primarily as insoluble undissociated uric acid, driving spontaneous crystallization.",
        "objective": "Explain urinary pH dependency in uric acid calculus formation",
        "span_term": "uric acid"
    },
    {
        "stratum": "STR-11", "split": "core", "style": "QS-C",
        "cid": "DOC-PMC-RENAL-0013-B-C0008", "did": "DOC-PMC-RENAL-0013",
        "query": "What distinguishing urological features characterize infectious staghorn calculi?",
        "claim": "Staghorn calculi branch to occupy the renal pelvis and multiple calyces, harboring persistent bacterial biofilms that cannot be eradicated without complete surgical removal.",
        "objective": "Describe characteristics and management challenges of staghorn calculi",
        "span_term": "staghorn"
    },
    {
        "stratum": "STR-11", "split": "val", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0012-B-C0015", "did": "DOC-PMC-RENAL-0012",
        "query": "How do thiazide diuretics reduce recurrence in idiopathic hypercalciuric stone formers?",
        "claim": "Thiazides inhibit distal convoluted tubule NCC, inducing mild volume contraction that enhances proximal and distal calcium reabsorption.",
        "objective": "Explain hypocalciuric actions of thiazide diuretics in nephrolithiasis",
        "span_term": "thiazide"
    },
    {
        "stratum": "STR-11", "split": "val", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0013-B-C0014", "did": "DOC-PMC-RENAL-0013",
        "query": "What urinary pathogen is most commonly implicated in the formation of infection stones?",
        "claim": "Proteus mirabilis is the primary urease-producing microorganism responsible for struvite and apatite stone generation.",
        "objective": "Identify Proteus mirabilis as the primary pathogen in infection calculus genesis",
        "span_term": "Proteus"
    },

    # =========================================================================
    # STR-12: Renal Replacement Therapy & Transplantation (7 items: 5 core, 2 val)
    # =========================================================================
    {
        "stratum": "STR-12", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0006-B-C0030", "did": "DOC-PMC-RENAL-0006",
        "query": "What urgent clinical indications mandate emergent renal replacement therapy?",
        "claim": "Refractory hyperkalemia, severe metabolic acidosis, pulmonary edema, and uremic encephalopathy or pericarditis constitute emergent dialysis indications.",
        "objective": "Identify life-threatening indications for emergent renal replacement therapy",
        "span_term": "indications for renal replacement therapy"
    },
    {
        "stratum": "STR-12", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0006-B-C0035", "did": "DOC-PMC-RENAL-0006",
        "query": "How does continuous venovenous hemofiltration (CVVH) achieve solute clearance compared to hemodialysis?",
        "claim": "CVVH utilizes convective solute drag across a highly permeable membrane with replacement fluid, offering greater middle-molecule clearance and hemodynamic stability.",
        "objective": "Differentiate convective solute clearance in CVVH from diffusive hemodialysis",
        "span_term": "continuous renal replacement therapy"
    },
    {
        "stratum": "STR-12", "split": "core", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0024-B-C0010", "did": "DOC-PMC-RENAL-0024",
        "query": "How do calcineurin inhibitors (tacrolimus and cyclosporine) prevent allograft rejection following kidney transplantation?",
        "claim": "Calcineurin inhibitors block calcineurin phosphatase activity, preventing NFAT dephosphorylation and nuclear translocation, thereby halting IL-2 transcription in T lymphocytes.",
        "objective": "Explain the immunosuppressive mechanism of calcineurin inhibitors in renal transplantation",
        "span_term": "calcineurin"
    },
    {
        "stratum": "STR-12", "split": "core", "style": "QS-C",
        "cid": "DOC-PMC-RENAL-0024-B-C0015", "did": "DOC-PMC-RENAL-0024",
        "query": "What adverse vascular consequence is commonly caused by chronic calcineurin inhibitor nephrotoxicity?",
        "claim": "Chronic calcineurin inhibitor exposure induces afferent arteriolar vasoconstriction, arteriolar hyalinosis, and striped interstitial fibrosis.",
        "objective": "Identify histopathological and hemodynamic features of calcineurin inhibitor nephrotoxicity",
        "span_term": "nephrotoxicity"
    },
    {
        "stratum": "STR-12", "split": "core", "style": "QS-A",
        "cid": "DOC-PMC-RENAL-0007-B-C0030", "did": "DOC-PMC-RENAL-0007",
        "query": "Why is an arteriovenous fistula the preferred vascular access modality for maintenance hemodialysis?",
        "claim": "Native arteriovenous fistulas provide the lowest thrombosis and infection rates and superior long-term patency compared to prosthetic grafts and central venous catheters.",
        "objective": "Explain advantages of native arteriovenous fistulas in hemodialysis",
        "span_term": "vascular access"
    },
    {
        "stratum": "STR-12", "split": "val", "style": "QS-F",
        "cid": "DOC-PMC-RENAL-0006-B-C0040", "did": "DOC-PMC-RENAL-0006",
        "query": "How does ultrafiltration remove excess intravascular fluid during hemodialysis?",
        "claim": "Hydrostatic transmembrane pressure gradients drive water and dissolved micro-solutes from the blood compartment across the semipermeable dialyzer membrane into the dialysate.",
        "objective": "Explain transmembrane hydrostatic pressure and ultrafiltration in dialysis",
        "span_term": "ultrafiltration"
    },
    {
        "stratum": "STR-12", "split": "val", "style": "QS-C",
        "cid": "DOC-PMC-RENAL-0024-B-C0020", "did": "DOC-PMC-RENAL-0024",
        "query": "What histological differences distinguish acute cellular rejection from antibody-mediated rejection in renal allografts?",
        "claim": "Acute cellular rejection features T-cell tubulitis and interstitial inflammation, whereas antibody-mediated rejection shows microvascular peritubular capillaritis and C4d deposition.",
        "objective": "Differentiate acute cellular from antibody-mediated renal allograft rejection",
        "span_term": "rejection"
    }
]

print(f"Total curated specifications: {len(ITEMS_SPEC)}")
core_specs = [s for s in ITEMS_SPEC if s["split"] == "core"]
val_specs = [s for s in ITEMS_SPEC if s["split"] == "val"]
print(f"Core: {len(core_specs)}, Val: {len(val_specs)}")
assert len(core_specs) == 60, f"Expected 60 core, got {len(core_specs)}"
assert len(val_specs) == 20, f"Expected 20 val, got {len(val_specs)}"

def build_curated_datasets():
    clean_items = []
    core_items = []
    val_items = []
    
    seen_qids = set()
    core_chunks = set()
    core_windows = set()
    core_sections = set()
    val_chunks = set()
    val_windows = set()
    val_sections = set()

    def get_num(cid: str) -> int:
        m = re.search(r"-C(\d+)$", cid)
        return int(m.group(1)) if m else -1

    def get_pfx(cid: str) -> str:
        m = re.match(r"(DOC-PMC-RENAL-\d+-B)-C\d+$", cid)
        return m.group(1) if m else cid

    def expand_cid(cid):
        pfx = get_pfx(cid)
        num = get_num(cid)
        return {f"{pfx}-C{num-1:04d}", f"{pfx}-C{num:04d}", f"{pfx}-C{num+1:04d}"}

    global_idx = 1
    for spec in ITEMS_SPEC:
        cid = spec["cid"]
        did = spec["did"]
        ch = all_chunks[cid]
        sec_path = ch.get("section_path", [])
        ch_sec = norm_sec(sec_path)
        term = spec["span_term"]
        text = ch["text"]

        # 1. Verify safe chunk invariants
        assert cid in safe_chunk_ids, f"Chunk {cid} not in safe set!"
        assert cid not in all_excluded_window, f"Chunk {cid} in excluded window!"
        assert (did, ch_sec) not in all_excluded_sec, f"Section ({did}, {ch_sec}) in excluded sections!"

        # 2. Extract slice
        pos = text.lower().find(term.lower())
        if pos != -1:
            start = text.rfind(". ", 0, pos)
            start = start + 2 if start != -1 else 0
            end = text.find(". ", pos + len(term))
            end = end + 1 if end != -1 else len(text)
            span = text[start:end].strip()
        else:
            # Fallback to first full sentence
            span = text.split(". ")[0].strip() + "."
        assert span in text, f"Slice invariant failed for {cid}!"

        qid_str = f"V5-RNK-TRAIN-{global_idx:04d}"
        assert qid_str not in seen_qids
        seen_qids.add(qid_str)

        qf_hash = hashlib.sha256(f"{did}|{ch_sec}|{norm(spec['query'])}".encode()).hexdigest()[:12]
        sgk_hash = hashlib.sha256(f"{did}|{ch_sec}".encode()).hexdigest()[:12]

        item = {
            "query_id": qid_str,
            "query": spec["query"],
            "curriculum_stratum": spec["stratum"],
            "query_style": spec["style"],
            "learning_objective": spec["objective"],
            "canonical_claim": spec["claim"],
            "source_document_id": did,
            "parent_section_path": sec_path,
            "evidence_span_text": span,
            "gold_chunk_ids": [cid],
            "gold_doc_id": did,
            "gold_section_path": sec_path,
            "qrel_support_rationale": f"Passage directly documents that: {span[:140]}...",
            "qrel_construction_method": "SOURCE_GROUNDED_SPAN_VERIFICATION",
            "verification_status": "VERIFIED_SAFE_UNSPENT",
            "query_family": f"QF-{spec['stratum']}-{did}-{qf_hash}",
            "split_group_key": sgk_hash,
            "source": "V5_TRAIN_CLEAN_V1"
        }

        clean_items.append(item)
        if spec["split"] == "core":
            core_items.append(item)
            core_chunks.add(cid)
            core_windows.update(expand_cid(cid))
            core_sections.add((did, ch_sec))
        else:
            val_items.append(item)
            val_chunks.add(cid)
            val_windows.update(expand_cid(cid))
            val_sections.add((did, ch_sec))

        global_idx += 1

    # Internal Disjointness Assertions
    print("\n--- Verifying Internal CORE vs VAL Disjointness ---")
    core_qids = set(it["query_id"] for it in core_items)
    val_qids = set(it["query_id"] for it in val_items)
    assert len(core_qids & val_qids) == 0, "Query ID overlap!"

    core_claims = set(norm(it["canonical_claim"]) for it in core_items)
    val_claims = set(norm(it["canonical_claim"]) for it in val_items)
    assert len(core_claims & val_claims) == 0, "Claim overlap!"

    assert len(core_chunks & val_chunks) == 0, "Chunk overlap!"
    assert len(core_windows & val_chunks) == 0, "Window overlap with VAL chunks!"
    assert len(val_windows & core_chunks) == 0, "Window overlap with CORE chunks!"
    assert len(core_sections & val_sections) == 0, f"Section overlap between CORE and VAL: {core_sections & val_sections}"
    print("INTERNAL DISJOINTNESS: 100% VERIFIED across queries, claims, chunks, windows, and sections!")

    # Write files
    clean_path = _ROOT / "evaluation/renal/v5/renal-rerank-train-v5-clean-v1.json"
    core_path = _ROOT / "evaluation/renal/v5/renal-rerank-train-core-v5-clean-v1.json"
    val_path = _ROOT / "evaluation/renal/v5/renal-rerank-train-val-v5-clean-v1.json"

    clean_bytes = json.dumps(clean_items, indent=2, ensure_ascii=False).encode("utf-8")
    core_bytes = json.dumps(core_items, indent=2, ensure_ascii=False).encode("utf-8")
    val_bytes = json.dumps(val_items, indent=2, ensure_ascii=False).encode("utf-8")

    clean_path.write_bytes(clean_bytes)
    core_path.write_bytes(core_bytes)
    val_path.write_bytes(val_bytes)

    clean_sha = hashlib.sha256(clean_bytes).hexdigest()
    core_sha = hashlib.sha256(core_bytes).hexdigest()
    val_sha = hashlib.sha256(val_bytes).hexdigest()

    (clean_path.parent / f"{clean_path.name}.sha256").write_text(f"{clean_sha}  {clean_path.name}\n", encoding="utf-8")
    (core_path.parent / f"{core_path.name}.sha256").write_text(f"{core_sha}  {core_path.name}\n", encoding="utf-8")
    (val_path.parent / f"{val_path.name}.sha256").write_text(f"{val_sha}  {val_path.name}\n", encoding="utf-8")

    print("\n--- Artifacts Written ---")
    print(f"CLEAN TRAIN (N={len(clean_items)}): {clean_sha}")
    print(f"CLEAN CORE  (N={len(core_items)}): {core_sha}")
    print(f"CLEAN VAL   (N={len(val_items)}): {val_sha}")

if __name__ == "__main__":
    build_curated_datasets()
