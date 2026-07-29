import os
import sys
import subprocess

try:
    import markdown
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown"])
    import markdown

md_file = r'C:\Users\rguti\Scraper.Neoauto\CRM-NEOAUTO\Tributario\Reglas.Tributarias.md'
out_html = r'C:\Users\rguti\Scraper.Neoauto\CRM-NEOAUTO\Tributario\Reglas.Tributarias.html'
out_pdf = r'C:\Users\rguti\Scraper.Neoauto\CRM-NEOAUTO\Tributario\Reglas.Tributarias.pdf'

with open(md_file, 'r', encoding='utf-8') as f:
    text = f.read()

html_content = markdown.markdown(text, extensions=['extra', 'tables', 'toc'])

full_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: #333;
        margin: 40px;
    }}
    @page {{
        size: A4 landscape;
        margin: 15mm;
    }}
    h1 {{ color: #004a99; border-bottom: 2px solid #004a99; padding-bottom: 10px; }}
    h2 {{ color: #004a99; margin-top: 30px; page-break-before: always; border-bottom: 1px solid #eee; }}
    /* Evita el salto de página si es el primer h2 justo después del título o cerca de él */
    h1 ~ h2:first-of-type {{ page-break-before: auto; }}
    h3 {{ color: #0056b3; margin-top: 20px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 0.9em; }}
    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
    th {{ background-color: #f8f9fa; }}
</style>
</head>
<body>
    {html_content}
</body>
</html>
"""

with open(out_html, 'w', encoding='utf-8') as f:
    f.write(full_html)

edge_paths = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
]

path = next((p for p in edge_paths if os.path.exists(p)), None)

if path:
    subprocess.run([path, '--headless', '--disable-gpu', '--no-pdf-header-footer', '--print-to-pdf=' + out_pdf, out_html], check=True)
    print(f"PDF generado: {out_pdf}")
else:
    print("No se encontró Edge para la conversión a PDF.")
