class Logic:
    def __init__(self, serial_port, baud_rate):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.flow_rate_data = []
        self.measurement_time = 0.0
        self.first_measurement = None

    def parse_received_data(self, data_line):
        try:
            parts = data_line.strip().split()
            if len(parts) != 2:
                return None

            temperature = round(float(parts[0]), 1)
            humidity = round(float(parts[1].strip(';')), 1)
            atmospheric_pressure = round(950.0, 1)  # Simulated data
            flow_rate = round(1.0 / (self.measurement_time + 1) * 60, 2)  # Simulated flow rate

            parsed_data = {
                "Year": 2024,  # Simulated year for example
                "Month": 12,
                "Day": 2,
                "Hour": 14,
                "Minute": 30,
                "Second": 15,
                "Temperature (C)": temperature,
                "Humidity (%)": humidity,
                "Atmospheric Pressure (hPa)": atmospheric_pressure,
                "Measurement Time (s)": round(self.measurement_time, 2),
                "Flow Rate (L/min)": flow_rate,
            }

            if self.first_measurement is None:
                self.first_measurement = parsed_data

            return parsed_data
        except Exception as e:
            print(f"Error parsing data: {e}")
            return None

    def update_measurement_time(self):
        self.measurement_time += 0.14

    def get_first_measurement(self):
        return self.first_measurement
