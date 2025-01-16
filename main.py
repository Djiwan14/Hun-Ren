import serial  # Library for serial communication with Arduino
import math  # Library for mathematical calculations
import pandas as pd  # Library for data handling and saving to CSV
import matplotlib.pyplot as plt  # Library for plotting
from matplotlib.animation import FuncAnimation  # Library for real-time updating plots
from tkinter import Tk, Label, StringVar, IntVar, DoubleVar, Entry, Button, ttk  # GUI components
from datetime import datetime  # Library for handling date and time
import time  # Library for adding delays

# ---------------------------- Inhaler Resistances Dictionary ---------------------------- #
# Dictionary containing inhaler names and their corresponding resistance values in
# (Pa^0.5 x s x L^-1) units.
INHALER_RESISTANCES = {
    "NEXThaler": 66.8,
    "Turbuhaler": 62.8,
    # Uncomment and add more inhalers if needed
    # "Ellipta": 52.5,
    # "Breezhaler": 36.2,
}

# ---------------------------- Serial Communication Logger ---------------------------- #
class InhalerLogger:
    """
    Handles serial communication, data parsing, and flow rate calculation.
    """

    def __init__(self, port, baud_rate):
        """
        Initializes the serial connection with the specified COM port and baud rate.
        """
        self.serial_port = port  # COM port
        self.baud_rate = baud_rate  # Baud rate for serial communication
        self.data = []  # List to store recorded data
        self.first_measurement = None  # Stores the first recorded data point
        self.inhaler_resistance = None  # Resistance of the selected inhaler
        self.serial_connection = None  # Serial connection object

        # Try connecting to the serial port, retrying up to 5 times if it fails.
        for _ in range(5):
            try:
                self.serial_connection = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
                print(f"Connected to {self.serial_port} at {self.baud_rate} baud.")
                break
            except Exception as e:
                print(f"Failed to connect to {self.serial_port}. Retrying... ({e})")
                time.sleep(2)  # Wait for 2 seconds before retrying

        if not self.serial_connection:
            print("Failed to establish serial connection. Please check the port and try again.")

    def calculate_flow_rate(self, pressure_drop_kpa):
        """
        Calculates the flow rate from the pressure drop using the inhaler resistance.
        """
        pressure_drop_pa = pressure_drop_kpa * 1000  # Convert kPa to Pa
        sqrt_pressure_drop = math.sqrt(pressure_drop_pa)  # Compute square root of pressure drop
        flow_rate = (sqrt_pressure_drop / self.inhaler_resistance) * 60  # Convert to L/min
        return round(flow_rate, 2)  # Round to 2 decimal places

    def parse_data(self, line):
        """
        Parses the incoming serial data and extracts relevant values.
        """
        try:
            parts = line.strip().split()  # Split the data by spaces
            if len(parts) != 11:
                print(f"Invalid data format: {line}")
                return None

            # Extract values from the serial data
            year, month, day, hour, minute, second = map(int, parts[:6])
            temp, humidity, pressure, meas_time, pressure_drop = map(float, parts[6:])

            # Compute flow rate using the inhaler resistance
            flow_rate = self.calculate_flow_rate(pressure_drop)

            # Store extracted values in a dictionary
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
                self.first_measurement = parsed_data  # Store the first measurement as reference

            return parsed_data
        except Exception as e:
            print(f"Error parsing data: {line} -> {e}")
            return None

# ---------------------------- GUI for User Input and Real-time Plot ---------------------------- #
class InhalerUI:
    """
    Provides a graphical interface for user inputs and real-time plotting.
    """

    def __init__(self, logger):
        self.logger = logger  # Reference to the logger class

        # Initialize GUI
        self.root = Tk()
        self.root.title("Inhaler Data Logger")
        self.running = True  # Boolean flag to check if the program is running

        # GUI variables for patient and measurement data
        self.location_id_var = StringVar()
        self.patient_id_var = StringVar(value="IE")
        self.sex_var = StringVar()
        self.inhaler_var = StringVar(value=list(INHALER_RESISTANCES.keys())[0])  # Default inhaler

        # Setup the GUI layout
        self.setup_ui()

        # Initialize Matplotlib figure and animation
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.ax.set_title("Flow Rate (L/min) vs. Measurement Time (s)")
        self.ax.set_xlabel("Measurement Time (s)")
        self.ax.set_ylabel("Flow Rate (L/min)")
        self.line, = self.ax.plot([], [], 'b-')  # Line plot for flow rate

        # Start real-time data update animation
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=100, cache_frame_data=False)

    def setup_ui(self):
        """
        Sets up the GUI layout with input fields and buttons.
        """
        Label(self.root, text="Measurement Location ID:").grid(row=0, column=0, sticky="w")
        Entry(self.root, textvariable=self.location_id_var).grid(row=0, column=1, sticky="w")

        Label(self.root, text="Patient ID (IEXXXX):").grid(row=1, column=0, sticky="w")
        Entry(self.root, textvariable=self.patient_id_var).grid(row=1, column=1, sticky="w")

        Label(self.root, text="Sex:").grid(row=2, column=0, sticky="w")
        ttk.Combobox(self.root, textvariable=self.sex_var, values=["Male", "Female"]).grid(row=2, column=1, sticky="w")

        Label(self.root, text="Select Inhaler:").grid(row=3, column=0, sticky="w")
        ttk.Combobox(self.root, textvariable=self.inhaler_var, values=list(INHALER_RESISTANCES.keys())).grid(row=3, column=1, sticky="w")

        Button(self.root, text="Quit", command=self.quit_program).grid(row=4, column=1, pady=10)

    def update_plot(self, i):
        """
        Updates the real-time plot with new data.
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
                self.logger.serial_connection = None  # Close connection on error

        # Update the plot
        times = [entry["Measurement Time (s)"] for entry in self.logger.data]
        flow_rates = [entry["Flow Rate (L/min)"] for entry in self.logger.data]
        self.line.set_data(times, flow_rates)
        self.ax.relim()
        self.ax.autoscale_view()

    def quit_program(self):
        """
        Stops the animation and closes the serial connection before exiting.
        """
        self.ani.event_source.stop()
        self.running = False
        if self.logger.serial_connection:
            self.logger.serial_connection.close()
        self.root.quit()

    def start(self):
        """
        Starts the GUI and real-time plotting.
        """
        plt.show()
        self.root.mainloop()

# ---------------------------- Main Program Execution ---------------------------- #
if __name__ == "__main__":
    port = "COM7"
    baud_rate = 9600
    logger = InhalerLogger(port, baud_rate)
    ui = InhalerUI(logger)
    ui.start()
