import network
def connect_wifi()->None:
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    #sta_if.scan()                             # Scan for available access points
    if not sta_if.isconnected():
        print("Connecting to DuranoWifi")
        sta_if.connect("DuranoWifi", "nHYyQP93") # Connect to an AP
    
    #sta_if.isconnected()                      # Check for successful connection
    print("Connected...")
    print("Network config :",sta_if.ifconfig()) #show ip address

connect_wifi()