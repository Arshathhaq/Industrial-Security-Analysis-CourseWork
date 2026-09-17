#!/usr/bin/env python3

import json
import os
import time
from datetime import datetime

from pymodbus.client.sync import ModbusTcpClient

PLC_IP = "10.21.4.40"
PLC_PORT = 5020

LOG_DIR = "/var/log/scada"
LOG_FILE = f"{LOG_DIR}/events.log"

HIGH_LIMIT = 80
LOW_LIMIT = 25

LEVEL_REG = 0
AUTO_COIL = 0
PUMP_COIL = 1
VALVE_COIL = 2
ESTOP_COIL = 3

previous_level = None

states = {
    "high_alarm": False,
    "low_alarm": False,
    "estop": False
}


os.makedirs(LOG_DIR, exist_ok=True)


def log_event(event, data=None):
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event
    }

    if data:
        payload.update(data)

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(payload) + "\n")

    print(payload, flush=True)


def connect():
    while True:
        client = ModbusTcpClient(PLC_IP, port=PLC_PORT)

        if client.connect():
            print("----------------PLC Connected----------------", flush=True)
            return client

        print("Waiting for PLC...", flush=True)
        time.sleep(5)


client = connect()

while True:

    try:

        rr = client.read_holding_registers(LEVEL_REG, 1, unit=1)
        if rr.isError():
            raise Exception(f"Register read failed: {rr}")

        level = rr.registers[0]

        rr = client.read_coils(PUMP_COIL, 1, unit=1)
        if rr.isError():
            raise Exception(f"Pump coil read failed: {rr}")

        pump = rr.bits[0]

        rr = client.read_coils(ESTOP_COIL, 1, unit=1)
        if rr.isError():
            raise Exception(f"E-Stop coil read failed: {rr}")

        estop = rr.bits[0]

        if level >= HIGH_LIMIT:
            if not states["high_alarm"]:
                log_event("high_level_alarm", {"level": level})
                states["high_alarm"] = True
        else:
            states["high_alarm"] = False

        if level <= LOW_LIMIT:
            if not states["low_alarm"]:
                log_event("low_level_alarm", {"level": level})
                states["low_alarm"] = True
        else:
            states["low_alarm"] = False

        if estop:
            if not states["estop"]:
                log_event("emergency_stop_activated")
                states["estop"] = True
        else:
            states["estop"] = False

        if previous_level is not None:
            delta = abs(level - previous_level)

            if delta > 20:
                log_event(
                    "process_anomaly",
                    {
                        "previous": previous_level,
                        "current": level,
                        "delta": delta
                    }
                )

        if level < 10 and pump:
            log_event(
                "dry_run_risk",
                {
                    "level": level
                }
            )

        previous_level = level

    except Exception as e:

        log_event(
            "modbus_error",
            {
                "error": str(e)
            }
        )

        try:
            client.close()
        except Exception:
            pass

        time.sleep(5)
        client = connect()

    time.sleep(2)
