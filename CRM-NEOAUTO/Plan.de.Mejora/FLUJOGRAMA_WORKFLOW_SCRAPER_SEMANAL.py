import graphviz
import os
import sys

def generate_pdf_workflow_scraper_semanal():
    # Flujograma Workflow Scraper Semanal - Camino Feliz (Semana Nueva - Flujo Exitoso)
    base_name = "flujograma_workflow_scraper_semanal"
    output_filename = base_name
    
    print(f"Generando Workflow Scraper Semanal (Camino Feliz): {output_filename}.pdf")
    
    potential_paths = [
        r"C:\Program Files\Graphviz\bin",
        r"C:\Program Files (x86)\Graphviz\bin",
    ]
    for p in potential_paths:
        if os.path.exists(p) and p not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + p

    dot_code = """
    digraph ScraperSemanalCaminoFeliz {
        rankdir=TB;
        newrank=true;
        splines=ortho;
        nodesep=0.5;
        ranksep=0.8;
        compound=true;
        
        node [shape=box, style="filled,rounded", fontname="Arial", fontsize=10];
        edge [fontname="Arial", fontsize=9];

        # ==========================================
        #  NIVEL 1: INICIALIZACIÓN Y COLA
        # ==========================================
        subgraph cluster_lvl1 {
            label = "NIVEL 1: INICIALIZACIÓN DE COLA (SEMANA NUEVA)"; style="filled,dashed"; fillcolor="#F5F5F5"; color="#9E9E9E"; margin=20;
            
            Start [label="🚀 Inicio del Proceso Semanal\\n(run_scraper_semanal.sh)", shape=ellipse, fillcolor="#E8F5E9"];
            
            ExtractorV2 [label="🕷️ Extractor V2\\n(2.SEMANAL.extractor_VCLI_v2.py)\\nLimpia 'urls_autos' y extrae URLs de marcas", shape=rect, fillcolor="#FFE0B2"];
            Randomize [label="🎲 Randomize\\n(3.SEMANAL.randomize_urls_autos.py)\\nLimpia 'urls_autos_random', mezcla y llena la cola", shape=rect, fillcolor="#FFE0B2"];
            
            Start -> ExtractorV2 [label="Cola vacía detectada"];
            ExtractorV2 -> Randomize [label="Guarda en urls_autos"];
        }

        # ==========================================
        #  NIVEL 2: EXTRACCIÓN PARALELA (PLAYWRIGHT)
        # ==========================================
        subgraph cluster_lvl2 {
            label = "NIVEL 2: EXTRACCIÓN EN PARALELO (SCRAPING)"; style="filled"; color="#ECEFF1"; fontcolor="#455A64"; margin=20;
            
            Launcher [label="🚀 Launcher Semanal\\n(parallel_launcher_semanal.py)\\nLanza 7 workers paralelos", shape=component, fillcolor="#B3E5FC", penwidth=2];
            
            subgraph cluster_workers {
                label = "POOL DE WORKERS (PLAYWRIGHT)"; style="filled,dashed"; fillcolor="#FFF3E0"; color="#FF9800";
                Worker1 [label="🤖 Worker-1", fillcolor="white"];
                WorkerDot [label="...", shape=plaintext, style=""];
                Worker7 [label="🤖 Worker-7", fillcolor="white"];
            }
            
            LocalTxt [label="📄 Archivos Planos (.txt)\\n(extractores/results_txt/\\nsemanal_result_*.txt)", shape=note, fillcolor="#FFF9C4"];
            
            Launcher -> Worker1 [style="dashed", color="#0288D1"];
            Launcher -> Worker7 [style="dashed", color="#0288D1"];
            
            Worker1 -> LocalTxt [label="Guarda datos"];
            Worker7 -> LocalTxt [label="Guarda datos"];
        }

        # Conexión Nivel 1 a Nivel 2
        Randomize -> Launcher [label="Urls listas en urls_autos_random"];

        # ==========================================
        #  NIVEL 3: TRANSFORMACIÓN Y CARGA
        # ==========================================
        subgraph cluster_lvl3 {
            label = "NIVEL 3: TRANSFORMACIÓN Y CARGA A SUPABASE"; style="filled,dashed"; fillcolor="#FFF8E1"; color="#F57C00"; margin=20;
            
            Procesador [label="🧮 Procesador TXT a JSON\\n(5.DIARIO.SEMANAL.Procesador...)\\nExtrae metadata y renombra a _procesado.txt", shape=rect, fillcolor="#C8E6C9"];
            LocalJson [label="📦 Archivos JSON (.json)\\n(extractores/results_json/)", shape=note, fillcolor="#E8F5E9"];
            SupabaseUploader [label="📤 Carga a Supabase\\n(6.json_a_supabase...)\\nInserta datos y mueve JSON a PROCESADO", shape=rect, fillcolor="#C8E6C9"];
            
            SupabaseDB [label="🗄️ Supabase DB\\n(Tabla: autos_detalles)", shape=cylinder, fillcolor="#A5D6A7"];
            
            Procesador -> LocalJson [label="Genera"];
            LocalJson -> SupabaseUploader [label="Lee"];
            SupabaseUploader -> SupabaseDB [label="Inserta en autos_detalles"];
        }

        # Conexión Nivel 2 a Nivel 3
        LocalTxt -> Procesador [label="Lee archivos planos"];

        # ==========================================
        #  NIVEL 4: ANALÍTICA Y REPORTES
        # ==========================================
        subgraph cluster_lvl4 {
            label = "NIVEL 4: ANÁLISIS DE MERCADO Y DASHBOARDS"; style="filled,dashed"; color="#9E9E9E"; margin=20;
            
            MainAnalizador [label="📊 Analizador de Mercado\\n(main.py)\\nCalcula métricas de mercado y tendencias", shape=rect, fillcolor="#D1C4E9"];
            ReportHTML [label="💻 Reporte HTML Semanal\\n(outputs/index.semanal.html)", shape=document, fillcolor="#E1BEE7"];
            ModelPages [label="📄 Páginas de Modelo\\n(model_pages/semanal/{slug}.html)", shape=folder, fillcolor="#E1BEE7"];
            AttractiveLeads [label="🔥 Leads Atractivos\\n(outputs/attractive_leads_report_*.html)", shape=document, fillcolor="#FFCDD2"];
        }

        # Conexiones Nivel 3 a Nivel 4
        SupabaseDB -> MainAnalizador [label="Descarga históricos", color="#673AB7", style="dashed"];
        MainAnalizador -> ReportHTML [label="Genera index.semanal.html"];
        MainAnalizador -> ModelPages [label="Genera páginas detalle"];
        MainAnalizador -> AttractiveLeads [label="Filtra oportunidades de trato"];

        # ==========================================
        #  NIVEL 5: DISTRIBUCIÓN Y APAGADO
        # ==========================================
        subgraph cluster_lvl5 {
            label = "NIVEL 5: DISTRIBUCIÓN Y FINALIZACIÓN"; style="filled,dashed"; fillcolor="#ECEFF1"; color="#607D8B"; margin=20;
            
            DriveUploader [label="☁️ Drive Uploader\\n(google_drive/drive_uploader.py)\\nSube outputs y genera link público", shape=rect, fillcolor="#CFD8DC"];
            GmailSender [label="📧 Envió de Gmail\\n(gmail_sender/gmail_sender.py)\\nNotifica al correo con link de Drive", shape=rect, fillcolor="#CFD8DC"];
            Shutdown [label="🔌 Apagado de Servidor\\n(shutdown -h now)", shape=ellipse, fillcolor="#FFCCBC"];
        }

        # Conexiones Nivel 4 a Nivel 5
        ReportHTML -> DriveUploader [label="Sube reporte"];
        ModelPages -> DriveUploader [style="dotted"];
        DriveUploader -> GmailSender [label="Enlace público"];
        GmailSender -> Shutdown [label="Fin exitoso de secuencia"];
    }
    """
    
    try:
        src = graphviz.Source(dot_code)
        output_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = src.render(filename=os.path.join(output_dir, output_filename), format='pdf', view=False, cleanup=True)
        print(f"Generado exitosamente: {os.path.abspath(file_path)}")
        
    except Exception as e:
        print(f"Error generando flujograma: {e}")

if __name__ == "__main__":
    generate_pdf_workflow_scraper_semanal()
