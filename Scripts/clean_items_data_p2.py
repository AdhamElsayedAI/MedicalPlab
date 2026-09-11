"""
Candidate Clean Train Items Data (N=80) — Part 2: STR-05 to STR-08
==================================================================
STR-05: 5 CORE, 2 VAL (7)
STR-06: 5 CORE, 1 VAL (6)
STR-07: 5 CORE, 2 VAL (7)
STR-08: 5 CORE, 2 VAL (7)
Total = 27 items.
"""

CLEAN_ITEMS_DATA_P2 = [
    # --------------------------------------------------------------------------
    # STR-05: Hyperkalemia Pathophysiology & Distal Transport (DOC-PMC-RENAL-0009)
    # --------------------------------------------------------------------------
    {
        "cid": "DOC-PMC-RENAL-0009-B-C0004",
        "did": "DOC-PMC-RENAL-0009",
        "strat": "STR-05",
        "split": "core",
        "query": "Why is rapid cellular uptake and kaliuresis essential to prevent lethal hyperkalemia following an acute dietary potassium load?",
        "span": "a banana smoothie delivering 35 mmol of potassium to an extracellular fluid volume of 12 L would induce a potentially fatal [K + ] e increase of ∼3 mM. We survive the banana smoothie because of a rapid response that shifts potassium into cells and into the urine",
        "claim": "Acute dietary potassium loads threaten fatal hyperkalemia unless counteracted by rapid intracellular shifting and renal excretion.",
        "obj": "Understand the physiological necessity of rapid transcellular buffering and renal potassium excretion",
        "rationale": "Illustrates how cellular uptake and urinary clearance buffer massive acute dietary potassium intakes."
    },
    {
        "cid": "DOC-PMC-RENAL-0009-B-C0009",
        "did": "DOC-PMC-RENAL-0009",
        "strat": "STR-05",
        "split": "core",
        "query": "What experimental evidence demonstrates that aldosterone-independent pathways can maintain potassium balance under physiological dietary intake?",
        "span": "AS-null mice can maintain a normal plasma [K + ] in the face of physiological (2%) dietary K + , demonstrating that aldosterone-independent pathways can stimulate kaliuresis in this context",
        "claim": "Aldosterone synthase-null mice maintain normokalemia on normal diets, showing aldosterone-independent kaliuresis pathways operate physiologically.",
        "obj": "Differentiate aldosterone-dependent versus aldosterone-independent mechanisms of renal potassium excretion",
        "rationale": "Shows normokalemia in AS-deficient mice under standard dietary potassium conditions."
    },
    {
        "cid": "DOC-PMC-RENAL-0009-B-C0011",
        "did": "DOC-PMC-RENAL-0009",
        "strat": "STR-05",
        "split": "core",
        "query": "What diurnal variation characterizes the circadian rhythm of renal potassium excretion in healthy humans?",
        "span": "Renal potassium excretion follows a circadian rhythm, being highest around noon and lowest around midnight",
        "claim": "Renal potassium excretion displays circadian variation, peaking around midday and reaching its nadir around midnight.",
        "obj": "Describe circadian rhythms governing renal potassium handling and urinary excretion",
        "rationale": "Directly defines the noon peak and midnight nadir in diurnal potassium excretion."
    },
    {
        "cid": "DOC-PMC-RENAL-0009-B-C0013",
        "did": "DOC-PMC-RENAL-0009",
        "strat": "STR-05",
        "split": "core",
        "query": "Which clinical conditions and acid-base disturbances cause acute hyperkalemia via transcellular potassium shifting?",
        "span": "Potassium shifted from the intra- to the extracellular space are induced by acute metabolic acidosis and opposed by insulin and β-adrenergic signalling [ 13 ]. Widespread cell death (as in tumour lysis or rhabdomyolysis) may also release potassium from the intracellular space",
        "claim": "Transcellular hyperkalemic shifts are provoked by acute metabolic acidosis, tumor lysis, and rhabdomyolysis, and opposed by insulin and beta-agonists.",
        "obj": "Identify causes and regulatory factors governing transcellular potassium redistribution",
        "rationale": "Details cellular release of potassium in metabolic acidosis, rhabdomyolysis, and tumor lysis syndrome."
    },
    {
        "cid": "DOC-PMC-RENAL-0009-B-C0015",
        "did": "DOC-PMC-RENAL-0009",
        "strat": "STR-05",
        "split": "core",
        "query": "Why is persistent hyperkalemia rarely observed in clinical practice when both renal function and the adrenal-aldosterone axis are normal?",
        "span": "Ninety percent of excreted potassium exits via the kidneys and the kidneys have a remarkable capacity to increase potassium excretion in the face of potassium excess [ 16 ]. Consequently hyperkalemia is almost never encountered clinically in the context of normal renal function and a normal adrenal–kidney axis",
        "claim": "Persistent hyperkalemia rarely occurs with intact kidney function and a normal adrenal-renal axis due to large renal reserve for potassium excretion.",
        "obj": "Explain the compensatory capacity of the kidneys to prevent hyperkalemia in healthy states",
        "rationale": "Explains why normal kidneys clear potassium excess to prevent chronic hyperkalemia."
    },
    {
        "cid": "DOC-PMC-RENAL-0009-B-C0017",
        "did": "DOC-PMC-RENAL-0009",
        "strat": "STR-05",
        "split": "val",
        "query": "How does electrogenic sodium reabsorption through ENaC create the electrochemical driving force for potassium secretion via ROMK channels?",
        "span": "Na + reabsorption through the ENaC generates a lumen-negative potential, favouring K + excretion",
        "claim": "Electrogenic sodium uptake through apical ENaC channels generates a lumen-negative potential difference driving passive potassium secretion through ROMK.",
        "obj": "Describe the coupling between ENaC sodium reabsorption and ROMK potassium secretion in distal principal cells",
        "rationale": "Explains electrical coupling between ENaC sodium influx and ROMK potassium secretion."
    },
    {
        "cid": "DOC-PMC-RENAL-0009-B-C0019",
        "did": "DOC-PMC-RENAL-0009",
        "strat": "STR-05",
        "split": "val",
        "query": "What sensor role do basolateral Kir4.1 potassium channels play in distal convoluted tubule cells during potassium depletion?",
        "span": "Potassium channels (Kir4.1) in the basolateral membranes of distal convoluted tubule cells act as ‘potassium sensors’, activating NCC in response to potassium depletion",
        "claim": "Basolateral Kir4.1 channels serve as potassium sensors that activate NCC cotransporters during hypokalemia to switch between electroneutral and electrogenic transport.",
        "obj": "Explain how basolateral Kir4.1 channels sense extracellular potassium and modulate NCC cotransporter activity",
        "rationale": "Identifies Kir4.1 as the basolateral potassium sensor activating distal tubule NCC."
    },

    # --------------------------------------------------------------------------
    # STR-06: Renal Acid-Base Regulation & Buffering (DOC-PMC-RENAL-0004, DOC-PMC-RENAL-0005)
    # --------------------------------------------------------------------------
    {
        "cid": "DOC-PMC-RENAL-0004-B-C0021",
        "did": "DOC-PMC-RENAL-0004",
        "strat": "STR-06",
        "split": "core",
        "query": "What extrarenal ocular and systemic manifestations accompany proximal renal tubular acidosis in patients with inactivating NBCe1 mutations?",
        "span": "inactivating mutations in NBCe1 cause severe pRTA associated with ocular and other extrarenal abnormalities",
        "claim": "Inactivating mutations in NBCe1 cause severe proximal renal tubular acidosis accompanied by ocular defects and extrarenal abnormalities.",
        "obj": "Recognize systemic ocular and extrarenal features associated with NBCe1 proximal tubulopathy",
        "rationale": "Identifies ocular and extrarenal phenotypes associated with genetic NBCe1 deficiency."
    },
    {
        "cid": "DOC-PMC-RENAL-0005-B-C0001",
        "did": "DOC-PMC-RENAL-0005",
        "strat": "STR-06",
        "split": "core",
        "query": "Which two organ systems cooperate to regulate systemic pH, and what is the renal contribution to bicarbonate buffering?",
        "span": "Two primary organ systems correct deviations from the standard pH balance: the respiratory system via gas exchange and the kidneys via proton/bicarbonate secretion and reabsorption",
        "claim": "Systemic pH homeostasis is maintained by respiratory gas exchange and renal proton secretion and bicarbonate reabsorption.",
        "obj": "Describe organ-level cooperation between the respiratory and renal systems in maintaining systemic pH",
        "rationale": "Defines respiratory and renal mechanisms maintaining whole-body acid-base balance."
    },
    {
        "cid": "DOC-PMC-RENAL-0005-B-C0007",
        "did": "DOC-PMC-RENAL-0005",
        "strat": "STR-06",
        "split": "core",
        "query": "How does the proximal convoluted tubule divide transport duties with distal nephron segments regarding filtered water, ions, and hormonal regulation?",
        "span": "The proximal convoluted tubule reabsorbs the major part of filtered ions, water and nutrients, while the distal tubule and collecting ducts perform selective reabsorption and excretion (controlled by hormones) to modify the final composition of urine",
        "claim": "The proximal tubule bulk-reabsorbs most filtered ions and water, whereas distal tubules and collecting ducts execute hormonally regulated fine-tuning of urinary excretion.",
        "obj": "Contrast bulk proximal tubular reabsorption with hormonally regulated distal nephron ion excretion",
        "rationale": "Delineates proximal bulk transport versus distal hormone-controlled ionic regulation."
    },
    {
        "cid": "DOC-PMC-RENAL-0005-B-C0009",
        "did": "DOC-PMC-RENAL-0005",
        "strat": "STR-06",
        "split": "core",
        "query": "How are human pluripotent stem cell-derived tubular organoids utilized to model renal diseases and drug toxicity in vitro?",
        "span": "pluripotent stem cells can be in vitro differentiated into tubular ‘organoids’ that express epithelial cell markers of renal tubules. The in vitro ‘organoids’ were successfully used to model a number of renal conditions including nephrotoxin-induced injuries",
        "claim": "Stem cell-derived tubular organoids expressing renal epithelial markers serve as physiological models for nephrotoxin injury and genetic kidney diseases.",
        "obj": "Explain the utility of pluripotent stem cell-derived kidney organoids in modeling nephrotoxicity",
        "rationale": "Details stem cell tubular organoid systems for nephrotoxic and genetic disease modeling."
    },
    {
        "cid": "DOC-PMC-RENAL-0005-B-C0011",
        "did": "DOC-PMC-RENAL-0005",
        "strat": "STR-06",
        "split": "core",
        "query": "Which accessory urinary buffers, notably phosphate and ammonium, play vital roles in renal net acid excretion and systemic acid-base balance?",
        "span": "Apart from the main ions responsible for AB balance, we consider renal exchange for some accessory ions including phosphate, ammonium and oxalate",
        "claim": "Renal net acid excretion relies on titratable buffers such as phosphate and the synthesis and excretion of ammonium ions.",
        "obj": "Identify the critical accessory buffer systems (phosphate, ammonium) involved in renal acid excretion",
        "rationale": "Specifies phosphate and ammonium as essential accessory ions in renal proton elimination."
    },
    {
        "cid": "DOC-PMC-RENAL-0005-B-C0018",
        "did": "DOC-PMC-RENAL-0005",
        "strat": "STR-06",
        "split": "val",
        "query": "How does dietary composition, specifically fruit and vegetable intake versus animal protein, affect systemic base loads and renal acid-base clearance?",
        "span": "The fruit- and vegetable-rich diets increase the bicarbonate/base loads; the excess is subject to clearance for the sake of proper base balance",
        "claim": "Diets rich in fruits and vegetables provide an alkaline bicarbonate load that requires renal base clearance to maintain systemic pH balance.",
        "obj": "Explain the dietary determinants of systemic acid-base loads and renal compensatory excretion",
        "rationale": "Explains dietary base loading from plant foods requiring renal excretion to maintain pH balance."
    },

    # --------------------------------------------------------------------------
    # STR-07: Acute Kidney Injury Criteria & Biomarkers (DOC-PMC-RENAL-0006)
    # --------------------------------------------------------------------------
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0001",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-07",
        "split": "core",
        "query": "Why is early clinical detection and prompt intervention critical in the management of acute kidney injury (AKI) across hospital settings?",
        "span": "Because AKI has significant impacts on prognosis in any clinical settings, early detection and intervention is necessary to improve the outcomes of AKI patients",
        "claim": "Early detection and intervention in acute kidney injury is essential because AKI independently worsens clinical prognosis and mortality across all hospital settings.",
        "obj": "Recognize the clinical importance of early detection and intervention in acute kidney injury",
        "rationale": "Directly states that early AKI detection and treatment improves outcomes given its prognostic impact."
    },
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0021",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-07",
        "split": "core",
        "query": "How does the time window for a 1.5-fold increase in serum creatinine differ between the KDIGO and AKIN definitions of acute kidney injury?",
        "span": "The KDIGO criteria diverge from the AKIN criteria in that the time course for a 1.5-fold increase in sCr from baseline was changed from within 48 h to within 7 days",
        "claim": "KDIGO criteria extend the observation window for a 1.5-fold baseline serum creatinine increase from 48 hours (AKIN) to within 7 days.",
        "obj": "Compare diagnostic creatinine timeframes between KDIGO and AKIN consensus criteria for AKI",
        "rationale": "Explicitly compares the 7-day KDIGO creatinine criterion to the 48-hour AKIN threshold."
    },
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0029",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-07",
        "split": "core",
        "query": "How do diagnostic rates and mortality risk stratification compare when applying RIFLE, AKIN, and KDIGO criteria in intensive care unit (ICU) populations?",
        "span": "reported the percentages of patients diagnosed with AKI according to the RIFLE, AKIN, and KDIGO criteria using both the sCr and urine output, and compared their in-hospital mortality rates",
        "claim": "In large ICU cohorts, evaluating AKI via KDIGO using both creatinine and urine output improves identification and hospital mortality stratification compared to older criteria.",
        "obj": "Evaluate clinical utility and comparative mortality prediction of RIFLE, AKIN, and KDIGO criteria in critically ill patients",
        "rationale": "Documents comparison of RIFLE, AKIN, and KDIGO criteria for AKI diagnosis and mortality in ICU patients."
    },
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0032",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-07",
        "split": "core",
        "query": "What diagnostic limitation arises when using estimated rather than true baseline serum creatinine to diagnose acute kidney injury?",
        "span": "compared to the use of the known baseline function, all of these methods have been reported to yield a certain rate of false positives or false negatives in their AKI diagnoses and mortality predictions",
        "claim": "Back-calculating baseline serum creatinine produces false-positive or false-negative AKI classifications compared to true pre-morbid baseline values.",
        "obj": "Identify diagnostic inaccuracies caused by estimating baseline renal function in acute kidney injury",
        "rationale": "Identifies rates of false positives and negatives when estimating baseline kidney function."
    },
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0044",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-07",
        "split": "core",
        "query": "Why does assuming a baseline eGFR of 75 mL/min/1.73 m2 to back-calculate serum creatinine cause false-positive AKI diagnoses?",
        "span": "assumed baseline renal function of eGFR 75 ml/min/1.73 m 2 yielded false positive AKI diagnoses",
        "claim": "Assuming a standard baseline eGFR of 75 mL/min/1.73 m2 frequently overestimates baseline kidney function in elderly or frail hospitalized cohorts, causing false-positive AKI diagnoses.",
        "obj": "Understand the risks of false-positive AKI overdiagnosis when back-calculating baseline creatinine from an assumed eGFR of 75",
        "rationale": "Shows that assuming baseline eGFR 75 mL/min causes false-positive AKI classifications in hospitalized cohorts."
    },
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0055",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-07",
        "split": "val",
        "query": "What is the reported incidence of acute kidney injury following cardiac surgery and its associated in-hospital mortality rate?",
        "span": "incidence of postoperative AKI was 22.3%, while 2.3% of the patients required renal replacement therapy (RRT). Furthermore, the in-hospital mortality of patients who developed AKI following cardiac surgery was 10.7%",
        "claim": "Postoperative AKI occurs in approximately 22% of cardiac surgery patients and carries an in-hospital mortality rate of over 10%.",
        "obj": "Quantify epidemiology, dialysis requirements, and mortality outcomes associated with cardiac surgery-induced AKI",
        "rationale": "Provides epidemiological figures: 22.3% AKI incidence and 10.7% in-hospital mortality after cardiac surgery."
    },
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0065",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-07",
        "split": "val",
        "query": "How does advanced patient age independently influence the risk of developing acute kidney injury after cardiac surgery?",
        "span": "reported that the risk of development of AKI from cardiac surgery increased with age (odds ratio 1.022, 95% confidence interval: 1.005–1.039)",
        "claim": "Advanced chronological age is an independent risk factor that significantly increases the odds of developing acute kidney injury after cardiac surgery.",
        "obj": "Identify advanced age as an independent preoperative risk factor for postoperative acute kidney injury",
        "rationale": "Documents statistically significant odds ratio (1.022 per year) for post-cardiac surgery AKI with aging."
    },

    # --------------------------------------------------------------------------
    # STR-08: Chronic Kidney Disease Guidelines & Evaluation (DOC-PMC-RENAL-0007)
    # --------------------------------------------------------------------------
    {
        "cid": "DOC-PMC-RENAL-0007-B-C0033",
        "did": "DOC-PMC-RENAL-0007",
        "strat": "STR-08",
        "split": "core",
        "query": "Which pharmacological classes and lifestyle interventions are recommended to reduce proteinuria and confer renoprotection in chronic kidney disease?",
        "span": "Pharmacotherapy using renin–angiotensin (RA) system inhibitors, mineralocorticoid receptor antagonists, sodium-glucose cotransporter-2 (SGLT2) inhibitors",
        "claim": "Renoprotection and albuminuria reduction in CKD are achieved using RAAS inhibitors, MRAs, SGLT2 inhibitors, alongside dietary sodium restriction and weight control.",
        "obj": "Identify guideline-recommended pharmacological classes that reduce albuminuria and slow CKD progression",
        "rationale": "Identifies RAAS inhibitors, MRAs, and SGLT2 inhibitors as guideline therapies for CKD renoprotection."
    },
    {
        "cid": "DOC-PMC-RENAL-0007-B-C0035",
        "did": "DOC-PMC-RENAL-0007",
        "strat": "STR-08",
        "split": "core",
        "query": "What three clinical components constitute the KDIGO CGA classification system for staging chronic kidney disease?",
        "span": "The cause, GFR, and albuminuria (CGA) classification severity, which is GFR- and urinary albumin-based severity combined with the cause of kidney disease, better reflects the prognosis",
        "claim": "The CGA staging system categorizes chronic kidney disease based on Cause, GFR category, and Albuminuria stage to accurately reflect prognosis.",
        "obj": "Apply the KDIGO Cause-GFR-Albuminuria (CGA) classification system to evaluate CKD risk and prognosis",
        "rationale": "Details the KDIGO Cause, GFR, and Albuminuria (CGA) framework for CKD prognostic evaluation."
    },
    {
        "cid": "DOC-PMC-RENAL-0007-B-C0040",
        "did": "DOC-PMC-RENAL-0007",
        "strat": "STR-08",
        "split": "core",
        "query": "What degree of eGFR decline after initiating RAAS inhibitors or SGLT2 inhibitors warrants referral to a nephrologist?",
        "span": "decrease in eGFR in the early stages of RA system and SGLT2 inhibitor administration; however, a nephrologist should be referred to in case a decrease of 30% or more is observed within three months",
        "claim": "An acute eGFR decline exceeding 30% within 3 months of starting RAAS inhibitors or SGLT2 inhibitors necessitates nephrology referral.",
        "obj": "Recognize the safety threshold (30% eGFR drop within 3 months) for nephrology referral upon initiating hemodynamic CKD medications",
        "rationale": "Defines the 30% drop in eGFR within 3 months threshold triggering nephrologist consultation."
    },
    {
        "cid": "DOC-PMC-RENAL-0007-B-C0073",
        "did": "DOC-PMC-RENAL-0007",
        "strat": "STR-08",
        "split": "core",
        "query": "What renal histopathological entity and clinical syndrome develops secondary to longstanding benign essential hypertension?",
        "span": "Hypertensive nephrosclerosis is a renal lesion caused by persistent hypertension. It generally refers to benign nephrosclerosis",
        "claim": "Persistent chronic hypertension leads to hypertensive nephrosclerosis, predominantly presenting as benign arteriolosclerosis with progressive loss of renal function.",
        "obj": "Describe the pathogenesis, clinical features, and management of hypertensive nephrosclerosis",
        "rationale": "Identifies hypertensive nephrosclerosis as benign renal damage caused by chronic hypertension."
    },
    {
        "cid": "DOC-PMC-RENAL-0007-B-C0135",
        "did": "DOC-PMC-RENAL-0007",
        "strat": "STR-08",
        "split": "core",
        "query": "What is the recommended lower limit for target hemoglobin when initiating erythropoiesis-stimulating agent (ESA) therapy for renal anemia in CKD?",
        "span": "suggested that the lower limit of the target Hb level be 10 g/dL",
        "claim": "Clinical practice guidelines recommend maintaining a target hemoglobin lower limit of at least 10 g/dL during ESA therapy for anemia in CKD.",
        "obj": "Identify target hemoglobin thresholds for erythropoiesis-stimulating agent therapy in chronic kidney disease anemia",
        "rationale": "Specifies 10 g/dL as the lower target threshold for hemoglobin during ESA administration in CKD anemia."
    },
    {
        "cid": "DOC-PMC-RENAL-0007-B-C0053",
        "did": "DOC-PMC-RENAL-0007",
        "strat": "STR-08",
        "split": "val",
        "query": "Why is strict blood pressure control recommended in non-CKD hypertensive patients to prevent incident chronic kidney disease?",
        "span": "preventing CKD onset through blood pressure management is important in terms of improving vital prognosis and reducing medical costs",
        "claim": "Effective blood pressure control in essential hypertension is recommended to reduce the risk of developing de novo chronic kidney disease.",
        "obj": "Explain blood pressure management strategies aimed at preventing incident chronic kidney disease in hypertensive populations",
        "rationale": "Emphasizes blood pressure control to prevent initial CKD onset and preserve vital prognosis."
    },
    {
        "cid": "DOC-PMC-RENAL-0007-B-C0065",
        "did": "DOC-PMC-RENAL-0007",
        "strat": "STR-08",
        "split": "val",
        "query": "Is there sufficient clinical trial evidence to recommend ACE inhibitors or ARBs over other antihypertensives in non-proteinuric CKD patients?",
        "span": "In CKD patients without proteinuria and with hypertension, there is insufficient evidence that ACE inhibitors/ARBs improve CVD events and renal prognosis",
        "claim": "Evidence is insufficient to demonstrate superior renal or cardiovascular outcomes for ACE inhibitors or ARBs over other antihypertensives in CKD patients lacking proteinuria.",
        "obj": "Critique the evidence base regarding ACE inhibitor/ARB selection in non-proteinuric hypertensive CKD patients",
        "rationale": "Documents lack of evidence that ACE/ARB agents improve prognosis in non-proteinuric hypertensive CKD patients."
    }
]

print(f"Loaded {len(CLEAN_ITEMS_DATA_P2)} items for Part 2 (STR-05 to STR-08).")
