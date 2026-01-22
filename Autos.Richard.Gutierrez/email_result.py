import os
import sys
# Force UTF-8 encoding for stdout/stderr to avoid Windows console issues
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import glob
from pathlib import Path

# Add parent directory to path to import gmail_sender
sys.path.append(str(Path(__file__).parent.parent / "gmail_sender"))

try:
    from gmail_sender import crear_mensaje_email, autenticar_google, build, base64, mover_correo_a_papelera
except ImportError:
    print("Could not import gmail_sender. check paths")
    sys.exit(1)

def send_latest_report():
    # 1. Find latest PDF
    outputs_dir = Path(__file__).parent / "outputs"
    # Fallback to current dir if outputs doesn't exist or is empty
    if not outputs_dir.exists():
        outputs_dir = Path(__file__).parent

    pdf_files = list(outputs_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found.")
        return

    # Sort by modification time
    latest_pdf = max(pdf_files, key=os.path.getmtime)
    print(f"Latest PDF found: {latest_pdf}")

    # 2. Authenticate
    creds = autenticar_google()
    if not creds:
        print("Authentication failed.")
        return
    service = build('gmail', 'v1', credentials=creds)

    # 3. Send Email
    recipient = "rgutil@gmail.com"
    subject = f"Reporte Autos Generado - {latest_pdf.name}"
    body = f"""
    <html>
        <body>
            <h2>Reporte Generado</h2>
            <p>Adjunto encontrarás el reporte generado recientemente.</p>
            <p>Archivo: {latest_pdf.name}</p>
        </body>
    </html>
    """

    print(f"Sending email to {recipient}...")
    msg = crear_mensaje_email(recipient, subject, body, pdf_path=str(latest_pdf))
    
    try:
        sent = service.users().messages().send(userId='me', body=msg).execute()
        print(f"Email sent successfully! ID: {sent['id']}")
        # mover_correo_a_papelera(service, sent['id']) # Disabled per user request
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    send_latest_report()
