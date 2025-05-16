import tkinter as tk
import pygame
import socket

# === Configuración ESP32 Wi-Fi ===
ESP32_IP       = "192.168.4.1"
ESP32_PORT     = 80
WIFI_TIMEOUT   = 0.5
DEAD_ZONE      = 0.2
STEP           = 2
DELAY          = 0.05
UPDATE_MS      = int(DELAY * 1000)
VIB_THRESHOLD  = 20
PWM_LIMIT      = 60
STEP_DECREMENT = 1

def send_pwm_once(val):
    try:
        with socket.create_connection((ESP32_IP, ESP32_PORT), timeout=WIFI_TIMEOUT) as s:
            s.sendall(f"{val}\n".encode())
        return True
    except:
        return False

class FanControllerUI:
    def __init__(self, root):
        self.root             = root
        self.brightness       = 0
        self.prev_brightness  = -1
        self.saved_brightness = 0
        self.axis_y           = tk.DoubleVar(value=0.0)
        self.current_pwm      = tk.IntVar(value=0)
        self.status_wifi      = tk.StringVar(value="Desconectado")
        self.vib_on           = True
        self.vib_status       = tk.StringVar(value="Encendido")
        self.last_y_button    = False
        self.last_x_button    = False
        self.last_a_button    = False
        self.a_override_active= False
        self.controller_status= tk.StringVar(value="Connecting...")
        self.error_message    = tk.StringVar(value="")

        # UI
        tk.Label(root, text="Eje Y: Joystick Izquierdo:").grid(row=0, column=0, sticky="w")
        tk.Label(root, textvariable=self.axis_y).grid(row=0, column=1, sticky="w")
        tk.Label(root, text="Valor PWM:").grid(row=1, column=0, sticky="w")
        tk.Label(root, textvariable=self.current_pwm).grid(row=1, column=1, sticky="w")
        tk.Label(root, text="ESP32 Wi-Fi:").grid(row=2, column=0, sticky="w")
        self.lbl_wifi = tk.Label(root, textvariable=self.status_wifi, fg="red")
        self.lbl_wifi.grid(row=2, column=1, sticky="w")
        tk.Label(root, text="Vibración:").grid(row=3, column=0, sticky="w")
        self.lbl_vib = tk.Label(root, textvariable=self.vib_status, fg="green")
        self.lbl_vib.grid(row=3, column=1, sticky="w")
        tk.Label(root, text="Controlador:").grid(row=4, column=0, sticky="w")
        self.controller_status_label = tk.Label(root, textvariable=self.controller_status, fg="orange")
        self.controller_status_label.grid(row=4, column=1, sticky="w")
        tk.Label(root, textvariable=self.error_message, fg="red").grid(row=5, column=0, columnspan=2, sticky="w")

        # Inicializar pygame y joystick
        pygame.init()
        pygame.joystick.init()
        self.joy = None
        self._init_joystick()

        # Arrancar bucle
        root.after(UPDATE_MS, self.loop)

    def _init_joystick(self):
        if pygame.joystick.get_count() > 0:
            try:
                self.joy = pygame.joystick.Joystick(0)
                self.joy.init()
                nombre = self.joy.get_name()
                self.controller_status.set(nombre)
                self.controller_status_label.config(fg="green")
                self.error_message.set("")
            except Exception as e:
                self.joy = None
                self.controller_status.set("Error")
                self.controller_status_label.config(fg="red")
                self.error_message.set(f"Joystick error: {e}")
        else:
            self.joy = None
            self.controller_status.set("Desconectado")
            self.controller_status_label.config(fg="red")
            self.error_message.set("Joystick desconectado")

    def perform_pwm(self, val):
        ok = send_pwm_once(val)
        self.status_wifi.set("Conectado" if ok else "Desconectado")
        self.lbl_wifi.config(fg="green" if ok else "red")
        self.brightness = val
        self.current_pwm.set(val)
        self.prev_brightness = val

    def loop(self):
        # Reconectar joystick si cambió estado
        if self.joy and pygame.joystick.get_count() == 0:
            self._init_joystick()
        elif not self.joy and pygame.joystick.get_count() > 0:
            self._init_joystick()

        if self.joy:
            pygame.event.pump()

            # Toggle vibración con Y
            y_pressed = self.joy.get_button(3)
            if y_pressed and not self.last_y_button:
                self.vib_on = not self.vib_on
                self.vib_status.set("Encendido" if self.vib_on else "Apagado")
                self.lbl_vib.config(fg="green" if self.vib_on else "red")
            self.last_y_button = y_pressed

            # Override con A
            a_pressed = self.joy.get_button(0)
            if a_pressed and not self.last_a_button:
                self.saved_brightness = self.brightness
                self.a_override_active = True
                self.perform_pwm(30)
            elif not a_pressed and self.last_a_button and self.a_override_active:
                self.perform_pwm(self.saved_brightness)
                self.a_override_active = False
            self.last_a_button = a_pressed

            # Reset con X
            x_pressed = self.joy.get_button(2)
            if x_pressed and not self.last_x_button:
                self.a_override_active = False
                self.perform_pwm(0)
            self.last_x_button = x_pressed

            # Control eje Y
            if not self.a_override_active and not x_pressed:
                y = -self.joy.get_axis(1)
                self.axis_y.set(round(y, 3))
                if abs(y) > DEAD_ZONE:
                    nuevo = max(0, min(PWM_LIMIT, self.brightness + int(y * STEP)))
                    self.perform_pwm(nuevo)

            # Decremento con B
            b_pressed = self.joy.get_button(1)
            if b_pressed and self.brightness > 0:
                self.perform_pwm(max(0, self.brightness - STEP_DECREMENT))

            # Si joystick se pierde, asegurar PWM a 0
        else:
            if self.prev_brightness != 0:
                self.perform_pwm(0)

        # Vibración proporcional
        if self.joy:
            if self.vib_on and self.brightness >= VIB_THRESHOLD:
                intensity = (self.brightness - VIB_THRESHOLD) / (70 - VIB_THRESHOLD)
                try:
                    self.joy.rumble(intensity, intensity, UPDATE_MS)
                except:
                    pass
            else:
                try:
                    self.joy.rumble(0, 0, 0)
                except:
                    pass

        # Siguiente iteración
        self.root.after(UPDATE_MS, self.loop)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Drone Controller Wi-Fi")
    root.geometry("350x130")
    root.resizable(True, False)
    FanControllerUI(root)
    root.mainloop()
