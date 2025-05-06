import pygame, serial, time

# Parámetros
COM = 'COM4'          # ajusta al puerto de tu Arduino
BAUD = 9600
DEAD_ZONE = 0.3       # zona muerta en eje
STEP = 5              # cuánto cambia el brillo por iteración
DELAY = 0.02          # retardo de loop (s)

# Inicialización serial y joystick
ser = serial.Serial(COM, BAUD, timeout=1)
time.sleep(2)
pygame.init()
if pygame.joystick.get_count() == 0:
    raise RuntimeError("No hay joystick conectado")
joy = pygame.joystick.Joystick(0)
joy.init()

brightness = 0
ser.write(f"{brightness}\n".encode())

try:
    while True:
        pygame.event.pump()
        y = -joy.get_axis(1)  # invertimos: +1 = palanca arriba
        if abs(y) > DEAD_ZONE:
            brightness += int(y * STEP)
            brightness = max(0, min(255, brightness))
            ser.write(f"{brightness}\n".encode())
        time.sleep(DELAY)

except KeyboardInterrupt:
    pass
finally:
    ser.close()
    pygame.quit()
