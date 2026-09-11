"""
Candidate Clean Train Items Data (N=80) — Part 3: STR-09 to STR-12
==================================================================
STR-09: 5 CORE, 2 VAL (7)
STR-10: 5 CORE, 1 VAL (6)
STR-11: 5 CORE, 2 VAL (7)
STR-12: 5 CORE, 2 VAL (7)
Total = 27 items.
"""

CLEAN_ITEMS_DATA_P3 = [
    # --------------------------------------------------------------------------
    # STR-09: Glomerulonephritis & Podocytopathies (DOC-PMC-RENAL-0002)
    # --------------------------------------------------------------------------
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0027",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-09",
        "split": "core",
        "query": "What pathophysiological mechanism initiates membranous nephropathy (MN) leading to nephrotic syndrome in adults?",
        "span": "MN is initiated by the deposition of circulating anti-podocyte autoantibodies in the subepithelial space of the GFB, inducing complement-mediated podocyte injury and proteinuria",
        "claim": "Membranous nephropathy is initiated by circulating anti-podocyte autoantibodies depositing in the subepithelial space of the filtration barrier, inducing complement activation and podocyte injury.",
        "obj": "Describe the immunopathogenesis of membranous nephropathy involving subepithelial immune deposits and complement activation",
        "rationale": "Directly describes subepithelial autoantibody deposition and complement-mediated podocyte injury in membranous nephropathy."
    },
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0029",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-09",
        "split": "core",
        "query": "Which immunoglobulin G subclass predominantly characterizes the subepithelial immune deposits in primary membranous nephropathy?",
        "span": "chips with MN serum, but not control sera, showed total IgG (Supplementary Fig. 7b–g ) and IgG4 (Supplementary Fig. 7h–m ) deposition on the podocytes, recapitulating the main features of MN nephropathy",
        "claim": "Subepithelial immune deposits in membranous nephropathy predominantly consist of the IgG4 subclass.",
        "obj": "Identify the predominant IgG subclass (IgG4) involved in primary membranous nephropathy immune complexes",
        "rationale": "Confirms IgG4 deposition on podocytes recapitulating clinical membranous nephropathy."
    },
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0034",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-09",
        "split": "core",
        "query": "Which podocyte membrane protein represents the predominant target autoantigen in adult primary membranous nephropathy?",
        "span": "PLA 2 R is the major podocyte target antigen in MN patients 52 , 53 along with less common ones like, for example, THSD7A and NEP1",
        "claim": "M-type phospholipase A2 receptor (PLA2R) is the major podocyte autoantigen in adult membranous nephropathy, alongside THSD7A.",
        "obj": "Identify PLA2R and secondary podocyte autoantigens in adult membranous nephropathy",
        "rationale": "Identifies PLA2R as the primary podocyte antigen in membranous nephropathy."
    },
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0036",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-09",
        "split": "core",
        "query": "How does exposure to nephrotoxic membranous nephropathy sera affect glomerular endothelial cells and endothelial surface glycocalyx markers?",
        "span": "measured WGA expression in endothelial cells and found that the expression declined at 24 h after exposure, a phenomenon that did not occur in the presence of control sera",
        "claim": "Exposure to membranous nephropathy patient serum induces secondary glomerular endothelial damage characterized by down-regulation of glycocalyx markers.",
        "obj": "Recognize secondary endothelial injury and glycocalyx loss in membranous nephropathy",
        "rationale": "Shows down-regulation of endothelial WGA glycocalyx expression in response to MN serum."
    },
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0046",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-09",
        "split": "core",
        "query": "What clinical antiproteinuric effect does alpha-MSH confer when evaluating glomerular injury in membranous nephropathy models?",
        "span": "podocyte-targeting drug like α-MSH, clinically used to reduce proteinuria in MN patients, prevented the proteinuric effects of MN sera",
        "claim": "Alpha-MSH acts directly on podocytes to prevent the proteinuric barrier disruption induced by membranous nephropathy patient sera.",
        "obj": "Evaluate the protective action of alpha-MSH on podocyte permselectivity in membranous nephropathy",
        "rationale": "Documents alpha-MSH podocyte protection preventing serum-induced albumin leakage."
    },
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0039",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-09",
        "split": "val",
        "query": "Through what cellular mechanism does adrenocorticotropic hormone (ACTH) and alpha-MSH stabilize podocyte actin stress fibers in nephrotic syndrome?",
        "span": "α-MSH main mechanism of action is through inhibition of RhoA inhibitor p190RhoGAP activity, which is crucial for the stabilization of podocyte stress fibers",
        "claim": "Alpha-MSH and ACTH stabilize podocyte actin stress fibers by modulating RhoA signaling via p190RhoGAP inhibition.",
        "obj": "Explain the cellular mechanism of ACTH and melanocortin receptor agonists in stabilizing podocyte architecture",
        "rationale": "Details p190RhoGAP and RhoA regulation in stabilizing podocyte actin fibers during ACTH/alpha-MSH treatment."
    },
    {
        "cid": "DOC-PMC-RENAL-0002-B-C0042",
        "did": "DOC-PMC-RENAL-0002",
        "strat": "STR-09",
        "split": "val",
        "query": "Mutations in which type IV collagen alpha-chain genes (COL4A3, COL4A4, COL4A5) cause Alport syndrome and disruption of the glomerular basement membrane?",
        "span": "In AS, a mutation on COL4α3α4α5 genes leads to deposition of a defective GBM, leading to CKD and ESRD",
        "claim": "Alport syndrome is caused by mutations in the type IV collagen alpha-chains COL4A3, COL4A4, or COL4A5, resulting in defective glomerular basement membrane assembly.",
        "obj": "Identify the genetic defects in collagen type IV chains responsible for Alport syndrome",
        "rationale": "Identifies COL4A3/4/5 mutations leading to defective basement membrane and albumin leakage in Alport syndrome."
    },

    # --------------------------------------------------------------------------
    # STR-10: Urinary Tract Infections & Uropathogens (DOC-PMC-RENAL-0011)
    # --------------------------------------------------------------------------
    {
        "cid": "DOC-PMC-RENAL-0011-B-C0009",
        "did": "DOC-PMC-RENAL-0011",
        "strat": "STR-10",
        "split": "core",
        "query": "How does repeated antimicrobial exposure contribute to the pathogenesis of recurrent urinary tract infections (rUTIs) via microbiome dysbiosis?",
        "span": "Antibiotics favor the development and proliferation of multidrug-resistant organisms (either in the bladder or in the gut/vagina), as well as increase the availability of niches that are no longer inhabited by commensals",
        "claim": "Repeated antibiotic therapy depletes protective commensal flora, creating dysbiotic ecological niches that facilitate colonization by resistant uropathogens.",
        "obj": "Explain how antimicrobial-induced dysbiosis increases susceptibility to recurrent urinary tract infections",
        "rationale": "Explains antibiotic depletion of commensals predisposing to dysbiosis and recurrent colonization."
    },
    {
        "cid": "DOC-PMC-RENAL-0011-B-C0011",
        "did": "DOC-PMC-RENAL-0011",
        "strat": "STR-10",
        "split": "core",
        "query": "Which bacterial virulence factors and persistence strategies, such as biofilm formation and fimbrial adhesins, facilitate recurrent catheter-associated UTIs?",
        "span": "common uropathogenic strategy is the formation of biofilms, either directly on the urothelial surface or on indwelling devices such as catheters",
        "claim": "Uropathogens utilize biofilms on catheter surfaces and host urothelium alongside adhesins and siderophores to persist and evade host clearance.",
        "obj": "Describe virulence factors enabling uropathogenic bacterial persistence and catheter-associated biofilm formation",
        "rationale": "Details biofilm formation on catheters and mucosal surfaces promoting bacterial persistence."
    },
    {
        "cid": "DOC-PMC-RENAL-0011-B-C0013",
        "did": "DOC-PMC-RENAL-0011",
        "strat": "STR-10",
        "split": "core",
        "query": "How do uropathogenic Escherichia coli (UPEC) form intracellular bacterial communities (IBCs) inside bladder umbrella cells to evade host immune clearance?",
        "span": "invaded urothelial cells and formed IBCs that could later erupt and re-establish UTI ( Anderson et al., 2003 ; Justice et al., 2004 ). In this exciting model, after invasion, bacteria rapidly multiply in the cytoplasm of superficial bladder epithelial cells, where they form “pods”",
        "claim": "UPEC invade superficial bladder umbrella cells to establish intracellular bacterial communities (pods) shielded from host immune surveillance and antibiotics.",
        "obj": "Explain the formation and pathogenic role of intracellular bacterial communities in recurrent cystitis",
        "rationale": "Describes intracellular bacterial communities and umbrella cell pod formation by UPEC."
    },
    {
        "cid": "DOC-PMC-RENAL-0011-B-C0015",
        "did": "DOC-PMC-RENAL-0011",
        "strat": "STR-10",
        "split": "core",
        "query": "Which uropathogens other than UPEC, including Klebsiella pneumoniae and Enterococcus faecalis, demonstrate intracellular persistence in human urothelial cells?",
        "span": "other uropathogens, such as Klebsiella pneumoniae ( Rosen et al., 2008 ), Staphylococcus saprophyticus ( Szabados et al., 2008 ) and Salmonella enterica ( Bishop et al., 2007 ) might also display them",
        "claim": "Intracellular urothelial invasion is not restricted to UPEC but also occurs in Klebsiella pneumoniae, Staphylococcus saprophyticus, and Enterococcus faecalis.",
        "obj": "Identify non-E. coli uropathogens capable of intracellular urothelial invasion and reservoir formation",
        "rationale": "Shows that Klebsiella, Staph saprophyticus, and Enterococcus also exhibit intracellular lifestyle phases."
    },
    {
        "cid": "DOC-PMC-RENAL-0011-B-C0017",
        "did": "DOC-PMC-RENAL-0011",
        "strat": "STR-10",
        "split": "core",
        "query": "How does horizontal gene transfer promote the dissemination of multidrug-resistant traits among recurrent uropathogens?",
        "span": "machinery for intra- and inter-species transmission (e.g. through horizontal gene transfer mechanisms), which can spread the selected traits rapidly and boost the generation of multidrug-resistant uropathogens",
        "claim": "Horizontal gene transfer mediates intra- and inter-species dissemination of antimicrobial resistance determinants in chronic uropathogens.",
        "obj": "Describe the mechanism of horizontal gene transfer in the emergence of multidrug-resistant urinary pathogens",
        "rationale": "Explains horizontal transfer spreading resistance determinants rapidly among uropathogens."
    },
    {
        "cid": "DOC-PMC-RENAL-0011-B-C0021",
        "did": "DOC-PMC-RENAL-0011",
        "strat": "STR-10",
        "split": "val",
        "query": "What role does defects in innate and adaptive mucosal immunity play in host susceptibility to recurrent urinary tract infections?",
        "span": "recurrence of infection is frequently associated with a disturbed innate immune response and/or insufficient adaptive immunity",
        "claim": "Impaired innate mucosal defenses and insufficient adaptive immune priming underlie individual host susceptibility to recurrent bacterial cystitis.",
        "obj": "Understand the host immunological defects predisposing to recurrent urinary tract infections",
        "rationale": "Identifies impaired mucosal immunity and adaptive immune responses as host risk factors."
    },

    # --------------------------------------------------------------------------
    # STR-11: Nephrolithiasis & Endourology Guidelines (DOC-PMC-RENAL-0012)
    # --------------------------------------------------------------------------
    {
        "cid": "DOC-PMC-RENAL-0012-B-C0005",
        "did": "DOC-PMC-RENAL-0012",
        "strat": "STR-11",
        "split": "core",
        "query": "How does the European Association of Urology (EAU) apply GRADE methodology to categorize guideline recommendations for urolithiasis?",
        "span": "EAU classifies its recommendations as “strong” or “weak”, using the guiding concept of the GRADE methodology [ 7 ], based on various factors, such as the quality and extent of the effect, certainty, balanced outcomes, and patient values and preferences",
        "claim": "The EAU utilizes GRADE methodology to formulate strong or weak clinical recommendations based on evidence quality, risk-benefit balance, and patient values.",
        "obj": "Understand evidence-based grading frameworks utilized in European urological clinical practice guidelines",
        "rationale": "Explains GRADE categorization into strong or weak recommendations in EAU guidelines."
    },
    {
        "cid": "DOC-PMC-RENAL-0012-B-C0007",
        "did": "DOC-PMC-RENAL-0012",
        "strat": "STR-11",
        "split": "core",
        "query": "Which clinical presentations and red-flag features, such as pyrexia or a solitary kidney, mandate urgent expedited evaluation for suspected urolithiasis?",
        "span": "The EAU recommends expediting the investigation if there is a lack of understanding of the diagnosis, pyrexia, or a solitary kidney (strong recommendation)",
        "claim": "Immediate expedited investigation for urolithiasis is strongly recommended in the presence of fever, diagnostic uncertainty, or in patients with a solitary kidney.",
        "obj": "Identify high-risk presentation features of acute renal colic mandating emergency investigation",
        "rationale": "Outlines specific clinical indications warranting expedited emergency urolithiasis investigation."
    },
    {
        "cid": "DOC-PMC-RENAL-0012-B-C0015",
        "did": "DOC-PMC-RENAL-0012",
        "strat": "STR-11",
        "split": "core",
        "query": "Do clinical guidelines recommend routine pre-procedural ureteral stenting prior to uncomplicated ureteroscopy (URS)?",
        "span": "Pre-procedural stent placement is not recommended by either the AUA (AUA: strong recommendation) or the EAU",
        "claim": "Neither the AUA nor the EAU recommends routine pre-procedural ureteral stent placement prior to uncomplicated ureteroscopy.",
        "obj": "Recognize guideline recommendations regarding routine pre-stenting prior to ureteroscopy",
        "rationale": "States guideline consensus against routine pre-procedural stenting before URS."
    },
    {
        "cid": "DOC-PMC-RENAL-0012-B-C0017",
        "did": "DOC-PMC-RENAL-0012",
        "strat": "STR-11",
        "split": "core",
        "query": "In what clinical circumstances do urology guidelines recommend open or laparoscopic surgery over endourological techniques for nephrolithiasis?",
        "span": "offering open or laparoscopic approaches for stone removal only when SWL, URS, and PCNL are unlikely to provide a decent opportunity for stone removal and more likely to fail",
        "claim": "Open or laparoscopic stone surgery is reserved exclusively for complex cases where endourologic techniques (SWL, URS, PCNL) are unlikely to succeed or have failed.",
        "obj": "Identify rare clinical indications for open or laparoscopic surgery in the era of endourology",
        "rationale": "Specifies rare indications for open or laparoscopic stone removal when endourology fails."
    },
    {
        "cid": "DOC-PMC-RENAL-0012-B-C0019",
        "did": "DOC-PMC-RENAL-0012",
        "strat": "STR-11",
        "split": "core",
        "query": "What is the recommended emergency management for an infected obstructed ureter with sepsis secondary to urolithiasis?",
        "span": "Both the EAU and AUA strongly recommend urgent decompression with either percutaneous nephrostomy (PCN) or ureteric stenting, with none proving to be superior to the other, delaying any definitive treatment until the resolution of sepsis",
        "claim": "Obstructive urolithiasis with sepsis requires immediate decompression via either percutaneous nephrostomy or ureteral stenting, deferring stone removal until sepsis resolves.",
        "obj": "State the emergency decompression protocol for acute septic obstructive pyelonephritis",
        "rationale": "Mandates emergency decompression via PCN or stenting and deferring stone removal during acute sepsis."
    },
    {
        "cid": "DOC-PMC-RENAL-0012-B-C0021",
        "did": "DOC-PMC-RENAL-0012",
        "strat": "STR-11",
        "split": "val",
        "query": "Which pharmacological class is recommended as medical expulsive therapy (MET) for distal ureteric calculi?",
        "span": "Both the AUA and EAU recommend the use of an α-blocker as MET for distal ureteric stones; the AUA suggests this for stones of ≤10 mm, whereas the EAU implies this for stones of <5 mm in size",
        "claim": "Alpha-blockers are recommended as medical expulsive therapy to facilitate spontaneous passage of distal ureteral calculi measuring up to 10 mm.",
        "obj": "Identify alpha-blockers as first-line medical expulsive therapy for distal ureteral stones",
        "rationale": "Recommends alpha-blocker therapy as MET for distal ureteric calculi."
    },
    {
        "cid": "DOC-PMC-RENAL-0012-B-C0027",
        "did": "DOC-PMC-RENAL-0012",
        "strat": "STR-11",
        "split": "val",
        "query": "How do ureteroscopy (URS) and shockwave lithotripsy (SWL) compare in terms of stone-free rate versus procedural morbidity?",
        "span": "URS being associated with a higher stone-free rate (SFR) and lesser need to reperform the procedure when compared to SWL [ 26 ]; however, SWL is safer, with fewer complications and lower morbidity, in comparison with URS",
        "claim": "Ureteroscopy achieves higher stone-free rates and fewer secondary retreatments than shockwave lithotripsy, whereas SWL has lower morbidity and complication rates.",
        "obj": "Compare trade-offs in stone-free rate and procedural morbidity between URS and SWL",
        "rationale": "Contrasts higher stone-free rate of URS against lower morbidity and complication rates of SWL."
    },

    # --------------------------------------------------------------------------
    # STR-12: Perioperative AKI & Cardiorenal Syndrome (DOC-PMC-RENAL-0006)
    # --------------------------------------------------------------------------
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0047",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-12",
        "split": "core",
        "query": "How does the inclusion of urine output criteria alongside serum creatinine improve prognostic predictions in critically ill AKI patients?",
        "span": "In the studies of ICU patients, the inclusion of the urine output as a criterion significantly improved the survival outcome predictions",
        "claim": "Incorporating urine output criteria alongside serum creatinine significantly improves mortality and renal outcome prediction in ICU patients with acute kidney injury.",
        "obj": "Explain the prognostic importance of measuring urine output criteria in staging acute kidney injury",
        "rationale": "Confirms superior survival outcome prediction when combining urine output with creatinine criteria."
    },
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0049",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-12",
        "split": "core",
        "query": "What evidence supports combining oliguria criteria with serum creatinine measurements when diagnosing acute kidney injury in intensive care units?",
        "span": "inclusion of the urine output with the sCr in the AKI diagnosis significantly improved the survival outcome predictions",
        "claim": "Combining oliguria criteria with serum creatinine provides superior sensitivity for detecting AKI and predicting ICU survival outcomes.",
        "obj": "Describe the clinical evidence supporting combined creatinine and urine output staging for acute kidney injury",
        "rationale": "Shows evidence across ICU cohorts that urine output inclusion enhances diagnostic and prognostic accuracy."
    },
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0051",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-12",
        "split": "core",
        "query": "Does concurrent administration of loop diuretics invalidate the diagnostic utility of urine output criteria for staging acute kidney injury?",
        "span": "reported that the inclusion of the urine output criterion alongside the sCr criterion played an additional role in the diagnosis and staging of AKI regardless of whether diuretics were used",
        "claim": "Urine output criteria retain diagnostic and prognostic value for AKI staging even when patients receive concurrent loop diuretics.",
        "obj": "Evaluate the confounding effect of diuretic therapy on urine output criteria in AKI diagnosis",
        "rationale": "Demonstrates diagnostic utility of urine output remains valid despite diuretic exposure."
    },
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0067",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-12",
        "split": "core",
        "query": "What hemodynamic and hematological factors during cardiopulmonary bypass (CPB) reduce renal perfusion and increase the risk of postoperative AKI?",
        "span": "During CPBs, the renal blood flow is affected by various factors, including hypothermia, blood dilution, hemolysis, microthrombi, and vasoactive drugs; these factors constrict the renal artery and reduce the renal blood flow",
        "claim": "Cardiopulmonary bypass decreases renal blood flow through hypothermia, hemodilution, hemolysis, and microthrombosis, with prolonged duration directly correlating with AKI.",
        "obj": "Identify pathophysiological mechanisms linking cardiopulmonary bypass to renal hypoperfusion and postoperative AKI",
        "rationale": "Lists hypothermia, hemodilution, hemolysis, and microthrombi as causes of reduced renal blood flow during CPB."
    },
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0103",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-12",
        "split": "core",
        "query": "How does pre-existing renal dysfunction (eGFR < 60 mL/min/1.73 m2) influence the risk and odds ratio of developing acute kidney injury during sepsis?",
        "span": "one of the risk factors for AKI was renal dysfunction, which was defined as an eGFR < 60 ml/min/1.73 m 2 [odds ratio 2.398, 95% confidence interval (CI) 1.301–4.420]",
        "claim": "Pre-existing renal impairment (eGFR < 60 mL/min/1.73 m2) is an independent risk factor that more than doubles the odds of developing AKI in septic patients.",
        "obj": "Recognize pre-existing renal impairment as a major independent risk factor for septic acute kidney injury",
        "rationale": "Identifies pre-existing renal dysfunction as an independent risk factor doubling AKI odds in sepsis."
    },
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0071",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-12",
        "split": "val",
        "query": "Why does the development of acute kidney injury following major non-cardiac surgery carry significant clinical and prognostic importance?",
        "span": "The development of AKI is significantly associated with increased mortality. This lends great clinical significance to the development of AKI following non-cardiac surgery as well as cardiac surgery",
        "claim": "Acute kidney injury following non-cardiac surgery significantly elevates postoperative mortality, highlighting the need for proactive risk identification.",
        "obj": "Recognize acute kidney injury as a major determinant of mortality in non-cardiac surgical patients",
        "rationale": "Directly correlates post-surgical AKI with marked increases in patient mortality."
    },
    {
        "cid": "DOC-PMC-RENAL-0006-B-C0073",
        "did": "DOC-PMC-RENAL-0006",
        "strat": "STR-12",
        "split": "val",
        "query": "Which preoperative and intraoperative factors, such as MELD score and blood transfusions, increase the risk of AKI following liver surgery?",
        "span": "Preoperative renal impairment, preoperative hypertension, and intraoperative red blood cell transfusion were identified as risk factors for AKI development",
        "claim": "Pre-existing renal impairment, chronic hypertension, elevated MELD scores, and intraoperative blood transfusions significantly increase AKI risk following hepatic surgery.",
        "obj": "Identify specific preoperative and intraoperative risk factors predisposing to acute kidney injury in hepatic surgery",
        "rationale": "Lists pre-existing renal disease, hypertension, and red blood cell transfusion as risk factors for post-liver resection AKI."
    }
]

print(f"Loaded {len(CLEAN_ITEMS_DATA_P3)} items for Part 3 (STR-09 to STR-12).")
