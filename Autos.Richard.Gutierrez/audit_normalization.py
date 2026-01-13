import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

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
                print(f"✓ Loaded {len(LOADED_MODEL_RULES)} model rules")
            else:
                print(f"❌ File not found: {RULES_CSV_PATH}")
                LOADED_MODEL_RULES = pd.DataFrame()
        except Exception as e:
            print(f"Error loading rules: {e}")
            LOADED_MODEL_RULES = pd.DataFrame()

def get_model_base(model_name: str, make_name: str) -> str:
    if pd.isna(model_name) or model_name == "Desconocido":
        return "Desconocido"
    model_lower = model_name.lower().strip()
    make_lower = make_name.lower().strip()
    
    if LOADED_MODEL_RULES is not None and not LOADED_MODEL_RULES.empty:
        rules_for_make = LOADED_MODEL_RULES[LOADED_MODEL_RULES['make_rule_match'] == make_lower]
        for _, rule in rules_for_make.iterrows():
            if (rule['match_type'] == 'exact' and model_lower == rule['model_pattern_input_lower']) or \
               (rule['match_type'] == 'startswith' and model_lower.startswith(rule['model_pattern_input_lower'])) or \
               (rule['match_type'] == 'contains' and rule['model_pattern_input_lower'] in model_lower):
                return rule['model_base_target']
    return model_name

def main():
    print("Connecting to Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    load_rules()
    
    print("Fetching distinct models from last 2000 records...")
    # Fetch recent records to get improved likelihood of seeing what user sees
    response = supabase.table("autos_detalles") \
        .select("Make, Model") \
        .order("id", desc=True) \
        .limit(2000) \
        .execute()
        
    df = pd.DataFrame(response.data)
    if df.empty:
        print("No data found.")
        return

    # Normalize Make for consistent grouping
    df['Make'] = df['Make'].str.upper().str.strip()
    df['Model'] = df['Model'].str.upper().str.strip()
    
    # Get unique combinations
    unique_models = df[['Make', 'Model']].drop_duplicates().sort_values(['Make', 'Model'])
    
    print(f"\nAnalyzing {len(unique_models)} unique models found...")
    print(f"\n{'MAKER':<15} | {'RAW MODEL (Input)':<30} | {'NORMALIZED (Result)':<30} | {'CHANGE?'}")
    print("-" * 100)
    
    # Filter for relevant brands if list is too long
    target_brands = ["KIA", "TOYOTA", "HYUNDAI", "NISSAN"]
    
    for _, row in unique_models.iterrows():
        make = row['Make']
        model_raw = row['Model']
        
        # Only show specific brands to keep output readable for now, or all if small
        if make not in target_brands:
            continue
            
        normalized = get_model_base(model_raw, make)
        
        is_changed = "✅ OK" if normalized == model_raw else "🔄 MODIFIED"
        # Highlight cases where normalization might be FAILING (i.e. returning raw verbose names)
        # If result closely matches input but is long, user might hate it
        
        print(f"{make:<15} | {model_raw:<30} | {normalized:<30} | {is_changed}")

if __name__ == "__main__":
    main()
