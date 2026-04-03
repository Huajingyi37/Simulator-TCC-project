import random
from datetime import datetime

# --- 1. FISCAL & ENERGY CONFIGURATION (SG Green Plan) ---
CARBON_TAX_2030 = 80.0    # SGD per tonne
ELEC_COST_KWH = 0.32      # Commercial rate
GRID_EMISSION_FACTOR = 0.40 # kg CO2 per kWh
HVAC_BASE_KW = 50.0       # Standard Chiller Load

# --- IoT SENSOR CONFIGURATION ---
ZONES = ["Conference A", "Hot Desk 1", "Boardroom", "Hallway", "Cafeteria", "Lab"]
PIR_SENSITIVITY = 0.85    # Motion detection probability during occupancy
LIGHT_THRESHOLD = 200     # Lux threshold for presence

# --- FLOOR PLAN CONFIGURATION ---
FLOOR_PLANS = {
    "Floor 1": {
        "name": "Ground Floor",
        "zones": [
            {"id": "reception", "name": "Reception", "x": 10, "y": 10, "width": 80, "height": 40, "type": "common"},
            {"id": "lobby", "name": "Main Lobby", "x": 10, "y": 60, "width": 80, "height": 40, "type": "common"},
            {"id": "cafeteria", "name": "Cafeteria", "x": 100, "y": 10, "width": 100, "height": 90, "type": "common"},
            {"id": "meeting_a", "name": "Conference A", "x": 210, "y": 10, "width": 80, "height": 60, "type": "meeting"},
            {"id": "meeting_b", "name": "Conference B", "x": 210, "y": 80, "width": 80, "height": 60, "type": "meeting"},
            {"id": "hallway_1", "name": "Hallway North", "x": 300, "y": 10, "width": 40, "height": 130, "type": "common"}
        ]
    },
    "Floor 2": {
        "name": "Executive Floor",
        "zones": [
            {"id": "boardroom", "name": "Executive Boardroom", "x": 10, "y": 10, "width": 120, "height": 80, "type": "meeting"},
            {"id": "exec_office_1", "name": "Exec Office 1", "x": 140, "y": 10, "width": 80, "height": 60, "type": "office"},
            {"id": "exec_office_2", "name": "Exec Office 2", "x": 140, "y": 80, "width": 80, "height": 60, "type": "office"},
            {"id": "hot_desk_1", "name": "Hot Desk Area 1", "x": 230, "y": 10, "width": 110, "height": 70, "type": "open"},
            {"id": "hot_desk_2", "name": "Hot Desk Area 2", "x": 230, "y": 90, "width": 110, "height": 50, "type": "open"},
            {"id": "hallway_2", "name": "Hallway South", "x": 10, "y": 100, "width": 210, "height": 40, "type": "common"}
        ]
    },
    "Floor 3": {
        "name": "Development Floor",
        "zones": [
            {"id": "lab_1", "name": "Dev Lab 1", "x": 10, "y": 10, "width": 100, "height": 80, "type": "lab"},
            {"id": "lab_2", "name": "Dev Lab 2", "x": 120, "y": 10, "width": 100, "height": 80, "type": "lab"},
            {"id": "open_space_1", "name": "Open Workspace A", "x": 10, "y": 100, "width": 100, "height": 40, "type": "open"},
            {"id": "open_space_2", "name": "Open Workspace B", "x": 120, "y": 100, "width": 100, "height": 40, "type": "open"},
            {"id": "meeting_c", "name": "Meeting Room C", "x": 230, "y": 10, "width": 80, "height": 60, "type": "meeting"},
            {"id": "pantry", "name": "Pantry", "x": 230, "y": 80, "width": 80, "height": 60, "type": "common"}
        ]
    }
}


def _get_color_intensity(occupancy):
    if occupancy < 30:
        return "#0066ff"
    elif occupancy < 70:
        return "#00cc00"
    elif occupancy < 85:
        return "#ff9900"
    else:
        return "#ff0000"


class AuraIQEngine:
    def __init__(self):
        self.daily_history = []
        self.zone_snapshot = []
        self.total_saved_kwh = 0.0
        self.occupancy_heatmap = []
        self.iot_sensors = []

    def run_simulation(self):
        self.daily_history = []
        self.total_saved_kwh = 0.0
        self.occupancy_heatmap = []
        self.iot_sensors = []

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

            saved = baseline_load - ai_load
            self.total_saved_kwh += saved

            self.daily_history.append({
                "hour": f"{hour:02d}:00",
                "baseline": baseline_load,
                "ai_usage": ai_load
            })

            self._generate_zone_occupancy(hour)

        self._generate_iot_sensor_readings()

        self.zone_snapshot = [
            {
                "name": "Conference Room A",
                "outlook": "Booked (20 pax)",
                "wifi": 0,
                "logic": "Ghost Meeting -> Wi-Fi Overrides Calendar",
                "status": "OFF (Deep Save)",
                "color": "#f85149"
            },
            {
                "name": "Hot Desk Area 1",
                "outlook": "Not Booked",
                "wifi": 14,
                "logic": "Unscheduled Occupancy -> Wi-Fi Overrides Calendar",
                "status": "ON (Comfort)",
                "color": "#3fb950"
            },
            {
                "name": "Executive Boardroom",
                "outlook": "Booked (8 pax)",
                "wifi": 7,
                "logic": "Standard Occupancy -> Calendar matches Wi-Fi",
                "status": "ON (Comfort)",
                "color": "#3fb950"
            },
            {
                "name": "North Wing Hallway",
                "outlook": "Not Booked",
                "wifi": 0,
                "logic": "Vacant Area -> Calendar matches Wi-Fi",
                "status": "OFF (Eco Mode)",
                "color": "#8b949e"
            }
        ]

    def _generate_zone_occupancy(self, hour):
        for floor_name, floor_data in FLOOR_PLANS.items():
            for zone in floor_data["zones"]:
                is_office_hour = 8 <= hour <= 18

                if zone["type"] == "meeting":
                    base_occupancy = random.randint(0, 95) if is_office_hour else random.randint(0, 10)
                elif zone["type"] == "office":
                    base_occupancy = random.randint(60, 100) if is_office_hour else random.randint(0, 5)
                elif zone["type"] == "open":
                    base_occupancy = random.randint(40, 85) if is_office_hour else random.randint(0, 15)
                elif zone["type"] == "lab":
                    base_occupancy = random.randint(70, 100) if is_office_hour else random.randint(0, 20)
                else:
                    base_occupancy = random.randint(20, 60) if is_office_hour else random.randint(0, 10)

                pir_motion = random.random() < (base_occupancy / 100 * PIR_SENSITIVITY)

                if pir_motion:
                    light_level = random.randint(LIGHT_THRESHOLD + 100, 500)
                else:
                    light_level = random.randint(0, LIGHT_THRESHOLD - 50)

                sensor_verified = pir_motion and light_level > LIGHT_THRESHOLD
                occupancy_percentage = base_occupancy if sensor_verified else base_occupancy * 0.3

                self.occupancy_heatmap.append({
                    "hour": hour,
                    "floor": floor_name,
                    "zone_id": zone["id"],
                    "zone_name": zone["name"],
                    "zone_type": zone["type"],
                    "occupancy": occupancy_percentage,
                    "pir_motion": pir_motion,
                    "light_lux": light_level,
                    "verified": sensor_verified,
                    "x": zone["x"],
                    "y": zone["y"],
                    "width": zone["width"],
                    "height": zone["height"]
                })

    def _generate_iot_sensor_readings(self):
        current_hour = datetime.now().hour
        is_office_hour = 8 <= current_hour <= 18

        for zone in ZONES:
            if is_office_hour and random.random() > 0.3:
                pir_detected = True
                motion_events = random.randint(5, 20)
            else:
                pir_detected = random.random() > 0.7
                motion_events = random.randint(0, 3)

            if pir_detected:
                light_reading = random.randint(LIGHT_THRESHOLD, 600)
                presence_confidence = random.randint(85, 99)
            else:
                light_reading = random.randint(0, LIGHT_THRESHOLD - 50)
                presence_confidence = random.randint(5, 25)

            battery_pct = random.randint(60, 100)

            self.iot_sensors.append({
                "zone": zone,
                "pir_motion": "Detected" if pir_detected else "No Motion",
                "motion_events": motion_events,
                "light_lux": light_reading,
                "temperature_c": round(random.uniform(20.5, 24.5), 1),
                "humidity_pct": random.randint(40, 70),
                "presence_confidence": presence_confidence,
                "battery_pct": battery_pct,
                "sensor_status": "Active" if battery_pct > 15 else "Low Battery",
                "last_update": f"{random.randint(1, 59)}s ago"
            })


