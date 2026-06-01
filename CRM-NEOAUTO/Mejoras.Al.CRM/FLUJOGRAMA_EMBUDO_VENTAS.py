import graphviz
import os
import sys

def generate_pdf_embudo():
    base_name = "flujograma_embudo_ventas_detalle"
    output_filename = base_name
    print(f"Generando Detalle Embudo de Ventas: {output_filename}.pdf")
    
    potential_paths = [
        r"C:\Program Files\Graphviz\bin",
        r"C:\Program Files (x86)\Graphviz\bin",
    ]
    for p in potential_paths:
        if os.path.exists(p) and p not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + p

    dot_code = """
    digraph EmbudoVentasCRM {
        rankdir=TB;
        splines=ortho;
        nodesep=1.0;
        ranksep=1.2;
        
        node [shape=box, style="filled,rounded", fontname="Arial", fontsize=11];
        edge [fontname="Arial", fontsize=10];

        # TÍTULO DEL GRÁFICO
        labelloc="t";
        label="DETALLE DEL EMBUDO DE VENTAS Y ESTADOS (PIPELINE)";
        fontsize=16;
        fontname="Arial bold";

        # ==========================================
        #  ESTADOS DEL EMBUDO
        # ==========================================
        subgraph cluster_pipeline {
            label = "FLUJO DE ESTADOS (crm_contactos.estado_embudo)"; style="filled"; fillcolor="#F5F5F5"; color="#9E9E9E"; margin=20;

            E1 [label="Estado 1: 1er Contacto WhatsApp\\n(Lead Nuevo)", shape=note, fillcolor="#E3F2FD"];
            E2 [label="Estado 2: Cita Concertada", shape=note, fillcolor="#FFF9C4"];
            E3 [label="Estado 3: Visita Ejecutada", shape=note, fillcolor="#FFE082"];
            
            E5 [label="Estado 5: Comprado (Stock)", shape=note, fillcolor="#A5D6A7"];
            E6 [label="Estado 6: Vendido\\n(Exit)", shape=doubleoctagon, fillcolor="#81C784", penwidth=2];
            
            E4 [label="Estado 4: Cerrado\\n(Deal Perdido)", shape=ellipse, fillcolor="#EF9A9A"];

            E1 -> E2 [label="Interés Confirmado", color="#1565C0"];
            E2 -> E3 [label="Asiste a Visita", color="#F57F17"];
            E3 -> E5 [label="Negociación Exitosa", color="#2E7D32", weight=10];
            E5 -> E6 [label="Liquidación Final", color="#2E7D32", weight=10];
            
            # Caminos de salida (Perdido)
            E1 -> E4 [style="dashed", color="#C62828"];
            E2 -> E4 [style="dashed", color="#C62828"];
            E3 -> E4 [style="dashed", color="#C62828"];
        }

        # ==========================================
        #  ACCIONES Y TRIGGERS SECUNDARIOS
        # ==========================================
        subgraph cluster_triggers {
            label = "EVENTOS Y TRIGGERS ASOCIADOS"; style="dashed"; color="#F57C00";
            
            Calendar [label="📅 Google Calendar API\\nCrea Evento (Fecha/Hora)", shape=component, fillcolor="#FFCCBC"];
            GyP_UI [label="💰 UI: Panel de Rentabilidad (GyP)\\nIngreso de Precios y Costos", shape=rect, fillcolor="#D7CCC8"];
            DB_Sync [label="🔄 Supabase UPDATE +\\nclear_crm_caches()", shape=cylinder, fillcolor="#FFE0B2", penwidth=2];
        }

        # Conexiones de Eventos
        E2 -> Calendar [label="Abre Modal Cita", color="#E65100", style="dotted"];
        E3 -> Calendar [label="Abre Modal Visita", color="#E65100", style="dotted"];
        
        E5 -> GyP_UI [label="Abre Panel Compras", color="#4E342E", style="dotted"];
        E6 -> GyP_UI [label="Calcula Utilidad Neta", color="#4E342E", style="dotted"];
        
        # Al cambiar cualquier estado:
        E1 -> DB_Sync [style="invis"]; # Para forzar layout
        E2 -> DB_Sync [color="#455A64", style="dashed", label="En cada cambio"];
        E3 -> DB_Sync [color="#455A64", style="dashed"];
        E4 -> DB_Sync [color="#455A64", style="dashed"];
        E5 -> DB_Sync [color="#455A64", style="dashed"];
        E6 -> DB_Sync [color="#455A64", style="dashed"];
        
        GyP_UI -> DB_Sync [color="#b71c1c", style="bold", label="Guarda GyP + Invalida Caché"];
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
    generate_pdf_embudo()
