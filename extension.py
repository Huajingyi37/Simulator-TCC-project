import random
import csv
import os
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, send_file, request

# --- 1. CONFIGURATION (National Stage Data) ---
CARBON_TAX_2030 = 80  # SGD per tonne
GREEN_AI_TAX_DEDUCTION = 2.5  # 250% deduction under 2026 Budget
HVAC_BASE_KW = 50.0  # Electricity used by a standard Zone-level Chiller 
ELEC_COST_KWH = 0.30  # Standard commercial rate in Singapore
CARBON_FACTOR_KG_PER_KWH = 0.4  # Approximate carbon intensity for Singapore electricity (kg CO2/kWh)

# Create public directory for CSV outputs
PUBLIC_DIR = Path(__file__).parent / 'public'
PUBLIC_DIR.mkdir(exist_ok=True)
CSV_OUTPUT_DIR = PUBLIC_DIR / 'reports'
CSV_OUTPUT_DIR.mkdir(exist_ok=True)

class AuraIQSimulator:
    def __init__(self):
        self.total_savings_sgd = 0.0
        self.carbon_avoided_tonnes = 0.0
        self.data = []
        
    def run_scenario(self, name, description, outlook_booked, wifi_count, tenant_complaint=False):
        # --- THE 'OLD WAY' (Static Schedule) ---
        # The BMS stays at 100% power regardless of the truth [cite: 96]
        old_cost = HVAC_BASE_KW * ELEC_COST_KWH
        
        # --- THE 'AURA-IQ WAY' (Predictive + Real-Time) ---
        power_usage_percent = 1.0 # Default to 100%
        logic_action = "Maintain Normal Comfort"

        # 1. Predictive Layer: Check Outlook 
        if not outlook_booked:
            power_usage_percent = 0.4 # Pre-set to Eco-Mode if not booked
            logic_action = "Eco-Mode (No Booking)"

        # 2. Real-Time Validation: Check Wi-Fi Density 
        if outlook_booked and wifi_count == 0:
            # The 'Ghost Meeting' Scenario
            power_usage_percent = 0.2 
            logic_action = "GHOST MEETING DETECTED -> Entering Deep Save"
        elif not outlook_booked and wifi_count > 0:
            power_usage_percent = 0.8
            logic_action = "UNSCHEDULED OCCUPANCY -> Adjusting for Comfort"

        # 3. Mitigation: Tenant Feedback Loop 
        if tenant_complaint:
            power_usage_percent = 1.0
            logic_action = "TENANT OVERRIDE -> Reverting to Max Comfort"

        # --- CALCULATIONS ---
        new_cost = (HVAC_BASE_KW * power_usage_percent) * ELEC_COST_KWH
        hourly_savings = old_cost - new_cost
        self.total_savings_sgd += hourly_savings
        
        energy_saved_kwh = HVAC_BASE_KW * (1 - power_usage_percent)
        carbon_avoided = energy_saved_kwh * (CARBON_FACTOR_KG_PER_KWH / 1000)  # Convert kg to tonnes
        self.carbon_avoided_tonnes += carbon_avoided
        
        energy_reduction_percent = int((1 - power_usage_percent) * 100)
        
        return {
            'Name': name,
            'Description': description,
            'Outlook Booked': outlook_booked,
            'WiFi Count': wifi_count,
            'Tenant Complaint': tenant_complaint,
            'Logic Action': logic_action,
            'Energy Reduction %': energy_reduction_percent,
            'Hourly Savings SGD': round(hourly_savings, 2),
            'Energy Saved kWh': round(energy_saved_kwh, 2),
            'Carbon Avoided Tonnes': round(carbon_avoided, 4)
        }

    def print_final_pitch(self):
        print("\n" + "="*50)
        print("FINAL IMPACT AUDIT (For REIT Board / Judges)")
        print("="*50)
        print(f"Total Operational Savings: ${self.total_savings_sgd:.2f}")
        
        tax_shield = self.total_savings_sgd * GREEN_AI_TAX_DEDUCTION
        print(f"Estimated 2026 Budget Tax Benefit: ${tax_shield:.2f}")
        
        carbon_tax_reduction = self.carbon_avoided_tonnes * CARBON_TAX_2030
        print(f"Carbon Tax Liability Reduction: ${carbon_tax_reduction:.2f}")
        print(f"Carbon Avoided: {self.carbon_avoided_tonnes:.4f} tonnes")
        print("Aura-IQ: Turning ESG from a cost into a financial asset.")
    
    def save_to_csv(self):
        """Save simulation results to CSV file in public directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'aura_iq_simulation_{timestamp}.csv'
        csv_path = CSV_OUTPUT_DIR / filename
        
        # Add totals row
        totals = {
            'Name': 'TOTAL',
            'Description': '',
            'Outlook Booked': '',
            'WiFi Count': '',
            'Tenant Complaint': '',
            'Logic Action': '',
            'Energy Reduction %': '',
            'Hourly Savings SGD': round(self.total_savings_sgd, 2),
            'Energy Saved kWh': '',
            'Carbon Avoided Tonnes': round(self.carbon_avoided_tonnes, 4)
        }
        
        data_with_totals = self.data + [totals]
        
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = ['Name', 'Description', 'Outlook Booked', 'WiFi Count', 'Tenant Complaint', 'Logic Action', 'Energy Reduction %', 'Hourly Savings SGD', 'Energy Saved kWh', 'Carbon Avoided Tonnes']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data_with_totals:
                writer.writerow(row)
        
        print(f"✓ CSV saved to: {csv_path}")
        return str(csv_path)
    
    def get_summary(self):
        """Return simulation summary as dict"""
        return {
            'total_savings_sgd': round(self.total_savings_sgd, 2),
            'carbon_avoided_tonnes': round(self.carbon_avoided_tonnes, 4),
            'tax_benefit': round(self.total_savings_sgd * GREEN_AI_TAX_DEDUCTION, 2),
            'carbon_tax_reduction': round(self.carbon_avoided_tonnes * CARBON_TAX_2030, 2),
            'scenario_count': len(self.data)
        }

def generate_realistic_scenarios(num_scenarios=100):
    """Generate realistic scenarios with proper distributions"""
    zones = [
        "North Wing", "South Wing", "East Wing", "West Wing",
        "Central Hub", "Executive Floor", "Open Plan", "Hot Desk Area",
        "Conference Suite A", "Conference Suite B", "Meeting Room 101",
        "Meeting Room 202", "Training Center", "Lobby Area", "Cafeteria"
    ]
    
    zone_capacities = {
        "North Wing": 40, "South Wing": 35, "East Wing": 50, "West Wing": 30,
        "Central Hub": 25, "Executive Floor": 20, "Open Plan": 80, "Hot Desk Area": 45,
        "Conference Suite A": 30, "Conference Suite B": 25, "Meeting Room 101": 15,
        "Meeting Room 202": 20, "Training Center": 60, "Lobby Area": 10, "Cafeteria": 100
    }
    
    descriptions = [
        "Standard office space with scheduled occupancy",
        "Meeting scheduled in calendar but attendees not present",
        "Unscheduled visitors occupying the space",
        "Regular working hours with standard occupancy",
        "Off-peak hours with minimal activity",
        "Team collaboration area with dynamic usage",
        "Executive meeting in progress",
        "Training session with full capacity expected",
        "Post-meeting cleanup period",
        "Early morning setup before main occupancy"
    ]
    
    scenarios = []
    for i in range(num_scenarios):
        zone = random.choice(zones)
        capacity = zone_capacities[zone]
        
        # Realistic probability distributions
        # 70% of time spaces are booked when occupied
        outlook_booked = random.choices([True, False], weights=[70, 30])[0]
        
        # WiFi count correlates with booking status and zone size
        if outlook_booked:
            # If booked, 30% chance it's a "ghost meeting" with 0 people
            if random.random() < 0.3:
                wifi_count = 0
            else:
                # Otherwise, realistic occupancy 40-100% of capacity
                occupancy = random.uniform(0.4, 1.0)
                wifi_count = int(capacity * occupancy)
        else:
            # If not booked, 60% chance of unscheduled occupancy (10-80% capacity)
            if random.random() < 0.6:
                occupancy = random.uniform(0.1, 0.8)
                wifi_count = int(capacity * occupancy)
            else:
                wifi_count = 0
        
        # Tenant complaints: 5% baseline + higher if comfort was sacrificed
        base_complaint_rate = 0.05
        if outlook_booked and wifi_count == 0:
            # Ghost meeting - no one to complain
            tenant_complaint = False
        elif not outlook_booked and wifi_count > 0:
            # Unscheduled occupancy - higher complaint likelihood
            tenant_complaint = random.choices([True, False], weights=[15, 85])[0]
        else:
            tenant_complaint = random.choices([True, False], weights=[5, 95])[0]
        
        name = f"{zone} - Slot {i+1}"
        description = random.choice(descriptions)
        
        scenarios.append((name, description, outlook_booked, wifi_count, tenant_complaint))
    
    return scenarios

def run_simulation(num_scenarios=100):
    """Run simulation and return results"""
    sim = AuraIQSimulator()
    scenarios = generate_realistic_scenarios(num_scenarios)
    
    for scenario in scenarios:
        result = sim.run_scenario(*scenario)
        sim.data.append(result)
    
    return sim

latest_simulation = None

# --- FLASK WEB SERVER ---
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    """API Homepage - List available endpoints"""
    return jsonify({
        'status': '🌍 Aura-IQ Simulator API Server Running',
        'message': 'Building Energy Management System with AI-Driven HVAC Optimization',
        'endpoints': {
            'GET /': 'This help message',
            'POST /api/simulate': 'Run new simulation (optional: ?scenarios=100)',
            'GET /api/reports': 'List all available CSV reports',
            'GET /api/reports/<filename>': 'Download specific CSV report',
            'GET /api/summary/<filename>': 'Get report summary in JSON',
            'GET /static/reports/<filename>': 'Direct CSV download link'
        },
        'examples': {
            'run_simulation': 'curl -X POST "http://localhost:5000/api/simulate?scenarios=50"',
            'list_reports': 'curl "http://localhost:5000/api/reports"',
            'download': 'curl "http://localhost:5000/api/reports/aura_iq_simulation_20260402_035510.csv" -o report.csv'
        }
    }), 200

@app.route('/api/simulate', methods=['POST'])
def simulate():
    """Run a new simulation and save to CSV"""
    try:
        num_scenarios = request.args.get('scenarios', 100, type=int)
        sim = run_simulation(num_scenarios)
        csv_file = sim.save_to_csv()
        
        return jsonify({
            'status': 'success',
            'message': f'✓ Simulation with {num_scenarios} scenarios completed',
            'summary': {
                'total_scenarios': num_scenarios,
                'total_savings_sgd': sim.get_summary()['total_savings_sgd'],
                'carbon_avoided_tonnes': sim.get_summary()['carbon_avoided_tonnes'],
                'tax_benefit': sim.get_summary()['tax_benefit'],
            },
            'csv_file': os.path.basename(csv_file),
            'download_url': f'/api/reports/{os.path.basename(csv_file)}'
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/reports', methods=['GET'])
def list_reports():
    """List all available CSV reports"""
    try:
        files = sorted([f.name for f in CSV_OUTPUT_DIR.glob('*.csv')], reverse=True)
        return jsonify({
            'status': 'success',
            'total_reports': len(files),
            'reports': files,
            'download_urls': [f'/api/reports/{f}' for f in files]
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/reports/<filename>', methods=['GET'])
def download_report(filename):
    """Download a specific CSV report"""
    try:
        csv_path = CSV_OUTPUT_DIR / filename
        if not csv_path.exists():
            return jsonify({'status': 'error', 'message': 'File not found'}), 404
        return send_file(csv_path, as_attachment=True, mimetype='text/csv')
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/summary/<filename>', methods=['GET'])
def get_report_summary(filename):
    """Get JSON summary of a report"""
    try:
        csv_path = CSV_OUTPUT_DIR / filename
        if not csv_path.exists():
            return jsonify({'status': 'error', 'message': 'File not found'}), 404
        
        # Parse CSV and extract summary info
        data = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        # Get totals row (last row)
        totals = data[-1] if data else {}
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'total_scenarios': len(data) - 1,
            'results': {
                'total_savings_sgd': float(totals.get('Hourly Savings SGD', 0)),
                'carbon_avoided_tonnes': float(totals.get('Carbon Avoided Tonnes', 0)),
                'estimated_tax_benefit': float(totals.get('Hourly Savings SGD', 0)) * GREEN_AI_TAX_DEDUCTION,
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data', methods=['GET'])
def get_latest_data():
    """Return latest in-memory simulation data as JSON"""
    if latest_simulation is None:
        return jsonify({'status': 'error', 'message': 'No simulation data available yet.'}), 404

    summary = latest_simulation.get_summary()
    return jsonify({
        'status': 'success',
        'summary': summary,
        'scenarios': latest_simulation.data
    }), 200

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """HTML dashboard showing latest data"""
    if latest_simulation is None:
        return '<h1>No simulation data available yet.</h1><p>Use /api/simulate to create one.</p>'

    summary = latest_simulation.get_summary()
    html = '<html><head><title>AuraIQ Dashboard</title></head><body>'
    html += '<h1>AuraIQ Simulation Dashboard</h1>'
    html += '<p><a href="/api/data">View JSON data</a> | <a href="/api/reports">List available reports</a></p>'
    html += '<h2>Summary</h2><ul>'
    html += f"<li>Total scenarios: {summary['scenario_count']}</li>"
    html += f"<li>Total savings SGD: {summary['total_savings_sgd']}</li>"
    html += f"<li>Carbon avoided tonnes: {summary['carbon_avoided_tonnes']}</li>"
    html += f"<li>Tax benefit: {summary['tax_benefit']}</li>"
    html += '</ul>'

    html += '<h2>Scenario sample (first 20)</h2><table border="1" cellpadding="4" cellspacing="0">'
    html += '<tr><th>Name</th><th>Description</th><th>Outlook Booked</th><th>WiFi</th><th>Tenant Complaint</th><th>Logic</th><th>Cost Saved</th></tr>'
    for row in latest_simulation.data[:20]:
        html += '<tr>'
        html += f"<td>{row['Name']}</td><td>{row['Description']}</td><td>{row['Outlook Booked']}</td><td>{row['WiFi Count']}</td><td>{row['Tenant Complaint']}</td><td>{row['Logic Action']}</td><td>{row['Hourly Savings SGD']}</td>"
        html += '</tr>'
    html += '</table>'
    html += '</body></html>'
    return html, 200


@app.route('/static/reports/<filename>', methods=['GET'])
def static_report(filename):
    """Direct static file access for CSV reports"""
    try:
        csv_path = CSV_OUTPUT_DIR / filename
        if not csv_path.exists():
            return jsonify({'status': 'error', 'message': 'File not found'}), 404
        return send_file(csv_path, as_attachment=True, mimetype='text/csv')
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# EXECUTION
if __name__ == '__main__':
    print("\n" + "="*70)
    print("🏢 AURA-IQ SIMULATOR - Building Energy Management System")
    print("="*70)
    print("Generating initial simulation with 100 realistic scenarios...")
    
    global latest_simulation
    latest_simulation = run_simulation(100)
    latest_simulation.print_final_pitch()
    
    print("\n" + "="*70)
    print("🌐 Starting Flask Web Server on Port 5000")
    print("="*70)
    print(f"📁 Public Reports Directory: {CSV_OUTPUT_DIR}")
    print(f"📡 Server: http://localhost:5000")
    print("\n📋 Available Endpoints:")
    print("   └─ GET  http://localhost:5000/")
    print("   └─ POST http://localhost:5000/api/simulate?scenarios=100")
    print("   └─ GET  http://localhost:5000/api/reports")
    print("   └─ GET  http://localhost:5000/api/reports/<filename>")
    print("   └─ GET  http://localhost:5000/api/summary/<filename>")
    print("   └─ GET  http://localhost:5000/api/data")
    print("   └─ GET  http://localhost:5000/dashboard")
    print("\n💡 Example: open http://localhost:5000/dashboard in browser")
    print("="*70 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000)