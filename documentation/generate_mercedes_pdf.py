import markdown2
from weasyprint import HTML, CSS
from pathlib import Path
import os

# Paths
MD_FILE = Path(r"C:\Users\rguti\Scraper.Neoauto\documentation\reporte_mercedes_glc.md")
PDF_FILE = Path(r"C:\Users\rguti\Scraper.Neoauto\documentation\reporte_mercedes_glc.pdf")

# CSS for a "Premium" look
STYLE = """
@page {
    size: A4 portrait;
    margin: 2cm;
    @bottom-right {
        content: "Analisis CRM Neoauto - Pagina " counter(page);
        font-size: 10pt;
        color: #666;
    }
}

body {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #333;
    line-height: 1.6;
    background-color: #fff;
}

h1 {
    color: #1a3a5a;
    border-bottom: 2px solid #1a3a5a;
    padding-bottom: 10px;
    margin-top: 0;
    font-size: 24pt;
}

h2 {
    color: #2c5282;
    border-left: 5px solid #2c5282;
    padding-left: 15px;
    margin-top: 30px;
    font-size: 18pt;
}

p, li {
    font-size: 12pt;
    margin-bottom: 10px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}

th, td {
    border: 1px solid #e2e8f0;
    padding: 10px;
    text-align: left;
    font-size: 10pt;
}

th {
    background-color: #1a3a5a;
    color: white;
    font-weight: bold;
}

tr:nth-child(even) {
    background-color: #f8fafc;
}

strong {
    color: #2d3748;
}
"""

def convert():
    print(f"Reading MD from {MD_FILE}...")
    if not MD_FILE.exists():
        print(f"Error: {MD_FILE} not found.")
        return

    with open(MD_FILE, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert MD to HTML with table support
    html_content = markdown2.markdown(md_content, extras=['tables'])
    
    # Wrap in basic HTML structure
    full_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Reporte Mercedes GLC 250</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    print(f"Generating PDF at {PDF_FILE}...")
    HTML(string=full_html).write_pdf(PDF_FILE, stylesheets=[CSS(string=STYLE)])
    print(f"Success! PDF generated at {PDF_FILE}")

if __name__ == "__main__":
    convert()
