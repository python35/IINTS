# IINTS - Open-Source Insulin Pump Project

## 🚀 About IINTS
**IINTS** (*Intelligent Insulin Therapy System*) is an **open-source insulin pump project** designed to provide an **affordable, customizable, and accessible** solution for insulin delivery. Built using **MicroPython in Thonny**, it allows users to control insulin dosage through a **stepper motor-driven infusion system** with a **TFT display** and **button-based interface**.

This project is aimed at **DIY medical technology enthusiasts**, researchers, and anyone interested in developing open-source medical devices.

## 🛠 Features
- **Stepper motor-controlled insulin delivery** for precision dosing
- **TFT screen display** for user interaction
- **Button-based interface** to adjust insulin dosage
- **Customizable settings** to fit individual insulin therapy needs
- **Built with MicroPython** on a microcontroller for efficiency and flexibility
- **Open-source and community-driven** for continuous improvement

## 📖 How It Works
1. **Input daily insulin dosage** using the button controls.
2. **Enter carbohydrate intake** to calculate the required insulin units.
3. **Stepper motor dispenses insulin** based on the calculated dosage.
4. **Optional manual override** for reversing or adjusting dosage.
5. **User interface updates in real time** on the TFT display.

## 🏗️ Getting Started
### **Hardware Requirements**
- Raspberry Pi Pico (or similar MicroPython-compatible board)
- Stepper motor + motor driver (e.g., ULN2003)
- TFT display (ST7789 or equivalent)
- Buttons for user input
- Insulin reservoir & delivery system
- Power supply (USB or battery-powered)

### **Software Requirements**
- [Thonny IDE](https://thonny.org/) (Recommended for MicroPython development)
- MicroPython firmware installed on the board

### **Installation Steps**
1. Clone this repository:
   ```bash
   git clone https://github.com/python35/IINTS.git
   ```
2. Open the project in **Thonny**.
3. Flash the MicroPython firmware onto your microcontroller.
4. Upload the Python scripts to the board.
5. Connect the hardware components as per the wiring diagram.
6. Run the main script and start using IINTS!

## 📜 License
This project is licensed under the **MIT License**, which means:
✅ You can use, modify, and distribute it freely.
✅ It comes with no warranty—use at your own risk.
✅ Contributions are welcome to improve and expand the project!

## 🤝 Contributing
We encourage contributions! Whether it's bug fixes, feature improvements, or documentation updates, feel free to **open a pull request** or **create an issue**.

## 📢 Disclaimer
**⚠️ This project is experimental and NOT intended for medical use without proper testing and validation. Always consult a medical professional before using DIY medical devices.**

---
**Join the Open-Source Medical Revolution! 💙**

