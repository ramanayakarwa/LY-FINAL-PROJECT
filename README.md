\# 🌱 ARES — Agentic Secure Smart Agriculture Scientific Robot



\*\*An AI-powered, six-wheel agricultural rover for intelligent crop monitoring, disease detection, yield prediction, and secure remote operations.\*\*



\*\*Project Type:\*\* Final-Year Engineering Project  

\*\*Project Name:\*\* ARES  

\*\*Repository:\*\* \[LY-FINAL-PROJECT](https://github.com/ramanayakarwa/LY-FINAL-PROJECT)



\---



\## 📌 Project Overview



ARES (Agentic Secure Smart Agriculture Scientific Robot) is a smart agriculture robotics project that combines \*\*Artificial Intelligence, Internet of Things (IoT), robotics, and web technologies\*\* to support precision agriculture.



The project is designed around a six-wheel agricultural rover that can collect field information, assist with crop health monitoring, analyze agricultural data, and provide information through a web-based dashboard.



ARES integrates AI-powered agricultural analysis with a FastAPI backend, React frontend, and ESP32-based embedded firmware.



> \*\*Development Status:\*\* The software components and firmware have been developed. Physical hardware integration, commissioning, and field validation are pending.



\## 🎯 Project Objectives



\- Develop an intelligent six-wheel agricultural rover.

\- Detect plant diseases using deep learning.

\- Recommend suitable crops based on agricultural parameters.

\- Predict crop yield using machine learning.

\- Provide a centralized web dashboard for monitoring and control.

\- Integrate ESP32-based communication and camera functionality.

\- Support secure, safety-aware rover operations.

\- Build a modular architecture for future agricultural automation.



\## 🚀 Key Features



\### 🌿 1. Crop Recommendation



A machine learning module designed to recommend suitable crops based on agricultural input parameters.



\### 🍃 2. Plant Disease Detection



A deep learning module designed to classify plant diseases using images of crop leaves.



\### 📈 3. Crop Yield Prediction



A machine learning module for estimating agricultural yield from relevant input parameters.



\### 🤖 4. Rover Control



A dashboard interface for rover operation, supported by backend control and safety-related services.



Physical rover movement must remain disabled until hardware commissioning and safety validation are completed.



\### 📷 5. Camera Integration



ESP32-CAM firmware and backend camera services intended to support visual crop inspection.



\### 📡 6. IoT Communication



The architecture includes MQTT and CoAP communication services for ESP32 integration.



\### 🔐 7. Security and Safety



Backend modules include authentication, security, action-gating, and safety-related services.



These software controls are not a substitute for physical emergency-stop mechanisms or hardware testing.



\### 📊 8. Monitoring Dashboard



A React-based frontend providing interfaces for:



\- System dashboard

\- Rover control

\- Crop recommendation

\- Disease detection

\- Yield prediction

\- Plant inspection

\- System logs



\## 🏗️ System Architecture



```text

&#x20;                 ┌─────────────────────┐

&#x20;                 │   React Dashboard   │

&#x20;                 │   (Frontend UI)     │

&#x20;                 └──────────┬──────────┘

&#x20;                            │

&#x20;                        HTTP / API

&#x20;                            │

&#x20;                 ┌──────────▼──────────┐

&#x20;                 │   FastAPI Backend   │

&#x20;                 │                     │

&#x20;                 │  Authentication     │

&#x20;                 │  AI Services        │

&#x20;                 │  Rover Control      │

&#x20;                 │  Safety Services    │

&#x20;                 │  System Monitoring  │

&#x20;                 └──────────┬──────────┘

&#x20;                            │

&#x20;                ┌───────────┴───────────┐

&#x20;                │                       │

&#x20;       ┌────────▼────────┐    ┌────────▼────────┐

&#x20;       │    AI Models    │    │ IoT Integration │

&#x20;       │                 │    │                 │

&#x20;       │ Crop Selection  │    │ MQTT / CoAP     │

&#x20;       │ Disease Model   │    │ ESP32 Firmware  │

&#x20;       │ Yield Model     │    │ ESP32-CAM       │

&#x20;       └─────────────────┘    └────────┬────────┘

&#x20;                                      │

&#x20;                             ┌────────▼────────┐

&#x20;                             │  Six-Wheel Rover│

&#x20;                             │                 │

&#x20;                             │ Motors / Sensors│

&#x20;                             │ Camera / Control│

&#x20;                             └─────────────────┘

```



\*The rover hardware layer represents the intended integrated system and is not yet field-validated.\*



\## 🛠️ Technology Stack



| Component | Technologies |

|---|---|

| Frontend | React, TypeScript, Vite |

| Backend | Python, FastAPI |

| Machine Learning | Scikit-learn, XGBoost |

| Deep Learning | TensorFlow / Keras |

| Embedded System | ESP32, ESP32-CAM |

| Communication | HTTP APIs, MQTT, CoAP |

| Development Tools | Git, GitHub, Arduino IDE |



\## 📁 Project Structure



```text

LY-FINAL-PROJECT/

│

├── backend/

│   ├── app/

│   │   ├── main.py

│   │   ├── routes/

│   │   └── services/

│   │

│   ├── models/

│   │   ├── class\_names.json

│   │   ├── crop\_recommendation\_model.pkl

│   │   ├── disease\_model.keras

│   │   ├── yield\_xgb\_meta.json

│   │   └── yield\_xgb\_tuned.json

│   │

│   ├── training/

│   ├── requirements.txt

│   └── .env.example

│

├── frontend/

│   ├── public/

│   ├── src/

│   │   ├── components/

│   │   ├── pages/

│   │   └── services/

│   ├── package.json

│   └── vite.config.ts

│

├── esp32/

│   ├── ARES\_ESP32\_MQTT\_CoAP.ino

│   └── ARES\_ESP32\_CAM/

│       └── ARES\_ESP32\_CAM.ino

│

├── .gitignore

└── README.md

```



\## ⚙️ Installation and Setup



\### Prerequisites



Install the following software:



\- Python

\- Node.js and npm

\- Git

\- Arduino IDE (for ESP32 firmware development)



\### 1. Clone the Repository



```bash

git clone https://github.com/ramanayakarwa/LY-FINAL-PROJECT.git

cd LY-FINAL-PROJECT

```



\### 2. Backend Setup



Navigate to the backend directory:



```bash

cd backend

```



Create a Python virtual environment:



```bash

python -m venv venv

```



Activate it on Windows PowerShell:



```powershell

.\\venv\\Scripts\\Activate.ps1

```



Install dependencies:



```bash

pip install -r requirements.txt

```



Create your local environment configuration using the provided template:



```powershell

Copy-Item .env.example .env

```



Review the environment variables and provide the values required for your local configuration. Never commit actual credentials.



Start the backend:



```bash

uvicorn app.main:app --reload

```



Backend development URL:



```text

http://127.0.0.1:8000

```



FastAPI API documentation:



```text

http://127.0.0.1:8000/docs

```



\### 3. Frontend Setup



Open another terminal and navigate to the frontend directory:



```bash

cd frontend

```



Install dependencies:



```bash

npm ci

```



Start the development server:



```bash

npm run dev

```



Open the local URL displayed by Vite in your terminal.



Configure the frontend's backend connection according to the project environment and API settings.



\### 4. ESP32 Firmware



The project includes two Arduino sketches:



\*\*Main ESP32 firmware\*\*



```text

esp32/ARES\_ESP32\_MQTT\_CoAP.ino

```



\*\*ESP32-CAM firmware\*\*



```text

esp32/ARES\_ESP32\_CAM/ARES\_ESP32\_CAM.ino

```



Open the corresponding sketch in Arduino IDE, configure the correct ESP32 board and required libraries, and compile it.



Do not operate motors or connect high-power actuators until wiring, motor drivers, power protection, emergency-stop functionality, and communication fail-safes have been validated.



\## 🧠 AI Models



| Model | Purpose | File |

|---|---|---|

| Crop Recommendation | Suggest suitable crops | `crop\_recommendation\_model.pkl` |

| Disease Detection | Classify plant leaf diseases | `disease\_model.keras` |

| Yield Prediction | Estimate crop yield | `yield\_xgb\_tuned.json` |



Supporting model metadata and class labels are stored in the `backend/models/` directory.



Training and prediction scripts are available under `backend/training/`.



Model accuracy, generalization, and real-world reliability should be established through documented evaluation and field-relevant testing.



\## 🧪 Current Development Status



| Module | Status |

|---|---|

| Backend source code | Developed |

| Frontend dashboard | Developed |

| AI model files | Available |

| AI training scripts | Available |

| ESP32 main firmware | Compiled |

| ESP32-CAM firmware | Compiled |

| Physical hardware integration | Pending |

| Sensor commissioning | Pending |

| End-to-end hardware testing | Pending |

| Agricultural field testing | Pending |



\## 🔒 Safety and Security Considerations



ARES is intended to operate with safety-aware control mechanisms.



Before physical deployment:



1\. Verify motor wiring, driver ratings, and power distribution.

2\. Implement and test a physical emergency stop.

3\. Validate authentication and authorization.

4\. Test communication-loss behavior.

5\. Verify sensor readings against known references.

6\. Validate rover control commands under supervised conditions.

7\. Test AI predictions using appropriate evaluation datasets.



\*\*Important:\*\* AI predictions are decision-support outputs and should not be treated as guaranteed agricultural recommendations.



\## 🔮 Future Scope



\- Full six-wheel rover hardware integration

\- Real-time environmental sensor monitoring

\- Field-based plant disease inspection

\- Autonomous navigation and obstacle avoidance

\- GPS-based agricultural mapping

\- Improved agricultural AI model evaluation

\- Remote monitoring and control

\- Real-world field trials and performance benchmarking



\## 🎓 Academic Project



ARES is developed as a final-year engineering project to explore the practical integration of artificial intelligence, robotics, IoT communication, and software engineering in precision agriculture.



\## 📜 License



No open-source license is specified in this repository. All rights remain with the respective copyright holders unless a license is added.



\---



\*\*ARES — Advancing Smart Agriculture Through AI, Robotics, and IoT.\*\* 🌾

