# Drone Controller Wi-Fi

Controlador de velocidad PWM para un ventilador o motor conectado a un ESP32 mediante Wi-Fi, utilizando un joystick compatible con pygame y una interfaz gráfica con Tkinter.

## Características

- Conexión automática a un ESP32 en modo Access Point (por defecto IP `192.168.4.1`, puerto `80`)
- Control de potencia PWM con el eje Y del joystick izquierdo
- Zona muerta configurable para evitar ruidos
- Vibración proporcional opcional basada en el valor PWM
- Botón `A`: fuerza un PWM temporal de 30 (override)
- Botón `B`: reduce gradualmente el PWM
- Botón `X`: reinicia el PWM a 0
- Botón `Y`: activa/desactiva vibración
- Indicadores visuales de conexión Wi-Fi, vibración y estado del controlador

## Modos de conexión del controlador

El joystick puede conectarse de dos formas distintas a la PC:

1. **Por cable USB** (modo estándar recomendado)
2. **Por Bluetooth** (si el controlador y la PC lo soportan)

Ambos métodos son detectados automáticamente por pygame.

## Requisitos

- Python 3
- [pygame](https://www.pygame.org/)
- Controlador compatible con pygame (ej. Xbox, Logitech)
- ESP32 configurado como servidor TCP para recibir valores PWM

### Instalación

```bash
pip install pygame

