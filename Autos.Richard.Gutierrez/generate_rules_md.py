import pandas as pd
from pathlib import Path

# Paths
RULES_CSV_PATH = Path(__file__).parent.parent / "Core" / "reglas_modelos_base.csv"
OUTPUT_MD_PATH = Path(__file__).parent / "MODEL_RULES_SUMMARY.md"

def main():
    print(f"Reading rules from {RULES_CSV_PATH}...")
    if not RULES_CSV_PATH.exists():
        print("Error: Rules file not found.")
        return
        
    df = pd.read_csv(RULES_CSV_PATH)
    
    # Sort for better reading: Make -> Target Model -> Pattern
    df['make_rule_match'] = df['make_rule_match'].astype(str).str.upper()
    df.sort_values(by=['make_rule_match', 'model_base_target', 'model_pattern_input_lower'], inplace=True)
    
    md_content = "# Resumen de Reglas de Normalización de Modelos\n\n"
    md_content += f"**Total de Reglas:** {len(df)}\n\n"
    md_content += "Este archivo muestra cómo se agrupan los modelos crudos (Patrones) en un Modelo Normalizado limpio.\n\n"
    
    # Filter for target brands only to keep it relevant
    target_brands = [
        "KIA", "TOYOTA", "HYUNDAI", "NISSAN", "MITSUBISHI",
        "BMW", "AUDI", "SUBARU", "JEEP"
    ]
    
    md_content += "| MARCA | MODELO NORMALIZADO | PATRONES AGRUPADOS (Inputs que activan la regla) |\n"
    md_content += "| :--- | :--- | :--- |\n"
    
    grouped = df.groupby(['make_rule_match', 'model_base_target'])['model_pattern_input_lower'].apply(list)
    
    for (make, target), patterns in grouped.items():
        if make not in target_brands:
            continue
            
        patterns.sort()
        # Format patterns as a list or comma string
        # If there are many, we might want to truncate, but user wants to see them.
        patterns_str = ", ".join([f"`{p}`" for p in patterns])
        
        md_content += f"| **{make}** | **{target}** | {patterns_str} |\n"
        
    with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"✅ Markdown summary generated at: {OUTPUT_MD_PATH}")

if __name__ == "__main__":
    main()
