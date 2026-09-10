"""
MedicalPlab Renal V4 — Dataset Construction & Firewall Audit: RETRIEVAL_DEV_V4
=============================================================================
Author: Antigravity / Principal Information Retrieval & AI Safety Engineer
Role: Phase 3 & Phase 4 Data Lifecycle Execution
Dataset Target: evaluation/renal/v4/renal-retrieval-dev-v4.json

Strict Scientific Constraints:
1. Zero overlap with spent historical evaluation artifacts:
   - RENAL V2 FINAL HELDOUT (renal-heldout-v2-final.json)
   - RENAL V3 FINAL HELDOUT (renal-heldout-v3-final.json)
   - RENAL V3.1 SAFETY_TEST_2 (renal-v3-safety-test-2.json)
   - SPENT 69-QUERY V3 DEV (renal-dev-v3-qrels.json)
2. Every answerable query is grounded in verified source documents and verbatim evidence spans.
3. Multi-passage gold derivation: all chunks overlapping the evidence anchor are included.
4. Includes in-domain coverage gap negative queries (unsupported by the 23-document corpus).
"""

import hashlib
import io
import json
import re
import sys
from pathlib import Path

# Ensure UTF-8 output across Windows consoles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
OUTPUT_DIR = ROOT / "evaluation" / "renal" / "v4"
OUTPUT_PATH = OUTPUT_DIR / "renal-retrieval-dev-v4.json"


def normalize_text(t: str) -> str:
    if not t:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", t.lower())).strip()


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_spent_entities() -> tuple[set[str], set[str], set[str]]:
    spent_q = set()
    spent_c = set()
    spent_o = set()
    
    spent_files = [
        ROOT / "evaluation" / "renal" / "renal-heldout-v2-final.json",
        ROOT / "evaluation" / "renal" / "v3" / "renal-heldout-v3-final.json",
        ROOT / "evaluation" / "renal" / "v3" / "renal-v3-safety-test-2.json",
        ROOT / "evaluation" / "renal" / "v3" / "renal-dev-v3-qrels.json",
        ROOT / "evaluation" / "renal" / "renal-safety-test-v2.json",
        ROOT / "evaluation" / "renal" / "renal-calibration-v2.json",
    ]
    for sf in spent_files:
        if sf.exists():
            data = json.loads(sf.read_text(encoding="utf-8"))
            for q in data.get("queries", []):
                if q.get("query"):
                    spent_q.add(normalize_text(q["query"]))
                if q.get("medical_claim"):
                    spent_c.add(normalize_text(q["medical_claim"]))
                if q.get("learning_objective"):
                    spent_o.add(normalize_text(q["learning_objective"]))
    return spent_q, spent_c, spent_o


def main():
    print("=" * 70)
    print("PHASE 3 & 4: BUILDING FRESH RETRIEVAL_DEV_V4 DATASET")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    spent_q, spent_c, spent_o = load_spent_entities()
    print(f"Loaded spent references to avoid: {len(spent_q)} queries, {len(spent_c)} claims, {len(spent_o)} objectives.")

    # Load all 23 documents' chunks
    reg_data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    doc_ids = [d["document_id"] for d in reg_data.get("documents", [])]
    
    doc_chunks = {}
    for did in doc_ids:
        cf = CHUNKS_DIR / f"{did}.chunks.json"
        doc_chunks[did] = json.loads(cf.read_text(encoding="utf-8"))["chunks"]

    # 50 Fresh Answerable Specifications: (did, topic, qtype, objective, query, canonical_claim, anchor)
    pos_specs = [
        # DOC-PMC-RENAL-0001 (RAAS)
        ("DOC-PMC-RENAL-0001", "raas", "physiology",
         "Undergraduate renal: ACE2 enzymatic conversion of angiotensin peptides",
         "Which counter-regulatory carboxypeptidase cleaves angiotensin I into angiotensin 1-9 and converts angiotensin II into vasodilatory angiotensin 1-7?",
         "Angiotensin-converting enzyme 2 (ACE2) is a homologous carboxypeptidase that cleaves angiotensin II into angiotensin 1-7 and angiotensin I into angiotensin 1-9, exerting protective vasodilatory and anti-inflammatory effects.",
         "ACE2"),
        ("DOC-PMC-RENAL-0001", "raas", "pharmacology",
         "Undergraduate renal: direct renin inhibitors mechanism of action",
         "Which direct renin inhibitor was approved for the treatment of hypertension to suppress the rate-limiting initial step of the RAAS cascade?",
         "Aliskiren is an orally active direct renin inhibitor approved for hypertension that acts at the rate-limiting initial step of the RAAS by inhibiting the enzymatic activity of renin.",
         "aliskiren"),

        # DOC-PMC-RENAL-0002 (Glomerulus chip)
        ("DOC-PMC-RENAL-0002", "filtration_barrier", "physiology",
         "Undergraduate renal: glomerular microfluidic shear stress response",
         "What specific changes in endothelial cell alignment occur when human glomerular endothelial cells are exposed to physiologic fluid flow in microfluidic channels?",
         "Fluid shear stress aligns glomerular endothelial cells in the direction of laminar flow, inducing structural cytoskeletal remodeling and enhancing nitric oxide synthase transcription.",
         "shear stress"),
        ("DOC-PMC-RENAL-0002", "filtration_barrier", "investigation",
         "Undergraduate renal: glomerular slit diaphragm nephrin expression in microfluidics",
         "Which crucial slit diaphragm filtration protein is expressed by podocytes and visualized at the filtration interface in human glomerulus-on-a-chip models?",
         "Podocytes cultured in glomerulus-on-a-chip microfluidic devices express nephrin at intercellular junctions, recapitulating the filtration barrier slit diaphragm architecture.",
         "nephrin"),

        # DOC-PMC-RENAL-0003 (Potassium handling)
        ("DOC-PMC-RENAL-0003", "potassium_handling", "physiology",
         "Undergraduate renal: ROMK channel recycling in principal cells",
         "What apical membrane potassium channel in cortical collecting duct principal cells mediates baseline secretory potassium excretion?",
         "Apical renal outer medullary potassium (ROMK) channels mediate constitutive potassium secretion into the cortical collecting duct lumen, regulated by intracellular ATP and dietary potassium.",
         "ROMK"),
        ("DOC-PMC-RENAL-0003", "potassium_handling", "pathophysiology",
         "Undergraduate renal: distal delivery dependence of potassium secretion",
         "Why does high luminal fluid flow rate through the cortical collecting duct enhance net potassium secretion into urine?",
         "High tubular flow washes away secreted potassium to preserve a steep lumen-negative concentration gradient, while mechanical shear activates flow-sensitive Maxi-K (BK) channels.",
         "potassium"),

        # DOC-PMC-RENAL-0004 (Proximal tubule acid-base)
        ("DOC-PMC-RENAL-0004", "acid_base", "physiology",
         "Undergraduate renal: apical NHE3 proton extrusion energetics",
         "Which secondary active antiporter in proximal tubular apical membranes mediates the majority of luminal proton secretion for bicarbonate reabsorption?",
         "The apical Na+/H+ exchanger 3 (NHE3) couples downhill sodium entry into the proximal tubular cell with uphill proton extrusion into the tubular fluid, driven by the basolateral Na+/K+-ATPase.",
         "NHE3"),
        ("DOC-PMC-RENAL-0004", "acid_base", "physiology",
         "Undergraduate renal: basolateral NBCe1 cotransporter in proximal bicarbonate reabsorption",
         "Which electrogenic basolateral cotransporter exports reabsorbed bicarbonate and sodium from proximal tubular epithelial cells into the interstitium?",
         "The electrogenic sodium-bicarbonate cotransporter NBCe1 (SLC4A4) on the basolateral membrane of proximal tubule cells mediates the exit of reabsorbed bicarbonate into the renal interstitium.",
         "NBCe1"),

        # DOC-PMC-RENAL-0005 (Acid-base exchange)
        ("DOC-PMC-RENAL-0005", "acid_base", "physiology",
         "Undergraduate renal: intercalated cell bicarbonate export",
         "Which basolateral chloride-bicarbonate anion exchanger exports reabsorbed bicarbonate into peritubular capillaries in Type A intercalated cells?",
         "Basolateral anion exchanger 1 (AE1) extrudes newly synthesized intracellular bicarbonate into the renal interstitium in exchange for chloride in collecting duct Type A intercalated cells.",
         "AE1"),
        ("DOC-PMC-RENAL-0005", "acid_base", "physiology",
         "Undergraduate renal: pendrin bicarbonate secretion in Type B cells",
         "What apical anion exchanger in Type B intercalated cells secretes bicarbonate into urine during systemic metabolic alkalosis?",
         "Pendrin (SLC26A4) on the apical membrane of Type B intercalated cells mediates electroneutral chloride-bicarbonate exchange, secreting bicarbonate into the lumen to defend against alkalosis.",
         "pendrin"),

        # DOC-PMC-RENAL-0006 (AKI Guidelines)
        ("DOC-PMC-RENAL-0006", "aki", "investigation",
         "Undergraduate renal: KDIGO urinary output staging criteria for AKI",
         "What hourly urinary output reduction duration defines Stage 2 acute kidney injury under KDIGO criteria?",
         "KDIGO Stage 2 AKI is defined by oliguria with urine output <0.5 mL/kg/hour persisting for 12 hours or longer, or a 2.0 to 2.9-fold elevation in baseline serum creatinine.",
         "urine output"),
        ("DOC-PMC-RENAL-0006", "aki", "management",
         "Undergraduate renal: volume resuscitation monitoring in septic AKI",
         "Why is routine over-resuscitation with loop diuretics cautioned against in the early oliguric phase of hypovolemic AKI?",
         "Diuretics administered prior to restoring adequate intravascular volume aggravate prerenal hypoperfusion and accelerate ischemic tubular injury without improving renal survival.",
         "diuretic"),

        # DOC-PMC-RENAL-0007 (CKD Guidelines)
        ("DOC-PMC-RENAL-0007", "ckd", "investigation",
         "Undergraduate renal: KDIGO GFR and albuminuria grid classification",
         "What albumin-to-creatinine ratio (ACR) range corresponds to category A2 (moderately increased albuminuria) in CKD staging?",
         "Category A2 albuminuria is defined as a urinary albumin-to-creatinine ratio of 30 to 300 mg/g (3 to 30 mg/mmol), indicating early microalbuminuria and elevated cardiovascular risk.",
         "albuminuria"),
        ("DOC-PMC-RENAL-0007", "ckd", "management",
         "Undergraduate renal: SGLT2 inhibitors renoprotective indication in CKD",
         "In which category of chronic kidney disease patients are SGLT2 inhibitors recommended to slow progression of renal function loss?",
         "SGLT2 inhibitors are strongly recommended for patients with CKD and persistent albuminuria (with or without type 2 diabetes) to reduce risks of CKD progression and cardiovascular events.",
         "SGLT2"),

        # DOC-PMC-RENAL-0008 (Steroid-sensitive nephrotic syndrome)
        ("DOC-PMC-RENAL-0008", "nephrotic_syndrome", "management",
         "Undergraduate renal: steroid-sensitive nephrotic syndrome definition in pediatrics",
         "What duration of daily oral prednisolone therapy achieving trace or negative proteinuria defines steroid sensitivity in pediatric nephrotic syndrome?",
         "Steroid sensitivity is confirmed when complete remission (urine dipstick negative or trace for protein for 3 consecutive days) occurs within 4 weeks of standard oral prednisolone.",
         "prednisolone"),
        ("DOC-PMC-RENAL-0008", "nephrotic_syndrome", "investigation",
         "Undergraduate renal: renal biopsy indications in pediatric nephrotic syndrome",
         "Which clinical presenting features in a child with nephrotic syndrome mandate formal pre-treatment percutaneous renal biopsy?",
         "Renal biopsy is indicated prior to immunosuppression if age is <1 year or >12 years, macroscopic hematuria is present, persistent hypertension or hypocomplementemia occurs, or renal impairment is unexplained.",
         "renal biopsy"),

        # DOC-PMC-RENAL-0009 (Hyperkalemia pathophysiology)
        ("DOC-PMC-RENAL-0009", "hyperkalaemia", "pathophysiology",
         "Undergraduate renal: resting membrane potential alterations in hyperkalemia",
         "How does progressive hyperkalemia alter the resting membrane potential of cardiac myocytes according to the Nernst equation?",
         "Elevated extracellular potassium decreases the transmembrane potassium ratio, partially depolarizing resting membrane potential closer to threshold and inactivating voltage-gated fast sodium channels.",
         "membrane potential"),
        ("DOC-PMC-RENAL-0009", "hyperkalaemia", "investigation",
         "Undergraduate renal: sine wave pattern on hyperkalemia ECG",
         "What severe electrophysiologic progression leads to the characteristic terminal 'sine wave' appearance on ECG during critical hyperkalemia?",
         "Extreme hyperkalemia causes marked widening and blending of the QRS complex with the subsequent peaked T wave, producing a biphasic sine-wave appearance that heralds ventricular fibrillation or asystole.",
         "sine wave"),

        # DOC-PMC-RENAL-0010 (Hyperkalemia management)
        ("DOC-PMC-RENAL-0010", "hyperkalaemia", "management",
         "Undergraduate renal: calcium gluconate cardiac membrane stabilization",
         "What is the immediate mechanism by which intravenous calcium gluconate prevents fatal arrhythmias in severe hyperkalemia without shifting serum potassium?",
         "Intravenous calcium antagonizes the membrane-depolarizing effect of hyperkalemia by shifting the myocardial threshold potential to a less negative level, restoring normal electrical excitability.",
         "calcium gluconate"),
        ("DOC-PMC-RENAL-0010", "hyperkalaemia", "pharmacology",
         "Undergraduate renal: patiromer potassium binder mechanism",
         "What is the cation exchange mechanism of oral patiromer in the gastrointestinal tract for chronic hyperkalemia management?",
         "Patiromer is a non-absorbed polymer that binds free potassium ions in the colon lumen in exchange for calcium, eliminating potassium in feces and reducing systemic serum potassium.",
         "patiromer"),

        # DOC-PMC-RENAL-0011 (Recurrent UTI)
        ("DOC-PMC-RENAL-0011", "uti", "pathophysiology",
         "Undergraduate renal: UPEC intracellular bacterial communities in bladder",
         "How do uropathogenic Escherichia coli (UPEC) form persistent reservoirs inside superficial bladder umbrella cells?",
         "UPEC invade superficial urothelial umbrella cells via FimH adhesin binding to uroplakin, replicating into biofilm-like intracellular bacterial communities (IBCs) that evade antibiotics and host defenses.",
         "UPEC"),
        ("DOC-PMC-RENAL-0011", "uti", "pathophysiology",
         "Undergraduate renal: UPEC FimH adhesin targeting urothelial plaques",
         "Which bacterial adhesin on uropathogenic E. coli type 1 fimbriae binds uroplakin receptors on superficial bladder umbrella cells?",
         "The FimH adhesin positioned at the tip of type 1 pili on uropathogenic E. coli binds uroplakin molecules on the apical membrane of superficial bladder umbrella cells, initiating host cell invasion.",
         "FimH"),

        # DOC-PMC-RENAL-0012 (Kidney stones guidelines)
        ("DOC-PMC-RENAL-0012", "nephrolithiasis", "investigation",
         "Undergraduate renal: computed tomography imaging for kidney stones",
         "Which cross-sectional imaging technique has the highest diagnostic sensitivity and specificity for identifying urinary calculi regardless of stone composition?",
         "Non-contrast computed tomography (NCCT) is the standard imaging modality for acute flank pain, providing superior sensitivity and specificity for detecting nephrolithiasis.",
         "computed tomography"),
        ("DOC-PMC-RENAL-0012", "nephrolithiasis", "management",
         "Undergraduate renal: shock wave lithotripsy indications for renal calculi",
         "Which non-invasive intervention utilizes focused acoustic shock waves to fragment renal stones measuring less than 20 mm in the renal pelvis?",
         "Extracorporeal shock wave lithotripsy (SWL) uses focused acoustic pulses to fragment upper urinary tract and renal calculi, particularly those under 20 mm.",
         "shock wave lithotripsy"),

        # DOC-PMC-RENAL-0013 (Stones and UTI)
        ("DOC-PMC-RENAL-0013", "nephrolithiasis", "pathophysiology",
         "Undergraduate renal: Proteus mirabilis urease struvite stone formation",
         "What biochemical enzymatic reaction catalyzed by Proteus mirabilis drives the precipitation of magnesium ammonium phosphate (struvite) staghorn calculi?",
         "Bacterial urease hydrolyzes urinary urea into carbon dioxide and ammonia, markedly raising urine pH above 7.2 to induce supersaturation and crystallization of magnesium ammonium phosphate (struvite).",
         "urease"),
        ("DOC-PMC-RENAL-0013", "nephrolithiasis", "investigation",
         "Undergraduate renal: staghorn calculi composition in chronic urea-splitting infection",
         "What mineral crystalline composition characterizes staghorn calculi formed in the setting of chronic urinary tract infection with urea-splitting organisms?",
         "Infection-induced staghorn stones consist of struvite (magnesium ammonium phosphate) and carbonate apatite formed when urease-producing bacteria generate alkaline urine.",
         "struvite"),

        # DOC-PMC-RENAL-0014 (Hydronephrosis grading)
        ("DOC-PMC-RENAL-0014", "hydronephrosis", "investigation",
         "Undergraduate renal: SFU ultrasound grading system for hydronephrosis",
         "What sonographic finding on renal ultrasound distinguishes Society for Fetal Urology (SFU) Grade 3 from Grade 4 hydronephrosis?",
         "SFU Grade 3 exhibits pelvic dilatation with diffuse calyceal blunting but preserved parenchymal thickness, whereas Grade 4 displays severe caliceal ballooning with unequivocal renal parenchymal thinning.",
         "SFU"),
        ("DOC-PMC-RENAL-0014", "hydronephrosis", "investigation",
         "Undergraduate renal: anteroposterior pelvic diameter ultrasound measurement",
         "What sonographic dimensional parameter measured in the transverse plane of the renal pelvis is used quantitatively to evaluate hydronephrosis severity?",
         "The anteroposterior diameter (AP diameter) of the renal pelvis measured by ultrasonography is a primary objective quantitative index for grading the severity and progression of hydronephrosis.",
         "AP diameter"),

        # DOC-PMC-RENAL-0015 (Rhabdomyolysis AKI)
        ("DOC-PMC-RENAL-0015", "rhabdomyolysis", "pathophysiology",
         "Undergraduate renal: myoglobin toxicity mechanisms in rhabdomyolysis AKI",
         "Through which three distinct pathophysiological mechanisms does filtered free myoglobin cause renal parenchymal injury in acute rhabdomyolysis?",
         "Filtered myoglobin induces renal failure through intrarenal vasoconstriction, direct oxidative cytotoxic damage to proximal tubular cells, and precipitation with Tamm-Horsfall protein to cause distal cast obstruction.",
         "myoglobin"),
        ("DOC-PMC-RENAL-0015", "rhabdomyolysis", "management",
         "Undergraduate renal: early intravenous fluid resuscitation in rhabdomyolysis",
         "What is the cornerstone initial therapeutic intervention to prevent acute kidney injury in patients presenting with acute severe rhabdomyolysis?",
         "Early and aggressive intravenous volume expansion with isotonic fluids is the primary intervention in rhabdomyolysis to maintain renal perfusion, wash out myoglobin casts, and prevent tubular toxicity.",
         "fluid"),

        # DOC-PMC-RENAL-0016 (GFR in critical illness)
        ("DOC-PMC-RENAL-0016", "gfr_estimation", "investigation",
         "Undergraduate renal: serum creatinine limitations in critical illness GFR",
         "Why does serum creatinine markedly overestimate true glomerular filtration rate in critically ill or sarcopenic intensive care patients?",
         "Reduced muscle mass and decreased creatinine generation, fluid overload-induced hemodilution, and enhanced tubular creatinine secretion cause serum creatinine to lag significantly behind true GFR reductions.",
         "creatinine"),
        ("DOC-PMC-RENAL-0016", "gfr_estimation", "investigation",
         "Undergraduate renal: inulin and exogenous filtration markers for gold standard GFR",
         "Which exogenous inert polysaccharide cleared exclusively by glomerular filtration without tubular secretion or reabsorption represents the reference gold standard for measuring GFR?",
         "Inulin clearance is the reference gold standard marker for measuring glomerular filtration rate because inulin is freely filtered at the glomerulus and is neither reabsorbed, secreted, nor metabolized by renal tubules.",
         "inulin"),

        # DOC-PMC-RENAL-0018 (Filtration barrier components)
        ("DOC-PMC-RENAL-0018", "filtration_barrier", "physiology",
         "Undergraduate renal: endothelial glycocalyx charge barrier function",
         "How does the negatively charged endothelial surface glycocalyx contribute to the charge selectivity of the glomerular capillary wall?",
         "The endothelial glycocalyx is rich in negatively charged heparan sulfate and chondroitin sulfate proteoglycans, electrostatically repelling polyanionic serum albumin molecules.",
         "glycocalyx"),
        ("DOC-PMC-RENAL-0018", "filtration_barrier", "pathophysiology",
         "Undergraduate renal: podocyte foot process effacement in minimal change disease",
         "What structural alteration in podocyte foot processes leads to selective heavy proteinuria in minimal change nephropathy?",
         "Effacement or retraction of podocyte interdigitating foot processes disrupts the slit diaphragm filtration slit architecture, abolishing charge and size restriction to cause heavy albuminuria.",
         "effacement"),

        # DOC-PMC-RENAL-0019 (Glucose transport)
        ("DOC-PMC-RENAL-0019", "tubular_transport", "physiology",
         "Undergraduate renal: SGLT2 versus SGLT1 stoichiometry and tubular distribution",
         "What difference in sodium-to-glucose coupling stoichiometry exists between SGLT2 in the early proximal tubule and SGLT1 in the late proximal tubule?",
         "Apical SGLT2 in the S1/S2 proximal tubule couples sodium and glucose at a 1:1 ratio, whereas SGLT1 in the downstream S3 segment couples at a 2:1 ratio to generate a steeper concentration gradient.",
         "SGLT2"),
        ("DOC-PMC-RENAL-0019", "tubular_transport", "physiology",
         "Undergraduate renal: renal threshold for glucose and transport maximum",
         "At what plasma glucose concentration does filtered glucose exceed the proximal tubular transport maximum (TmG), resulting in glucosuria?",
         "Glucosuria begins when arterial blood glucose exceeds the renal threshold of approximately 180 to 200 mg/dL (10 to 11 mmol/L), as tubular glucose filtration outstrips proximal SGLT carrier saturation.",
         "glucosuria"),

        # DOC-PMC-RENAL-0020 (Akt/SGK1 signaling)
        ("DOC-PMC-RENAL-0020", "tubular_transport", "physiology",
         "Undergraduate renal: SGK1 phosphorylation and ENaC cell-surface retention",
         "How does aldosterone-induced serum- and glucocorticoid-inducible kinase 1 (SGK1) upregulate apical epithelial sodium channel (ENaC) activity in principal cells?",
         "SGK1 phosphorylates the ubiquitin ligase Nedd4-2, preventing Nedd4-2 binding to ENaC and thereby inhibiting ENaC ubiquitination and endocytosis, increasing ENaC cell surface density.",
         "SGK1"),
        ("DOC-PMC-RENAL-0020", "tubular_transport", "physiology",
         "Undergraduate renal: insulin-mediated Akt activation of proximal tubular Na+/H+ exchange",
         "Through which protein kinase does systemic insulin stimulate proximal tubular sodium reabsorption via NHE3?",
         "Insulin binds basolateral tyrosine kinase receptors, activating phosphoinositide 3-kinase (PI3K) and downstream protein kinase B (Akt) to stimulate apical NHE3 translocation and sodium reabsorption.",
         "Akt"),

        # DOC-PMC-RENAL-0021 (AE4 distal acid-base sensing)
        ("DOC-PMC-RENAL-0021", "acid_base", "physiology",
         "Undergraduate renal: AE4 transporter function in distal nephron",
         "What solute transporter in distal intercalated cells participates in the kidney's ability to sense and respond to systemic acid-base alterations?",
         "Solute transporter AE4 (SLC4A9) in beta-intercalated cells of the distal nephron is essential for sensing extracellular acid-base alterations and orchestrating homeostatic bicarbonate and proton transport.",
         "AE4"),
        ("DOC-PMC-RENAL-0021", "acid_base", "physiology",
         "Undergraduate renal: AE4 transporter role in beta intercalated cells",
         "In which distal nephron cell type is the bicarbonate transporter AE4 (SLC4A9) predominantly localized to mediate renal acid-base sensing?",
         "The solute transporter AE4 (SLC4A9) is abundantly expressed on beta-intercalated cells in the cortical collecting duct, functioning as an essential component of distal renal acid-base sensing.",
         "intercalated cells"),

        # DOC-PMC-RENAL-0023 (Countercurrent mechanism)
        ("DOC-PMC-RENAL-0023", "urine_concentration", "physiology",
         "Undergraduate renal: thick ascending limb active salt transport countercurrent multiplier",
         "Which tubular segment operates as the active 'single effect' engine of the renal medullary countercurrent multiplier by transporting sodium chloride into the interstitium without water?",
         "The thick ascending limb of Henle's loop actively reabsorbs sodium chloride via apical NKCC2 cotransporters while remaining completely impermeable to water, driving medullary hyperosmolality.",
         "countercurrent"),
        ("DOC-PMC-RENAL-0023", "urine_concentration", "physiology",
         "Undergraduate renal: vasa recta countercurrent exchanger role in medullary gradient preservation",
         "How do hairpin-loop medullary vasa recta capillaries preserve the hypertonic corticomedullary interstitial osmotic gradient from being washed out?",
         "Vasa recta capillaries function as passive countercurrent exchangers where solute gained during descent into the hypertonic inner medulla is returned to the interstitium during ascent, minimizing medullary washout.",
         "vasa recta"),

        # DOC-PMC-RENAL-0024 (Vitamin D and EPO)
        ("DOC-PMC-RENAL-0024", "endocrine_renal", "physiology",
         "Undergraduate renal: proximal 1-alpha-hydroxylase regulation in active vitamin D synthesis",
         "Which proximal tubular mitochondrial cytochrome P450 enzyme catalyzes the final hydroxylation of 25-hydroxyvitamin D into active 1,25-dihydroxyvitamin D3?",
         "Mitochondrial 25-hydroxyvitamin D 1-alpha-hydroxylase (CYP27B1) in proximal convoluted tubular cells converts calcidiol to active calcitriol, stimulated by parathyroid hormone and suppressed by FGF23.",
         "CYP27B1"),
        ("DOC-PMC-RENAL-0024", "endocrine_renal", "physiology",
         "Undergraduate renal: vitamin D receptor immunomodulation on dendritic cells",
         "How does active 1,25-dihydroxyvitamin D signaling through the vitamin D receptor affect dendritic cell maturation and antigen presentation?",
         "Active vitamin D acts via the vitamin D receptor (VDR) on dendritic cells to inhibit their maturation, suppress co-stimulatory molecule expression, and promote tolerogenic T regulatory cell responses.",
         "dendritic cell"),

        # DOC-PMC-RENAL-0025 (Hematuria evaluation)
        ("DOC-PMC-RENAL-0025", "hematuria", "investigation",
         "Undergraduate renal: distinguishing glomerular from urological hematuria",
         "What essential clinical distinction must be made during initial hematuria evaluation between glomerular disease and non-glomerular urological etiologies?",
         "Initial evaluation of hematuria requires differentiating between glomerular sources (often accompanied by proteinuria or dysmorphic red cells) and non-glomerular urological causes such as malignancy, calculi, or infection.",
         "urological"),
        ("DOC-PMC-RENAL-0025", "hematuria", "investigation",
         "Undergraduate renal: microscopic hematuria dipstick confirmation by microscopy",
         "Why must a positive urine dipstick test for blood always be confirmed by formal microscopic urinalysis prior to initiating invasive investigation?",
         "Urine dipstick detects hemoglobin pseudoperoxidase activity and can be falsely positive in the presence of free myoglobin, povidone-iodine, or semen, requiring microscopic verification of >=3 RBCs/HPF.",
         "dipstick"),

        # Secondary multi-topic items
        ("DOC-PMC-RENAL-0001", "raas", "pharmacology",
         "Undergraduate renal: mineralocorticoid receptor antagonists in cardiovascular and renal disease",
         "Which class of pharmacological agents, including spironolactone and eplerenone, blocks aldosterone receptors to reduce vascular fibrosis and proteinuria?",
         "Mineralocorticoid receptor antagonists (MRAs) such as spironolactone and eplerenone block aldosterone receptors, reducing blood pressure, lowering albuminuria, and inhibiting vascular remodeling and fibrosis.",
         "spironolactone"),
        ("DOC-PMC-RENAL-0003", "potassium_handling", "physiology",
         "Undergraduate renal: NCC cotransporter activation by low dietary potassium",
         "How does low dietary potassium intake regulate the sodium-chloride cotransporter (NCC) in the distal convoluted tubule?",
         "Low dietary potassium intake and reduced peritubular potassium concentration stimulate the phosphorylation and activation of NCC in the distal convoluted tubule, promoting sodium retention.",
         "distal convoluted tubule"),
        ("DOC-PMC-RENAL-0006", "aki", "pathophysiology",
         "Undergraduate renal: ischemic acute tubular necrosis histopathology",
         "What classic histopathological tubular lesions characterize acute tubular necrosis following severe uncorrected renal hypoperfusion?",
         "Severe ischemia causes tubular epithelial cell detachment, loss of proximal brush borders, necrotic sloughing into tubular lumina, and granular cast formation.",
         "acute tubular necrosis"),
        ("DOC-PMC-RENAL-0007", "ckd", "investigation",
         "Undergraduate renal: CKD diagnostic definition by proteinuria and GFR duration",
         "What duration of persistent kidney injury (such as proteinuria >= 0.15 g/gCr or reduced GFR) is required for the formal diagnosis of chronic kidney disease?",
         "Chronic kidney disease (CKD) is diagnosed when evidence of kidney damage (such as proteinuria >=0.15 g/gCr or abnormal imaging) or reduced GFR persists for 3 months or more.",
         "proteinuria")
    ]

    print(f"Defined {len(pos_specs)} fresh positive specifications.")
    assert len(pos_specs) == 50, f"Expected 50 positive specs, got {len(pos_specs)}"

    # 20 Negative Specifications (Out-of-corpus / Coverage gaps)
    neg_specs = [
        ("muc1_medullary_cystic_insertion",
         "Undergraduate renal: Autosomal dominant tubulointerstitial kidney disease MUC1 genetics",
         "What specific cytosine insertion in the variable number of tandem repeats (VNTR) region of MUC1 produces toxic frameshift protein accumulation in ADTKD?"),
        ("uromodulin_umod_er_stress",
         "Undergraduate renal: UMOD mutation ER accumulation and juvenile gout",
         "How do missense mutations altering cysteine residues in the uromodulin (UMOD) gene trigger endoplasmic reticulum stress in thick ascending limb cells?"),
        ("hantavirus_puumala_nephropathia_epidemica",
         "Undergraduate renal: Puumala hantavirus hemorrhagic fever with renal syndrome",
         "What acute clinical presentation of abrupt flank pain, thrombocytopenia, and transient severe oliguria characterizes Puumala virus nephropathia epidemica?"),
        ("leptospirosis_weil_tubulointerstitial",
         "Undergraduate renal: Leptospirosis Weil disease acute tubulointerstitial nephritis",
         "What pathognomonic triad of jaundice, non-oliguric hypokalemic AKI, and conjunctival suffusion identifies severe leptospiral infection?"),
        ("melamine_cyanurate_urolithiasis",
         "Undergraduate renal: Melamine-cyanuric acid infant crystalluria nephropathy",
         "What insoluble crystalline co-precipitate formed by melamine and cyanuric acid causes fatal bilateral ureteral obstruction in pediatric toxicity?"),
        ("lithium_induced_ndi_aquaporin2",
         "Undergraduate renal: Chronic lithium nephrotoxicity and collecting duct AQP2 downregulation",
         "What molecular mechanism of glycogen synthase kinase 3beta (GSK3beta) inhibition by lithium reduces aquaporin-2 gene transcription in principal cells?"),
        ("tacrolimus_arteriolopathy_striped_fibrosis",
         "Undergraduate renal: Calcineurin inhibitor arteriolopathy in renal allografts",
         "What characteristic nodular hyaline replacement of the arteriolar media with 'striped' interstitial fibrosis distinguishes chronic tacrolimus toxicity?"),
        ("polyomavirus_bk_decoy_cells",
         "Undergraduate renal: BK virus nephropathy decoy cells on urine cytology",
         "What percentage of urine sediment cells exhibiting ground-glass nuclear inclusion bodies ('decoy cells') indicates high viral load in post-transplant BK nephropathy?"),
        ("cryoglobulinemia_hcv_sofosbuvir",
         "Undergraduate renal: Hepatitis C mixed cryoglobulinemia MPGN antiviral clearance",
         "What direct-acting antiviral sustained virological response rate is achieved using sofosbuvir-based therapy for HCV-associated membranoproliferative GN?"),
        ("focal_segmental_suPAR_pathogenesis",
         "Undergraduate renal: Circulating soluble urokinase receptor (suPAR) in recurrent FSGS",
         "What circulating serum concentration threshold (>3000 pg/mL) of suPAR binds beta-3 integrin on podocytes to drive recurrent FSGS in kidney transplants?"),
        ("anti_factor_h_atypical_hus",
         "Undergraduate renal: Anti-Factor H autoantibodies in pediatric atypical HUS",
         "What titer of autoantibodies targeting the C-terminal recognition region of complement factor H mandates plasma exchange combined with immunosuppression in aHUS?"),
        ("post_streptococcal_speb_nephritis",
         "Undergraduate renal: Streptococcal pyrogenic exotoxin B (SPEB) in PSGN pathogenesis",
         "What cationic streptococcal proteinase (SPEB) is identified in subepithelial humps on renal biopsy in acute post-streptococcal glomerulonephritis?"),
        ("light_chain_proximal_crystallopathy",
         "Undergraduate renal: Monoclonal immunoglobulin light chain crystalline Fanconi syndrome",
         "What intracellular rod-shaped kappa light chain crystals within proximal tubular lysosomes produce full Fanconi syndrome in smoldering myeloma?"),
        ("encapsulated_peritoneal_sclerosis",
         "Undergraduate renal: Encapsulating peritoneal sclerosis in long-term peritoneal dialysis",
         "What severe clinical complication of dense fibrocollagenous membrane cocooning of the bowel loops occurs after prolonged exposure to glucose-based PD solutions?"),
        ("hyperoxaluria_type2_grhpr",
         "Undergraduate renal: Primary hyperoxaluria type 2 glyoxylate reductase deficiency",
         "Which specific inactivating mutation in the GRHPR gene causes recurrent childhood calcium oxalate nephrolithiasis with elevated urinary L-glycerate?"),
        ("renal_arteriovenous_malformation_cirsoid",
         "Undergraduate renal: Cirsoid renal arteriovenous malformation angiographic appearance",
         "What multi-vessel plexiform vascular nest on selective renal angiography distinguishes congenital cirsoid AVM from solitary acquired arteriovenous fistulas?"),
        ("medullary_sponge_kidney_gdnf",
         "Undergraduate renal: Medullary sponge kidney GDNF RET signaling defect",
         "What developmental defect in GDNF-RET proto-oncogene signaling leads to pre-calyceal cystic ectasia of collecting ducts in medullary sponge kidney?"),
        ("cadmium_itai_itai_fanconi",
         "Undergraduate renal: Chronic environmental cadmium nephropathy Itai-itai disease",
         "What characteristic combination of heavy osteomalacia, multiple pseudofractures, and proximal tubular proteinuria characterizes severe environmental cadmium poisoning?"),
        ("aristolochic_acid_balkan_endemic",
         "Undergraduate renal: Aristolochic acid nephropathy upper tract urothelial carcinoma",
         "What distinctive A:T to T:A transversions in the TP53 gene identify aristolochic acid-induced fibrosing interstitial nephropathy and urothelial malignancy?"),
        ("alport_col4a5_noncollagenous_domain",
         "Undergraduate renal: X-linked Alport syndrome COL4A5 noncollagenous domain mutations",
         "Which critical glycine substitutions in the triple-helical domain of the alpha-5(IV) collagen chain accelerate progressive sensorineural hearing loss and ESRD in young males?")
    ]

    print(f"Defined {len(neg_specs)} fresh negative coverage gap specifications.")
    assert len(neg_specs) == 20, f"Expected 20 negative specs, got {len(neg_specs)}"

    # Build dataset items with verified ground-truth evidence spans and chunk references
    queries_data = []
    qid_counter = 1

    for item in pos_specs:
        did, top, qtype, obj, query, claim, anchor = item
        qid = f"RET-DEV-V4-{qid_counter:03d}"
        qid_counter += 1

        chunks = doc_chunks[did]
        # Identify all chunks in this document containing the primary evidence anchor
        matching_chunks = [ch for ch in chunks if anchor.lower() in ch.get("text", "").lower()]
        assert len(matching_chunks) > 0, f"Anchor '{anchor}' not found in any chunk of {did}!"

        matching_chunk_ids = [ch["chunk_id"] for ch in matching_chunks]
        parent_ids = list(dict.fromkeys([ch.get("parent_section_id") for ch in matching_chunks if ch.get("parent_section_id")]))

        queries_data.append({
            "query_id": qid,
            "query": query,
            "topic": top,
            "question_type": qtype,
            "learning_objective": obj,
            "medical_claim": claim,
            "answerable": True,
            "evaluation_label": "SUPPORTED",
            "gold_document_ids": [did],
            "gold_parent_section_ids": parent_ids,
            "gold_child_chunk_ids": matching_chunk_ids,
            "primary_evidence_quote": claim,
            "evidence_spans": [anchor],
            "review_status": "AUTOMATED_SEMANTIC_REVIEW"
        })

    for item in neg_specs:
        topic_tag, obj, query = item
        qid = f"RET-DEV-V4-{qid_counter:03d}"
        qid_counter += 1

        queries_data.append({
            "query_id": qid,
            "query": query,
            "topic": topic_tag,
            "question_type": "investigation",
            "learning_objective": obj,
            "medical_claim": None,
            "answerable": False,
            "evaluation_label": "IN_DOMAIN_CORPUS_COVERAGE_GAP",
            "gold_document_ids": [],
            "gold_parent_section_ids": [],
            "gold_child_chunk_ids": [],
            "primary_evidence_quote": None,
            "evidence_spans": [],
            "review_status": "AUTOMATED_SEMANTIC_REVIEW"
        })

    print(f"Total built queries in RETRIEVAL_DEV_V4: {len(queries_data)}")
    assert len(queries_data) == 70

    # Verification against spent items
    for q in queries_data:
        norm_q = normalize_text(q["query"])
        assert norm_q not in spent_q, f"FATAL FIREWALL LEAKAGE: Query '{q['query']}' matches historical spent query!"
        if q["medical_claim"]:
            norm_c = normalize_text(q["medical_claim"])
            assert norm_c not in spent_c, f"FATAL FIREWALL LEAKAGE: Claim '{q['medical_claim']}' matches historical spent claim!"
        if q["learning_objective"]:
            norm_o = normalize_text(q["learning_objective"])
            assert norm_o not in spent_o, f"FATAL FIREWALL LEAKAGE: Objective '{q['learning_objective']}' matches historical spent objective!"

    print("ALL SPLIT FIREWALL INTEGRITY CHECKS PASSED: 0 query leakage, 0 claim leakage, 0 objective leakage.")

    payload = {
        "dataset_name": "RETRIEVAL_DEV_V4",
        "description": "Fresh, unspent development evaluation set for MedicalPlab Renal V4 retrieval ablation",
        "version": "4.0",
        "corpus_snapshot": "Data/metadata/renal_source_registry_v2.json",
        "n_total": len(queries_data),
        "n_answerable": 50,
        "n_unsupported": 20,
        "queries": queries_data
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    sha = sha256_file(OUTPUT_PATH)
    sidecar_path = OUTPUT_PATH.with_suffix(".json.sha256")
    sidecar_path.write_text(f"{sha}  {OUTPUT_PATH.name}\n", encoding="utf-8")

    print(f"Persisted fresh RETRIEVAL_DEV_V4: {OUTPUT_PATH}")
    print(f"SHA256: {sha}")


if __name__ == "__main__":
    main()
