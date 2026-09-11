"""
Candidate Clean Train Items Data (N=80) — Part 1: STR-01 to STR-04
==================================================================
STR-01: 5 CORE, 2 VAL (7)
STR-02: 5 CORE, 2 VAL (7)
STR-03: 5 CORE, 1 VAL (6)
STR-04: 5 CORE, 1 VAL (6)
Total = 26 items.
"""

CLEAN_ITEMS_DATA_P1 = [
    # --------------------------------------------------------------------------
    # STR-01: Glomerular Biology & Podocytes (DOC-PMC-RENAL-0002)
    # --------------------------------------------------------------------------
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0004",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-01",
        "split": "core",
        "query": "What is the primary early pathological hallmark of chronic kidney disease (CKD) affecting the glomeruli?",
        "span": "a common early pathologic hallmark of chronic kidney disease (CKD) is decreased glomerular filtration and loss of functional glomeruli",
        "claim": "A common early pathologic hallmark of chronic kidney disease is decreased glomerular filtration and loss of functional glomeruli.",
        "obj": "Understand early pathological hallmarks and functional decline in chronic kidney disease glomeruli",
        "rationale": "Directly identifies loss of functional glomeruli and reduced filtration as early CKD hallmarks."
    },
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0009",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-01",
        "split": "core",
        "query": "What cellular sources are utilized to obtain human podocytes for in vitro kidney research models?",
        "span": "primary podocytes (hpPOD); obtained from discarded kidneys harvested from patients with non-nephrological cause of death, thus the cells were healthy; (2) immortalized podocytes (hiPOD) considered for many years the gold standard for in vitro cultures",
        "claim": "Human podocytes for in vitro research are isolated from discarded healthy kidneys, immortalized lines, and progenitor sources.",
        "obj": "Identify human podocyte cellular sources and isolation models for renal research",
        "rationale": "Explains the derivation and characteristics of primary and immortalized human podocytes."
    },
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0012",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-01",
        "split": "core",
        "query": "Which specific endothelial surface markers and receptors characterize the fenestrated human glomerular endothelial cells (hGEC)?",
        "span": "Primary hGEC, isolated from the same kidneys from which hpPOD were derived, were negative for podocyte markers (WT1, nephrin) and positive for CD31 and vascular endothelial growth factor receptor 2 (VEGFR2",
        "claim": "Human glomerular endothelial cells lack podocyte markers WT1 and nephrin but express endothelial markers CD31 and VEGFR2.",
        "obj": "Distinguish glomerular endothelial cell surface markers and fenestration characteristics from podocyte markers",
        "rationale": "Specifies phenotypic markers distinguishing glomerular endothelium from podocytes."
    },
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0044",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-01",
        "split": "core",
        "query": "How does an intact glomerular filtration barrier selectively handle inulin compared to serum albumin?",
        "span": "demonstrated the filtration of inulin and the retention of albumin within the GOAC, thus resembling the human GFB",
        "claim": "The glomerular filtration barrier permits the filtration of inulin while selectively retaining serum albumin.",
        "obj": "Describe the permselectivity of the glomerular filtration barrier regarding inulin and albumin",
        "rationale": "Confirms physiologic permselectivity with free inulin filtration and albumin retention."
    },
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0045",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-01",
        "split": "core",
        "query": "Which chemical agent and model insults are utilized to evaluate glomerular filtration barrier injury in glomerulus-on-a-chip systems?",
        "span": "responded to chemical injury with PAN, glucose-induced damage, and nephrotoxic serum from MN patients similarly to in vivo glomeruli",
        "claim": "Glomerular filtration barrier models reproduce in vivo disease features by responding to chemical injury with PAN, glucose damage, and nephrotoxic membranous nephropathy sera.",
        "obj": "Identify experimental injury agents including PAN and nephrotoxic sera used to model glomerular barrier disruption",
        "rationale": "Demonstrates barrier disruption response to chemical injury with PAN and nephrotoxic sera."
    },
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0022",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-01",
        "split": "val",
        "query": "What functional threshold of albumin retention efficiency defines acceptable permselectivity in glomerular microfluidic barrier systems?",
        "span": "corresponding to a 15% loss of efficiency in retaining albumin) represents the threshold chosen as lower acceptable performance",
        "claim": "A 15% loss of efficiency in retaining albumin serves as the threshold for acceptable baseline glomerular permselectivity.",
        "obj": "Evaluate functional permselectivity thresholds for albumin retention in glomerular filtration models",
        "rationale": "Defines quantitative permselectivity limits for albumin barrier retention."
    },
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0024",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-01",
        "split": "val",
        "query": "Why do static transwell podocyte-endothelial co-cultures fail to establish an effective semi-permeable barrier compared to dynamic microfluidic chips?",
        "span": "all transwells exhibited a significant albumin leakage thus suggesting that, under the same conditions, this platform cannot perform as efficiently",
        "claim": "Static transwell podocyte-endothelial co-cultures display significant albumin leakage, failing to replicate physiologic filtration barrier permselectivity.",
        "obj": "Compare dynamic versus static culture limitations in modeling glomerular permselectivity",
        "rationale": "Demonstrates albumin leakage across static transwell filters lacking dynamic fluid shear."
    },

    # --------------------------------------------------------------------------
    # STR-02: Proximal Tubule Transport & Acid-Base (DOC-PMC-RENAL-0004)
    # --------------------------------------------------------------------------
    {
        "cid": "DOC-PMC-RENAL-0004-B-C0006",
        "did": "DOC-PMC-RENAL-0004",
        "strat": "STR-02",
        "split": "core",
        "query": "Which electrogenic sodium bicarbonate cotransporter variant mediates basolateral bicarbonate absorption in the renal proximal tubule?",
        "span": "NBCe1A is transcribed from the alternative promoter in exon 1 and abundantly expressed in the basolateral membrane of PTs, representing the major bicarbonate exit pathway in this nephron segment",
        "claim": "NBCe1A is abundantly expressed on the basolateral membrane of renal proximal tubules, mediating primary bicarbonate exit.",
        "obj": "Identify the electrogenic sodium bicarbonate cotransporter isoform responsible for proximal tubular bicarbonate reabsorption",
        "rationale": "Documents NBCe1A as the predominant basolateral bicarbonate cotransporter in proximal tubules."
    },
    {
        "cid": "DOC-PMC-RENAL-0004-B-C0008",
        "did": "DOC-PMC-RENAL-0004",
        "strat": "STR-02",
        "split": "core",
        "query": "What metabolic acid-base disorder develops from genetic inactivating mutations in the proximal tubular cotransporter NBCe1?",
        "span": "Two types of NBCe1-deficient mice, NBCe1-KO mice [ 25 ] and W516X-knockin mice [ 26 ], present with very severe acidemia due to pRTA and die within 30 days",
        "claim": "Inactivating mutations in NBCe1 produce severe acidemia due to proximal renal tubular acidosis (pRTA).",
        "obj": "Understand the pathogenesis of proximal renal tubular acidosis caused by NBCe1 mutations",
        "rationale": "Shows severe acidemia and proximal RTA resulting from NBCe1 gene inactivation."
    },
    {
        "cid": "DOC-PMC-RENAL-0004-B-C0010",
        "did": "DOC-PMC-RENAL-0004",
        "strat": "STR-02",
        "split": "core",
        "query": "Through what renal tubular mechanism does chronic hyperinsulinemia contribute to the pathogenesis of hypertension in metabolic syndrome?",
        "span": "hyperinsulinemia-induced hypertension seems to be an attractive hypothesis in view of the antinatriuretic action of insulin",
        "claim": "Hyperinsulinemia contributes to hypertension in metabolic syndrome through its antinatriuretic effect promoting renal sodium retention.",
        "obj": "Explain the antinatriuretic action of insulin and its role in obesity-associated hypertension",
        "rationale": "Explains how insulin antinatriuresis in tubules drives sodium retention and blood pressure elevation."
    },
    {
        "cid": "DOC-PMC-RENAL-0004-B-C0012",
        "did": "DOC-PMC-RENAL-0004",
        "strat": "STR-02",
        "split": "core",
        "query": "What is the functional difference between IRS1 and IRS2 in mediating tissue-specific insulin signaling and resistance states?",
        "span": "The two major substrates IRS1 and IRS2 may mediate distinct pathways in insulin signaling, and they are not functionally interchangeable in many insulin-sensitive tissues",
        "claim": "IRS1 and IRS2 mediate distinct signaling pathways and are not functionally interchangeable across insulin-sensitive tissues.",
        "obj": "Describe the specific roles of insulin receptor substrate proteins IRS1 and IRS2 in cellular insulin resistance",
        "rationale": "Clarifies non-redundant functions of IRS1 and IRS2 in metabolic and vascular insulin responses."
    },
    {
        "cid": "DOC-PMC-RENAL-0004-B-C0014",
        "did": "DOC-PMC-RENAL-0004",
        "strat": "STR-02",
        "split": "core",
        "query": "How does impaired IRS1-dependent insulin signaling in glomerular podocytes and endothelial cells promote diabetic nephropathy?",
        "span": "Because insulin signaling may be required not only for the nitric oxide (NO) production by glomerular endothelium but also for the preservation of normal podocyte functions [ 53 , 55 ], insulin resistance in glomeruli may promote the occurrence and progression of diabetic nephropathy",
        "claim": "Attenuated glomerular IRS1 insulin signaling impairs endothelial nitric oxide production and podocyte survival, accelerating diabetic nephropathy.",
        "obj": "Understand the consequences of glomerular insulin resistance on endothelial nitric oxide and podocyte function",
        "rationale": "Directly links glomerular endothelial and podocyte insulin signaling loss to diabetic kidney disease progression."
    },
    {
        "cid": "DOC-PMC-RENAL-0004-B-C0016",
        "did": "DOC-PMC-RENAL-0004",
        "strat": "STR-02",
        "split": "val",
        "query": "What describes the biphasic concentration-dependent regulatory effect of angiotensin II on proximal tubule sodium and bicarbonate transport?",
        "span": "effects of Ang II on PT transport are biphasic: transport is stimulated by picomolar to nanomolar concentrations of Ang II, while it is inhibited by nanomolar to micromolar concentrations of Ang II",
        "claim": "Angiotensin II exerts biphasic effects on proximal tubule transport, stimulating at picomolar-to-nanomolar concentrations and inhibiting at higher micromolar concentrations.",
        "obj": "Describe the biphasic concentration response of proximal tubular transport to angiotensin II",
        "rationale": "Details concentration-dependent dual action of Ang II on proximal tubular transport systems."
    },
    {
        "cid": "DOC-PMC-RENAL-0004-B-C0018",
        "did": "DOC-PMC-RENAL-0004",
        "strat": "STR-02",
        "split": "val",
        "query": "Which intracellular signaling cascade mediates the high-dose inhibitory effect of angiotensin II on proximal tubule transport?",
        "span": "activation of phospholipase A 2 (PLA 2 )/arachidonic acid/5,6-epoxyeicosatrienoic acid (EET) pathway and/or the NO/cGMP pathway is thought to mediate the inhibitory effect of Ang II",
        "claim": "The inhibitory effect of high-dose angiotensin II on proximal tubular transport is mediated by PLA2, arachidonic acid metabolites (EET), and the NO/cGMP cascade.",
        "obj": "Differentiate intracellular second messenger pathways mediating stimulatory versus inhibitory actions of angiotensin II in the proximal tubule",
        "rationale": "Identifies PLA2, arachidonic acid, and NO/cGMP pathways as mediators of transport inhibition."
    },

    # --------------------------------------------------------------------------
    # STR-03: Renal Potassium Handling & Tubulopathies (DOC-PMC-RENAL-0003, DOC-PMC-RENAL-0023)
    # --------------------------------------------------------------------------
    {
        "cid": "DOC-PMC-RENAL-0003-B-C0001",
        "did": "DOC-PMC-RENAL-0003",
        "strat": "STR-03",
        "split": "core",
        "query": "How does low urinary potassium excretion relate to the clinical progression of chronic kidney disease?",
        "span": "low urinary potassium excretion (as a proxy for insufficient dietary intake) is increasingly recognized as a risk factor for the progression of kidney disease",
        "claim": "Low urinary potassium excretion, reflecting insufficient dietary potassium intake, is recognized as a risk factor for chronic kidney disease progression.",
        "obj": "Recognize low urinary potassium excretion as an independent risk factor in chronic kidney disease progression",
        "rationale": "Directly correlates low urinary potassium excretion with adverse renal outcomes."
    },
    {
        "cid": "DOC-PMC-RENAL-0003-B-C0003",
        "did": "DOC-PMC-RENAL-0003",
        "strat": "STR-03",
        "split": "core",
        "query": "What cardiovascular and systemic risks are associated with habitually low dietary potassium intake in population studies?",
        "span": "Population studies have clearly shown that a low potassium diet is associated with an increased risk of hypertension and cardiovascular morbidity and mortality",
        "claim": "Habitually low dietary potassium intake increases the risk of hypertension, cardiovascular morbidity, and all-cause mortality in population cohorts.",
        "obj": "Understand systemic cardiovascular risks associated with insufficient dietary potassium intake",
        "rationale": "Documents cardiovascular morbidity and hypertension risks resulting from low dietary potassium."
    },
    {
        "cid": "DOC-PMC-RENAL-0003-B-C0013",
        "did": "DOC-PMC-RENAL-0003",
        "strat": "STR-03",
        "split": "core",
        "query": "What histopathological features of hypokalemic nephropathy develop in young animals subjected to dietary potassium depletion?",
        "span": "features of hypokalemic nephropathy including tubulointerstitial injury with the proliferation of tubular epithelial cells, macrophage infiltration, and fibrosis",
        "claim": "Potassium depletion induces hypokalemic nephropathy characterized by tubulointerstitial injury, epithelial proliferation, macrophage infiltration, and fibrosis.",
        "obj": "Describe the histopathologic lesions of tubulointerstitial injury in hypokalemic nephropathy",
        "rationale": "Details cellular pathology of hypokalemic tubulointerstitial damage and fibrosis."
    },
    {
        "cid": "DOC-PMC-RENAL-0003-B-C0022",
        "did": "DOC-PMC-RENAL-0003",
        "strat": "STR-03",
        "split": "core",
        "query": "How does female sex and estrogen influence distal tubular potassium handling and NCC activity?",
        "span": "Female rats and mice have a lower plasma potassium set point which coincides with higher NCC activity, depends on estrogen, and is maintained after a potassium challenge",
        "claim": "Estrogen promotes higher distal tubule NCC activity in females, establishing a lower plasma potassium set point that protects against gestational hyperkalemia.",
        "obj": "Explain sex hormone differences in renal distal potassium transport and NCC activity",
        "rationale": "Details estrogen-driven enhancement of distal NCC activity and lower plasma potassium set point."
    },
    {
        "cid": "DOC-PMC-RENAL-0003-B-C0024",
        "did": "DOC-PMC-RENAL-0003",
        "strat": "STR-03",
        "split": "core",
        "query": "What mathematical relationship characterizes the association between urinary potassium excretion and blood pressure in hypertensive populations?",
        "span": "the relationship between urinary potassium excretion and blood pressure follows a U-shaped relationship",
        "claim": "The relationship between urinary potassium excretion and blood pressure follows a U-shaped curve.",
        "obj": "Evaluate the non-linear relationship between potassium excretion and systemic blood pressure",
        "rationale": "Describes the U-shaped association between potassium excretion and systemic blood pressure."
    },
    {
        "cid": "DOC-PMC-RENAL-0023-B-C0006",
        "did": "DOC-PMC-RENAL-0023",
        "strat": "STR-03",
        "split": "val",
        "query": "What physiological mechanism maintains hypertonic medullary solute gradients against continuous washout by blood and tubular fluid?",
        "span": "if the solute losses along with solute outflow or dilution by water uptake are permanently balanced by solute addition from an external source, a solute gradient can well be established and maintained. Precisely this mechanism stabilizes the solute gradients in the medulla",
        "claim": "Medullary hypertonic solute gradients are maintained by active countercurrent multiplication balancing solute washout by blood flow and tubular fluid.",
        "obj": "Explain the countercurrent mechanism sustaining medullary osmotic hypertonicity",
        "rationale": "Describes how active solute delivery counterbalances vascular washout in the renal medulla."
    },

    # --------------------------------------------------------------------------
    # STR-04: RAAS, Vascular Inflammation & Remodeling (DOC-PMC-RENAL-0001)
    # --------------------------------------------------------------------------
    {
        "cid": "DOC-PMC-RENAL-0001-B-C0006",
        "did": "DOC-PMC-RENAL-0001",
        "strat": "STR-04",
        "split": "core",
        "query": "How does tumor necrosis factor alpha (TNF-alpha) induce endothelial dysfunction and impair vascular relaxation?",
        "span": "TNF α impairs endothelium-dependent nitric oxide (NO) mediated vasorelaxation in coronary arteries or carotid artery via superoxide radical production",
        "claim": "Tumor necrosis factor alpha impairs nitric oxide-mediated vasorelaxation by stimulating superoxide radical generation.",
        "obj": "Understand how proinflammatory cytokines impair vascular endothelial nitric oxide bioavailability",
        "rationale": "Demonstrates TNF-alpha-induced superoxide production blunting endothelium-dependent NO vasodilation."
    },
    {
        "cid": "DOC-PMC-RENAL-0001-B-C0008",
        "did": "DOC-PMC-RENAL-0001",
        "strat": "STR-04",
        "split": "core",
        "query": "What role does C-reactive protein (CRP) play as an acute-phase reactant and cardiovascular risk predictor in renal patients?",
        "span": "CRP is considered a hallmark of the acute-phase response and a predictor of cardiovascular event risk [ 28 ]. C-reactive protein is mainly produced in the liver",
        "claim": "C-reactive protein is a liver-derived acute-phase reactant that serves as a recognized predictor of cardiovascular event risk.",
        "obj": "Identify the diagnostic utility of C-reactive protein in systemic inflammation and cardiovascular assessment",
        "rationale": "Defines CRP synthesis and clinical prognostic role for cardiovascular events."
    },
    {
        "cid": "DOC-PMC-RENAL-0001-B-C0010",
        "did": "DOC-PMC-RENAL-0001",
        "strat": "STR-04",
        "split": "core",
        "query": "What vascular adhesion molecules are upregulated by endothelial inflammation to recruit circulating monocytes?",
        "span": "expression of intercellular adhesion molecule-1 (ICAM-1) and vascular cell adhesion molecule-1 (VCAM-1), both of which recruit blood monocytes to vascular wall",
        "claim": "Endothelial inflammatory injury upregulates ICAM-1 and VCAM-1, which mediate circulating monocyte recruitment to vascular walls.",
        "obj": "Explain the role of vascular cell adhesion molecules in endothelial leukocyte recruitment",
        "rationale": "Specifies ICAM-1 and VCAM-1 upregulation mediating monocyte recruitment in vascular injury."
    },
    {
        "cid": "DOC-PMC-RENAL-0001-B-C0012",
        "did": "DOC-PMC-RENAL-0001",
        "strat": "STR-04",
        "split": "core",
        "query": "How does angiotensin II-induced oxidative stress cause endothelial dysfunction in the kidney?",
        "span": "Ang II induces the production of superoxide anions and activates the prooxidant NADH/NADPH signaling [ 52 ]. Ang II-mediated oxidative stress reduces nitric oxide (NO) level",
        "claim": "Angiotensin II stimulates NADH/NADPH oxidase to produce superoxide anions, reducing nitric oxide bioavailability and promoting vascular inflammation.",
        "obj": "Describe molecular pathways by which angiotensin II induces oxidative stress and reduces nitric oxide",
        "rationale": "Links Ang II, NADPH oxidase activation, superoxide production, and NO depletion."
    },
    {
        "cid": "DOC-PMC-RENAL-0001-B-C0021",
        "did": "DOC-PMC-RENAL-0001",
        "strat": "STR-04",
        "split": "core",
        "query": "Which mineralocorticoid receptor antagonists (MRAs) are utilized to block adverse aldosterone effects on endothelial and cardiac tissue?",
        "span": "Blocking aldosterone effects at the level of MR with the currently available antagonists, eplerenone and spironolactone, have been shown to be effective treatment options for hypertension and heart failure",
        "claim": "Mineralocorticoid receptor antagonists eplerenone and spironolactone block aldosterone signaling to treat hypertension and heart failure.",
        "obj": "Identify therapeutic indications and agents within the mineralocorticoid receptor antagonist class",
        "rationale": "Specifies spironolactone and eplerenone as targeted MR antagonists mitigating cardiovascular damage."
    },
    {
        "cid": "DOC-PMC-RENAL-0001-B-C0023",
        "did": "DOC-PMC-RENAL-0001",
        "strat": "STR-04",
        "split": "val",
        "query": "How do aldosterone synthase inhibitors (ASIs) reduce aldosterone-mediated organ damage?",
        "span": "Decreasing aldosterone synthesis at its enzyme step, aldosterone synthase (AS), CYP11B2, is the novel alternative approach to MRA to limit aldosterone effects [ 105 ]. Aldosterone synthase inhibitors (ASI) represent the latest therapeutic strategy to decrease aldosterone production",
        "claim": "Aldosterone synthase inhibitors target the CYP11B2 enzyme step to decrease systemic aldosterone production directly.",
        "obj": "Understand the enzymatic mechanism and therapeutic role of aldosterone synthase inhibitors (ASIs)",
        "rationale": "Describes CYP11B2 inhibition by ASIs as an upstream approach to block aldosterone effects."
    }
]

print(f"Loaded {len(CLEAN_ITEMS_DATA_P1)} items for Part 1 (STR-01 to STR-04).")
