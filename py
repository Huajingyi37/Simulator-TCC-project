from flask import Flask
import random
import json

app = Flask(__name__)

# --- 1. FISCAL CONFIGURATION (SG Green Plan 2030) ---
CARBON_TAX_2024 = 25.0  # SGD per tonne
CARBON_TAX_2030 = 80.0  # Projected SGD per tonne
ELEC_COST_KWH = 0.32    # Current SG Commercial Rate
EMISSION_FACTOR = 0.40  # kg CO2 per kWh (SG Grid average)
GREEN_AI_TAX_REBATE = 2.5 # 250% Tax Deduction logic

class AuraIQEngine:
    def __init__(self):
        self.daily_log = []
        self.total_kwh_saved = 0.0
        
    def simulate_day(self):
        """Simulates 24 hours of building activity with random noise."""
        self.daily_log = []
        self.total_kwh_saved = 0.0
        
        for hour in range(24):
            # 1. Generate Input Data
            # Outlook says people should be there 9am-6pm
            outlook_expected = 50 if 9 <= hour <= 18 else 0
            # Wi-Fi detects actual humans (with random variance/ghost meetings)
            wifi_count = max(0, outlook_expected + random.randint(-15, 5)) if outlook_expected > 0 else random.randint(0, 5)
            
            # 2. Baseline BMS Logic (Static 100% power during office hours)
            baseline_kwh = 50.0 if 8 <= hour <= 19 else 10.0
            
            # 3. Aura-IQ AI Logic (Dynamic Setpoint Control)
            if wifi_count == 0:
                ai_power_factor = 0.20 # Deep Save
                action = "Deep Save (Vacant)"
            elif wifi_count < (outlook_expected * 0.5):
                ai_power_factor = 0.50 # Partial Load
                action = "Optimized (Low Density)"
            else:
                ai_power_factor = 0.90 # Standard Comfort
                action = "Comfort Mode"
                
            ai_kwh = baseline_kwh * ai_power_factor
            saved_kwh = baseline_kwh - ai_kwh
            self.total_kwh_saved += saved_kwh
            
            self.daily_log.append({
                "hour": f"{hour}:00",
                "expected": outlook_expected,
                "actual": wifi_count,
                "baseline": baseline_kwh,
                "ai_usage": ai_kwh,
                "action": action
            })

@app.route('/')
def dashboard():
    engine = AuraIQEngine()
    engine.simulate_day()
    
    # --- Statistics Analysis ---
    total_savings_sgd = engine.total_kwh_saved * ELEC_COST_KWH
    carbon_saved_tonnes = (engine.total_kwh_saved * EMISSION_FACTOR) / 1000
    
    # 2030 Carbon Tax Impact
    future_tax_avoided = carbon_saved_tonnes * CARBON_TAX_2030
    
    # Prepare Data for Chart.js
    hours = [row['hour'] for row in engine.daily_log]
    baseline_data = [row['baseline'] for row in engine.daily_log]
    ai_data = [row['ai_usage'] for row in engine.daily_log]
    occupancy_data = [row['actual'] for row in engine.daily_log]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aura-IQ | BME AI Control</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #0b0e14; color: #adbac7; margin: 30px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
            .card {{ background: #1c2128; border: 1px solid #444c56; padding: 20px; border-radius: 10px; }}
            .chart-container {{ background: #1c2128; padding: 20px; border-radius: 10px; border: 1px solid #444c56; }}
            .metric {{ font-size: 24px; color: #57abff; font-weight: bold; }}
            .green {{ color: #3fb950; }}
            h1, h2 {{ color: #f0f6fc; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
            th, td {{ border-bottom: 1px solid #444c56; padding: 8px; text-align: left; }}
        </style>
    </head>
    <body>
        <h1>Aura-IQ: Smart Building AI Control</h1>
        <p>Operational Status: <span class="green">● AI Optimized (Active)</span></p>

        <div class="grid">
            <div class="card">
                <div style="font-size: 14px;">Total Daily Savings</div>
                <div class="metric">${total_savings_sgd:.2f} <small style="font-size:12px; color:#aaa;">SGD/day</small></div>
            </div>
            <div class="card">
                <div style="font-size: 14px;">Carbon Offset (SG Grid)</div>
                <div class="metric" style="color: #3fb950;">{carbon_saved_tonnes * 1000:.1f} kg <small style="font-size:12px;">CO2</small></div>
            </div>
            <div class="card">
                <div style="font-size: 14px;">2030 Tax Shield (Projected)</div>
                <div class="metric" style="color: #d29922;">${future_tax_avoided:.2f} <small style="font-size:12px;">/day avoided</small></div>
            </div>
        </div>

        <div class="chart-container">
            <h2>24-Hour Energy Load: Baseline vs. Aura-IQ</h2>
            <canvas id="energyChart" height="80"></canvas>
        </div>

        <br>
        <div class="card">
            <h3>Live Telemetry Log (Micro-Zone Analysis)</h3>
            <table>
                <tr><th>Time</th><th>Expected (Outlook)</th><th>Actual (Wi-Fi)</th><th>AI Command</th><th>Power Saved</th></tr>
                {"".join([f"<tr><td>{r['hour']}</td><td>{r['expected']}</td><td>{r['actual']}</td><td>{r['action']}</td><td>{r['baseline'] - r['ai_usage']:.1f} kW</td></tr>" for r in engine.daily_log[8:20]])}
            </table>
        </div>

        <script>
            new Chart(document.getElementById('energyChart'), {{
                type: 'line',
                data: {{
                    labels: {json.dumps(hours)},
                    datasets: [
                        {{ label: 'Baseline (Standard BMS)', data: {json.dumps(baseline_data)}, borderColor: '#f85149', fill: false, borderDash: [5,5] }},
                        {{ label: 'Aura-IQ Optimized', data: {json.dumps(ai_data)}, borderColor: '#3fb950', backgroundColor: 'rgba(63, 185, 80, 0.1)', fill: true, tension: 0.3 }},
                        {{ label: 'Occupancy (Wi-Fi Density)', data: {json.dumps(occupancy_data)}, borderColor: '#57abff', yAxisID: 'y1', type: 'bar', barThickness: 10 }}
                    ]
                }},
                options: {{ 
                    scales: {{ 
                        y: {{ title: {{ display: true, text: 'Energy (kW)' }} }},
                        y1: {{ position: 'right', title: {{ display: true, text: 'People Count' }}, grid: {{ drawOnChartArea: false }} }}
                    }} 
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)