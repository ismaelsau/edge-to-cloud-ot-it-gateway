import network
import time
import ujson
from machine import Pin
import dht
from umqtt.simple import MQTTClient

# ==========================================
# 1. CONFIGURACIÓN DE RED Y HARDWARE
# ==========================================
WIFI_SSID = "Nombre de tu internet"
WIFI_PASSWORD = "*******"

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "ismael/taller/telemetria"
CLIENT_ID = "ESP32_Ismael_Planta"

sensor_dht = dht.DHT22(Pin(15))
opto_canal1 = Pin(16, Pin.IN, Pin.PULL_UP)

# ==========================================
# 2. CONEXIÓN WI-FI
# ==========================================
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"[WIFI] Conectando a {WIFI_SSID}...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            time.sleep(0.5)
            timeout -= 1
            
    if wlan.isconnected():
        print(f"[WIFI] Conectado. IP: {wlan.ifconfig()[0]}")
        return True
    return False

# ==========================================
# 3. CICLO DE PUBLICACIÓN MQTT
# ==========================================
if conectar_wifi():
    try:
        print(f"[MQTT] Conectando al broker {MQTT_BROKER}...")
        client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.connect()
        print("[MQTT] ¡Conexión establecida con éxito!")
        print("--- Transmitiendo Telemetría al Dashboard Local ---")
        
        while True:
            try:
                sensor_dht.measure()
                temp = sensor_dht.temperature()
                hum = sensor_dht.humidity()
                senal_industrial = opto_canal1.value()
                
                if senal_industrial == 0:
                    estatus = "CRITICAL (PARO EXTERNO)"
                elif temp > 45.0:
                    estatus = "CRITICAL (SOBRECALENTAMIENTO)"
                elif temp > 35.0:
                    estatus = "WARNING"
                else:
                    estatus = "OPERATIONAL"
                
                payload = {
                    "temperature": temp,
                    "humidity": hum,
                    "status": estatus,
                    "opto_signal": senal_industrial
                }
                
                client.publish(MQTT_TOPIC, ujson.dumps(payload))
                print(f"[MQTT PUB] Temp: {temp}°C | Hum: {hum}% | Estado: {estatus}")
                
            except Exception as e:
                print(f"[ERROR SENSOR] Error al leer/publicar: {e}")
                
            time.sleep(2)

    except Exception as err:
        print(f"[ERROR MQTT] No se pudo conectar al Broker: {err}")