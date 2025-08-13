from machine import Pin
import network
import time
import _thread
from microdot import Microdot, Response

led = Pin(2, Pin.OUT)

ssid = 'Test'
password = '12345678'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
print("Connecting to Wi-Fi...")
while not wlan.isconnected():
    time.sleep(0.5)
ip = wlan.ifconfig()[0]
print("Connected! IP:", ip)

app = Microdot()
Response.default_content_type = 'text/html'

# Background blinking thread
def blink_led():
    while True:
        led.value(not led.value())
        time.sleep(3)

_thread.start_new_thread(blink_led, ())

@app.route('/status')
def status(request):
    return 'ON' if led.value() else 'OFF'

app.run(host='0.0.0.0', port=80)
