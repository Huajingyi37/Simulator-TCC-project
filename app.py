from flask import Flask, render_template_string
import random
import json

app = Flask(__name__)

# --- 1. CONFIGURATION (SG Green Plan & Building Physics) ---
CARBON_TAX_2030 = 80.0    
ELEC_COST_KWH = 0.32      
GRID_EMISSION_FACTOR = 0.40 
HVAC_BASE_KW = 50.0       

class AuraIQEngine:
    def __init__(self):
        self.daily_history = []
        self.total_saved_kwh = 0.0
        self.total_baseline_kwh = 0.0
        self.ml_device_ratio = 2.4 # The learned Device-to-Human ratio

    def run_simulation(self):
        # 1. Generate 24h Data
        for hour in range(24):
            is_office_hour = 8 <= hour <= 18
            outlook_expected = 100 if is_office_hour else 0
            
            if is_office_hour:
                wifi_actual = random.randint(70, 110) if random.random() > 0.2 else random.randint(0, 10)
            else:
                wifi_actual = random.randint(0, 5)

            baseline_load = HVAC_BASE_KW if is_office_hour else (HVAC_BASE_KW * 0.2)
            
            if wifi_actual <= 5: 
                ai_load = baseline_load * 0.1 
            elif wifi_actual < (outlook_expected * 0.5):
                ai_load = baseline_load * 0.5 
            else:
                ai_load = baseline_load * 0.9 

            self.total_saved_kwh += (baseline_load - ai_load)
            self.total_baseline_kwh += baseline_load
            self.daily_history.append({"hour": f"{hour:02d}:00", "baseline": baseline_load, "ai_usage": ai_load})

        # 2. Generate Live Micro-Zone Data (K-Means Output)
        self.live_zones = [
            {"name": "North Open Office", "devices": 42, "status": "Comfort Mode", "color": "#3b82f6"}, # Blue
            {"name": "South Open Office", "devices": 3, "status": "Deep Save", "color": "#34d399"}, # Green
            {"name": "Conf Room A", "devices": 18, "status": "Comfort Mode", "color": "#3b82f6"},
            {"name": "Conf Room B (Ghost)", "devices": 0, "status": "Eco-Mode", "color": "#fbbc04"}, # Yellow
            {"name": "Executive Suite", "devices": 5, "status": "Comfort Mode", "color": "#3b82f6"},
            {"name": "Cafeteria", "devices": 85, "status": "Max Cooling", "color": "#f43f5e"}, # Red
            {"name": "East Hallway", "devices": 1, "status": "Deep Save", "color": "#34d399"},
            {"name": "West Hallway", "devices": 2, "status": "Deep Save", "color": "#34d399"}
        ]

        # 3. Generate Tenant Feedback Logs
        self.feedback_logs = [
            "🟢 [14:42] Zone 2 (South Office): Ghost Meeting detected. Switched to Deep Save.",
            "🔴 [14:15] Zone 6 (Cafeteria): Tenant override 'Too Hot'. AI suspending Eco-Mode. Increasing VAV airflow.",
            "🔵 [13:50] ML Core: Device-to-Human ratio adjusted to 2.4 based on historical MAC address clustering.",
            "🟡 [13:10] Zone 4 (Conf B): AP-04 detected 0 devices for 15 mins. Calendar Overridden."
        ]

@app.route('/')
def dashboard():
    engine = AuraIQEngine()
    engine.run_simulation()
    
    # Analytics
    total_savings_sgd = engine.total_saved_kwh * ELEC_COST_KWH
    ai_actual_cost = (engine.total_baseline_kwh * ELEC_COST_KWH) - total_savings_sgd
    tax_avoided = ((engine.total_saved_kwh * GRID_EMISSION_FACTOR) / 1000) * CARBON_TAX_2030

    # Prepare HTML Snippets safely
    zone_html = "".join([f"<div class='zone-card' style='border-top: 4px solid {z['color']}'><div class='zone-title'>{z['name']}</div><div class='zone-stat'>Wi-Fi Devices: <span>{z['devices']}</span></div><div class='zone-stat'>Est. Humans: <span>{int(z['devices']/engine.ml_device_ratio)}</span></div><div class='status-badge' style='background:{z['color']}'>{z['status']}</div></div>" for z in engine.live_zones])
    log_html = "".join([f"<div class='log-entry'>{log}</div>" for log in engine.feedback_logs])

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Aura-IQ | BME Cockpit</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ margin: 0; font-family: 'Inter', sans-serif; background: #0f1423; color: #94a3b8; display: flex; height: 100vh; overflow: hidden; }}
            .sidebar {{ width: 220px; background: #151a2d; padding: 20px; display: flex; flex-direction: column; z-index: 10; box-shadow: 2px 0 10px rgba(0,0,0,0.5); }}
            .brand {{ font-size: 20px; color: white; font-weight: bold; margin-bottom: 40px; letter-spacing: 1px; }}
            .brand span {{ color: #34d399; font-size: 11px; margin-left: 5px; vertical-align: top; }}
            .nav-item {{ padding: 14px 12px; margin-bottom: 8px; border-radius: 8px; color: #94a3b8; cursor: pointer; transition: all 0.2s; font-size: 14px; }}
            .nav-item:hover {{ background: #1e2640; color: white; }}
            .nav-item.active {{ background: #1e2640; color: white; border-left: 4px solid #34d399; font-weight: bold; }}
            
            .main-content {{ flex: 1; padding: 30px 40px; overflow-y: auto; background: radial-gradient(circle at top right, #151a2d, #0f1423); }}
            .header-title {{ color: white; font-size: 28px; margin-bottom: 5px; font-weight: 300; }}
            .sub-header {{ color: #3b82f6; font-size: 14px; margin-bottom: 30px; letter-spacing: 0.5px; }}
            
            /* Tabs */
            .section {{ display: none; animation: fadeIn 0.4s; }}
            .section.active {{ display: block; }}
            @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: translateY(0); }} }}
            
            /* Layout Grids */
            .dashboard-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 20px; }}
            .floorplan-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px; }}
            
            /* Cards & Elements */
            .card {{ background: #1c2339; border-radius: 12px; padding: 22px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); border: 1px solid #2d3748; }}
            .card-title {{ font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 15px; color: #cbd5e1; }}
            .metric-large {{ font-size: 32px; color: white; font-weight: 600; margin-bottom: 5px; }}
            .metric-large span {{ font-size: 16px; font-weight: normal; }}
            
            /* Specific Components */
            .chart-container {{ position: relative; height: 220px; width: 100%; }}
            .log-box {{ background: #0f1423; border-radius: 6px; padding: 15px; height: 160px; overflow-y: auto; font-family: monospace; font-size: 12px; border: 1px solid #2d3748; }}
            .log-entry {{ margin-bottom: 10px; color: #cbd5e1; border-bottom: 1px solid #1e2640; padding-bottom: 5px; }}
            
            .zone-card {{ background: #151a2d; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }}
            .zone-title {{ color: white; font-weight: bold; font-size: 14px; margin-bottom: 10px; }}
            .zone-stat {{ font-size: 12px; margin-bottom: 5px; }}
            .zone-stat span {{ color: white; font-weight: bold; }}
            .status-badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #0f1423; margin-top: 10px; }}
        </style>
    </head>
    <body>

        <div class="sidebar">
            <div class="brand">AURA-IQ <span>v3.5</span></div>
            <div class="nav-item active" data-section="dashboard">Enterprise Dashboard</div>
            <div class="nav-item" data-section="zone">Micro-Zone Mapping</div>
            <div class="nav-item" data-section="logs">Tenant & ML Logs</div>
        </div>

        <div class="main-content">
            <div class="header-title" id="sectionTitle">Enterprise Dashboard</div>
            <div class="sub-header" id="sectionSubtitle">SG Green Plan 2030 Aligned • Edge AI Active</div>

            <div id="dashboard" class="section active">
                <div class="dashboard-grid">
                    <div class="card">
                        <div class="card-title">Daily Energy Cost</div>
                        <div class="metric-large">${ai_actual_cost:.2f} <span>SGD</span></div>
                        <div style="color: #34d399; font-size: 13px;">↓ ${total_savings_sgd:.2f} saved by AI today</div>
                    </div>
                    
                    <div class="card">
                        <div class="card-title">2030 Carbon Shield</div>
                        <div class="metric-large">${tax_avoided:.2f} <span>Avoided</span></div>
                        <div style="color: #94a3b8; font-size: 13px;">Projected offset vs Static BMS</div>
                    </div>

                    <div class="card">
                        <div class="card-title">ML Ratio Tuner</div>
                        <div class="metric-large">{engine.ml_device_ratio} <span>Devices/Human</span></div>
                        <div style="color: #3b82f6; font-size: 13px;">AI dynamically tracking office density</div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">24-Hour Energy Load: Static BMS vs Aura-IQ</div>
                    <div class="chart-container">
                        <canvas id="loadChart"></canvas>
                    </div>
                </div>
            </div>

            <div id="zone" class="section">
                <div class="card">
                    <div class="card-title">Live Floorplan (K-Means Clustered)</div>
                    <p style="font-size: 13px;">Wi-Fi MAC addresses are mapped to physical space. The AI divides devices by the ML Ratio ({engine.ml_device_ratio}) to command specific HVAC VAV boxes.</p>
                    <div class="floorplan-grid">
                        {zone_html}
                    </div>
                </div>
            </div>

            <div id="logs" class="section">
                <div class="card">
                    <div class="card-title">System Telemetry & Tenant Override Feed</div>
                    <p style="font-size: 13px;">Aggregates IoT sensors, API requests, and desktop widget inputs (Too Hot/Too Cold).</p>
                    <div class="log-box">
                        {log_html}
                    </div>
                </div>
            </div>

        </div>

        <script>
            Chart.defaults.color = '#94a3b8';
            Chart.defaults.font.family = 'Inter';
            Chart.defaults.plugins.legend.display = true;

            // Load Chart
            new Chart(document.getElementById('loadChart'), {{
                type: 'line',
                data: {{
                    labels: {json.dumps([h['hour'] for h in engine.daily_history])},
                    datasets: [
                        {{ label: 'Static Schedule BMS (kW)', data: {json.dumps([h['baseline'] for h in engine.daily_history])}, borderColor: '#f43f5e', borderDash: [5,5], fill: false, tension: 0.3, pointRadius: 0 }},
                        {{ label: 'Aura-IQ Wi-Fi Driven (kW)', data: {json.dumps([h['ai_usage'] for h in engine.daily_history])}, borderColor: '#34d399', backgroundColor: 'rgba(52, 211, 153, 0.1)', fill: true, tension: 0.3, pointRadius: 2 }}
                    ]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: true, grid: {{ color: '#2d3748' }} }}, x: {{ grid: {{ display: false }} }} }} }}
            }});

            // Tab Navigation Logic
            document.querySelectorAll('.nav-item').forEach((item) => {{
                item.addEventListener('click', () => {{
                    const selected = item.getAttribute('data-section');
                    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
                    item.classList.add('active');
                    document.querySelectorAll('.section').forEach(sec => sec.classList.remove('active'));
                    document.getElementById(selected).classList.add('active');

                    const titles = {{ dashboard: 'Enterprise Dashboard', zone: 'Micro-Zone Mapping', logs: 'Tenant & ML Logs' }};
                    document.getElementById('sectionTitle').textContent = titles[selected];
                }});
            }});
        </script>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)