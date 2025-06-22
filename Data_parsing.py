import serial
import csv
import requests
import time

# === Configuration ===
UPLOAD_INTERVAL       = 5                   # seconds between uploads
EXPECTED_DEVICE_COUNT = 1                   # number of devices expected per batch
SERIAL_PORT           = 'COM8'
BAUD_RATE             = 9600
SERVER_URL            = "https://kargalex.eu.pythonanywhere.com/submit"

# === Serial Init ===
arduino_serial = serial.Serial(SERIAL_PORT, BAUD_RATE)

# === Field Identifiers in Serial Data ===
fields = {
    "device":      "Dev=",
    "time":        ",Time=",
    "longitude":   ",Lon=",
    "latitude":    ",Lat=",
    "altitude":    ",Alt=",
    "temperature": ",Temp=",
    "humidity":    ",Hum=",
    "UV":          ",UV=",
    "rain":        ",Rain=",
    "end":         ",end"
}

def parse_serial_line(line):
    """Extracts all fields from one well-formed serial line or returns None."""
    try:
        d, t  = line.find(fields["device"]),     line.find(fields["time"])
        lo, la = line.find(fields["longitude"]), line.find(fields["latitude"])
        al, tp = line.find(fields["altitude"]),  line.find(fields["temperature"])
        hu, uv = line.find(fields["humidity"]),  line.find(fields["UV"])
        ra, en = line.find(fields["rain"]),      line.find(fields["end"])

        if d == -1 or en == -1:
            return None

        return {
            "device": int( line[d + len(fields["device"]): t].strip() ),
            "time":   line[t + len(fields["time"]):      lo].strip(),
            "long":   float( line[lo + len(fields["longitude"]): la] ),
            "lat":    float( line[la + len(fields["latitude"]):  al] ),
            "alt":    float( line[al + len(fields["altitude"]):  tp] ),
            "temp":   float( line[tp + len(fields["temperature"]): hu] ),
            "hum":    float( line[hu + len(fields["humidity"]):   uv] ),
            "uv":     float( line[uv + len(fields["UV"]):         ra] ),
            "rain":   int(   line[ra + len(fields["rain"]):       en] )
        }
    except Exception:
        print("Failed to parse:", line)
        return None

# === Main Loop ===
while True:
    device_data = {}

    # 1) Read exactly EXPECTED_DEVICE_COUNT valid lines
    for _ in range(EXPECTED_DEVICE_COUNT):
        while not arduino_serial.inWaiting():
            pass

        raw = arduino_serial.readline().decode(errors='ignore').strip()
        parsed = parse_serial_line(raw)
        if not parsed:
            print("Skipped malformed:", raw)
            continue

        dev_id = parsed["device"]
        payload = {k: v for k, v in parsed.items() if k != "device"}
        device_data[str(dev_id)] = payload

    # 4) Upload batch if we got anything
    if device_data:
        print("Uploading:", device_data)
        try:
            resp = requests.post(SERVER_URL, json=device_data)
            if resp.status_code == 200:
                print("Upload successful.")
            else:
                print(f"Upload failed {resp.status_code}:", resp.text)
        except Exception as e:
            print("Upload exception:", e)

    # 5) Wait before next batch
    time.sleep(UPLOAD_INTERVAL)
