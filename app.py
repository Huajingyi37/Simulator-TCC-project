from flask import Flask, render_template
import random
import json
import iotmap
from datetime import datetime

app = Flask(__name__)

# --- 1. CONFIGURATION (SG Green Plan) ---
CARBON_TAX_2030 = 80.0    
ELEC_COST_KWH = 0.32      
GRID_EMISSION_FACTOR = 0.40
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

    def run_simulation(self):
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
                self.feedback_logs.append(f"🟢 [{datetime.now().strftime('%H:%M')}] Zone '{name}': Vacancy confirmed. Engaging Deep Save.")
            elif devices < 15:
                status, color = "Eco-Mode", "#fbbc04" 
            else:
                status, color = "Comfort Mode", "#3b82f6" 
                
            if random.random() > 0.85:
                status, color = "OVERRIDE", "#f43f5e" 
                self.feedback_logs.append(f"🔴 [{datetime.now().strftime('%H:%M')}] Zone '{name}': Tenant reported discomfort. Reverting to Max Comfort.")

            self.live_zones.append({
                "id": f"zone-{i}", 
                "name": name,
                "devices": devices,
                "status": status,
                "color": color
            })

@app.route('/')
def dashboard():
    engine = AuraIQSimulator()
    engine.run_simulation()

    iot_engine = iotmap.AuraIQEngine()
    iot_engine.run_simulation()

    # Analytics
    total_savings_sgd = engine.total_saved_kwh * ELEC_COST_KWH
    ai_actual_cost = (engine.total_baseline_kwh * ELEC_COST_KWH) - total_savings_sgd
    tax_avoided = ((engine.total_saved_kwh * GRID_EMISSION_FACTOR) / 1000) * CARBON_TAX_2030

    # Format chart data for JavaScript
    chart_labels = json.dumps([h['hour'] for h in engine.daily_history])
    chart_ai_data = json.dumps([h['ai_usage'] for h in engine.daily_history])
    chart_baseline_data = json.dumps([h['baseline'] for h in engine.daily_history])

    zone_html = "".join([f"<div class='zone-card'><div class='zone-title'>{z['name']}</div><div class='zone-stat'>Devices: <span>{z['devices']}</span></div><div class='zone-stat'>Status: <span>{z['status']}</span></div><div class='status-badge' style='background:{z['color']};'>{z['status']}</div></div>" for z in engine.live_zones])

    log_html = "".join([f"<div class='log-entry'>{log}</div>" for log in engine.feedback_logs])

    iot_zone_snapshot_html = "".join([f"<tr><td>{z['name']}</td><td>{z['outlook']}</td><td>{z['wifi']}</td><td>{z['status']}</td><td>{z['logic']}</td></tr>" for z in iot_engine.zone_snapshot])

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

    # Sensor cards with detailed readings
    iot_sensor_html = ''.join([
        f"<div class='sensor-card'><div class='sensor-title'>{s['zone']}</div><div class='sensor-line'>PIR Motion: <span class='{('active' if s['pir_motion']=='Detected' else 'inactive')}'>{s['pir_motion']}</span></div><div class='sensor-line'>Events: {s['motion_events']} in 1h</div><div class='sensor-line'>Light: <strong>{s['light_lux']} lux</strong></div><div class='sensor-line'>Presence: <strong>{s['presence_confidence']}%</strong></div><div class='sensor-line'>T/H: {s['temperature_c']}°C / {s['humidity_pct']}%</div><div class='sensor-line'>Battery: {s['battery_pct']}%</div><div class='sensor-line'>Status: {s['sensor_status']} • {s['last_update']}</div></div>"
        for s in iot_engine.iot_sensors
    ])
    iot_heatmap_html = iot_occ_heatmap_html

    return render_template('index.html', 
                           sim=engine, 
                           ai_actual_cost=ai_actual_cost,
                           chart_labels=chart_labels,
                           chart_ai_data=chart_ai_data,
                           chart_baseline_data=chart_baseline_data,
                           iot_zone_snapshot_html=iot_zone_snapshot_html,
                           iot_sensor_html=iot_sensor_html,
                           iot_heatmap_html=iot_heatmap_html)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5080)