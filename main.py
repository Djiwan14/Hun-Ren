import serial
import math
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime

# Inhaler resistances (Pa^0.5 x s x L^-1)
INHALER_RESISTANCES = {
    "Inhaler A": 1.0,
    "Inhaler B": 1.2,
    "Inhaler C": 1.5,
}

class InhalerLogger:
    def __init__(self, port, baud_rate, inhaler="Inhaler A"):
        self.serial_port = port
        self.baud_rate = baud_rate
        self.inhaler_resistance = INHALER_RESISTANCES[inhaler]
        self.data = []
        self.start_time = None

        # Serial connection
        try:
            self.serial_connection = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            print(f"Connected to {self.serial_port} at {self.baud_rate} baud.")
        except Exception as e:
            print(f"Failed to connect to {self.serial_port}: {e}")
            self.serial_connection = None

        # Plot setup
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.ax.set_title("Flow Rate (L/min) vs. Measurement Time (s)")
        self.ax.set_xlabel("Measurement Time (s)")
        self.ax.set_ylabel("Flow Rate (L/min)")
        self.line, = self.ax.plot([], [], 'b-')

    def calculate_flow_rate(self, pressure_drop_kpa):
        """
        Calculate the flow rate from the pressure drop using the inhaler resistance.
        """
        pressure_drop_pa = pressure_drop_kpa * 1000
        sqrt_pressure_drop = math.sqrt(pressure_drop_pa)
        flow_rate = (sqrt_pressure_drop / self.inhaler_resistance) * 60  # Convert to L/min
        return round(flow_rate, 2)

    def parse_data(self, line):
        """
        Parse the incoming serial data.
        """
        try:
            parts = line.strip().split()
            if len(parts) != 11:
                print(f"Invalid data format: {line}")
                return None

            # Extract data
            year, month, day, hour, minute, second = map(int, parts[:6])
            temp, humidity, pressure, meas_time, pressure_drop = map(float, parts[6:])

            # Calculate flow rate
            flow_rate = self.calculate_flow_rate(pressure_drop)

            # Create a dictionary to store the parsed data
            parsed_data = {
                "Year": year,
                "Month": month,
                "Day": day,
                "Hour": hour,
                "Minute": minute,
                "Second": second,
                "Temperature (C)": temp,
                "Humidity (%)": humidity,
                "Atmospheric Pressure (hPa)": pressure,
                "Measurement Time (s)": meas_time,
                "Pressure Drop (kPa)": pressure_drop,
                "Flow Rate (L/min)": flow_rate,
            }

            if not self.start_time:
                self.start_time = datetime(year, month, day, hour, minute, second)

            return parsed_data
        except Exception as e:
            print(f"Error parsing data: {line} -> {e}")
            return None

    def update_plot(self, i):
        """
        Update the plot dynamically with new data.
        """
        if self.serial_connection and self.serial_connection.in_waiting > 0:
            try:
                line = self.serial_connection.readline().decode('utf-8').strip()
                print(f"Raw Data Received: {line}")  # Debugging
                parsed_data = self.parse_data(line)
                if parsed_data:
                    print(f"Parsed Data: {parsed_data}")  # Debugging
                    self.data.append(parsed_data)
            except Exception as e:
                print(f"Error reading serial data: {e}")

        # Prepare data for plotting
        times = [entry["Measurement Time (s)"] for entry in self.data]
        flow_rates = [entry["Flow Rate (L/min)"] for entry in self.data]

        self.line.set_data(times, flow_rates)
        self.ax.relim()
        self.ax.autoscale_view()

    def start_logging(self):
        """
        Start logging and plotting data.
        """
        ani = FuncAnimation(self.fig, self.update_plot, interval=100, cache_frame_data=False)
        plt.show()

    def save_data(self, filename="inhaler_data.csv"):
        """
        Save the data to a CSV file.
        """
        if self.data:
            df = pd.DataFrame(self.data)
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
        else:
            print("No data to save.")

    def close_connection(self):
        """
        Close the serial connection.
        """
        if self.serial_connection:
            self.serial_connection.close()
            print("Serial connection closed.")

if __name__ == "__main__":
    # Set up parameters
    port = "COM7"  # Replace with your actual COM port
    baud_rate = 9600
    inhaler = "Inhaler A"  # Replace with the desired inhaler type

    # Initialize logger
    logger = InhalerLogger(port, baud_rate, inhaler)

    try:
        # Start logging and plotting
        logger.start_logging()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # Save data and close connection
        logger.save_data()
        logger.close_connection()
