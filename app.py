from flask import Flask, render_template
import random
import json
import datetime

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
    sim = AuraIQSimulator()
    sim.generate_dynamic_data()
    
    ai_actual_cost = (sim.total_baseline_kwh * ELEC_COST_KWH) - sim.total_savings_sgd

    # Format chart data for JavaScript
    chart_labels = json.dumps([h['hour'] for h in sim.daily_history])
    chart_ai_data = json.dumps([h['ai_usage'] for h in sim.daily_history])
    chart_baseline_data = json.dumps([h['baseline'] for h in sim.daily_history])

    # This passes all your Python math directly to the clean HTML file!
    return render_template('index.html', 
                           sim=sim, 
                           ai_actual_cost=ai_actual_cost,
                           chart_labels=chart_labels,
                           chart_ai_data=chart_ai_data,
                           chart_baseline_data=chart_baseline_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)