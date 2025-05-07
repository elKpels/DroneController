import tkinter as tk
import pygame
import serial
import serial.tools.list_ports
import time

# Parámetros
BAUD_RATE = 9600
DEAD_ZONE = 0.3
STEP      = 5
DELAY     = 0.02
UPDATE_MS = int(DELAY * 1000)
RECONNECT_INTERVAL = 2.0

class FanControllerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Joystick → Fan PWM Controller")

        # Estado interno
        self.brightness    = 0
        self.axis_y        = tk.DoubleVar(value=0.0)
        self.pwm_speed     = tk.StringVar(value="0 /s")
        self.current_pwm   = tk.IntVar(value=0)
        self.arduino_status    = tk.StringVar(value="Connecting...")
        self.controller_status = tk.StringVar(value="Connecting...")
        self.error_message     = tk.StringVar(value="")

        self.send_count     = 0
        self.last_send_time = time.time()
        self.last_joy_check = time.time()

        # UI
        tk.Label(root, text="Controller Status:").grid(row=0, column=0, sticky="w")
        self.controller_status_label = tk.Label(root, textvariable=self.controller_status, fg="orange")
        self.controller_status_label.grid(row=0, column=1, sticky="w")

        tk.Label(root, text="Joystick Y-Axis:").grid(row=1, column=0, sticky="w")
        tk.Label(root, textvariable=self.axis_y).grid(row=1, column=1, sticky="w")

        tk.Label(root, text="Current PWM:").grid(row=2, column=0, sticky="w")
        tk.Label(root, textvariable=self.current_pwm).grid(row=2, column=1, sticky="w")

        tk.Label(root, text="PWM Send Rate:").grid(row=3, column=0, sticky="w")
        tk.Label(root, textvariable=self.pwm_speed).grid(row=3, column=1, sticky="w")

        tk.Label(root, text="Arduino Status:").grid(row=4, column=0, sticky="w")
        self.arduino_status_label = tk.Label(root, textvariable=self.arduino_status, fg="orange")
        self.arduino_status_label.grid(row=4, column=1, sticky="w")

        tk.Label(root, textvariable=self.error_message, fg="red").grid(row=5, column=0, columnspan=2, sticky="w")

        # Inicializar
        self._init_serial()
        pygame.init()
        self._init_joystick()
        self.root.after(UPDATE_MS, self.update_loop)

    def _init_serial(self):
        try:
            # Busca el puerto donde esté el Arduino Uno
            ports = serial.tools.list_ports.comports()
            arduino_port = None
            for port in ports:
                if "Arduino Uno" in port.description:
                    arduino_port = port.device
                    break
            if not arduino_port:
                raise Exception("Arduino Uno no encontrado")

            # Conecta al puerto detectado
            self.ser = serial.Serial(arduino_port, BAUD_RATE, timeout=1)
            time.sleep(2)  # espera a que el Arduino se reinicie
            self.arduino_status.set("Connected")
            self.arduino_status_label.config(fg="green")
        except Exception as e:
            self.ser = None
            self.arduino_status.set("Error")
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

        # Reconexión de joystick si se desconecta
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

        # Lectura joystick y envío PWM
        if self.joy:
            pygame.event.pump()
            try:
                y_raw = -self.joy.get_axis(1)
                self.axis_y.set(round(y_raw, 3))

                # Botón X reinicia PWM
                if self.joy.get_button(2):
                    self.brightness = 0

                if abs(y_raw) > DEAD_ZONE:
                    self.brightness += int(y_raw * STEP)
                    self.brightness = max(0, min(255, self.brightness))

                if self.ser and self.ser.is_open:
                    self.ser.write(f"{self.brightness}\n".encode())
                    self.send_count += 1
                    elapsed = time.time() - self.last_send_time
                    if elapsed >= 1.0:
                        self.pwm_speed.set(f"{self.send_count} /s")
                        self.send_count = 0
                        self.last_send_time = time.time()

                self.current_pwm.set(self.brightness)
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
