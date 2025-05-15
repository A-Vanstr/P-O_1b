# AI gebruikt zoals chatGPT en Gemini voor debuggen, herschrijven en documentatie opzoeken

import time
import os
import math
import board
import pwmio
import analogio
import digitalio
import busio
import socketpool
import wifi
from adafruit_motor import servo
from adafruit_httpserver import Server, Request, Response, GET, Websocket

# ======== HARDWARE CONFIGURATION ========
# --- Pin Definitions ---
# RGB LED Pins
RGB_RED_PIN = board.GP16
RGB_GREEN_PIN = board.GP18
RGB_BLUE_PIN = board.GP17

# Light Sensor Pins
PIN_LICHTSENSOR_LINKS = board.GP28
PIN_LICHTSENSOR_RECHTS = board.GP27
PIN_LICHTSENSOR_ACHTER = board.GP26

# Light Sensor LED Pins
PIN_LED_LINKS = board.GP21
PIN_LED_RECHTS = board.GP19
PIN_LED_ACHTER = board.GP20

# Motor Pins
PIN_MOTOR_LINKS_PWM = board.GP4
PIN_MOTOR_RECHTS_PWM = board.GP13
PIN_MOTOR_LINKS_DIR = board.GP5
PIN_MOTOR_RECHTS_DIR = board.GP12

# Distance Sensor Pins
PIN_UART_TX = board.GP8
PIN_UART_RX = board.GP9

# Servo Pin
PIN_SERVO = board.GP6

# --- Constants ---
# LED Colors
LED_OFF = (0, 0, 0)
LED_RED = (65535, 0, 0)
LED_GREEN = (0, 65535, 0)
LED_BLUE = (0, 0, 65535)
LED_YELLOW = (65535, 65535, 0)
LED_PURPLE = (65535, 0, 65535)
LED_WHITE = (65535, 65535, 65535)

# Calibration Constants
#CALIBRATION_FILE = "calibration_data.txt"
KALIB_OFFSET = 4000  
KALIB_DUUR = 12.4   

# Servo Positions
SERVO_DOWN_POS = 18   
SERVO_UP_POS = 147 
SERVO_MID_POS = 50  

# Distance sensor Constants
DREMPEL_AFSTAND = 10 #cm

# Network Config
WIFI_SSID = "PICO-TEAM-209"
WIFI_PASSWORD = "password209"

# Time Intervals
WEB_INTERVAL = 0.1
DRIVE_INTERVAL = 0.05
SENSOR_INTERVAL = 0.05
LED_UPDATE_INTERVAL = 0.05

# ======== HARDWARE INITIALIZATION ========
# --- RGB LED Setup ---
rgb_red = pwmio.PWMOut(RGB_RED_PIN, frequency=1000, duty_cycle=0)
rgb_green = pwmio.PWMOut(RGB_GREEN_PIN, frequency=1000, duty_cycle=0)
rgb_blue = pwmio.PWMOut(RGB_BLUE_PIN, frequency=1000, duty_cycle=0)

# --- Light Sensors Setup ---
lichtsensor_links = analogio.AnalogIn(PIN_LICHTSENSOR_LINKS)
lichtsensor_rechts = analogio.AnalogIn(PIN_LICHTSENSOR_RECHTS)
lichtsensor_achter = analogio.AnalogIn(PIN_LICHTSENSOR_ACHTER)

# --- Light Sensor LEDs Setup ---
led_links = digitalio.DigitalInOut(PIN_LED_LINKS)
led_rechts = digitalio.DigitalInOut(PIN_LED_RECHTS)
led_achter = digitalio.DigitalInOut(PIN_LED_ACHTER)

led_links.direction = digitalio.Direction.OUTPUT
led_rechts.direction = digitalio.Direction.OUTPUT
led_achter.direction = digitalio.Direction.OUTPUT

led_links.value = True
led_rechts.value = True
led_achter.value = True

# --- Motors Setup ---
motor_links = pwmio.PWMOut(PIN_MOTOR_LINKS_PWM, frequency=1000, duty_cycle=0)
motor_rechts = pwmio.PWMOut(PIN_MOTOR_RECHTS_PWM, frequency=1000, duty_cycle=0)

motor_links_switch = digitalio.DigitalInOut(PIN_MOTOR_LINKS_DIR)
motor_links_switch.direction = digitalio.Direction.OUTPUT
motor_rechts_switch = digitalio.DigitalInOut(PIN_MOTOR_RECHTS_DIR)
motor_rechts_switch.direction = digitalio.Direction.OUTPUT

# --- Distance Sensor Setup ---
uart = busio.UART(tx=PIN_UART_TX, rx=PIN_UART_RX, baudrate=9600, timeout=0.05)

# --- Servo Setup ---
pwm = pwmio.PWMOut(PIN_SERVO, frequency=40)
my_servo = servo.Servo(pwm, min_pulse=500, max_pulse=2500, actuation_range=180)
my_servo.angle = SERVO_DOWN_POS  # Initialize servo to down position

# --- Network Setup ---
wifi.radio.start_ap(ssid=WIFI_SSID, password=WIFI_PASSWORD)
print("My IP address is", wifi.radio.ipv4_address_ap)

pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)
server.start(str(wifi.radio.ipv4_address_ap), 80)

# ======== GLOBAL STATE VARIABLES ========
# --- General State ---
gestart = False      # is de robot gestart
manueel = False      # handmatige besturing
rijden = False       # rijden
naar_garage = False  # naar de garage

# --- LED State ---
current_led_state = "normal"  # normal, manual, error, lift, turn, garage
led_animation_time = 0.0      # voor de LED animaties
manual_last_cmd = None        # laatste handmatige sturing
pickup_active = False         # of de pickup active is

# --- Sensor State ---
# Calibration values
DREMPELWAARDE_LINKS = 29565   # waarde voor de calibratie
DREMPELWAARDE_RECHTS = 19179  # waarde voor de calibratie
DREMPELWAARDE_ACHTER = 22380  # waarde voor de calibratie
min_links = 65535             # waarde voor de calibratie
min_rechts = 65535            # waarde voor de calibratie
min_achter = 65535            # waarde voor de calibratie

# Sensor readings
links_op_lijn = False      
rechts_op_lijn = False      
achter_op_lijn = False       

# Distance sensor
afstand_metingen_bezig = False  # of de afstandsbepaling actief is
afstand_starttijd = 0           # wanneer de afstandsbepaling begon
laatste_afstand = None          # laatste gemeten afstand

# --- Navigation State ---
# Route
try:
    with open("instructions.txt", "r") as file:
        content = file.read().strip()
        instructions_list = content.split("\n")
except FileNotFoundError:
    instructions_list = [] 

route = instructions_list  # F = forward, L = left, R = right, T180 = turn 180, P = pickup, S = stop
print("Route:", route)
route_index = 0
command = ""

# Crosspoint detection
kruispunt_teller = 0
laatste_kruispunt_tijd = 0

# Backup mode
post_backup_mode = False
distance_traveled_since_backup = 0

# --- Maneuver States ---
is_manoeuvre_active = False 

# Right turn
rechterbocht_status = "idle"  # idle, bocht
rechterbocht_starttijd = 0

# Left turn
linkerbocht_status = "idle"   # idle, bocht
linkerbocht_starttijd = 0

# 180 turn
turn_180_status = "idle"      # idle, bocht
turn_180_starttijd = 0
turn_180_lijn_confirmaties = 0

# Pickup
pickup_status = "idle"        # idle, lift
pickup_starttijd = 0

# Reverse
achteruit_bezig = False
achteruit_starttijd = 0

# Completed turn
bocht_voltooid = False

# --- Timing Variables ---
web_next_activation = time.monotonic()
drive_next_activation = time.monotonic()
sensor_next_activation = time.monotonic()

# --- WebSocket ---
websocket = None

# ======== FUNCTION DEFINITIONS ========
# -------- WebSocket Functions --------
def is_websocket_connected(ws):
    return ws is not None

@server.route("/connect-websocket", GET)
def connect_client(request: Request):
    global websocket
    if websocket is not None:
        try:
            websocket.close()
        except Exception as e:
            print(f" Fout bij sluiten oude WebSocket: {e}")
    
    try:
        websocket = Websocket(request)
        print("✅ WebSocket connection established")
        return websocket
    except ValueError as e:
        print(f" Invalid WebSocket handshake request: {e}")
        return Response("WebSocket handshake failed", status=400)
    except Exception as e:
        print(f" Onverwachte fout bij WebSocket verbinding: {e}")
        return Response("Internal server error", status=500)

def send_websocket_message(message, fail_silently=True):
    global websocket
    if websocket is None:
        return False
        
    try:
        websocket.send_message(message, fail_silently=fail_silently)
        return True
    except Exception as e:
        print(f" Error sending websocket message: {e}")
        websocket = None
        return False

# -------- LED Control Functions --------

def L_t(t): return 0.5 + 0.5 * math.sin(2 * math.pi * t)
def set_rgb_led(r, g, b):
    rgb_red.duty_cycle = int(max(0, min(65535, r)))
    rgb_green.duty_cycle = int(max(0, min(65535, g)))
    rgb_blue.duty_cycle = int(max(0, min(65535, b)))

def led_cycle_white_green(t):
    set_rgb_led(L_t(t)*65535, 65535, L_t(t)*65535)
def led_blink_orange(t):
    set_rgb_led(65535*(t%2<1), 8000*(t%2<1), 0)
def led_blink_red(t):
    set_rgb_led(65535*(t%2<1), 0, 0)

def update_led_state(state, manual_cmd=None):
    global current_led_state, manual_last_cmd, pickup_active
    if state == "lift": pickup_active = True
    elif state == "normal": pickup_active = False
    if current_led_state != "garage" or state == "garage":
        current_led_state = state
    if manual_cmd: manual_last_cmd = manual_cmd

    if naar_garage or state == "garage":
        set_rgb_led(0, 0, 65535)
    elif pickup_active:
        led_blink_orange(led_animation_time)
    elif gestart and state == "normal":
        led_cycle_white_green(led_animation_time)
    elif state == "error":
        led_blink_red(led_animation_time)
    elif state == "manual":
        set_rgb_led(40000, 0, 40000 if manual_last_cmd != "backward" else 65535)
    else:
        set_rgb_led(0, 0, 0)

# === Sensorfuncties ===
def lees_sensor(sensor, drempel): 
    return sensor.value < drempel

def start_meet_afstand():
    global afstand_metingen_bezig, afstand_starttijd
    uart.write(b"\x55")
    afstand_starttijd = time.monotonic()
    afstand_metingen_bezig = True

def update_meet_afstand():
    global afstand_metingen_bezig, laatste_afstand
    if afstand_metingen_bezig and (time.monotonic() - afstand_starttijd) >= 0.1:
        try:
            data = uart.read(2)  # probeer 2 bytes te lezen
            if data and len(data) == 2:
                # bereken de afstand in cm
                afstand = (data[0] * 256 + data[1]) / 10
                laatste_afstand = afstand
            else:
                laatste_afstand = None
                print(" Geen geldige data ontvangen van afstandssensor")
        except Exception as e:
            print(f" Fout bij afstandsmeting: {e}")
            laatste_afstand = None
        finally:
            afstand_metingen_bezig = False

# === Bewegingsfuncties === (DOE ALTIJD EERST RICHTING DAN KRACHT)
def set_motoren_richting(link_dir, rechts_dir): # True is vooruit, False achteruit
    motor_links_switch.value = link_dir
    motor_rechts_switch.value = rechts_dir
    time.sleep(0.01)

def set_motoren_kracht(link_kracht, rechts_kracht): # maximum is 65535
    motor_links.duty_cycle = link_kracht
    motor_rechts.duty_cycle = rechts_kracht

def stop():
    global post_backup_mode
    print("STOP motoren!!!")
    #set_motoren_richting(0, 0) #onnodig
    set_motoren_kracht(0, 0)
    if not (achteruit_bezig or turn_180_status != "idle" or rechterbocht_status != "idle" or linkerbocht_status != "idle"):
        update_led_state("normal")
        post_backup_mode = False

def rijd_rechtdoor(): 
    print("rijd rechtdoor motoren!!!")
    set_motoren_richting(True, True)
    set_motoren_kracht(60000, 60000)
    update_led_state("normal")

def draai_links_correctie(): 
    print("draai links motoren!!!")
    set_motoren_richting(True, True)
    set_motoren_kracht(35000, 65000)
    update_led_state("normal")

def draai_rechts_correctie(): 
    print("draai rechts motoren!!!")
    set_motoren_richting(True, True)
    set_motoren_kracht(65000, 35000)
    update_led_state("normal")

def kruispunt_oversteken():
    print("kruispunt oversteken motoren!!!")
    snelheid = 55000 if post_backup_mode else 45000
    tijd = 0.5 if post_backup_mode else 0.3
    print("Kruispunt oversteken...")
    set_motoren_richting(True, True)
    set_motoren_kracht(snelheid, snelheid)
    time.sleep(tijd)

def start_rijd_achteruit():
    global achteruit_bezig, achteruit_starttijd
    print("🚗 Achteruit!")
    update_led_state("error")
    set_motoren_richting(False, False)
    set_motoren_kracht(25000, 25000)
    achteruit_bezig = True
    achteruit_starttijd = time.monotonic()

def update_rijd_achteruit():
    global achteruit_bezig
    if achteruit_bezig and time.monotonic() - achteruit_starttijd >= 1.5:
        stop()
        achteruit_bezig = False
        print("Achteruit klaar")

# === Bochten ===
def start_rechterbocht():
    global rechterbocht_status, rechterbocht_starttijd
    print("▶️ Rechterbocht...")
    set_motoren_richting(True, False)
    set_motoren_kracht(58000, 5000)
    rechterbocht_status = "bocht"
    rechterbocht_starttijd = time.monotonic()

def update_rechterbocht():
    global rechterbocht_status, rijden, bocht_voltooid
    if rechterbocht_status == "bocht" and time.monotonic() - rechterbocht_starttijd > 0.8:
        set_motoren_kracht(5000, 30000)
        if lees_sensor(lichtsensor_links, DREMPELWAARDE_LINKS) or lees_sensor(lichtsensor_rechts, DREMPELWAARDE_RECHTS):
            stop()
            rechterbocht_status = "idle"
            print("✅ Rechterbocht klaar")
            bocht_voltooid = True
            rijden = True


def start_linkerbocht():
    global linkerbocht_status, linkerbocht_starttijd
    print("linkerbocht maken...")
    set_motoren_richting(False, True)
    set_motoren_kracht(5000,58000)
    linkerbocht_status = ("bocht")
    linkerbocht_starttijd = time.monotonic()

def update_linkerbocht():
    global linkerbocht_status, linkerbocht_starttijd, rijden, bocht_voltooid
    if linkerbocht_status == "bocht" and time.monotonic() - linkerbocht_starttijd > 0.8:
        set_motoren_kracht(30000, 5000)
        if lees_sensor(lichtsensor_links, DREMPELWAARDE_LINKS) or lees_sensor(lichtsensor_rechts, DREMPELWAARDE_RECHTS):
            stop()
            linkerbocht_status = "idle"
            print("✅ Linkerbocht klaar")
            bocht_voltooid = True
            rijden = True


def start_turn_180():
    global turn_180_status, turn_180_starttijd, rijden, turn_180_lijn_confirmaties

    if turn_180_status == "idle":
        print("--> Start 180 Turn Manoeuvre...")
        stop()
        rijden = False
        time.sleep(0.1)
        set_motoren_richting(False, True)
        set_motoren_kracht(50000, 50000)
        turn_180_status = "bocht"
        turn_180_starttijd = time.monotonic()
        turn_180_lijn_confirmaties = 0


def update_turn_180():
    global turn_180_status, turn_180_starttijd, rijden, bocht_voltooid, turn_180_lijn_confirmaties

    if turn_180_status != "bocht":
        return

    current_time = time.monotonic()
    elapsed_time = current_time - turn_180_starttijd
    MAX_TURN_180_TIME = 10.0  # maximum tijd
    MIN_DETECT_TIME_180 = 2  # wanneer de lijn detectie begint
    NODIGE_CONFIRMATIES = 1  # bevestigingen voor de lijn detectie (soms kan er een false positive meting zijn)

    # Timeout safety
    if elapsed_time > MAX_TURN_180_TIME:
        print("!!! FOUT: Timeout tijdens 180 graden draai !!!")
        stop()
        turn_180_status = "idle"
        rijden = False
        turn_180_lijn_confirmaties = 0
        return

   # After minimum time, start checking for line
    if elapsed_time > MIN_DETECT_TIME_180:
        # vertraging voor nauwkeurigere lijn detectie
        set_motoren_kracht(20000, 20000)

        if lees_sensor(lichtsensor_links, DREMPELWAARDE_LINKS) or lees_sensor(lichtsensor_rechts, DREMPELWAARDE_RECHTS):
            turn_180_lijn_confirmaties += 1
            
        if turn_180_lijn_confirmaties >= NODIGE_CONFIRMATIES:
            stop()
            turn_180_status = "idle"
            bocht_voltooid = True
            rijden = True
            turn_180_lijn_confirmaties = 0
            print("✅ Turn 180: Lijn bevestigd.")

# -------- Pickup Functions --------
def start_pickup():
    global pickup_status, pickup_starttijd, is_manoeuvre_active
    
    print("Draai servo-motor (Pickup)")
    update_led_state("lift")
    my_servo.angle = SERVO_UP_POS
    
    # Make sure maneuver is active to block crosspoint detection
    is_manoeuvre_active = True
    
    pickup_status = "lift"
    
    pickup_starttijd = time.monotonic()


def update_pickup():
    global pickup_status, pickup_starttijd, rijden, drive_next_activation
    global post_backup_mode, distance_traveled_since_backup, is_manoeuvre_active
    global laatste_kruispunt_tijd
    
    current_time = time.monotonic()
    
    # om de kruipuntendetectie te blokkeren
    if pickup_status != "idle":
        is_manoeuvre_active = True
    
    if pickup_status == "lift" and (current_time - pickup_starttijd) >= 0.8:
        my_servo.angle = SERVO_MID_POS
        pickup_status = "idle"

        if current_led_state != "garage":
            update_led_state("normal")
        
        rijden = True
        is_manoeuvre_active = False
        print("Regular pickup completed")

# -------- Calibration Functions --------
def kalibratie_draai_rechts():
    set_motoren_richting(True,True)
    set_motoren_kracht(37000,0)
   
def draai_kalibratie():
    global min_links, min_rechts, min_achter
    
    print("\U0001F504 Start kalibratie... Beweegt rechtdoor.")


    start_tijd = time.monotonic()
    while time.monotonic() - start_tijd < KALIB_DUUR:
        kalibratie_draai_rechts()
        
        waarde_links = lichtsensor_links.value
        waarde_rechts = lichtsensor_rechts.value
        waarde_achter = lichtsensor_achter.value
        
        if waarde_links > 10000 and waarde_rechts > 10000 and waarde_achter > 10000:
            min_links = min(min_links, waarde_links)
            min_rechts = min(min_rechts, waarde_rechts)
            min_achter = min(min_achter, waarde_achter)
            
        print("Links", waarde_links, "Rechts", waarde_rechts, "Achter", waarde_achter)
        time.sleep(0.1)


        stop()
    print("\u2705 Kalibratie voltooid!")

def kalibratie():
    global DREMPELWAARDE_LINKS, DREMPELWAARDE_RECHTS, DREMPELWAARDE_ACHTER
    global rijden, gestart, web_next_activation, websocket
    global rechterbocht_status, linkerbocht_status, turn_180_status, pickup_status, achteruit_bezig
    
    rijden = False
    stop()
    
    rechterbocht_status = "idle"
    linkerbocht_status = "idle"
    turn_180_status = "idle"
    pickup_status = "idle"
    achteruit_bezig = False
    #Start kalibratie
    draai_kalibratie()

    DREMPELWAARDE_LINKS = min_links + KALIB_OFFSET
    DREMPELWAARDE_RECHTS = min_rechts + KALIB_OFFSET
    DREMPELWAARDE_ACHTER = min_achter + KALIB_OFFSET

    print("Eindwaarden: Links", DREMPELWAARDE_LINKS, "Rechts", DREMPELWAARDE_RECHTS, "Achter", DREMPELWAARDE_ACHTER)

    stop()
    web_next_activation = time.monotonic()
    server.poll()
  
    if websocket is not None:
        if not is_websocket_connected(websocket):
            print(" WebSocket connection lost during calibration. Waiting for reconnection.")
            websocket = None
        else:
            try:
                websocket.send_message("calibration_complete", fail_silently=True)
                print("✅ WebSocket message sent successfully.")
            except Exception as e:
                print(f" Error sending calibration complete message: {e}")
                websocket = None

    # Update LED
    update_led_state("normal")
    
    print("✅ Kalibratie voltooid en systeem reset. Klaar voor nieuwe commando's.")

# -------- Manual Control Functions --------
def manual_forward():
    try:
        set_motoren_richting(True,True)
        set_motoren_kracht(50000,42000)
        time.sleep(0.1)
        stop()
    except Exception as e:
        print(f" Error in manual_forward: {e}")
        stop()

def manual_backward():
    try:
        set_motoren_richting(False,False)
        set_motoren_kracht(50000,42000)
        time.sleep(0.1)
        stop()
    except Exception as e:
        print(f" Error in manual_backward: {e}")
        stop()

def manual_turn_left():
    try:
        set_motoren_richting(False,True)
        set_motoren_kracht(30000,30000)
        time.sleep(0.1)
        stop()
    except Exception as e:
        print(f" Error in manual_turn_left: {e}")
        stop()

def manual_turn_right():
    try:
        set_motoren_richting(True,False)
        set_motoren_kracht(30000,30000)
        time.sleep(0.1)
        stop()
    except Exception as e:
        print(f" Error in manual_turn_right: {e}")
        stop()

def manual_pickup():
    try:
        my_servo.angle = SERVO_UP_POS
        time.sleep(0.8)
        my_servo.angle = SERVO_DOWN_POS
    except Exception as e:
        print(f" Error in manual_pickup: {e}")

# -------- Cleanup Function --------
def cleanup_resources():
    print("Cleaning up hardware resources...")
  
    try:
        # Stop motoren
        stop()
      
        # Reset servo
        my_servo.angle = SERVO_DOWN_POS
        
        # zet de LEDs uit
        set_rgb_led(*LED_OFF)
        led_links.value = False
        led_rechts.value = False
        led_achter.value = False
        
        # Reset alle globale status variabelen
        global turn_180_lijn_confirmaties, turn_180_status
        global rechterbocht_status, linkerbocht_status
        turn_180_lijn_confirmaties = 0
        turn_180_status = "idle"
        rechterbocht_status = "idle"
        linkerbocht_status = "idle"
        
        # Sluit de WebSocket
        if websocket is not None:
            try:
                websocket.close()
            except Exception as e:
                print(f" Error closing WebSocket: {e}")
        
        # Stop de server
        try:
            server.stop()
        except Exception as e:
            print(f" Error stopping server: {e}")
            
    except Exception as e:
        print(f" Error during cleanup: {e}")

# -------- WebSocket Command Handler --------
def handle_websocket_command(data):
    global rijden, gestart, manueel, route, route_index, command
    global achteruit_bezig, pickup_status, is_manoeuvre_active, turn_180_status, rechterbocht_status, linkerbocht_status

    print(f"received: {data}")
    send_websocket_message(data)  # de command terugsturen (voor debug en log)
    
    # commands
    if data == "start":
        rijden = True
        gestart = True
        if not manueel:
            update_led_state("normal")
        
        # Start beweging direct wanneer op start wordt gedrukt
        set_motoren_richting(True,True)
        set_motoren_kracht(60000,60000)
        print(">>> start met rijden")
    
    elif data == "stop":
        stop()
        rijden = False
        # Reset alle actieve manoeuvres
        is_manoeuvre_active = False
        achteruit_bezig = False
        pickup_status = "idle"
        turn_180_status = "idle"
        rechterbocht_status = "idle" 
        linkerbocht_status = "idle"
        #time.sleep(2)
        
        if not manueel:
            update_led_state("off")
        print(">>> noodstop geactiveerd")
    
    elif data == "manualcontrol":
        manueel = not manueel
        if manueel:
            update_led_state("manual")
        else:
            update_led_state("normal")
        print(f">>> manual mode: {manueel}")
    
    elif data == "kalibratie":
        rijden = False
        stop()
        kalibratie()
    
    elif data == "resetroute":
        route = instructions_list
        route_index = 0
        command = ""
        print("route gereset!")

# Manual mode commands
    elif manueel:
        if data == "forward":
            manual_forward()
            update_led_state("manual", manual_cmd="forward")
            print(">>> manual forward")
        
        elif data == "backward":
            manual_backward()
            update_led_state("manual", manual_cmd="backward")
            print(">>> manual backward")
        
        elif data == "left":
            manual_turn_left()
            update_led_state("manual", manual_cmd="left")
            print(">>> manual left")
        
        elif data == "right":
            manual_turn_right()
            update_led_state("manual", manual_cmd="right")
            print(">>> manual right")

        elif data == "pickup":
            manual_pickup()
            print(">>> manual pickup")

# lichtsensor check
if lichtsensor_links.value < 7000:
    print("linker lichtsensor heel lage waarde")
if lichtsensor_rechts.value < 7000:
    print("rechter lichtsensor heel lage waarde")
if lichtsensor_achter.value < 7000:
    print("achter lichtsensor heel lage waarde")

print("Initializing system...")
time.sleep(3)


# ======== MAIN PROGRAM LOOP ========
try:
    # Main program loop
    while True:
        current_time = time.monotonic()
        led_animation_time += LED_UPDATE_INTERVAL


        # Update LED in manual mode
        if manueel:
            current_led_state = "manual"
        
        # Update LED
        update_led_state(current_led_state, manual_last_cmd)


        if gestart:
            # --- Sensor Reading Logic ---
            if current_time >= sensor_next_activation:
                links_op_lijn = lees_sensor(lichtsensor_links, DREMPELWAARDE_LINKS)
                rechts_op_lijn = lees_sensor(lichtsensor_rechts, DREMPELWAARDE_RECHTS)
                achter_op_lijn = lees_sensor(lichtsensor_achter, DREMPELWAARDE_ACHTER)

                sensor_next_activation = current_time + SENSOR_INTERVAL
            
            # --- Maneuver Updates ---
            update_rijd_achteruit()
            update_linkerbocht()
            update_rechterbocht()
            update_turn_180()
            update_pickup()
            update_meet_afstand()

            is_manoeuvre_active = (
                achteruit_bezig or
                rechterbocht_status != "idle" or
                linkerbocht_status != "idle" or
                turn_180_status != "idle" or
                                pickup_status != "idle"
            )


            # --- Line Following Logic ---
            if rijden and not is_manoeuvre_active:
                if current_time >= drive_next_activation:
                    drive_next_activation = current_time + DRIVE_INTERVAL
                    
                    #--- Afstandsensor Check ---
                    if not afstand_metingen_bezig:
                        start_meet_afstand()
                    
                    if laatste_afstand is not None:
                        if laatste_afstand < DREMPEL_AFSTAND:
                            print(f"OBJECT GEDETECTEERD! op {laatste_afstand}cm")
                            start_rijd_achteruit()
                            continue

                    # --- Kruispunt Detectie & Route Navigatie ---
                    is_kruispunt_conditie = achter_op_lijn or command == "P" or bocht_voltooid
                    print(f"is_kruispunt_conditie:{is_kruispunt_conditie}, achter_op_lijn:{achter_op_lijn}, is command = P?:{command}, bocht voltooid:{bocht_voltooid}. !!!")

                    if is_kruispunt_conditie:
                        bocht_voltooid = False
                        if (current_time - laatste_kruispunt_tijd > 1) or command == "P":
                            stop()
                            laatste_kruispunt_tijd = current_time
                            print(f"Kruispunt! Index: {route_index}")


                            if route_index < len(route):
                                command = route[route_index]
                                send_websocket_message(f"route_index:{route_index}:{command}")
                                print(f"  Uitvoeren: '{command}'")
                                rijden = False
                                time.sleep(0.1)
                                
                                if not naar_garage and "P" not in route[route_index:]:
                                    update_led_state("garage")
                                    naar_garage = True


                                if command == 'F':    
                                    kruispunt_oversteken()
                                    rijden = True
                                elif command == 'L':
                                    start_linkerbocht()
                                elif command == 'R':
                                    start_rechterbocht()
                                elif command == 'S':
                                    print("Route: STOP.")
                                    stop()
                                    rijden = False
                                elif command == "T180":
                                    start_turn_180()
                                elif command == "P":
                                    print(f"P command detected at index {route_index}")
                                    start_pickup()
                                else:
                                    print(f"  Onbekend commando: {command}")
                                    rijden = True
                                route_index += 1
                            else:
                                print(" Einde route, kruispunt genegeerd.")
                                stop()
                                rijden = False
                            continue


                    # --- Line Following Corrections ---
                    if rijden and (laatste_afstand is None or laatste_afstand >= DREMPEL_AFSTAND):
                        my_servo.angle = SERVO_DOWN_POS
                        
                        if links_op_lijn and rechts_op_lijn:
                            rijd_rechtdoor()
                        elif links_op_lijn and not rechts_op_lijn:
                            draai_links_correctie()
                        elif rechts_op_lijn and not links_op_lijn:
                            draai_rechts_correctie()
                        elif not links_op_lijn and not rechts_op_lijn:
                            draai_rechts_correctie()


        # --- WebSocket Communication ---
        if current_time >= web_next_activation:
            web_next_activation = current_time + WEB_INTERVAL
            
            try:
                server.poll()
                
                if websocket is not None:
                    if not is_websocket_connected(websocket):
                        print(" WebSocket connection lost. Waiting for reconnection.")
                        websocket = None
                    else:
                        try:
                            data = websocket.receive(fail_silently=True)
                            if data is not None:
                                handle_websocket_command(data)
                        except Exception as e:
                            print(f" WebSocket receive error: {e}")
                            websocket = None
            except Exception as e:
                print(f" Server polling error: {e}")


        # kleine rust voor CPU
        time.sleep(0.01)


except KeyboardInterrupt:
   print("Programma gestopt door gebruiker.")
except Exception as e:
   print(f"Onverwachte fout: {e}")
   update_led_state("error")
finally:
   print("Opschonen...")
   cleanup_resources()
   print("Klaar.")
