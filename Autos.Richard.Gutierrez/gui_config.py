import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
from pathlib import Path

class CollapsibleFrame(ttk.Frame):
    def __init__(self, parent, title, models, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title = title
        self.models = models
        self.model_vars = {}
        self.is_collapsed = True
        
        # --- HEADER ---
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill="x", expand=True)
        
        # Toggle Button
        self.toggle_btn = ttk.Button(self.header_frame, text="+", width=3, command=self.toggle)
        self.toggle_btn.pack(side="left")
        
        # Title Label
        self.label = ttk.Label(self.header_frame, text=title, font=("Helvetica", 10, "bold"))
        self.label.pack(side="left", padx=5)
        
        # Select All Checkbox for this Brand
        self.var_all = tk.BooleanVar(value=False)
        self.chk_all = ttk.Checkbutton(self.header_frame, text="(Todos)", variable=self.var_all, 
                                      command=self.toggle_all_models)
        self.chk_all.pack(side="right", padx=5)

        # --- CONTENT (Initially Hidden) ---
        self.content_frame = ttk.Frame(self)
        # Don't pack content_frame yet
        
        # Create checkboxes in a GRID layout (4 columns)
        num_cols = 4
        for idx, model in enumerate(self.models):
            var = tk.BooleanVar(value=False)
            # Bind trace to update label when checkbox changes
            var.trace_add('write', lambda *args: self.update_label())
            chk = ttk.Checkbutton(self.content_frame, text=model, variable=var)
            
            # Place in grid: row = idx // num_cols, column = idx % num_cols
            row = idx // num_cols
            col = idx % num_cols
            chk.grid(row=row, column=col, sticky="w", padx=10, pady=2)
            
            self.model_vars[model] = var

    def update_label(self):
        """Update label to show selected models when collapsed"""
        selected = self.get_selected_models()
        if selected:
            # Show first 3 models, add "..." if more
            display_models = selected[:3]
            suffix = "..." if len(selected) > 3 else ""
            models_text = ", ".join(display_models) + suffix
            self.label.configure(text=f"{self.title} ({models_text})")
        else:
            self.label.configure(text=self.title)

    def toggle(self):
        if self.is_collapsed:
            self.content_frame.pack(fill="x", expand=True)
            self.toggle_btn.configure(text="-")
            # Reset label to just title when expanded
            self.label.configure(text=self.title)
        else:
            self.content_frame.pack_forget()
            self.toggle_btn.configure(text="+")
            # Update label with selected models when collapsed
            self.update_label()
        self.is_collapsed = not self.is_collapsed
        
    def toggle_all_models(self):
        state = self.var_all.get()
        for var in self.model_vars.values():
            var.set(state)
        # Update label after toggling all
        if self.is_collapsed:
            self.update_label()
            
    def get_selected_models(self):
        selected = [model for model, var in self.model_vars.items() if var.get()]
        return selected

# --- FILTER PERSISTENCE ---
FILTERS_FILE = Path(__file__).parent / "last_filters.json"

def save_filters(filters_data):
    """Save filter configuration to JSON file"""
    try:
        with open(FILTERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(filters_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save filters: {e}")

def load_filters():
    """Load last used filter configuration from JSON file"""
    try:
        if FILTERS_FILE.exists():
            with open(FILTERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load filters: {e}")
    return None

class FilterDialog:
    def __init__(self, root, data_summary):
        self.root = root
        self.root.title("Configuración de Reporte de Autos")
        self.data_summary = data_summary # { 'Brand': ['Model1', 'Model2'] }
        self.result = None
        
        # Load saved filters
        saved_filters = load_filters()
        
        # Main Layout
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # --- 1. SETTINGS (Top) ---
        settings_frame = ttk.LabelFrame(main_frame, text="Configuración General", padding="5")
        settings_frame.pack(fill="x", pady=5)
        
        # Row 1: Mileage & Year
        ttk.Label(settings_frame, text="Max Km:").grid(row=0, column=0, padx=5)
        self.km_max = ttk.Entry(settings_frame, width=10)
        km_default = str(int(saved_filters['km_max'])) if saved_filters and 'km_max' in saved_filters else "100000"
        self.km_max.insert(0, km_default)
        self.km_max.grid(row=0, column=1, padx=5)
        
        ttk.Label(settings_frame, text="Antigüedad Max (años):").grid(row=0, column=2, padx=5)
        self.age_max = tk.Scale(settings_frame, from_=0, to=30, orient="horizontal", showvalue=True, width=10, sliderlength=20)
        current_year = datetime.now().year
        if saved_filters and 'year_min' in saved_filters:
            age_default = current_year - int(saved_filters['year_min'])
        else:
            age_default = 10
        self.age_max.set(age_default)
        self.age_max.grid(row=0, column=3, padx=5)
        
        ttk.Label(settings_frame, text="Días atrás:").grid(row=0, column=4, padx=5)
        self.days_back = ttk.Entry(settings_frame, width=5)
        days_default = str(saved_filters['days_back']) if saved_filters and 'days_back' in saved_filters else "30"
        self.days_back.insert(0, days_default)
        self.days_back.grid(row=0, column=5, padx=5)
        
        # Row 2: Fuel
        fuel_frame = ttk.Frame(settings_frame)
        fuel_frame.grid(row=1, column=0, columnspan=6, pady=5, sticky="w")
        ttk.Label(fuel_frame, text="Combustible:").pack(side="left", padx=5)
        self.var_diesel = tk.BooleanVar(value=True)
        self.var_gasoline = tk.BooleanVar(value=False)
        
        # Apply saved fuel preferences
        if saved_filters and 'fuels' in saved_filters:
            self.var_diesel.set("Diesel" in saved_filters['fuels'])
            self.var_gasoline.set("Gasolina" in saved_filters['fuels'])
        
        ttk.Checkbutton(fuel_frame, text="Diesel", variable=self.var_diesel).pack(side="left", padx=5)
        ttk.Checkbutton(fuel_frame, text="Gasolina", variable=self.var_gasoline).pack(side="left", padx=5)


        # --- 2. BRANDS SCROLLABLE ACCORDION ---
        list_frame = ttk.LabelFrame(main_frame, text="Selección de Vehículos (Marcas / Modelos)", padding="5")
        list_frame.pack(fill="both", expand=True, pady=5)
        
        self.canvas = tk.Canvas(list_frame)
        self.scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Populate Brands in 2-column grid
        self.brand_frames = {}
        sorted_brands = sorted(self.data_summary.keys())
        
        # Create grid container
        grid_container = ttk.Frame(self.scrollable_frame)
        grid_container.pack(fill="both", expand=True)
        
        # Configure grid to have 2 columns with equal weight
        grid_container.columnconfigure(0, weight=1)
        grid_container.columnconfigure(1, weight=1)
        
        # Get saved selections
        saved_selections = saved_filters.get('selected_map', {}) if saved_filters else {}
        
        for idx, brand in enumerate(sorted_brands):
            models = sorted(self.data_summary[brand])
            bf = CollapsibleFrame(grid_container, title=brand, models=models)
            
            # Place in grid: row = idx // 2, column = idx % 2
            row = idx // 2
            col = idx % 2
            bf.grid(row=row, column=col, sticky="ew", padx=5, pady=2)
            
            # Apply saved model selections for this brand
            if brand in saved_selections:
                for model in saved_selections[brand]:
                    if model in bf.model_vars:
                        bf.model_vars[model].set(True)
                # Update label if collapsed
                if bf.is_collapsed:
                    bf.update_label()
            
            self.brand_frames[brand] = bf

        # --- BUTTONS ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        # Timer label (will be populated by get_user_filters if auto-submit is enabled)
        self.timer_label = tk.Label(btn_frame, text="", fg="red", font=("Helvetica", 10, "bold"))
        self.timer_label.pack(side="left", padx=10)
        
        ttk.Button(btn_frame, text="Generar Reporte", command=self.on_submit).pack(side="right", padx=10)
        ttk.Button(btn_frame, text="Cancelar", command=self.root.destroy).pack(side="right", padx=10)

    def on_submit(self):
        try:
            # Validate inputs
            km_max_val = float(self.km_max.get())
            age_val = int(self.age_max.get())
            current_year = datetime.now().year
            y_min = current_year - age_val
            d_back = int(self.days_back.get())
            
            # Get selected fuels
            fuels = []
            if self.var_diesel.get(): fuels.append("Diesel")
            if self.var_gasoline.get(): fuels.append("Gasolina")
            
            # Get selected map { Brand: [Models] }
            selected_map = {}
            for brand, frame in self.brand_frames.items():
                models = frame.get_selected_models()
                if models:
                    selected_map[brand] = models
            
            # Warning if nothing selected
            if not selected_map:
                if not messagebox.askyesno("Confirmación", "No has seleccionado ningún modelo específico. ¿Deseas buscar TODOS los autos de la base de datos que cumplan los filtros generales?"):
                    return

            self.result = {
                "km_max": km_max_val,
                "year_min": y_min,
                "days_back": d_back,
                "selected_map": selected_map,
                "fuels": fuels
            }
            
            # Save filters for next time
            save_filters(self.result)
            
            self.root.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Por favor ingresa valores numéricos válidos.")

def get_user_filters(data_summary):
    root = tk.Tk()
    # Center window - 2 columns layout
    window_width = 1000
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    app = FilterDialog(root, data_summary)
    
    # Force window to front - Standard Robust Method
    root.deiconify()
    root.lift()
    root.focus_force()
    root.attributes('-topmost', True)
    root.after(1000, lambda: root.attributes('-topmost', False))
    
    print("DEBUG: GUI Window Launched and Focused")
    
    # Auto-submit countdown timer
    countdown_seconds = [30]
    timer_running = [True]
    
    def on_interaction(event):
        """Cancel timer on any user interaction"""
        if timer_running[0]:
            timer_running[0] = False
            app.timer_label.config(text="Auto-submit CANCELADO. Tómate tu tiempo.", fg="blue")
            
    def update_countdown():
        if not timer_running[0]:
            return
            
        if countdown_seconds[0] > 0:
            app.timer_label.config(text=f"Auto-submit en {countdown_seconds[0]}s (toca para cancelar)...")
            countdown_seconds[0] -= 1
            root.after(1000, update_countdown)
        else:
            if timer_running[0]: # Double check
                app.timer_label.config(text="Auto-submitting...")
                app.on_submit()
    
    # Bind interactions to stop timer
    root.bind_all('<Button-1>', on_interaction)
    root.bind_all('<Key>', on_interaction)

    # Start countdown
    print("GUI will auto-submit in 30 seconds unless interacted with...")
    update_countdown()
    
    root.mainloop()
    return app.result

if __name__ == "__main__":
    # Test data
    test_data = {
        "TOYOTA": ["HILUX", "COROLLA", "YARIS", "RAV4", "ETIOS", "PRIUS", "LAND CRUISER", "PRADO", "FORTUNER", "RUSH"],
        "KIA": ["SPORTAGE", "SORENTO", "PICANTO", "SELTOS", "RIO", "CERATO", "SONET", "SOLUTO", "CARENS"],
        "FORD": ["RANGER", "F-150", "EXPLORER", "ESCAPE", "ECOSPORT", "EDGE", "EXPEDITION", "MAVERICK"],
        "HYUNDAI": ["TUCSON", "SANTA FE", "ACCENT", "ELANTRA", "CRETA", "i10", "i20", "H-1", "VENUE", "PALISADE"],
        "NISSAN": ["FRONTIER", "SENTRA", "VERSA", "KICKS", "X-TRAIL", "QASHQAI", "PATHFINDER", "URVAN"],
        "MITSUBISHI": ["L200", "MONTERO", "OUTLANDER", "ASX", "XPANDER", "ECLIPSE CROSS", "MIRAGE"],
        "SUBARU": ["FORESTER", "XV", "IMPREZA", "OUTBACK", "WRX", "EVOLTIS"],
        "BMW": ["X1", "X3", "X5", "SERIE 3", "SERIE 1"],
        "AUDI": ["A3", "A4", "Q3", "Q5", "Q7"],
        "JEEP": ["GRAND CHEROKEE", "WRANGLER", "COMPASS", "RENEGADE"],
        "VOLKSWAGEN": ["AMAROK", "GOL", "TIGUAN", "TAOS"],
        "VOLVO": ["XC40", "XC60", "XC90"],
        "HONDA": ["CR-V", "PILOT", "CIVIC", "HR-V"],
        "MAZDA": ["CX-5", "CX-3", "MAZDA 3", "BT-50"]
    }
    print(get_user_filters(test_data))
