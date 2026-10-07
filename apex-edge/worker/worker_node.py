from fastapi import FastAPI
import psutil
import time
import threading
import uvicorn
import requests
app = FastAPI(title="Apex-Edge Worker")

MASTER_IP = ""
MASTER_PORT = 8000


worker_status = {
    "node": "sandeep-victus",
    "cpu": 0,
    "ram": 0,
    "temperature": 0,
    "workload": "LOW",
    "health": "HEALTHY"
}


def get_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return int(f.read().strip()) / 1000
    except Exception:
        return None


def determine_workload(cpu, ram, temperature):
    if cpu >= 85 or ram >= 85 or (temperature is not None and temperature >= 75):
        return "HIGH"

    if cpu >= 60 or ram >= 60 or (temperature is not None and temperature >= 65):
        return "MEDIUM"

    return "LOW"


def monitor_resources():
    while True:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        temperature = get_temperature()

        workload = determine_workload(
            cpu,
            ram,
            temperature
        )

        health = "HEALTHY"

        if cpu >= 90 or ram >= 90 or (
            temperature is not None and temperature >= 80
        ):
            health = "CRITICAL"

        elif cpu >= 75 or ram >= 75 or (
            temperature is not None and temperature >= 70
        ):
            health = "WARNING"

        worker_status["cpu"] = cpu
        worker_status["ram"] = ram
        worker_status["temperature"] = temperature
        worker_status["workload"] = workload
        worker_status["health"] = health

        print(
            f"[TELEMETRY] "
            f"CPU={cpu:.1f}% | "
            f"RAM={ram:.1f}% | "
            f"TEMP={temperature}°C | "
            f"WORKLOAD={workload} | "
            f"HEALTH={health}"
        )

        time.sleep(2)







def send_telemetry():

    while True:

        try:
            response = requests.post(
                f"http://{MASTER_IP}:{MASTER_PORT}/telemetry",
                json=worker_status,
                timeout=3
            )

            if response.ok:
                print("[MASTER] Telemetry sent successfully")
            else:
                print(
                    f"[MASTER] Telemetry rejected: "
                    f"{response.status_code}"
                )

        except requests.RequestException as e:
            print(f"[MASTER] Connection failed: {e}")

        time.sleep(2)










@app.get("/")
def root():
    return {
        "system": "Apex-Edge",
        "role": "worker",
        "status": "online"
    }


@app.get("/health")
def health():
    return worker_status


@app.get("/telemetry")
def telemetry():
    return worker_status


if __name__ == "__main__":

    monitor_thread = threading.Thread(
        target=monitor_resources,
        daemon=True
    )

    telemetry_thread = threading.Thread(
        target=send_telemetry,
        daemon=True
    )

    monitor_thread.start()
    telemetry_thread.start()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000
    )
