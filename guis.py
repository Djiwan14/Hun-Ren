import tkinter as tk
from tkinter import Label, StringVar
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial

class Guis:
    def __init__(self, logic):
        self.logic = logic

        self.root = tk.Tk()
        self.root.title("Inhaler Data Logger")

        self.date_time_var = StringVar()
        self.temperature_var = StringVar()
        self.humidity_var = StringVar()
        self.atmospheric_pressure_var = StringVar()

        self.setup_ui()

        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.ax.set_title("Flow Rate (L/min) vs. Measurement Time (s)")
        self.ax.set_xlabel("Measurement Time (s)")
        self.ax.set_ylabel("Flow Rate (L/min)")
        self.line, = self.ax.plot([], [], 'b-')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()

    def setup_ui(self):
        """
        Setup the user interface elements.
        """
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        # Display constants
        Label(frame, text="Date and Time (Start):").grid(row=0, column=0, sticky='w')
        Label(frame, textvariable=self.date_time_var).grid(row=0, column=1, sticky='w')

        Label(frame, text="Temperature (C):").grid(row=1, column=0, sticky='w')
        Label(frame, textvariable=self.temperature_var).grid(row=1, column=1, sticky='w')

        Label(frame, text="Humidity (%):").grid(row=2, column=0, sticky='w')
        Label(frame, textvariable=self.humidity_var).grid(row=2, column=1, sticky='w')

        Label(frame, text="Atmospheric Pressure (hPa):").grid(row=3, column=0, sticky='w')
        Label(frame, textvariable=self.atmospheric_pressure_var).grid(row=3, column=1, sticky='w')

    def update_constants(self, first_measurement):
        """
        Update the constant values on the UI.
        """
        if first_measurement:
            self.date_time_var.set(f"{first_measurement['Year']}-{first_measurement['Month']}-{first_measurement['Day']} "
                                   f"{first_measurement['Hour']}:{first_measurement['Minute']}:{first_measurement['Second']}")
            self.temperature_var.set(f"{first_measurement['Temperature (C)']}")
            self.humidity_var.set(f"{first_measurement['Humidity (%)']}")
            self.atmospheric_pressure_var.set(f"{first_measurement['Atmospheric Pressure (hPa)']}")

    def update_plot(self, data):
        """
        Update the plot dynamically with new data.
        """
        self.ax.clear()
        self.ax.set_title("Flow Rate (L/min) vs. Measurement Time (s)")
        self.ax.set_xlabel("Measurement Time (s)")
        self.ax.set_ylabel("Flow Rate (L/min)")
        if data:
            times = [entry['Measurement Time (s)'] for entry in data]
            flow_rates = [entry['Flow Rate (L/min)'] for entry in data]
            self.ax.plot(times, flow_rates, 'b-')
        self.canvas.draw()

    def start_gui(self):
        """
        Start the GUI and handle serial communication in the background.
        """
        try:
            ser = serial.Serial(self.logic.serial_port, self.logic.baud_rate, timeout=1)
            print(f"Connected to {self.logic.serial_port} at {self.logic.baud_rate} baud.")
        except Exception as e:
            print(f"Failed to connect to {self.logic.serial_port}: {e}")
            return

        def update():
            try:
                line = ser.readline().decode('utf-8')
                if line:
                    print(f"Received: {line.strip()}")
                    parsed_data = self.logic.parse_received_data(line)
                    if parsed_data:
                        self.logic.flow_rate_data.append(parsed_data)
                        self.logic.update_measurement_time()
                        self.update_plot(self.logic.flow_rate_data)
                        if self.logic.get_first_measurement():
                            self.update_constants(self.logic.get_first_measurement())
            except Exception as e:
                print(f"Error during update: {e}")
            self.root.after(100, update)  # Schedule next update

        self.root.after(100, update)
        self.root.mainloop()