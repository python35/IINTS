# 🩸 IINTS – Open-Source Insulin Pump for Raspberry Pi Pico  

<div align="center">
  <img src="assets/IINTS_banner.png" width="100%" height="70%">
</div>

**IINTS** (Insuline Is Not The Solution) is an **open-source insulin pump project** designed for affordability and accessibility.  
Built with **MicroPython** on a **Raspberry Pi Pico**, it controls insulin delivery using stepper motors and a user-friendly interface.  

🔹 **Customizable** | 🔹 **Affordable** | 🔹 **Open-Source** | 🔹 **Made for Everyone**  

---

## 🌜 Project History  
IINTS was created in **2024** as a personal project to learn more about insulin pumps and their mechanics. As someone with 13 years of experience living with diabetes, I was curious about how these devices work and wanted to build one myself. While not intended as a commercial alternative, I am sharing this project as an open-source learning experience for anyone interested in electronics, programming, and medical technology.

--- 

🚀 **Milestones:**  
📌 **May 2024** – First working prototype using Raspberry Pi Pico  
📌 **July 2024** – Added OLED display and user interface  
📌 **December 2024** – Introduced microstepping for improved precision  
📌 **April 2025** – Showcasing at **Coolest Projects Belgium**  

💡 **Special Thanks**  

A huge thank you to the **coaches of CoderDojo Genk and Hasselt** for their incredible guidance and support throughout this project. Their mentorship has been invaluable in helping me bring this idea to life! 🙌  
---

## 📌 Features  
✅ **Stepper Motor Control** – Accurate insulin delivery using stepper motors  
✅ **User-Friendly Interface** – Buttons & Display for easy control  
✅ **Safety Mechanisms** – Basic fail-safes for reliable operation  
✅ **Customizable** – Modify dosage & settings as needed  
✅ **3D Printable** – Open-source STL files for hardware  
✅ **Open-Source** – Licensed under **MIT**, free for personal & medical research use  

---

## 🖼️ Project Images  

<table align="center">
  <tr>
    <td align="center"><img src="assets/depomp.jpg" width="300"></td>
  </tr>
  <tr>
    <td align="center">Prototype final version</td>
  </tr>
</table>

---

## 🛠️ Hardware Requirements  
### 🎧 Core Hardware  
- **Raspberry Pi Pico (RP2040)**
- **OLED/TFT Display** (for UI)
- **Stepper Motor + Driver** (e.g., A4988, ULN2003)
- **Push Buttons** (for user input)
- **Battery / Power Supply**  

### 💉 Insulin Pump Mechanism  
- **Syringe Pump Setup** (or peristaltic pump)
- **3D Printed Mounts** (STL files included!)  

---

## 🤝 3D Printing Files  

All necessary 3D printable parts can be found in the `/stl` folder.  

👅 **Download STL Files**: [STL Folder](https://github.com/python35/IINTS/tree/main/stl)  

### 🛠️ Recommended Print Settings  
- **Material:** PLA or PETG  
- **Layer height:** 0.2mm  
- **Infill:** 20%  
- **Supports:** Not required  
- **Bed adhesion:** Brim or skirt  

---

## 🎥 Timelapse of 3D Printing

### Watch the 3D printing process in action! 🎥  
![3D Print Timelapse 1](assets/filmpje1.gif)  
![3D Print Timelapse 2](assets/filmpje2.gif)  

---

## 🚀 Installation Guide  

### 1️⃣ Install **MicroPython**  
Ensure you're using the correct **MicroPython version**:  
🔹 **MicroPython v1.23.0 (2024-06-02) for Raspberry Pi Pico**  

👅 **Download Here:** [https://micropython.org/download/RPI_PICO](https://micropython.org/download/RPI_PICO)  

#### Check Your MicroPython Version:  
Connect to your Raspberry Pi Pico and run:  
```python
import os
os.uname()
```

---

### 2️⃣ Install **Thonny IDE**  
Thonny is recommended for coding and uploading MicroPython scripts.  

👅 Download: [https://thonny.org](https://thonny.org)  

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

## 📚 License  
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

### 👅 Download & Start Building!  
🔽 **[Clone the repository](https://github.com/YOUR_USERNAME/IINTS.git) and start experimenting!**

