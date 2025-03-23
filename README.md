# 🩸 IINTS – Open-Source Insulin Pump for Raspberry Pi Pico  

<div align="center">
  <img src="assets/IINTS logo.png" width="300">
</div>  

**IINTS** (Intelligent Insulin Therapy System) is an **open-source insulin pump project** designed for affordability and accessibility.  
Built with **MicroPython** on a **Raspberry Pi Pico**, it controls insulin delivery using stepper motors and a user-friendly interface.  

🔹 **Customizable** | 🔹 **Affordable** | 🔹 **Open-Source** | 🔹 **Made for Everyone**  

---

## 📜 Project History  
IINTS was created in **2024** as a response to the high cost of commercial insulin pumps. The goal was to build a **low-cost, open-source alternative** using **readily available components** like the Raspberry Pi Pico.  

The project started as a **simple stepper motor controller** for a syringe pump. Over time, it evolved into a **fully programmable insulin delivery system** with an OLED display, buttons, and safety features.  

🚀 **Milestones:**  
📌 **June 2024** – First working prototype using Raspberry Pi Pico  
📌 **July 2024** – Implemented stepper motor control for precise insulin delivery  
📌 **August 2024** – Added OLED display and user interface  
📌 **September 2024** – Released as an open-source project under **MIT License**  

---

## 📌 Features  
✅ **Stepper Motor Control** – Accurate insulin delivery using stepper motors  
✅ **User-Friendly Interface** – Buttons & Display for easy control  
✅ **Safety Mechanisms** – Basic fail-safes for reliable operation  
✅ **Customizable** – Modify dosage & settings as needed  
✅ **Open-Source** – Licensed under **MIT**, free for personal & medical research use  

---

## 🖼️ Project Images  

<table>
  <tr>
    <td><img src="assets/prototype1.jpg" width="300"></td>
    <td><img src="assets/prototype2.jpg" width="300"></td>
  </tr>
  <tr>
    <td align="center">Prototype v1</td>
    <td align="center">OLED Display UI</td>
  </tr>
</table>

---

## 🛠️ Hardware Requirements  
### 🎛️ Core Hardware  
- **Raspberry Pi Pico (RP2040)**
- **OLED/TFT Display** (for UI)
- **Stepper Motor + Driver** (e.g., A4988, ULN2003)
- **Push Buttons** (for user input)
- **Battery / Power Supply**  

### 💉 Insulin Pump Mechanism  
- **Syringe Pump Setup** (or peristaltic pump)
- **3D Printed Mounts** (optional, for secure placement)  

---

## 🚀 Installation Guide  

### 1️⃣ Install **MicroPython**  
Ensure you're using the correct **MicroPython version**:  
🔹 **MicroPython v1.23.0 (2024-06-02) for Raspberry Pi Pico**  

📥 **Download Here:** [https://micropython.org/download/RPI_PICO](https://micropython.org/download/RPI_PICO)  

#### Check Your MicroPython Version:  
Connect to your Raspberry Pi Pico and run:  
```python
import os
os.uname()
```

---

### 2️⃣ Install **Thonny IDE**  
Thonny is recommended for coding and uploading MicroPython scripts.  

📥 Download: [https://thonny.org](https://thonny.org)  

Steps:  
1. Open Thonny  
2. Select **Raspberry Pi Pico** as the interpreter  
3. Install **MicroPython firmware** if not already installed  

---

### 3️⃣ Clone This Repository  
Run this command to download the project:  
```sh
git clone https://github.com/python35/IINTS.git
```
Or manually **Download ZIP** from GitHub.  

---

### 4️⃣ Upload to Raspberry Pi Pico  
1. Connect **Raspberry Pi Pico** via USB  
2. Open **Thonny**  
3. Copy `main.py` and other files to the Pico  
4. Click **Run**  

---

## ⚙️ Configuration  
Edit **config.py** to set parameters:  
```python
INSULIN_RATE = 1.0  # Units per second
STEP_MOTOR_SPEED = 200  # Steps per second
DISPLAY_BRIGHTNESS = 0.8  # 80% brightness
```
Adjust based on your needs.  

---

## 📜 License  
This project is **MIT Licensed**, meaning you can freely use, modify, and distribute it.  
However, **this is NOT a certified medical device** – use it responsibly.  

---

## 🤝 Contributing  
Want to improve the project? Fork the repository and submit a **Pull Request**.  

---

## 📢 Disclaimer  
🚨 **Warning:** This project is for **educational and research purposes only**.  
It is **not an FDA-approved medical device**. Always consult a medical professional before using insulin pumps.  

---

### 📥 Download & Start Building!  
⬇️ **[Clone the repository](https://github.com/python35/IINTS.git) and start experimenting!**  
