from PIL import Image
import sys

def png_to_ico(png_path, ico_path):
    """Convierte PNG a ICO para usar como ícono de Windows"""
    img = Image.open(png_path)
    
    # Redimensionar a tamaños estándar de íconos de Windows
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    # Crear lista de imágenes en diferentes tamaños
    images = []
    for size in icon_sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        images.append(resized)
    
    # Guardar como ICO
    images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in images])
    print(f"✓ Ícono creado: {ico_path}")

if __name__ == "__main__":
    png_path = r"C:\Users\rguti\Scraper.Neoauto\Anny.Bot\anny_bot_icon.png"
    ico_path = r"C:\Users\rguti\Scraper.Neoauto\Anny.Bot\anny_bot_icon.ico"
    
    try:
        png_to_ico(png_path, ico_path)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
