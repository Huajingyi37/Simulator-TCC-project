from flask import Flask
import random

app = Flask(__name__)

# --- 1. CONFIGURATION (Keep yours!) ---
CARBON_TAX_2030 = 80
GREEN_AI_TAX_DEDUCTION = 2.5
HVAC_BASE_KW = 50.0
ELEC_COST_KWH = 0.30

# --- 2. THE BRAIN (Your Class) ---
class AuraIQSimulator:
    def __init__(self):
        self.scenarios_results = []
        self.total_savings_sgd = 0.0
        
    def run_scenario(self, name, description, outlook_booked, wifi_count, tenant_complaint=False):
        # ... (Keep all your logic layers here) ...
        # Make sure this function still appends to self.scenarios_results
        pass

# --- 3. THE INTERFACE (The New UI) ---
@app.route('/')
def dashboard():
    sim = AuraIQSimulator()
    # Run scenarios to generate data
    sim.run_scenario("North Wing", "10,000 sq ft office, booked for 50 people, but 0 present.", True, 0)
    sim.run_scenario("Flexible Zone", "Hot-desking area with 5 unscheduled workers.", False, 5)
    sim.run_scenario("Conference Room", "AI energy save triggered tenant complaint.", True, 2, True)

    # Prepare data for Chart.js
    labels = [r['name'] for r in sim.scenarios_results]
    savings_data = [float(r['saved'].replace('$', '')) for r in sim.scenarios_results]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aura-IQ Command Center</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #0d1117; color: #c9d1d9; margin: 40px; }}
            .container {{ max-width: 1000px; margin: auto; }}
            .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            h1 {{ color: #58a6ff; }}
            .metric {{ font-size: 2rem; color: #3fb950; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ text-align: left; border-bottom: 2px solid #30363d; padding: 10px; }}
            td {{ padding: 10px; border-bottom: 1px solid #21262d; }}
            .status-tag {{ background: #238636; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Aura-IQ | Operational Command</h1>
            
            <div class="card">
                <h2>Real-Time Savings Analysis</h2>
                <canvas id="savingsChart" height="100"></canvas>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="card">
                    <div style="font-size: 14px; color: #8b949e;">Total Savings (SGD)</div>
                    <div class="metric">${sim.total_savings_sgd:.2f}</div>
                </div>
                <div class="card">
                    <div style="font-size: 14px; color: #8b949e;">Carbon Offset (Est.)</div>
                    <div class="metric">{sim.total_savings_sgd * 0.12:.2f} kg</div>
                </div>
            </div>

            <div class="card">
                <h3>Zone Status</h3>
                <table>
                    <tr><th>Zone</th><th>AI Logic Action</th><th>Reduction</th></tr>
                    {"".join([f"<tr><td>{r['name']}</td><td><span class='status-tag'>{r['logic']}</span></td><td>{r['reduction']}</td></tr>" for r in sim.scenarios_results])}
                </table>
            </div>
        </div>

        <script>
            const ctx = document.getElementById('savingsChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {labels},
                    datasets: [{{
                        label: 'Hourly Savings ($)',
                        data: {savings_data},
                        backgroundColor: '#58a6ff',
                        borderRadius: 5
                    }}]
                }},
                options: {{ scales: {{ y: {{ beginAtZero: true, grid: {{ color: '#30363d' }} }} }} }}
            }});
        </script>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)