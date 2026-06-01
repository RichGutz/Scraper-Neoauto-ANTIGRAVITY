import os
from drive_api import get_drive_service, create_folder, upload_file

CRM_ROOT_FOLDER_ID = "1_BvUhnTI5J987wsJao4sK3mDX31uNKcd"

def run_test():
    print("Iniciando prueba de subida con OAuth (User Token)...")
    
    print("1. Obteniendo servicio de Google Drive (token.json)...")
    try:
        service = get_drive_service()
        print("   OK - Servicio obtenido con exito.")
    except Exception as e:
        print(f"   ERROR - al obtener servicio: {e}")
        return

    # 2. Variables de prueba
    fecha_venta = "20260601"
    placa = "XYZ123"
    folder_vehiculo = f"{fecha_venta}_{placa}"
    
    # 3. Crear Carpeta Padre
    print(f"\n2. Creando carpeta padre para el vehiculo: '{folder_vehiculo}'")
    success, parent_id_or_err = create_folder(service, CRM_ROOT_FOLDER_ID, folder_vehiculo)
    
    if not success:
        print(f"   ERROR - al crear carpeta padre: {parent_id_or_err}")
        return
        
    print(f"   OK - Carpeta padre creada (ID: {parent_id_or_err})")
    parent_folder_id = parent_id_or_err
    
    # 4. Crear Subcarpetas
    subcarpetas = ["Fotos", "Testimonios", "Tarjeta De propiedad"]
    sub_ids = {}
    
    print("\n3. Creando subcarpetas por defecto...")
    for sub in subcarpetas:
        suc, sub_id_err = create_folder(service, parent_folder_id, sub)
        if suc:
            sub_ids[sub] = sub_id_err
            print(f"   OK - Subcarpeta '{sub}' creada.")
        else:
            print(f"   ERROR - creando '{sub}': {sub_id_err}")
            return
            
    # 5. Generar Archivos Dummy y Subir
    print("\n4. Subiendo archivos Dummy...")
    
    # Dummy Foto 1
    foto_bytes = b"Esto es una foto de prueba (FOTO 1)."
    foto_name = f"{folder_vehiculo}_FOTO1.txt"
    suc_f, res_f = upload_file(service, foto_bytes, foto_name, sub_ids["Fotos"], mime_type='text/plain')
    if suc_f:
        print(f"   OK - Foto Dummy subida: {foto_name}")
        print(f"      Link: {res_f.get('webViewLink')}")
    else:
        print(f"   ERROR - subiendo Foto: {res_f}")
        
    # Dummy Testimonio
    testimonio_bytes = b"Esto es un pdf falso de testimonio de compra."
    testimonio_name = f"{folder_vehiculo}_TESTIMONIO_COMPRA.pdf"
    suc_t, res_t = upload_file(service, testimonio_bytes, testimonio_name, sub_ids["Testimonios"], mime_type='application/pdf')
    if suc_t:
        print(f"   OK - Testimonio Dummy subido: {testimonio_name}")
        print(f"      Link: {res_t.get('webViewLink')}")
    else:
        print(f"   ERROR - subiendo Testimonio: {res_t}")

    # Dummy Tarjeta de propiedad
    tarjeta_bytes = b"Esto es una imagen falsa de tarjeta."
    tarjeta_name = f"{folder_vehiculo}_TARJETA_DE_PROPIEDAD.png"
    suc_tp, res_tp = upload_file(service, tarjeta_bytes, tarjeta_name, sub_ids["Tarjeta De propiedad"], mime_type='image/png')
    if suc_tp:
        print(f"   OK - Tarjeta Dummy subida: {tarjeta_name}")
        print(f"      Link: {res_tp.get('webViewLink')}")
    else:
        print(f"   ERROR - subiendo Tarjeta: {res_tp}")

    print("\nPrueba concluida exitosamente!")

if __name__ == "__main__":
    run_test()
