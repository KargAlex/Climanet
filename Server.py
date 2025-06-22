from flask import Flask, request, jsonify, send_file
import csv
import os
import zipfile
from io import BytesIO

app = Flask(__name__)
DATA_DIR = "/home/Kargalex"

def save_device(device_id: int, data: dict):
    """
    Writes one row into <device_id>_data.csv (creating file + header if needed).
    Expects `data` to be a dict containing:
      "time", "long", "lat", "alt", "temp", "hum", "uv", "rain"
    """
    filename = f"{device_id}_data.csv"
    filepath = os.path.join(DATA_DIR, filename)

    # Map internal keys to proper header names
    headers = ["time", "longitude", "latitude", "altitude",
               "temp", "hum", "uv", "rain"]

    row = [
        data.get("time"),
        data.get("long"),
        data.get("lat"),
        data.get("alt"),
        data.get("temp"),
        data.get("hum"),
        data.get("uv"),
        data.get("rain")
    ]

    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)  # Write header only once
        writer.writerow(row)


@app.route('/')
def home():
    return "Server is running."

@app.route('/submit', methods=['POST'])
def submit():
    """
    Accepts a dict-of-dicts where:
      - Each key is a device ID (as a string, e.g. "0", "1", "42", etc.)
      - Each value is itself a dict containing exactly:
          "time", "long", "lat", "alt", "temp", "hum", "uv", "rain"

    Example JSON payload:
    {
      "0": {
        "time": "2025-06-02 12:00:08",
        "long": 22.947412,
        "lat": 40.629269,
        "alt": 10,
        "temp": 26.4,
        "hum": 58.0,
        "uv": 4.7,
        "rain": 0
      },
      "1": {
        "time": "2025-06-02 12:00:15",
        "long": 23.727539,
        "lat": 37.983810,
        "alt": 70,
        "temp": 25.9,
        "hum": 60.2,
        "uv": 4.9,
        "rain": 1
      }
    }
    """
    payload = request.get_json()
    if not isinstance(payload, dict):
        return (
            jsonify({"status": "error", "message": "Expected a JSON object (dict)"}),
            400
        )

    # Iterate over each (device_id_str, subdict) pair
    for device_str, subdict in payload.items():
        try:
            device_id = int(device_str)
        except ValueError:
            return (
                jsonify({
                    "status": "error",
                    "message": f"Device key '{device_str}' is not a valid integer"
                }),
                400
            )

        if not isinstance(subdict, dict):
            return (
                jsonify({
                    "status": "error",
                    "message": f"Payload for device '{device_str}' is not a JSON object"
                }),
                400
            )

        required_fields = {
            "time", "long", "lat", "alt", "temp", "hum", "uv", "rain"
        }
        missing = required_fields - subdict.keys()
        extra = subdict.keys() - required_fields

        if missing:
            return (
                jsonify({
                    "status": "error",
                    "message": (
                        f"Device '{device_str}' is missing fields: {sorted(missing)}"
                    )
                }),
                400
            )
        if extra:
            return (
                jsonify({
                    "status": "error",
                    "message": (
                        f"Device '{device_str}' has unexpected fields: {sorted(extra)}"
                    )
                }),
                400
            )

    try:
        for device_str, subdict in payload.items():
            device_id = int(device_str)
            save_device(device_id, subdict)

        return jsonify({"status": "success", "message": "Batch processed"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/latest", methods=["GET"])
def get_latest_data_all_devices():
    result = {}
    try:
        for filename in os.listdir(DATA_DIR):
            if not filename.endswith("_data.csv"):
                continue

            device_id = filename.replace("_data.csv", "")
            filepath = os.path.join(DATA_DIR, filename)

            try:
                with open(filepath, newline="") as f:
                    reader = csv.DictReader(f)
                    last_row_dict = None
                    for row_dict in reader:
                        last_row_dict = row_dict

                    if last_row_dict:
                        result[device_id] = last_row_dict

            except Exception as e:
                result[device_id] = {"error": f"Could not read file: {e}"}

        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_logs", methods=["GET"])
def get_all_logs():
    try:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for filename in os.listdir(DATA_DIR):
                if filename.endswith("_data.csv"):
                    file_path = os.path.join(DATA_DIR, filename)
                    zipf.write(file_path, arcname=filename)

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name="logs.zip"
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
