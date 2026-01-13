from auto_contact_neoauto import autenticar_google, create_google_contact
from googleapiclient.discovery import build

def main():
    print("=== INICIANDO BACKFILL DE CONTACTOS GOOGLE (V3: +51 & MyContacts) ===")
    
    # 1. Autenticar
    creds = autenticar_google()
    if not creds:
        print("Fallo de autenticación.")
        return

    # 2. Lista Manual
    contactos = [
        {
            'nombre_completo': 'Ana María Galdos Valdes',
            'telefono_real': '975054300',
            'info_auto': 'Kia Picanto 2017'
        },
        {
            'nombre_completo': 'Jorge Huaman Herencia',
            'telefono_real': '999221760',
            'info_auto': 'Hyundai Creta 2024'
        },
        {
            'nombre_completo': 'Gisella Marrufo Malmaceda',
            'telefono_real': '998239387',
            'info_auto': 'Hyundai Santa Fe 2017'
        }
    ]

    # 3. Procesar
    for c in contactos:
        create_google_contact(creds, c)
    
    print("\nBackfill Completado.")

if __name__ == "__main__":
    main()
