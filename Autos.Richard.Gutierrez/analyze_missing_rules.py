import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from collections import defaultdict
import difflib

# Load environment variables
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Rules path
RULES_CSV_PATH = Path(__file__).parent.parent / "Core" / "reglas_modelos_base.csv"
LOADED_MODEL_RULES = None

def load_rules():
    global LOADED_MODEL_RULES
    if LOADED_MODEL_RULES is None:
        try:
            if RULES_CSV_PATH.exists():
                LOADED_MODEL_RULES = pd.read_csv(RULES_CSV_PATH)
                LOADED_MODEL_RULES['make_rule_match'] = LOADED_MODEL_RULES['make_rule_match'].astype(str).str.lower().str.strip()
                LOADED_MODEL_RULES['model_pattern_input_lower'] = LOADED_MODEL_RULES['model_pattern_input_lower'].astype(str).str.lower().str.strip()
                LOADED_MODEL_RULES.sort_values(by=['priority', 'pattern_length'], ascending=[False, False], inplace=True)
            else:
                LOADED_MODEL_RULES = pd.DataFrame()
        except Exception as e:
            print(f"Error loading rules: {e}")
            LOADED_MODEL_RULES = pd.DataFrame()

def get_model_base_debug(model_name: str, make_name: str) -> tuple[str, bool]:
    """Returns (normalized_name, is_normalized)"""
    if pd.isna(model_name) or model_name == "Desconocido":
        return "Desconocido", False
        
    model_lower = model_name.lower().strip()
    make_lower = make_name.lower().strip()
    
    if LOADED_MODEL_RULES is not None and not LOADED_MODEL_RULES.empty:
        rules_for_make = LOADED_MODEL_RULES[LOADED_MODEL_RULES['make_rule_match'] == make_lower]
        for _, rule in rules_for_make.iterrows():
            if (rule['match_type'] == 'exact' and model_lower == rule['model_pattern_input_lower']) or \
               (rule['match_type'] == 'startswith' and model_lower.startswith(rule['model_pattern_input_lower'])) or \
               (rule['match_type'] == 'contains' and rule['model_pattern_input_lower'] in model_lower):
                return rule['model_base_target'], True
                
    return model_name, False

def main():
    print("Connecting to Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    load_rules()
    
    # 1. Fetch ALL distinct models
    print("Fetching ALL distinct models from database...")
    # Using a larger limit to be safe, though unique models shouldn't be massive
    response = supabase.table("autos_detalles") \
        .select("Make, Model") \
        .order("id", desc=True) \
        .limit(10000) \
        .execute()
        
    df = pd.DataFrame(response.data)
    if df.empty:
        print("No data.")
        return

    df['Make'] = df['Make'].str.upper().str.strip()
    df['Model'] = df['Model'].str.upper().str.strip()
    unique_rows = df[['Make', 'Model']].drop_duplicates()
    
    # 2. Identify UN-NORMALIZED models
    missing_dict = defaultdict(list)
    
    target_brands = ["KIA", "TOYOTA", "HYUNDAI", "NISSAN", "MITSUBISHI", "FORD", "CHEVROLET",
                     "MAZDA", "SUBARU", "SUZUKI", "HONDA",
                     "BMW", "MERCEDES-BENZ", "AUDI", "VOLKSWAGEN", "VOLVO", "PORSCHE",
                     "JEEP", "DODGE", "RAM"]
    print(f"Scanning {len(unique_rows)} unique models for brands: {', '.join(target_brands)}...\n")
    
    for _, row in unique_rows.iterrows():
        make = row['Make']
        model = row['Model']
        
        if make not in target_brands:
            continue
            
        normalized_name, is_matched = get_model_base_debug(model, make)
        
        if not is_matched:
            missing_dict[make].append(model)

    # 3. Smart Grouping & Display
    # We want to show: TOYOTA: [PROPOSED_RULE] -> [LIST OF VICTIMS]
    
    print("="*80)
    print("CANDIDATOS A NUEVAS REGLAS (Agrupados por similitud)")
    print("="*80)
    
    for make, models_list in missing_dict.items():
        if not models_list:
            continue
            
        print(f"\n--- {make} ({len(models_list)} variantes sin regla) ---")
        
        # Simple clustering by first word
        clusters = defaultdict(list)
        for m in models_list:
            first_word = m.split()[0]
            clusters[first_word].append(m)
            
        # Display clusters
        for key_word, variants in sorted(clusters.items()):
            # Heuristic: If we have multiple variants sharing a word, suggest a rule
            # Rule suggestion: "TOYOTA COROLLA" -> "Toyota Corolla"
            
            # Formatting:
            # HIACE (3): HIACE, HIACE GL, NEW HIACE
            
            variants_str = ", ".join(sorted(variants))
            count = len(variants)
            
            # Suggest a target name (Title Case the make + keyword)
            suggested_target = f"{make.title()} {key_word.title()}"
            
            print(f"[{count}] {key_word:<15}  -> Sugerencia: '{suggested_target}'")
            print(f"      Variantes: {variants_str}")
            print("-" * 60)

if __name__ == "__main__":
    main()
