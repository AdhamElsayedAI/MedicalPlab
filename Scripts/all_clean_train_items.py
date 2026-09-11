"""
MedicalPlab Renal V5 — Complete Clean Train Items (N=80)
========================================================
Combines Part 1, Part 2, and Part 3 with C0023 replacing C0022.
Exactly 60 CORE and 20 VAL items across 12 curriculum strata.
"""

from clean_items_data_p1 import CLEAN_ITEMS_DATA_P1
from clean_items_data_p2 import CLEAN_ITEMS_DATA_P2
from clean_items_data_p3 import CLEAN_ITEMS_DATA_P3

# Replace C0022 with C0023 in Part 1
p1_items = []
for it in CLEAN_ITEMS_DATA_P1:
    if it["cid"] == "DOC-PMC-RENAL-0002-B-C0022":
        p1_items.append({
            "cid": "DOC-PMC-RENAL-0002-B-C0023",
            "did": "DOC-PMC-RENAL-0002",
            "strat": "STR-01",
            "split": "val",
            "query": "What physiological marker molecule is freely filtered across the glomerular filtration barrier to evaluate small molecule permselectivity in glomerulus-on-a-chip models?",
            "span": "capacity of filtering molecules that are freely filtered by glomerulus in vivo, such as inulin",
            "claim": "Inulin is freely filtered across the glomerular filtration barrier and serves as a functional marker of small-molecule permselectivity.",
            "obj": "Evaluate small molecule filtration and inulin handling across the glomerular filtration barrier",
            "rationale": "Demonstrates free filtration of inulin across the functional glomerular microfluidic barrier."
        })
    else:
        p1_items.append(it)

ALL_CLEAN_ITEMS_DATA = p1_items + CLEAN_ITEMS_DATA_P2 + CLEAN_ITEMS_DATA_P3

assert len(ALL_CLEAN_ITEMS_DATA) == 80, f"Expected 80 items, got {len(ALL_CLEAN_ITEMS_DATA)}"
core_count = sum(1 for it in ALL_CLEAN_ITEMS_DATA if it["split"] == "core")
val_count = sum(1 for it in ALL_CLEAN_ITEMS_DATA if it["split"] == "val")
assert core_count == 60, f"Expected 60 core items, got {core_count}"
assert val_count == 20, f"Expected 20 val items, got {val_count}"

print(f"Successfully loaded all {len(ALL_CLEAN_ITEMS_DATA)} clean train items (CORE: {core_count}, VAL: {val_count}).")
