# 🩸 IINTS – Open-Source Insulin Pump for Raspberry Pi Pico  

<div align="center">
  <img src="assets/IINTS_banner.png" width="1200">
</div>

**IINTS** (Insuline Is Not The Solution) is an **open-source insulin pump project** designed for affordability and accessibility.  
Built with **MicroPython** on a **Raspberry Pi Pico**, it controls insulin delivery using stepper motors and a user-friendly interface.  

🔹 **Customizable** | 🔹 **Affordable** | 🔹 **Open-Source** | 🔹 **Made for Everyone**  

---

## 🌜 Project History  
IINTS was created in **2024** as a personal project to learn more about insulin pumps and their mechanics. As someone with 13 years of experience living with diabetes, I was curious about how these devices work and wanted to build one myself. While not intended as a commercial alternative, I am sharing this project as an open-source learning experience for anyone interested in electronics, programming, and medical technology.

--- 

<h3>🚀 <strong>Milestones:</strong></h3>
<ul>
  <li>📌 <strong>May 2024</strong> – First working prototype using Raspberry Pi Pico</li>
  <li>📌 <strong>July 2024</strong> – Added OLED display and user interface</li>
  <li>📌 <strong>December 2024</strong> – Introduced microstepping for improved precision</li>
  <li>📌 <strong>April 2025</strong> – Awarded "Most Technically Complex Project" at <strong>Coolest Projects Belgium</strong></li>
  <li>📌 <strong>May 2025</strong> – Named "Student in the Spotlight" for the third time, this year for IINTS!</li>
</ul>

---

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
````

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

---

## 💉 **Mathematical and Scientific Explanation of Insulin Dosing**

Insulin dosing is often calculated based on several key factors, including the individual's blood glucose level, the amount of carbohydrates they have consumed, and their insulin sensitivity. Below is an overview of how insulin dosages can be calculated:

---

### 1️⃣ **Insulin to Carbohydrate Ratio (ICR)**

The **Insulin to Carbohydrate Ratio (ICR)** determines how much insulin is needed to process a certain amount of carbohydrates. A common ratio might be 1 unit of insulin for every 10 grams of carbohydrates (1:10 ratio). This ratio varies per individual based on their insulin sensitivity and time of day.

#### **Formula for calculating insulin dosage based on carbohydrates:**

$$
\text{Insulin dosage (units)} = \frac{\text{Carbohydrate intake (grams)}}{\text{Insulin-Carbohydrate Ratio (grams per unit)}}
$$

**Example:**
If a person eats 30 grams of carbohydrates and their insulin-to-carbohydrate ratio is 1:10, the calculation would be:

$$
\text{Insulin dosage} = \frac{30}{10} = 3 \text{ units of insulin}
$$

---

### 2️⃣ **Insulin Sensitivity Factor (ISF)**

The **Insulin Sensitivity Factor (ISF)** measures how much the blood glucose level of a person will drop for each unit of insulin injected. A typical value might be that 1 unit of insulin lowers the blood glucose level by 50 mg/dL.

#### **Formula for calculating insulin dosage based on blood glucose:**

$$
\text{Insulin dosage (units)} = \frac{\text{Current blood glucose level} - \text{Target blood glucose}}{\text{Insulin Sensitivity Factor}}
$$

**Example:**
If the current blood glucose level is 200 mg/dL, the target is 120 mg/dL, and the ISF is 50 mg/dL per unit:

$$
\text{Insulin dosage} = \frac{200 - 120}{50} = \frac{80}{50} = 1.6 \text{ units of insulin}
$$

---

### 3️⃣ **Total Daily Dose (TDD)**

The **Total Daily Dose (TDD)** is an estimate of the total amount of insulin a person needs in a day. It can vary based on individual needs, but a common formula is:

#### **Formula for calculating TDD:**

$$
\text{TDD} = \text{Basal insulin} + \text{Bolus insulin (for meals and corrections)}
$$

A rough estimate of the TDD can be calculated based on the individual's weight:

$$
\text{TDD (units)} = \text{Weight (kg)} \times 0.5 \, \text{to} \, 1.0
$$

**Example:**
For a person weighing 70 kg, the estimated TDD might range between 35 and 70 units, depending on their specific needs.

---

### 4️⃣ **Bolus Insulin and Correction Dose**

Bolus insulin is given to address the blood glucose levels after meals or to correct elevated blood glucose levels. The dosage is calculated based on the insulin-to-carbohydrate ratio (for meals) and the insulin sensitivity factor (for corrections).

#### **Formula for bolus insulin for a meal:**

$$
\text{Bolus insulin (units)} = \frac{\text{Carbohydrates consumed}}{\text{Insulin-Carbohydrate Ratio}}
$$

#### **Formula for correction dose:**

$$
\text{Correction dose} = \frac{\text{Current blood glucose level} - \text{Target blood glucose}}{\text{Insulin Sensitivity Factor}}
$$

---

### 5️⃣ **Complications of Incorrect Calculations**

Incorrect insulin dosages can lead to **hypoglycemia** (low blood glucose) or **hyperglycemia** (high blood glucose), which can result in serious health risks. Regular blood glucose monitoring and accurate calculations are crucial for proper diabetes management. This is where a device like the **IINTS insulin pump** can help ensure precise, tailored dosages for better diabetes management.

---

### 6️⃣ **Advanced Algorithms for Insulin Delivery**

Advanced insulin pumps use algorithms to automatically adjust insulin delivery based on real-time needs. These systems take into account:

* **Carbohydrate intake prediction**
* **Blood glucose trends**
* **Physical activity**
* **Sleep cycles**

Such algorithms can provide **smarter insulin delivery**, ensuring more accurate and efficient insulin management than manual calculations.

---
