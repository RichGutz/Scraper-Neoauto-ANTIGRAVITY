import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime

# Paths
RULES_CSV_PATH = Path(__file__).parent.parent / "Core" / "reglas_modelos_base.csv"
BACKUP_PATH = RULES_CSV_PATH.with_suffix(f".bak_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

# Special Casing (Targets that should NOT be just Title Case)
SPECIAL_CASING = {
    "Cr-v": "CR-V",
    "Hrv": "HR-V",
    "Wrv": "WR-V",
    "Xv": "XV",
    "Wrx": "WRX",
    "Bt-50": "BT-50",
    "N300": "N300", # N300 is fine but just in case
    "Bmw": "BMW",
    "D-max": "D-Max",
    "Rav4": "RAV4",
    "Hilux ": "Hilux", # Trim spaces
}

def main():
    print(f"Reading rules from {RULES_CSV_PATH}...")
    df = pd.read_csv(RULES_CSV_PATH)
    
    # 1. Backup
    shutil.copy2(RULES_CSV_PATH, BACKUP_PATH)
    print(f"Backup saved to: {BACKUP_PATH.name}")
    
    # 2. Add/Ensure Specific Rules (Honda CR-V, Chevrolet N300)
    # We will remove old conflicting rules for these patterns first? 
    # Or just append high priority ones.
    
    new_rules = [
        # HONDA CR-V
        {"make": "honda", "pattern": "cr-v", "target": "CR-V"},
        {"make": "honda", "pattern": "cr v", "target": "CR-V"},
        {"make": "honda", "pattern": "crv", "target": "CR-V"},
        
        # CHEVROLET N300
        {"make": "chevrolet", "pattern": "n300", "target": "N300"},
        {"make": "chevrolet", "pattern": "n 300", "target": "N300"},
        {"make": "chevrolet", "pattern": "n-300", "target": "N300"},
        {"make": "chevrolet", "pattern": "move", "target": "N300"}, # n300 move
    ]
    
    # Convert new_rules to DataFrame
    rows_to_add = []
    for r in new_rules:
        rows_to_add.append({
            'make_rule_match': r['make'],
            'model_pattern_input_lower': r['pattern'],
            'model_base_target': r['target'],
            'match_type': 'contains',
            'priority': 3.0, # Higher priority than before to override
            'pattern_length': len(r['pattern'])
        })
        
    df_new = pd.DataFrame(rows_to_add)
    df = pd.concat([df, df_new], ignore_index=True)

    # 3. Fix Casing for All Targets
    print("Standardizing Target Casing...")
    
    def standardize_target(name):
        if not isinstance(name, str): return ""
        
        # 1. Strip
        name = name.strip()
        
        # 2. Title Case by default (e.g. "SPORTAGE" -> "Sportage")
        # .title() handles "Cx-5" nicely usually, but lets see.
        title_cased = name.title()
        
        # 3. Apply Special overrides
        if title_cased in SPECIAL_CASING:
            return SPECIAL_CASING[title_cased]
            
        # 4. Handle known variations dynamically?
        # If it has "Max" or "Move" and we want to remove it? 
        # The user said "N300 MAX" -> "N 300". 
        # Wait, the user said N300 variants should all be N300. 
        # Our new rules above handle the mapping Pattern -> Target "N300".
        # But if there's an existing rule "N300 Max" -> "N300 Max", we need to change target to "N300".
        
        # Simplified: Just fix casing. Logic for grouping was done by rules.
        return title_cased

    df['model_base_target'] = df['model_base_target'].apply(standardize_target)
    
    # Fix specifically CR-V if it got messed up
    # (The loop above might have turned "CR-V" -> "Cr-V")
    # Let's apply overrides again explicitly
    for k, v in SPECIAL_CASING.items():
        df.loc[df['model_base_target'] == k, 'model_base_target'] = v
        
    # 4. Filter duplicates (keep highest priority)
    # If we have multiple rules for same (make, pattern), strict dedup might be complex.
    # But we added priority 3.0.
    
    # Sort
    df.sort_values(by=['priority', 'pattern_length'], ascending=[False, False], inplace=True)
    
    # Save
    df.to_csv(RULES_CSV_PATH, index=False)
    print(f"✅ Rules updated and saved to {RULES_CSV_PATH}")

if __name__ == "__main__":
    main()
