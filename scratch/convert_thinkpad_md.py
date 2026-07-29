import markdown2
from weasyprint import HTML, CSS
from pathlib import Path

md_path = Path(r"C:\Users\rguti\Scraper.Neoauto\Automatizacion_VPS_UNIFI\guia_conexion_remota_thinkpad.md")
pdf_path = Path(r"C:\Users\rguti\Scraper.Neoauto\Automatizacion_VPS_UNIFI\guia_conexion_remota_thinkpad.pdf")

html = markdown2.markdown(md_path.read_text(encoding="utf-8"), extras=["tables", "fenced-code-blocks"])
style = """
body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; padding: 25px; color: #222; }
pre { background: #f4f6f8; padding: 12px; border-radius: 5px; font-size: 11pt; border: 1px solid #e1e4e8; }
code { font-family: 'Consolas', monospace; }
h1 { color: #1a3a5a; border-bottom: 2px solid #1a3a5a; padding-bottom: 8px; }
h2 { color: #2c5282; margin-top: 25px; border-left: 4px solid #2c5282; padding-left: 10px; }
blockquote { background: #fffbe6; border-left: 4px solid #ffe58f; margin: 15px 0; padding: 10px 15px; }
"""

full_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{html}</body></html>"
HTML(string=full_html).write_pdf(pdf_path, stylesheets=[CSS(string=style)])
print(f"PDF successfully generated at: {pdf_path}")
