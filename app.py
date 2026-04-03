from flask import Flask, render_template
import random
import json
import iotmap

app = Flask(__name__)

# --- 1. CONFIGURATION (SG Green Plan) ---
CARBON_TAX_2030 = 80.0    
ELEC_COST_KWH = 0.32      
HVAC_BASE_KW = 50.0       

class AuraIQSimulator:
    def __init__(self):
        self.daily_history = []
        self.live_zones = []
        self.feedback_logs = []
        self.total_saved_kwh = 0.0
        self.total_savings_sgd = 0.0
        self.total_baseline_kwh = 0.0
        self.ml_device_ratio = random.uniform(2.1, 2.8) 
        self.efficiency_score = 0

    def generate_dynamic_data(self):
        # 1. Generate 24-Hour Timeline Data
        for hour in range(24):
            is_office_hour = 8 <= hour <= 18
            outlook_expected = 100 if is_office_hour else 0
            
            if is_office_hour:
                wifi_actual = random.randint(60, 120) if random.random() > 0.15 else random.randint(0, 15) 
            else:
                wifi_actual = random.randint(0, 8) 

            baseline_kwh = HVAC_BASE_KW if is_office_hour else (HVAC_BASE_KW * 0.2)
            
            if wifi_actual <= 5: 
                ai_kwh = baseline_kwh * 0.1 
            elif wifi_actual < (outlook_expected * 0.5):
                ai_kwh = baseline_kwh * 0.5 
            else:
                ai_kwh = baseline_kwh * 0.85 

            saved_kwh = baseline_kwh - ai_kwh
            self.total_saved_kwh += saved_kwh
            self.total_savings_sgd += (saved_kwh * ELEC_COST_KWH)
            self.total_baseline_kwh += baseline_kwh

            self.daily_history.append({"hour": f"{hour:02d}:00", "baseline": baseline_kwh, "ai_usage": ai_kwh})

        self.efficiency_score = int((self.total_saved_kwh / self.total_baseline_kwh) * 100 * 2) 

        # 2. Generate Live Zone Data
        zone_names = ["North Wing", "South Open Plan", "Exec Suite", "Cafeteria", "Conf Room A", "Conf Room B", "Lobby", "Data Center Corridor"]
        
        for i, name in enumerate(zone_names):
            devices = random.randint(0, 45)
            
            if devices <= 2:
                status, color = "Deep Save", "#34d399" 
                self.feedback_logs.append(f"🟢 [{datetime.datetime.now().strftime('%H:%M')}] Zone '{name}': Vacancy confirmed. Engaging Deep Save.")
            elif devices < 15:
                status, color = "Eco-Mode", "#fbbc04" 
            else:
                status, color = "Comfort Mode", "#3b82f6" 
                
            if random.random() > 0.85:
                status, color = "OVERRIDE", "#f43f5e" 
                self.feedback_logs.append(f"🔴 [{datetime.datetime.now().strftime('%H:%M')}] Zone '{name}': Tenant reported discomfort. Reverting to Max Comfort.")

            self.live_zones.append({
                "id": f"zone-{i}", 
                "name": name,
                "devices": devices,
                "status": status,
                "color": color
            })

@app.route('/')
def dashboard():
    engine = AuraIQEngine()
    engine.run_simulation()

    iot_engine = iotmap.AuraIQEngine()
    iot_engine.run_simulation()

    # Analytics
    total_savings_sgd = engine.total_saved_kwh * ELEC_COST_KWH
    ai_actual_cost = (engine.total_baseline_kwh * ELEC_COST_KWH) - total_savings_sgd
    tax_avoided = ((engine.total_saved_kwh * GRID_EMISSION_FACTOR) / 1000) * CARBON_TAX_2030

    # Format chart data for JavaScript
    chart_labels = json.dumps([h['hour'] for h in sim.daily_history])
    chart_ai_data = json.dumps([h['ai_usage'] for h in sim.daily_history])
    chart_baseline_data = json.dumps([h['baseline'] for h in sim.daily_history])

    iot_zone_snapshot_html = "".join([f"<tr><td>{z['name']}</td><td>{z['outlook']}</td><td>{z['wifi']}</td><td>{z['status']}</td><td>{z['logic']}</td></tr>" for z in iot_engine.zone_snapshot])
    iot_sensor_html = "".join([f"<tr><td>{s['zone']}</td><td>{s['pir_motion']}</td><td>{s['motion_events']}</td><td>{s['light_lux']}</td><td>{s['temperature_c']}°C</td><td>{s['humidity_pct']}%</td><td>{s['presence_confidence']}%</td><td>{s['battery_pct']}%</td><td>{s['sensor_status']}</td><td>{s['last_update']}</td></tr>" for s in iot_engine.iot_sensors])

    # Build 24-hour occupancy heatmap by zone for iotmap tab
    occupancy_by_zone = {zone: [0]*24 for zone in iotmap.ZONES}
    for entry in iot_engine.occupancy_heatmap:
        zone = entry['zone_name']
        hour = entry['hour']
        occupancy = round(entry['occupancy'])
        if zone in occupancy_by_zone and 0 <= hour < 24:
            occupancy_by_zone[zone][hour] = occupancy

    heatmap_rows = []
    for zone in iotmap.ZONES:
        row_cells = ''.join([
            f"<div class='heat-cell' style='background:{iotmap._get_color_intensity(occupancy_by_zone[zone][h])};'>{occupancy_by_zone[zone][h]}</div>"
            for h in range(24)
        ])
        heatmap_rows.append(f"<div class='heat-row'><div class='zone-label'>{zone}</div>{row_cells}</div>")
    iot_occ_heatmap_html = ''.join(heatmap_rows)

    sensor_cards_html = ''.join([
        f"<div class='sensor-card'><div class='sensor-title'>{s['zone']}</div><div class='sensor-line'>PIR Motion: <span class='{('active' if s['pir_motion']=='Detected' else 'inactive')}'>{s['pir_motion']}</span></div><div class='sensor-line'>Events: {s['motion_events']} in 1h</div><div class='sensor-line'>Light: <strong>{s['light_lux']} lux</strong></div><div class='sensor-line'>Presence: <strong>{s['presence_confidence']}%</strong></div><div class='sensor-line'>T/H: {s['temperature_c']}°C / {s['humidity_pct']}%</div><div class='sensor-line'>Battery: {s['battery_pct']}%</div><div class='sensor-line'>Status: {s['sensor_status']} • {s['last_update']}</div></div>"
        for s in iot_engine.iot_sensors
    ])
    iot_zone_snapshot_html = iot_zone_snapshot_html
    iot_sensor_html = iot_sensor_html
    iot_heatmap_html = iot_occ_heatmap_html

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
            .heatmap-cell {{ background: #1a2340; color: #cbd5e1; padding: 10px; border: 1px solid #2d3748; border-radius: 6px; text-align: center; font-size: 11px; }}

            .heatmap-wrapper {{ margin-top: 10px; border: 1px solid #2d3748; border-radius: 10px; padding: 12px; background: #101526; }}
            .heatmap-head {{ display: flex; align-items: center; margin-bottom: 10px; }}
            .heatmap-head .hour-cell {{ width: 30px; text-align: center; font-size: 11px; font-weight: 600; color: #94a3b8; margin-right: 2px; }}
            .heat-row {{ display: flex; align-items: center; margin-bottom: 4px; }}
            .zone-label {{ width: 100px; font-size: 13px; color: #a5b4fc; font-weight: 600; margin-right: 10px; }}
            .heat-cell {{ width: 30px; height: 30px; border-radius: 5px; color: #fff; font-size: 12px; line-height: 30px; text-align: center; margin-right: 2px; }}

            .sensor-grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(220px,1fr)); gap: 12px; }}
            .sensor-card {{ background: #1b2541; border: 1px solid #22325f; border-radius: 10px; padding: 14px; box-shadow: inset 0 0 10px rgba(0,0,0,0.25); }}
            .sensor-title {{ color: #60a5fa; font-size: 14px; font-weight: 700; margin-bottom: 8px; }}
            .sensor-line {{ font-size: 12px; color: #cbd5e1; margin-bottom: 6px; }}
            .sensor-line small {{ color: #94a3b8; }}
            .active {{ color: #34d399; font-weight: 700; }}
            .inactive {{ color: #f87171; font-weight: 700; }}
        </style>
    </head>
    <body>

        <div class="sidebar">
            <div class="brand">AURA-IQ <span>v3.5</span></div>
            <div class="nav-item active" data-section="dashboard">Enterprise Dashboard</div>
            <div class="nav-item" data-section="zone">Micro-Zone Mapping</div>
            <div class="nav-item" data-section="logs">Tenant & ML Logs</div>
            <div class="nav-item" data-section="iotmap">IoT Floorplan</div>
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

            <div id="iotmap" class="section">
                <div class="card">
                    <div class="card-title">24-Hour Occupancy Heat Map by Zone</div>
                    <p style="font-size: 13px; color:#94a3b8;">Real-time occupancy percentage across each zone as predicted by PIR and light fusion sensors.</p>
                    <div class="heatmap-wrapper">
                        <div class="heatmap-head">
                            <div class="zone-label"></div>
                            {''.join([f"<div class='hour-cell'>{h:02d}h</div>" for h in range(24)])}
                        </div>
                        {iot_heatmap_html}
                    </div>
                </div>

                <div class="card" style="margin-top:20px;">
                    <div class="card-title">IoT Sensor Real-Time Readings</div>
                    <p style="font-size: 13px; color:#94a3b8;">PIR motion + light sensors show current behavior and confidence per zone.</p>
                    <div class="sensor-grid" style="margin-top:10px;">
                        {sensor_cards_html}
                    </div>
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

                    const titles = {{ dashboard: 'Enterprise Dashboard', zone: 'Micro-Zone Mapping', logs: 'Tenant & ML Logs', iotmap: 'IoT Floorplan & Sensors' }};
                    document.getElementById('sectionTitle').textContent = titles[selected];
                }});
            }});
        </script>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5080)