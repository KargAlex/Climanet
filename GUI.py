import customtkinter
import tkinter
from PIL import Image
from tkintermapview import TkinterMapView
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests
from geopy.geocoders import Nominatim
import mplcursors
import matplotlib.ticker as ticker
from datetime import datetime, time
from matplotlib.dates import DateFormatter, HourLocator, num2date

# API URL
API_URL = "https://kargalex.eu.pythonanywhere.com/latest"

# Initialize geolocator for reverse geocoding
geolocator = Nominatim(user_agent="weather_app")

# Store current markers by API key with their data
current_markers = {}  # {key: {'marker': marker, 'coords': (lat, lon), 'name': city_name, 'temperature_data': [], 'uv_data': [], 'humidity_data': [], 'time_data': []}}

# Track currently displayed location
current_location = "No Location Selected"

def is_daytime():
    """Determine if it's daytime (6 AM to 6 PM) based on current time."""
    now = datetime.now().time()
    return time(6, 0) <= now <= time(21, 0)

def update_clock():
    now = datetime.now()
    current_date = now.strftime("%A - %d/%m/%Y")  # Format: Day - DD/MM/YYYY
    current_time = now.strftime("%H:%M")  # Format: HH:MM (24-hour)
    date_label.configure(text=f"{current_date}")
    time_label.configure(text=f"{current_time}")
    app.after(6000, update_clock)  # Update every 60,000 ms (1 minute)

def get_weather_icon(uv, rain):
    """Select weather icon based on UV, rain, and time of day."""
    is_day = is_daytime()
    rain = rain == '1'
    uv = float(uv)

    if is_day:
        if rain:
            if uv > 1:
                return scattered_showers_day_icon
            else:
                return showers_rain_icon
        else:  # No rain
            if uv == 0:
                return cloudy_icon
            elif 1 <= uv <= 2:
                return mostly_cloudy_day_icon
            elif 3 <= uv <= 6:
                return partly_cloudy_icon
            elif 6 < uv <= 8:
                return mostly_sunny_icon
            elif uv > 8:
                return sunny_icon
    else:  # Nighttime
        if rain:
            return scattered_showers_night_icon
        else:
            return clear_night_icon
    return cloudy_icon  # Fallback

def on_marker_click(marker):
    global current_location
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data_dict = response.json()
            for key, data in data_dict.items():
                if key in current_markers and current_markers[key]['name'] == marker.text:
                    current_location = marker.text
                    location_label.configure(text=f"Location: {current_location}")
                    humidity = float(data['hum'])
                    uv = float(data['uv'])
                    temp = float(data['temp'])
                    rain = data['rain']
                    new_icon = get_weather_icon(uv, rain)
                    new_text = f"Humidity: {humidity:.1f}%\n\nUV Index: {uv:.1f}\n\nRain: {'Yes' if rain == '1' else 'No Rain'}"
                    label_board.configure(text=new_text)
                    image_label.configure(image=new_icon)
                    text_label.configure(text=f"{temp:.1f}°C")
                    text_label2.configure(text="Sunny" if uv > 5 else "Cloudy")
                    # Update graph with stored data for this location
                    temp_line.set_data(current_markers[key]['time_data'], current_markers[key]['temperature_data'])
                    uv_line.set_data(current_markers[key]['time_data'], current_markers[key]['uv_data'])
                    humidity_line.set_data(current_markers[key]['time_data'], current_markers[key]['humidity_data'])
                    for ax in [temp_ax, uv_ax, humidity_ax]:
                        ax.relim()
                        ax.autoscale_view()
                    canvas.draw_idle()
                    return
            print(f"No matching data found for city: {marker.text}")
            current_location = "No Location Selected"
            location_label.configure(text=f"Location: {current_location}")
            label_board.configure(text="No data for this location")
            temp_line.set_data([], [])
            uv_line.set_data([], [])
            humidity_line.set_data([], [])
            for ax in [temp_ax, uv_ax, humidity_ax]:
                ax.relim()
                ax.autoscale_view()
            canvas.draw_idle()
        else:
            print(f"Failed to fetch data: {response.status_code}")
            current_location = "No Location Selected"
            location_label.configure(text=f"Location: {current_location}")
            label_board.configure(text="Error fetching data")
    except Exception as e:
        print(f"Error fetching API data: {e}")
        current_location = "No Location Selected"
        location_label.configure(text=f"Location: {current_location}")
        label_board.configure(text="Error fetching data")

def open_full_map():
    map_window = customtkinter.CTkToplevel(app)
    map_window.title("Full Map")
    map_window.geometry("1280x720")
    map_window.grid_columnconfigure(0, weight=1)
    map_window.grid_rowconfigure(0, weight=1)

    full_map_widget = TkinterMapView(map_window)
    full_map_widget.grid(row=0, column=0, sticky="nsew")

    # Center on Greece
    full_map_widget.set_position(39.0, 22.0)  # Center of Greece
    full_map_widget.set_zoom(6)  # Zoom to show all of Greece

    # Add all persisted markers
    for marker_info in current_markers.values():
        full_map_widget.set_marker(
            marker_info['coords'][0],
            marker_info['coords'][1],
            text=marker_info['name'],
            command=on_marker_click
        )

    close_button = customtkinter.CTkButton(
        master=map_window,
        text="Close",
        command=map_window.destroy,
        fg_color="#29a329"
    )
    close_button.grid(row=1, column=0, pady=10)

def reset_graph():
    global current_markers
    for key in current_markers:
        current_markers[key]['temperature_data'] = []
        current_markers[key]['uv_data'] = []
        current_markers[key]['humidity_data'] = []
        current_markers[key]['time_data'] = []
    temp_line.set_data([], [])
    uv_line.set_data([], [])
    humidity_line.set_data([], [])
    for ax in [temp_ax, uv_ax, humidity_ax]:
        ax.relim()
        ax.autoscale_view()
    canvas.draw_idle()

def refresh_markers():
    global current_markers, current_location
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data_dict = response.json()
        else:
            print(f"Failed to fetch data: {response.status_code}")
            current_location = "No Location Selected"
            location_label.configure(text=f"Location: {current_location}")
            return
    except Exception as e:
        print(f"Error fetching API data: {e}")
        current_location = "No Location Selected"
        location_label.configure(text=f"Location: {current_location}")
        return

    # Clear existing markers
    for marker_info in current_markers.values():
        marker_info['marker'].delete()
    current_markers.clear()

    # Flag to check if Thessaloniki is in API data
    thessaloniki_added = False

    # Process each location in the API response
    for key, data in data_dict.items():
        if not isinstance(data, dict):
            print(f"Invalid data for key {key}: not a dictionary")
            continue
        required_keys = ['latitude', 'longitude', 'temp', 'uv', 'hum', 'rain']
        if not all(k in data for k in required_keys):
            print(f"Missing keys in data for key {key}: {data}")
            continue
        try:
            lat = float(data['latitude'])
            lon = float(data['longitude'])
            new_temp = float(data['temp'])
            new_uv = float(data['uv'])
            new_humidity = float(data['hum'])
            rain = data['rain']

            # Reverse geocode to get city name
            try:
                location = geolocator.reverse((lat, lon), language='en')
                city_name = (
                    location.raw['address'].get('city') or
                    location.raw['address'].get('town') or
                    location.raw['address'].get('village') or
                    location.raw['address'].get('locality') or
                    f"Unknown City {key}"
                ) if location and location.raw.get('address') else f"Unknown City {key}"
            except Exception as e:
                print(f"Error reverse geocoding for key {key}: {e}")
                city_name = f"Unknown City {key}"

            # Check if this is Thessaloniki (based on coordinates proximity)
            if abs(lat - 40.6401) < 0.1 and abs(lon - 22.9444) < 0.1:
                city_name = "Thessaloniki"
                thessaloniki_added = True

            # Add marker
            marker = map_widget.set_marker(
                lat,
                lon,
                text=city_name,
                command=on_marker_click
            )
            current_markers[key] = {
                'marker': marker,
                'coords': (lat, lon),
                'name': city_name,
                'temperature_data': [new_temp],
                'uv_data': [new_uv],
                'humidity_data': [new_humidity],
                'time_data': [datetime.now()]
            }

            # Update displayed data if this is Thessaloniki or first location
            if city_name == "Thessaloniki" or (key == '0' and not thessaloniki_added):
                current_location = city_name
                location_label.configure(text=f"Location: {current_location}")
                text_label.configure(text=f"{new_temp:.1f}°C")
                text_label2.configure(text="Sunny" if new_uv > 5 else "Cloudy")
                image_label.configure(image=get_weather_icon(new_uv, rain))
                label_board.configure(
                    text=f"Humidity: {new_humidity:.1f}%\n\nUV Index: {new_uv:.1f}\n\nRain: {'Yes' if rain == '1' else 'No Rain'}"
                )
                temp_line.set_data(current_markers[key]['time_data'], current_markers[key]['temperature_data'])
                uv_line.set_data(current_markers[key]['time_data'], current_markers[key]['uv_data'])
                humidity_line.set_data(current_markers[key]['time_data'], current_markers[key]['humidity_data'])
                for ax in [temp_ax, uv_ax, humidity_ax]:
                    ax.relim()
                    ax.autoscale_view()
                canvas.draw_idle()
        except ValueError as e:
            print(f"Error converting data to float for key {key}: {e}")
            continue

    # Add Thessaloniki marker if not already added
    if not thessaloniki_added:
        thessaloniki_lat = 40.6401
        thessaloniki_lon = 22.9444
        city_name = "Thessaloniki"
        # Try to fetch data for Thessaloniki from API or use placeholder
        placeholder_data = {
            'temp': 20.0,  # Placeholder values
            'uv': 5.0,
            'hum': 60.0,
            'rain': '0'
        }
        marker = map_widget.set_marker(
            thessaloniki_lat,
            thessaloniki_lon,
            text=city_name,
            command=on_marker_click
        )
        key = f"thessaloniki_{len(current_markers)}"
        current_markers[key] = {
            'marker': marker,
            'coords': (thessaloniki_lat, thessaloniki_lon),
            'name': city_name,
            'temperature_data': [placeholder_data['temp']],
            'uv_data': [placeholder_data['uv']],
            'humidity_data': [placeholder_data['hum']],
            'time_data': [datetime.now()]
        }
        # Set as current location if no other location is selected
        if current_location == "No Location Selected":
            current_location = city_name
            location_label.configure(text=f"Location: {current_location}")
            text_label.configure(text=f"{placeholder_data['temp']:.1f}°C")
            text_label2.configure(text="Sunny" if placeholder_data['uv'] > 5 else "Cloudy")
            image_label.configure(image=get_weather_icon(placeholder_data['uv'], placeholder_data['rain']))
            label_board.configure(
                text=f"Humidity: {placeholder_data['hum']:.1f}%\n\nUV Index: {placeholder_data['uv']:.1f}\n\nRain: {'Yes' if placeholder_data['rain'] == '1' else 'No Rain'}"
            )
            temp_line.set_data(current_markers[key]['time_data'], current_markers[key]['temperature_data'])
            uv_line.set_data(current_markers[key]['time_data'], current_markers[key]['uv_data'])
            humidity_line.set_data(current_markers[key]['time_data'], current_markers[key]['humidity_data'])
            for ax in [temp_ax, uv_ax, humidity_ax]:
                ax.relim()
                ax.autoscale_view()
            canvas.draw_idle()

    # Update map position
    map_widget.set_position(39.0, 22.0)  # Center of Greece
    map_widget.set_zoom(6)  # Zoom to show all of Greece

def update_data():
    global current_markers, current_location
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data_dict = response.json()
        else:
            print(f"Failed to fetch data: {response.status_code}")
            label_board.configure(text="Error fetching data")
            return
    except Exception as e:
        print(f"Error fetching API data: {e}")
        label_board.configure(text="Error fetching data")
        return

    # Update data for all locations
    for key, data in data_dict.items():
        if key not in current_markers:
            continue
        # Check if data is a dictionary and has all required keys
        if not isinstance(data, dict):
            print(f"Invalid data for key {key}: not a dictionary")
            continue
        required_keys = ['temp', 'uv', 'hum', 'rain']
        if not all(k in data for k in required_keys):
            print(f"Missing keys in data for key {key}: {data}")
            continue
        try:
            new_temp = float(data['temp'])
            new_uv = float(data['uv'])
            new_humidity = float(data['hum'])
            rain = data['rain']
            # Append data with current timestamp
            current_time = datetime.now()
            current_markers[key]['temperature_data'].append(new_temp)
            current_markers[key]['uv_data'].append(new_uv)
            current_markers[key]['humidity_data'].append(new_humidity)
            current_markers[key]['time_data'].append(current_time)

            # Limit to last 3600 points (5 seconds * 3600 = 5 hours)
            if len(current_markers[key]['temperature_data']) > 3600:
                current_markers[key]['temperature_data'].pop(0)
                current_markers[key]['uv_data'].pop(0)
                current_markers[key]['humidity_data'].pop(0)
                current_markers[key]['time_data'].pop(0)

            # Update displayed data if this is the current location
            if current_markers[key]['name'] == current_location:
                new_icon = get_weather_icon(new_uv, rain)
                new_text = f"Humidity: {new_humidity:.1f}%\n\nUV Index: {new_uv:.1f}\n\nRain: {'Yes' if rain == '1' else 'No Rain'}"
                label_board.configure(text=new_text)
                image_label.configure(image=new_icon)
                text_label.configure(text=f"{new_temp:.1f}°C")
                text_label2.configure(text="Sunny" if new_uv > 5 else "Cloudy")
                temp_line.set_data(current_markers[key]['time_data'], current_markers[key]['temperature_data'])
                uv_line.set_data(current_markers[key]['time_data'], current_markers[key]['uv_data'])
                humidity_line.set_data(current_markers[key]['time_data'], current_markers[key]['humidity_data'])
                for ax in [temp_ax, uv_ax, humidity_ax]:
                    ax.relim()
                    ax.autoscale_view()
                canvas.draw_idle()
        except ValueError as e:
            print(f"Error converting data to float for key {key}: {e}")
            continue

    # Schedule next update
    app.after(5000, update_data)

app = customtkinter.CTk()
app.title("ClimaNET")
app.geometry("1920x1080")

app.grid_columnconfigure(0, weight=3)
app.grid_columnconfigure(1, weight=1)
app.grid_columnconfigure(2, weight=1)
app.grid_columnconfigure(3, weight=1)
app.grid_rowconfigure(0, weight=4)
app.grid_rowconfigure(1, weight=5)

icon_size = (270, 270)
sunny_icon = customtkinter.CTkImage(light_image=Image.open("sunny.png"), size=icon_size)
cloudy_icon = customtkinter.CTkImage(light_image=Image.open("cloudy.png"), size=icon_size)
clear_night_icon = customtkinter.CTkImage(light_image=Image.open("clear_night.png"), size=icon_size)
mostly_cloudy_day_icon = customtkinter.CTkImage(light_image=Image.open("mostly_cloudy_day.png"), size=icon_size)
mostly_sunny_icon = customtkinter.CTkImage(light_image=Image.open("mostly_sunny.png"), size=icon_size)
partly_cloudy_icon = customtkinter.CTkImage(light_image=Image.open("partly_cloudy.png"), size=icon_size)
scattered_showers_day_icon = customtkinter.CTkImage(light_image=Image.open("scattered_showers_day.png"), size=icon_size)
scattered_showers_night_icon = customtkinter.CTkImage(light_image=Image.open("scattered_showers_night.png"), size=icon_size)
showers_rain_icon = customtkinter.CTkImage(light_image=Image.open("showers_rain.png"), size=icon_size)

frame1 = customtkinter.CTkFrame(app, corner_radius=10)
frame1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
frame1.pack_propagate(False)

frame2 = customtkinter.CTkFrame(app, corner_radius=10)
frame2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
frame2.grid_rowconfigure(0, weight=1)
frame2.grid_columnconfigure(0, weight=1)

frame3 = customtkinter.CTkFrame(app, corner_radius=10)
frame3.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
frame3.grid_rowconfigure(0, weight=1)
frame3.grid_columnconfigure(0, weight=1)

frame4 = customtkinter.CTkFrame(app, corner_radius=10)
frame4.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")
frame4.grid_rowconfigure(0, weight=1)
frame4.grid_columnconfigure(0, weight=1)

frame5 = customtkinter.CTkFrame(app, corner_radius=10)
frame5.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
frame5.grid_rowconfigure(0, weight=1)
frame5.grid_columnconfigure(0, weight=1)

image_label = customtkinter.CTkLabel(frame1, image=sunny_icon, text="")
image_label.place(relx=0.5, rely=0.47, anchor="e")

button = customtkinter.CTkButton(
    master=frame3,
    text="Open Full Map",
    fg_color="#294aa3",
    command=open_full_map,
    width=200,         # increase width
    height=50,         # increase height
    font=("Arial", 18)
)
button.place(relx=0.5, rely=0.3, anchor="center")

refresh_button = customtkinter.CTkButton(
    master=frame3,
    text="Refresh Markers",
    fg_color="#29a329",
    command=refresh_markers,
    width=200,         # increase width
    height=50,         # increase height
    font=("Arial", 18)
)
refresh_button.place(relx=0.5, rely=0.5, anchor="center")

reset_button = customtkinter.CTkButton(
    master=frame3,
    text="Reset Graph",
    fg_color="#29a329",
    command=reset_graph,
    width=200,         # increase width
    height=50,         # increase height
    font=("Arial", 18)
)
reset_button.place(relx=0.5, rely=0.7, anchor="center")

w_condition = "Sunny"
text_label = customtkinter.CTkLabel(frame1, text="22°C", font=("Helvetica", 70, "bold"), text_color="#29a329")
text_label.place(relx=0.72, rely=0.45, anchor="center")

text_label2 = customtkinter.CTkLabel(frame1, text=w_condition, font=("Helvetica", 23, "bold"))
text_label2.place(relx=0.35, rely=0.8, anchor="e")

location_label = customtkinter.CTkLabel(frame1, text=f"Location: {current_location}", font=("Helvetica", 30, "bold"), text_color="#FF0000")
location_label.place(relx=0.5, rely=0.1, anchor="center")

date_label = customtkinter.CTkLabel(
    master=frame2,
    text="Tuesday - 03/06/2025",
    font=("Helvetica", 28, "bold"),
    text_color="#886800"
)
date_label.place(relx=0.5, rely=0.18, anchor="center")

# Create the time label in frame2
time_label = customtkinter.CTkLabel(
    master=frame2,
    text="00:00",
    font=("Helvetica", 36, "bold"),
    text_color="#886800"
)
time_label.place(relx=0.5, rely=0.3, anchor="center")

update_clock()

text = f"Humidity: 60%\n\nUV Index: Sunny\n\nRain: No Rain"
label_board = customtkinter.CTkLabel(frame2, text=text, justify="left", font=("Helvetica", 18, "bold"))
label_board.place(relx=0.5, rely=0.55, anchor="center")

fig, (temp_ax, uv_ax, humidity_ax) = plt.subplots(1, 3, figsize=(23, 5), sharex=True)
fig.patch.set_facecolor('none')
fig.set_alpha(0)

for ax in [temp_ax, uv_ax, humidity_ax]:
    ax.set_facecolor('none')
    ax.grid(True, color="white", alpha=0.5)
    ax.tick_params(axis='x', colors='white', labelbottom=False)
    ax.tick_params(axis='y', colors='white')
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')

temp_line, = temp_ax.plot([], [], color="red")
temp_ax.set_title("Temperature", color="white")
temp_ax.set_ylabel("°C", rotation=0, color="white", y=0.45)
temp_ax.set_ylim(15, 40)

uv_line, = uv_ax.plot([], [], color="purple")
uv_ax.set_title("UV Index", color="white")
uv_ax.set_ylabel("UV", rotation=0, color="white", y=0.45)
uv_ax.set_ylim(0, 10)

humidity_line, = humidity_ax.plot([], [], color="blue")
humidity_ax.set_title("Humidity", color="white")
humidity_ax.set_ylabel("%", rotation=0, color="white", y=0.45)
humidity_ax.set_ylim(40, 100)

# Configure x-axis to show time
humidity_ax.tick_params(axis='x', colors='white', labelbottom=True)
humidity_ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
humidity_ax.xaxis.set_major_locator(HourLocator(interval=1))

uv_ax.tick_params(axis='x', colors='white', labelbottom=True)
uv_ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
uv_ax.xaxis.set_major_locator(HourLocator(interval=1))

temp_ax.tick_params(axis='x', colors='white', labelbottom=True)
temp_ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
temp_ax.xaxis.set_major_locator(HourLocator(interval=1))

for line, ax, label in [(temp_line, temp_ax, "Temp"), (uv_line, uv_ax, "UV"), (humidity_line, humidity_ax, "Humidity")]:
    cursor = mplcursors.cursor(line, hover=mplcursors.HoverMode.Transient)
    cursor.connect("add", lambda sel, l=label: sel.annotation.set_text(f"Time: {num2date(sel.target[0]).strftime('%H:%M')}\n{l}: {sel.target[1]:.1f}"))
    cursor.connect("remove", lambda sel: sel.annotation.set_visible(False))

canvas = FigureCanvasTkAgg(fig, master=frame5)
bg_color = frame5.cget("fg_color")[1] if customtkinter.get_appearance_mode() == "Dark" else frame5.cget("fg_color")[0]
canvas.get_tk_widget().configure(bg=bg_color)
canvas_widget = canvas.get_tk_widget()
canvas_widget.place(relx=0.5, rely=0.5, anchor="center")
label_board.lift()

map_widget = TkinterMapView(frame4)
map_widget.grid(row=0, column=0, sticky="nsew")
map_widget.set_position(39.0, 22.0)  # Initial center on Greece
map_widget.set_zoom(6)  # Zoom to show all of Greece

# Start periodic data updates
update_data()

app.mainloop()