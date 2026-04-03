from flask import Flask, render_template_string
import random
import json

app = Flask(__name__)

# --- 1. FISCAL & ENERGY CONFIGURATION (SG Green Plan) ---
CARBON_TAX_2030 = 80.0    # SGD per tonne
ELEC_COST_KWH = 0.32      # Commercial rate
GRID_EMISSION_FACTOR = 0.40 # kg CO2 per kWh
HVAC_BASE_KW = 50.0       # Standard Chiller Load

class AuraIQEngine:
    def __init__(self):
        self.daily_history = []
        self.zone_snapshot = []
        self.total_saved_kwh = 0.0

    def run_simulation(self):
        self.daily_history = []
        self.total_saved_kwh = 0.0
        
        # --- PART A: 24-Hour Building Simulation (For Budget Analysis) ---
        for hour in range(24):
            is_office_hour = 8 <= hour <= 18
            outlook_expected = 100 if is_office_hour else 0
            
            # Simulate real-world variance
            if is_office_hour:
                wifi_actual = random.randint(70, 110) if random.random() > 0.2 else random.randint(0, 10)
            else:
                wifi_actual = random.randint(0, 5)

            baseline_load = HVAC_BASE_KW if is_office_hour else (HVAC_BASE_KW * 0.2)
            
            # THE CRITICAL LOGIC: Wi-Fi completely overrides Outlook
            if wifi_actual <= 5: 
                ai_load = baseline_load * 0.1 # DEEP SAVE (Empty building)
            elif wifi_actual < (outlook_expected * 0.5):
                ai_load = baseline_load * 0.5 # ECO MODE (Low occupancy)
            else:
                ai_load = baseline_load * 0.9 # COMFORT MODE (Optimized cooling)

            saved = baseline_load - ai_load
            self.total_saved_kwh += saved

            self.daily_history.append({
                "hour": f"{hour:02d}:00",
                "baseline": baseline_load,
                "ai_usage": ai_load
            })

        # --- PART B: Real-Time Zone Snapshot (To show execution) ---
        # Demonstrating specific override scenarios
        self.zone_snapshot = [
            {
                "name": "Conference Room A",
                "outlook": "Booked (20 pax)",
                "wifi": 0,
                "logic": "Ghost Meeting -> Wi-Fi Overrides Calendar",
                "status": "OFF (Deep Save)",
                "color": "#f85149" # Red
            },
            {
                "name": "Hot Desk Area 1",
                "outlook": "Not Booked",
                "wifi": 14,
                "logic": "Unscheduled Occupancy -> Wi-Fi Overrides Calendar",
                "status": "ON (Comfort)",
                "color": "#3fb950" # Green
            },
            {
                "name": "Executive Boardroom",
                "outlook": "Booked (8 pax)",
                "wifi": 7,
                "logic": "Standard Occupancy -> Calendar matches Wi-Fi",
                "status": "ON (Comfort)",
                "color": "#3fb950" # Green
            },
            {
                "name": "North Wing Hallway",
                "outlook": "Not Booked",
                "wifi": 0,
                "logic": "Vacant Area -> Calendar matches Wi-Fi",
                "status": "OFF (Eco Mode)",
                "color": "#8b949e" # Gray
            }
        ]

@app.route('/')
def dashboard():
    engine = AuraIQEngine()
    engine.run_simulation()
    
    # Financial Analytics
    total_savings_sgd = engine.total_saved_kwh * ELEC_COST_KWH
    carbon_tonnes = (engine.total_saved_kwh * GRID_EMISSION_FACTOR) / 1000
    tax_avoided = carbon_tonnes * CARBON_TAX_2030

    # Chart Data
    labels = [h['hour'] for h in engine.daily_history]
    baseline_data = [h['baseline'] for h in engine.daily_history]
    ai_data = [h['ai_usage'] for h in engine.daily_history]

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Aura-IQ | AI Edge Controller</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #010409; color: #c9d1d9; margin: 40px; }}
            .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
            .card {{ background: #0d1117; border: 1px solid #30363d; padding: 20px; border-radius: 12px; }}
            .stat {{ font-size: 28px; font-weight: bold; color: #58a6ff; }}
            h1, h2, h3 {{ color: #e6edf3; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #21262d; }}
            th {{ color: #8b949e; font-weight: normal; }}
            .badge {{ padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px; color: white; }}
        </style>
    </head>
    <body>
        <h1>Aura-IQ System Control</h1>
        <p style="color: #8b949e;">Core Logic: <b>Wi-Fi Device Density strictly overrides Outlook Graph API scheduling.</b></p>

        <div class="card" style="margin-bottom: 30px; border-left: 4px solid #a371f7;">
            <h3>Live Zone Execution (Micro-Zoning)</h3>
            <table>
                <tr><th>Zone Name</th><th>Outlook Calendar</th><th>Wi-Fi Density</th><th>AI Decision Matrix</th><th>HVAC Status</th></tr>
                {"".join([f"<tr><td>{z['name']}</td><td>{z['outlook']}</td><td style='font-weight:bold;'>{z['wifi']} devices</td><td style='color:#8b949e;'>{z['logic']}</td><td><span class='badge' style='background:{z['color']};'>{z['status']}</span></td></tr>" for z in engine.zone_snapshot])}
            </table>
        </div>

        <div class="grid">
            <div class="card">
                <div style="color: #8b949e;">Daily OPEX Reclaimed</div>
                <div class="stat" style="color: #3fb950;">${total_savings_sgd:.2f} <small style="font-size:12px;">SGD</small></div>
            </div>
            <div class="card">
                <div style="color: #8b949e;">Carbon Emission Offset</div>
                <div class="stat">{carbon_tonnes * 1000:.1f} <small style="font-size:12px;">kg CO2</small></div>
            </div>
            <div class="card">
                <div style="color: #8b949e;">2030 Carbon Tax Shield</div>
                <div class="stat" style="color: #d29922;">${tax_avoided:.2f} <small style="font-size:12px;">Saved</small></div>
            </div>
        </div>

        <div class="card">
            <h2>24-Hour Energy Efficiency Gap</h2>
            <canvas id="energyChart" height="80"></canvas>
        </div>

        <script>
            new Chart(document.getElementById('energyChart'), {{
                type: 'line',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [
                        {{ label: 'Static Schedule BMS (kW)', data: {json.dumps(baseline_data)}, borderColor: '#f85149', borderDash: [5,5], fill: false }},
                        {{ label: 'Aura-IQ Wi-Fi Driven (kW)', data: {json.dumps(ai_data)}, borderColor: '#58a6ff', backgroundColor: 'rgba(88, 166, 255, 0.1)', fill: true, tension: 0.3 }}
                    ]
                }},
                options: {{ responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
            }});
        </script>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
    