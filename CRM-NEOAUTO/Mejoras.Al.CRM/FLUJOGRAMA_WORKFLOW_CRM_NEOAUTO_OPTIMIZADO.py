import graphviz
import os
import sys

def generate_pdf_workflow_crm_neoauto():
    # Flujograma Workflow CRM Neoauto - Ultra Vertical con Ecosistema Local
    base_name = "flujograma_workflow_crm_neoauto_optimizado_vertical"
    output_filename = base_name
    
    print(f"Generando Workflow CRM Neoauto (Incluyendo Ecosistema Local): {output_filename}.pdf")
    
    potential_paths = [
        r"C:\Program Files\Graphviz\bin",
        r"C:\Program Files (x86)\Graphviz\bin",
    ]
    for p in potential_paths:
        if os.path.exists(p) and p not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + p

    dot_code = """
    digraph CRMNeoautoWorkflow {
        rankdir=TB;
        newrank=true;
        splines=ortho;
        nodesep=0.8;
        ranksep=1.5;
        compound=true;
        
        node [shape=box, style="filled,rounded", fontname="Arial", fontsize=11];
        edge [fontname="Arial", fontsize=10];

        # ==========================================
        #  NIVEL 0: ECOSISTEMA EXTERNO / CAPTACIÓN LOCAL
        # ==========================================
        subgraph cluster_lvl0 {
            label = "NIVEL 0: ECOSISTEMA EXTERNO / CAPTACIÓN (LOCAL PC)"; style="filled,dashed"; fillcolor="#F5F5F5"; color="#9E9E9E"; margin=20;
            
            ScraperReport [label="📄 Informe Scraper Neoauto", shape=note, fillcolor="#FFF3E0"];
            HumanAssistant [label="👩‍💻 Asistente Humana (Anny)\\nSelecciona autos y hace click en Contactar", shape=ellipse, fillcolor="#F8BBD0"];
            EmailInbox [label="📧 Bandeja de Entrada Gmail\\n(Recibe datos del vendedor de Neoauto)", shape=folder, fillcolor="#E3F2FD"];
            LocalBot [label="🤖 Bot Local WhatsApp (PC Anny)\\nLee correo y dispara 1er Mensaje", shape=component, fillcolor="#B2DFDB", penwidth=2];
            
            ScraperReport -> HumanAssistant [label="Filtro Humano"];
            HumanAssistant -> EmailInbox [label="Portal Neoauto"];
            EmailInbox -> LocalBot [label="Extrae N° Celular"];
        }

        # ==========================================
        #  NIVEL 1: INGESTIÓN DE DATOS (NUBE)
        # ==========================================
        subgraph cluster_lvl1 {
            label = "NIVEL 1: INGESTIÓN DE DATOS (NUBE)"; style="filled"; color="#ECEFF1"; fontcolor="#455A64"; margin=20;
            Scraper [label="🕷️ Bot Scraper Diario\\n(Neoauto)", shape=cylinder, fillcolor="#FFE0B2", color="#FF9800"];
        }

        # ==========================================
        #  NIVEL 2: ALMACENAMIENTO Y CACHÉ
        # ==========================================
        subgraph cluster_lvl2 {
            label = "NIVEL 2: BASE DE DATOS Y CACHÉ"; style="filled,dashed"; fillcolor="#FFF8E1"; color="#F57C00"; margin=20;
            
            SupabaseDB [label="🗄️ Supabase DB\\n(autos_detalles, crm_contactos, crm_gyp)", shape=cylinder, fillcolor="#FFE082"];
            
            subgraph cluster_cache {
                label = "CAPA DE CACHÉ EN MEMORIA"; style="filled"; fillcolor="#FFE0B2"; color="#FB8C00"; margin=20;
                CacheLeads [label="⚡ Cache Leads (300s)", shape=note, fillcolor="white"];
                CacheMkt [label="⚡ Cache Market Research (1800s)", shape=note, fillcolor="white"];
                CacheGyP [label="⚡ Cache GyP Masivo (60s)\\nMerge instantáneo O(1)", shape=note, fillcolor="white", penwidth=2];
            }
        }

        # ==========================================
        #  NIVEL 3: FRONTEND CRM Y GESTIÓN
        # ==========================================
        subgraph cluster_lvl3 {
            label = "NIVEL 3: FRONTEND CRM (STREAMLIT)"; style="filled,dashed"; color="#9E9E9E"; margin=20;
            
            subgraph cluster_investigacion {
                label = "MÓDULO: INVESTIGACIÓN DE MERCADO"; style=filled; fillcolor="#C8E6C9"; margin=20;
                MarketFilters [label="🔍 Filtros Dinámicos\\n(Carga Instantánea)", shape=rect, fillcolor="#A5D6A7"];
                PricingCalc [label="🧮 Calculadora de Tratos\\n(Buen Trato vs Mal Trato)", shape=rect, fillcolor="#81C784"];
            }

            subgraph cluster_gestion {
                label = "MÓDULO: GESTIÓN DE LEADS Y P&L"; style="filled"; fillcolor="#D7CCC8"; color="#795548"; margin=20;
                Pipeline [label="{EMBUDO DE VENTAS|• 1er Contacto\\n• Citas / Visitas\\n• Comprado / Vendido}", shape=record, fillcolor="#D7CCC8"];
                GyPPanel [label="💰 Panel GyP (P&L)\\nCálculo USD/PEN Neto", shape=record, fillcolor="#BCAAA4"];
                SelectiveClear [label="🧹 Refresco Selectivo\\n(clear_crm_caches)", shape=ellipse, fillcolor="#FFAB91"];
            }
        }

        # ==========================================
        #  NIVEL 4: OUTPUTS Y REPORTES
        # ==========================================
        subgraph cluster_lvl4 {
            label = "NIVEL 4: REPORTES Y OUTPUTS"; style="filled,dashed"; fillcolor="#ECEFF1"; color="#607D8B"; margin=20;
            ReportLab [label="📄 Generador PDF ReportLab\\n(Carga Diferida)", shape=component, fillcolor="#B3E5FC", penwidth=2];
            PlotlyCharts [label="📈 Gráficos Plotly Interactivos", shape=note, fillcolor="#90CAF9"];
            CalendarSync [label="📅 Sincronización Google Calendar", shape=note, fillcolor="#FFCCBC"];
        }

        # ==========================================
        #  CONEXIONES PRINCIPALES
        # ==========================================
        
        # Scraper Nube a Nivel Local
        Scraper -> ScraperReport [label="Genera"];
        Scraper -> SupabaseDB [label="BBDD Diaria Maestra", color="#455A64"];
        
        # Bot Local a BBDD Nube
        LocalBot -> SupabaseDB [label="Ingresa Nuevo Lead CRM", color="#00695C", style="bold"];
        
        # Flujo Nube DB -> Cache
        SupabaseDB -> CacheMkt [style="dashed", color="#F57C00"];
        SupabaseDB -> CacheLeads [style="dashed", color="#F57C00"];
        SupabaseDB -> CacheGyP [style="dashed", color="#F57C00"];
        
        # Modulo Mercado
        CacheMkt -> MarketFilters [label="Lee RAM", color="#388E3C"];
        MarketFilters -> PricingCalc [weight=10];
        PricingCalc -> ReportLab [label="Genera PDF", color="#388E3C"];
        PricingCalc -> PlotlyCharts [label="Dibuja", color="#388E3C"];
        
        # Modulo CRM
        CacheLeads -> Pipeline [label="Lee RAM", color="#5D4037"];
        Pipeline -> CalendarSync [label="Agenda", color="#5D4037"];
        CacheGyP -> GyPPanel [label="Dict RAM", color="#5D4037"];
        Pipeline -> GyPPanel [label="Estados Finales", weight=10];
        
        GyPPanel -> SelectiveClear [label="Limpia Caché", color="#b71c1c", style="bold", weight=10];
        
        # Conexiones ascendentes sin afectar la cascada
        GyPPanel -> SupabaseDB [label="Guardar a DB", color="#b71c1c", style="dashed", constraint=false];
        SelectiveClear -> CacheLeads [label="Invalida RAM", style="dotted", color="#E65100", constraint=false];
        SelectiveClear -> CacheGyP [label="Invalida RAM", style="dotted", color="#E65100", constraint=false];
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
    generate_pdf_workflow_crm_neoauto()
