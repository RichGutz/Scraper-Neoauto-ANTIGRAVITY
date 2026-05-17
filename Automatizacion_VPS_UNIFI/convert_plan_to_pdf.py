import markdown2
from weasyprint import HTML, CSS
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
MD_FILE = BASE_DIR / "Plan.md"
PDF_FILE = BASE_DIR / "Plan.pdf"

# CSS for a "Premium" look (A4 Portrait)
STYLE = """
@page {
    size: A4 portrait;
    margin: 2cm;
    @bottom-right {
        content: "Proyecto Antigravity - Página " counter(page);
        font-size: 8pt;
        color: #718096;
    }
    @bottom-left {
        content: "Richard + Gemini VPS-UNIFI";
        font-size: 8pt;
        color: #718096;
    }
}

body {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #2d3748;
    line-height: 1.6;
    background-color: #ffffff;
}

h1 {
    color: #1a365d;
    border-bottom: 3px solid #2b6cb0;
    padding-bottom: 8px;
    margin-top: 0;
    font-size: 24pt;
}

h2 {
    color: #2b6cb0;
    border-left: 4px solid #2b6cb0;
    padding-left: 12px;
    margin-top: 30px;
    font-size: 18pt;
}

h3 {
    color: #2d3748;
    margin-top: 20px;
    font-size: 14pt;
}

p, li {
    font-size: 11pt;
    margin-bottom: 10px;
    color: #4a5568;
}

ul, ol {
    margin-top: 5px;
    margin-bottom: 15px;
    padding-left: 20px;
}

code {
    font-family: 'Consolas', 'Courier New', monospace;
    background-color: #edf2f7;
    color: #e53e3e;
    padding: 2px 4px;
    border-radius: 4px;
    font-size: 10pt;
}

pre {
    background-color: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 12px;
    overflow-x: auto;
    margin-top: 10px;
    margin-bottom: 15px;
}

pre code {
    background-color: transparent;
    color: #2d3748;
    padding: 0;
    font-size: 9.5pt;
}

blockquote {
    border-left: 4px solid #dd6b20;
    background-color: #fffaf0;
    padding: 10px 15px;
    margin: 15px 0;
    border-radius: 0 4px 4px 0;
}

blockquote p {
    color: #dd6b20;
    font-weight: bold;
    margin: 0;
}

hr {
    border: 0;
    height: 1px;
    background: #e2e8f0;
    margin: 30px 0;
}
"""

def convert():
    print(f"Leyendo MD desde {MD_FILE}...")
    if not MD_FILE.exists():
        print(f"Error: {MD_FILE} no existe.")
        return

    with open(MD_FILE, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert MD to HTML (tables and fenced-code-blocks support)
    html_content = markdown2.markdown(md_content, extras=['tables', 'fenced-code-blocks'])
    
    # Wrap in HTML
    full_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Plan Maestro: Proyecto Antigravity</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    print(f"Generando PDF en {PDF_FILE}...")
    HTML(string=full_html).write_pdf(PDF_FILE, stylesheets=[CSS(string=STYLE)])
    print(f"¡Éxito! PDF generado en {PDF_FILE}")

if __name__ == "__main__":
    convert()
