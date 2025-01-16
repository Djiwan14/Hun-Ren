import serial
import math
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from tkinter import Tk, Label, StringVar, IntVar, DoubleVar, Entry, Button, ttk
from datetime import datetime
import time

# Inhaler names and resistances (Pa^0.5 x s x L^-1)
INHALER_RESISTANCES = {
    "NEXThaler": 66.8,
    "Turbuhaler": 62.8,
    # "Ellipta": 52.5,
    # "Breezhaler": 36.2,
    # "Diskus": 48.7,
    # "Easyhaler": 90.0,
    # "Genuair": 59.2,
    # "Aerolizer": 35.5,
    # "HandiHaler": 91.0,
    # "Elpenhaler": 55.2,
    # "Spiromax": 59.4,
    # "Axahaler": 36.0,
    # "Forspiro": 49.3,
    # "Twisthaler": 78.6,
    # "Novolizer": 52.5,
    # "Spinhaler": 25.7
}

class InhalerLogger:
    def __init__(self, port, baud_rate):
        self.serial_port = port
        self.baud_rate = baud_rate
        self.data = []
        self.first_measurement = None
        self.inhaler_resistance = None
        self.serial_connection = None

        # Retry connecting to the serial port
        for _ in range(5):  # Retry 5 times
            try:
                self.serial_connection = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
                print(f"Connected to {self.serial_port} at {self.baud_rate} baud.")
                break
            except Exception as e:
                print(f"Failed to connect to {self.serial_port}. Retrying... ({e})")
                time.sleep(2)

        if not self.serial_connection:
            print("Failed to establish serial connection. Please check the port and try again.")

    def calculate_flow_rate(self, pressure_drop_kpa):
        """
        Calculate the flow rate from the pressure drop using the inhaler resistance.
        """
        pressure_drop_pa = pressure_drop_kpa * 1000  # Convert to Pa
        sqrt_pressure_drop = math.sqrt(pressure_drop_pa)  # Square root
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

            if not self.first_measurement:
                self.first_measurement = parsed_data  # Save the first measurement

            return parsed_data
        except Exception as e:
            print(f"Error parsing data: {line} -> {e}")
            return None

class InhalerUI:
    def __init__(self, logger):
        self.logger = logger

        # GUI Setup
        self.root = Tk()
        self.root.title("Inhaler Data Logger")
        self.running = True  # To track if the program is still running

        # Variables for patient and measurement data
        self.location_id_var = StringVar()
        self.patient_id_var = StringVar(value="IE")
        self.sex_var = StringVar()
        self.birth_year_var = IntVar()
        self.birth_month_var = IntVar()
        self.birth_day_var = IntVar()
        self.height_var = DoubleVar()
        self.weight_var = DoubleVar()
        self.inhaler_var = StringVar(value=list(INHALER_RESISTANCES.keys())[0])  # Default to the first inhaler

        # Variables to hold constant values
        self.date_time_var = StringVar(value="N/A")
        self.temp_var = StringVar(value="N/A")
        self.humidity_var = StringVar(value="N/A")
        self.pressure_var = StringVar(value="N/A")

        # GUI Layout
        self.setup_ui()

        # Plot Setup
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.ax.set_title("Flow Rate (L/min) vs. Measurement Time (s)")
        self.ax.set_xlabel("Measurement Time (s)")
        self.ax.set_ylabel("Flow Rate (L/min)")
        self.line, = self.ax.plot([], [], 'b-')
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=100, cache_frame_data=False)

    def setup_ui(self):
        """
        Setup the user interface with fields for patient and measurement data.
        """
        # Patient and measurement data
        Label(self.root, text="Measurement Location ID:").grid(row=0, column=0, sticky="w")
        Entry(self.root, textvariable=self.location_id_var).grid(row=0, column=1, sticky="w")

        Label(self.root, text="Patient ID (IEXXXX):").grid(row=1, column=0, sticky="w")
        Entry(self.root, textvariable=self.patient_id_var).grid(row=1, column=1, sticky="w")

        Label(self.root, text="Sex:").grid(row=2, column=0, sticky="w")
        ttk.Combobox(self.root, textvariable=self.sex_var, values=["Male", "Female"]).grid(row=2, column=1, sticky="w")

        Label(self.root, text="Birth Year:").grid(row=3, column=0, sticky="w")
        Entry(self.root, textvariable=self.birth_year_var).grid(row=3, column=1, sticky="w")

        Label(self.root, text="Birth Month:").grid(row=4, column=0, sticky="w")
        Entry(self.root, textvariable=self.birth_month_var).grid(row=4, column=1, sticky="w")

        Label(self.root, text="Birth Day:").grid(row=5, column=0, sticky="w")
        Entry(self.root, textvariable=self.birth_day_var).grid(row=5, column=1, sticky="w")

        Label(self.root, text="Height (cm):").grid(row=6, column=0, sticky="w")
        Entry(self.root, textvariable=self.height_var).grid(row=6, column=1, sticky="w")

        Label(self.root, text="Weight (kg):").grid(row=7, column=0, sticky="w")
        Entry(self.root, textvariable=self.weight_var).grid(row=7, column=1, sticky="w")

        Label(self.root, text="Select Inhaler:").grid(row=8, column=0, sticky="w")
        ttk.Combobox(self.root, textvariable=self.inhaler_var, values=list(INHALER_RESISTANCES.keys())).grid(row=8, column=1, sticky="w")

        Button(self.root, text="Save Data", command=self.save_data).grid(row=9, column=0, pady=10)
        Button(self.root, text="Quit", command=self.quit_program).grid(row=9, column=1, pady=10)

    def update_plot(self, i):
        """
        Update the plot dynamically with new data.
        """
        if self.running and self.logger.serial_connection:
            try:
                if self.logger.serial_connection.in_waiting > 0:
                    line = self.logger.serial_connection.readline().decode('utf-8').strip()
                    self.logger.inhaler_resistance = INHALER_RESISTANCES[self.inhaler_var.get()]
                    parsed_data = self.logger.parse_data(line)
                    if parsed_data:
                        self.logger.data.append(parsed_data)
            except serial.SerialException as e:
                print(f"SerialException: {e}")
                self.logger.serial_connection = None  # Mark the connection as invalid
            except Exception as e:
                print(f"Error reading serial data: {e}")

        # Prepare data for plotting
        times = [entry["Measurement Time (s)"] for entry in self.logger.data]
        flow_rates = [entry["Flow Rate (L/min)"] for entry in self.logger.data]

        self.line.set_data(times, flow_rates)
        self.ax.relim()
        self.ax.autoscale_view()

    def save_data(self):
        """
        Save the data to a CSV file.
        """
        if self.logger.data:
            df = pd.DataFrame(self.logger.data)
            df["Measurement Location ID"] = self.location_id_var.get()
            df["Patient ID"] = self.patient_id_var.get()
            df["Sex"] = self.sex_var.get()
            df["Birth Date"] = f"{self.birth_year_var.get()}-{self.birth_month_var.get():02d}-{self.birth_day_var.get():02d}"
            df["Height (cm)"] = self.height_var.get()
            df["Weight (kg)"] = self.weight_var.get()
            filename = "inhaler_data.csv"
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
        else:
            print("No data to save.")

    def quit_program(self):
        """
        Exit the program and close the serial connection.
        """
        # Stop the animation loop
        self.ani.event_source.stop()
        self.running = False

        # Close the serial connection
        if self.logger.serial_connection:
            try:
                self.logger.serial_connection.close()
                print("Serial connection closed.")
            except Exception as e:
                print(f"Error closing serial connection: {e}")

        self.root.quit()

    def start(self):
        """
        Start the GUI and the plotting process.
        """
        plt.show()
        self.root.mainloop()

if __name__ == "__main__":
    port = "COM7"  # Update with your actual COM port
    baud_rate = 9600

    logger = InhalerLogger(port, baud_rate)
    ui = InhalerUI(logger)

    try:
        ui.start()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if logger.serial_connection:
            logger.serial_connection.close()