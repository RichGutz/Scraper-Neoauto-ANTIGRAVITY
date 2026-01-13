import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime

# Paths
RULES_CSV_PATH = Path(__file__).parent.parent / "Core" / "reglas_modelos_base.csv"
BACKUP_PATH = RULES_CSV_PATH.with_suffix(f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

# New Rules to Add (Detected from Analysis)
# Format: (make, pattern, target_model)
NEW_RULES = [
    # TOYOTA
    ("toyota", "hiace", "Hiace"),
    ("toyota", "prius", "Prius"),
    ("toyota", "tacoma", "Tacoma"),
    ("toyota", "raize", "Raize"),
    ("toyota", "4runner", "4Runner"),
    ("toyota", "4 runner", "4Runner"),
    ("toyota", "agya", "Agya"),
    ("toyota", "avanza", "Avanza"),
    ("toyota", "c-hr", "C-HR"),
    ("toyota", "chr", "C-HR"),
    ("toyota", "rush", "Rush"),
    ("toyota", "land cruiser prado", "Land Cruiser Prado"),
    
    # KIA
    ("kia", "sonet", "Sonet"),
    ("kia", "soluto", "Soluto"),
    ("kia", "seltos", "Seltos"),
    ("kia", "carens", "Carens"),
    ("kia", "carnival", "Carnival"),
    ("kia", "niro", "Niro"),
    ("kia", "k2700", "K2700"),
    ("kia", "mohave", "Mohave"),
    ("kia", "optima", "Optima"),
    
    # HYUNDAI
    ("hyundai", "creta", "Creta"),
    ("hyundai", "venue", "Venue"),
    ("hyundai", "palisade", "Palisade"),
    ("hyundai", "staria", "Staria"),
    ("hyundai", "veloster", "Veloster"),
    ("hyundai", "kona", "Kona"),
    ("hyundai", "atos", "Atos"),
    
    # NISSAN
    ("nissan", "kicks", "Kicks"),
    ("nissan", "versa", "Versa"),
    ("nissan", "note", "Note"),
    ("nissan", "juke", "Juke"),
    ("nissan", "march", "March"),
    ("nissan", "qashqai", "Qashqai"),
    ("nissan", "murano", "Murano"),
    ("nissan", "xtrail", "X-Trail"),
    ("nissan", "x-trail", "X-Trail"),
    ("nissan", "x trail", "X-Trail"),
    ("nissan", "frontier", "Frontier"),
    # JEEP
    ("jeep", "grand cherokee", "Grand Cherokee"),
    ("jeep", "cherokee", "Cherokee"),
    ("jeep", "compass", "Compass"),
    ("jeep", "renegade", "Renegade"),
    ("jeep", "wrangler", "Wrangler"),
    ("jeep", "gladiator", "Gladiator"),

    # SUBARU
    ("subaru", "forester", "Forester"),
    ("subaru", "xv", "XV"),
    ("subaru", "crosstrek", "Crosstrek"),
    ("subaru", "outback", "Outback"),
    ("subaru", "impreza", "Impreza"),
    ("subaru", "wrx", "WRX"),
    ("subaru", "evoltis", "Evoltis"),

    # BMW
    ("bmw", "x1", "X1"),
    ("bmw", "x2", "X2"),
    ("bmw", "x3", "X3"),
    ("bmw", "x4", "X4"),
    ("bmw", "x5", "X5"),
    ("bmw", "x6", "X6"),
    ("bmw", "x7", "X7"),
    ("bmw", "serie 1", "Serie 1"),
    ("bmw", "serie 2", "Serie 2"),
    ("bmw", "serie 3", "Serie 3"),
    ("bmw", "serie 4", "Serie 4"),
    ("bmw", "serie 5", "Serie 5"),
    ("bmw", "i3", "i3"),
    ("bmw", "ix", "iX"),
    ("bmw", "ix1", "iX1"),
    ("bmw", "ix3", "iX3"),

    # AUDI
    ("audi", "a3", "A3"),
    ("audi", "a4", "A4"),
    ("audi", "a5", "A5"),
    ("audi", "a6", "A6"),
    ("audi", "q2", "Q2"),
    ("audi", "q3", "Q3"),
    ("audi", "q5", "Q5"),
    ("audi", "q7", "Q7"),
    ("audi", "q8", "Q8"),
    ("audi", "e-tron", "e-tron"),
    ("audi", "etron", "e-tron"),
]


def clean_target_name(target, make):
    """Removes Make name from Target Model name (case insensitive)"""
    if not isinstance(target, str):
        return str(target) if target is not None else ""
        
    target_lower = target.lower()
    make_lower = make.lower()
    
    # Simple check: if target starts with make
    # e.g. "Kia Sportage" starts with "kia"
    if target_lower.startswith(make_lower + " "):
        # Return substring from len(make) + 1
        return target[len(make)+1:]
    elif target_lower == make_lower:
         # Edge case: Target is just "Kia"
         return target
    
    return target

def main():
    print(f"Reading rules from {RULES_CSV_PATH}...")
    df = pd.read_csv(RULES_CSV_PATH)
    initial_count = len(df)
    
    # 1. CLEAN EXISTING TARGETS
    print("Cleaning existing targets (Removing Brand Name)...")
    cleaned_count = 0
    for idx, row in df.iterrows():
        original = row['model_base_target']
        cleaned = clean_target_name(original, row['make_rule_match'])
        
        if original != cleaned:
            df.at[idx, 'model_base_target'] = cleaned
            cleaned_count += 1
            
    print(f"  ✓ Cleaned {cleaned_count} existing rules.")
    
    # 2. ADD NEW RULES
    print("Adding new rules...")
    new_rows = []
    
    # Check for duplicates to avoid adding same rule twice
    # Key = (make, pattern)
    existing_keys = set(zip(df['make_rule_match'].str.lower(), df['model_pattern_input_lower'].str.lower()))
    
    added_count = 0
    for make, pattern, target in NEW_RULES:
        if (make.lower(), pattern.lower()) not in existing_keys:
            new_rows.append({
                'make_rule_match': make,
                'model_pattern_input_lower': pattern.lower(),
                'model_base_target': target, # Already clean in our list
                'match_type': 'contains',    # Use CONTAINS for robustness
                'priority': 2,               # High priority for these explicit fixes
                'pattern_length': len(pattern)
            })
            added_count += 1
            
    if new_rows:
        df_new = pd.DataFrame(new_rows)
        df = pd.concat([df, df_new], ignore_index=True)
    
    print(f"  ✓ Added {added_count} new rules.")
    
    # 3. SAVE
    # Backup first
    shutil.copy2(RULES_CSV_PATH, BACKUP_PATH)
    print(f"Backup saved to: {BACKUP_PATH.name}")
    
    # Re-sort just in case
    df.sort_values(by=['priority', 'pattern_length'], ascending=[False, False], inplace=True)
    
    df.to_csv(RULES_CSV_PATH, index=False)
    print(f"Saved updated rules to {RULES_CSV_PATH}")
    print(f"Total Rules: {len(df)} (Was: {initial_count})")
    
    
    # 4. SHOW SUMMARY TABLE
    print("\n" + "="*80)
    print(f"{'MARCA':<15} | {'MODELO NORMALIZADO':<25} | {'PATRONES (Ejemplos Agrupados)'}")
    print("="*80)
    
    # Group by (Make, Target) to show what patterns map to what
    grouped = df.groupby(['make_rule_match', 'model_base_target'])['model_pattern_input_lower'].apply(list)
    
    # Filter to show only the ones we care about (Target Brands + meaningful groups)
    target_brands = ["kia", "toyota", "hyundai", "nissan"]
    
    for (make, target), patterns in grouped.items():
        if make not in target_brands:
            continue
            
        # Only show if there are interesting patterns or if it's one of our new ones
        is_relevant = False
        target_lower = target.lower()
        
        # Check if this target is in our NEW_RULES targets
        for _, _, new_t in NEW_RULES:
            if new_t == target:
                is_relevant = True
                break
        
        # Or if it has multiple patterns
        if len(patterns) > 1:
            is_relevant = True
            
        if is_relevant:
            patterns_str = ", ".join(patterns[:5]) # Show max 5 patterns
            if len(patterns) > 5: patterns_str += "..."
            
            print(f"{make.upper():<15} | {target:<25} | {patterns_str}")

if __name__ == "__main__":
    main()
