import tkinter as tk
import pygame
import serial
import time

# Parámetros
COM_PORT  = 'COM4'    # Ajusta al puerto de tu Arduino
BAUD_RATE = 9600
DEAD_ZONE = 0.3       # zona muerta del joystick
STEP      = 5         # cuánto cambia el valor por iteración
DELAY     = 0.02      # retardo del bucle en segundos
UPDATE_MS = int(DELAY * 1000)
RECONNECT_INTERVAL = 2.0  # segundos entre intentos de reconexión joystick o arduino

class FanControllerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Joystick → Fan PWM Controller")

        # Estado interno
        self.brightness = 0
        self.axis_y     = tk.DoubleVar(value=0.0)
        self.arduino_status    = tk.StringVar(value="Connecting...")
        self.controller_status = tk.StringVar(value="Connecting...")
        self.error_message     = tk.StringVar(value="")

        # Tiempos para reconexión
        self.last_joy_check = time.time()
        self.last_arduino_check = time.time()

        # Construcción de la UI
        tk.Label(root, text="Controller Status:").grid(row=0, column=0, sticky="w")
        self.controller_status_label = tk.Label(root, textvariable=self.controller_status, fg="orange")
        self.controller_status_label.grid(row=0, column=1, sticky="w")

        tk.Label(root, text="Joystick Y-Axis:").grid(row=1, column=0, sticky="w")
        tk.Label(root, textvariable=self.axis_y).grid(row=1, column=1, sticky="w")

        tk.Label(root, text="Arduino Status:").grid(row=2, column=0, sticky="w")
        self.arduino_status_label = tk.Label(root, textvariable=self.arduino_status, fg="orange")
        self.arduino_status_label.grid(row=2, column=1, sticky="w")

        tk.Label(root, textvariable=self.error_message, fg="red").grid(row=3, column=0, columnspan=2, sticky="w")

        # Inicializar serial y joystick
        self._init_serial()
        pygame.init()
        self._init_joystick()

        # Iniciar bucle de actualización
        self.root.after(UPDATE_MS, self.update_loop)

    def _init_serial(self):
        try:
            self.ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)  # espera a que el Arduino se reinicie
            self.arduino_status.set("Connected")
            self.arduino_status_label.config(fg="green")
        except Exception as e:
            self.ser = None
            self.arduino_status.set("Disconnected")
            self.arduino_status_label.config(fg="red")
            self.error_message.set(f"Arduino error: {e}")

    def _init_joystick(self):
        if pygame.joystick.get_count() > 0:
            try:
                self.joy = pygame.joystick.Joystick(0)
                self.joy.init()
                self.controller_status.set(self.joy.get_name())
                self.controller_status_label.config(fg="green")
                self.error_message.set("")
            except Exception as e:
                self.joy = None
                self.controller_status.set("Error")
                self.controller_status_label.config(fg="red")
                self.error_message.set(f"Joystick error: {e}")
        else:
            self.joy = None
            self.controller_status.set("Disconnected")
            self.controller_status_label.config(fg="red")
            self.error_message.set("Joystick disconnected")

    def update_loop(self):
        now = time.time()

        # Verificar estado de joystick y reconexión periódica
        if self.joy:
            if pygame.joystick.get_count() == 0:
                self.joy = None
                self.controller_status.set("Disconnected")
                self.controller_status_label.config(fg="red")
                self.error_message.set("Joystick disconnected")
        else:
            if now - self.last_joy_check >= RECONNECT_INTERVAL:
                self.last_joy_check = now
                if pygame.joystick.get_count() > 0:
                    self._init_joystick()

        # Reconectar Arduino si está desconectado
        if not self.ser or not self.ser.is_open:
            if now - self.last_arduino_check >= RECONNECT_INTERVAL:
                self.last_arduino_check = now
                self._init_serial()

        # Lectura joystick y envío PWM
        if self.joy:
            pygame.event.pump()
            try:
                y_raw = -self.joy.get_axis(1)
                self.axis_y.set(round(y_raw, 3))
                if abs(y_raw) > DEAD_ZONE:
                    self.brightness += int(y_raw * STEP)
                    self.brightness = max(0, min(255, self.brightness))
                    if self.ser and self.ser.is_open:
                        self.ser.write(f"{self.brightness}\n".encode())
                self.error_message.set("")
            except Exception as e:
                self.joy = None
                self.controller_status.set("Error")
                self.controller_status_label.config(fg="red")
                self.error_message.set(f"Joystick read error: {e}")

        # Verificar Arduino
        if self.ser:
            if self.ser.is_open:
                self.arduino_status.set("Connected")
                self.arduino_status_label.config(fg="green")
            else:
                self.arduino_status.set("Disconnected")
                self.arduino_status_label.config(fg="red")
                self.error_message.set("Serial port closed")

        self.root.after(UPDATE_MS, self.update_loop)


if __name__ == "__main__":
    root = tk.Tk()
    app  = FanControllerUI(root)
    root.mainloop()
