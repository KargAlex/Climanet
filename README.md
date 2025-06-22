# 🌤️ Climanet – Distributed Weather Monitoring with Arduino & Raspberry Pi

**Climanet** is a distributed environmental monitoring system inspired by platforms like **Meteo**. It collects real-time weather data from multiple **Arduino-based sensor stations**, each connected to a **Raspberry Pi**, and sends the data to a central **Flask server**. All data is stored in a structured database and displayed through a clean, interactive GUI.

## 🔧 Key Features

- 🌡️ **Real-time weather data** (temperature, humidity, etc.) from each station  
- 📡 **Sensor nodes**: Arduino collects data, Raspberry Pi handles network communication  
- 🧠 **Central Flask server** receives, stores, and manages the data  
- 💾 **Persistent storage** using [SQLite/MySQL/etc.] for historical access  
- 🖥️ **Graphical interface** to view live and past data per station  
- 📈 **Expandable architecture** – supports multiple stations across locations  

> **Climanet** brings the idea of localized weather monitoring to life with accessible hardware and a full-stack pipeline for data logging and visualization.
