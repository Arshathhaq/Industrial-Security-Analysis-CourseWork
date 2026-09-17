from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext
from pymodbus.datastore import ModbusServerContext

import threading
import random
import time

store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0] * 100),
    co=ModbusSequentialDataBlock(0, [0] * 100),
    hr=ModbusSequentialDataBlock(0, [0] * 100),
    ir=ModbusSequentialDataBlock(0, [0] * 100)
)

context = ModbusServerContext(slaves=store, single=True)

context[0].setValues(1, 0, [1])   # Auto mode
context[0].setValues(1, 1, [0])   # Pump
context[0].setValues(1, 2, [0])   # Valve
context[0].setValues(1, 3, [0])   # EStop

tank_level =  context[0].getValues(3, 0, count=1)[0]

def update_data():

    global tank_level

    while True:

        automatic = context[0].getValues(1, 0, count=1)[0]
        pumpcmd = context[0].getValues(1, 1, count=1)[0]
        inletvalve = context[0].getValues(1, 2, count=1)[0]
        estop = context[0].getValues(1, 3, count=1)[0]

        if estop: inletvalve = 0; pumpcmd = 0;
        if automatic == 1 and estop == 0:

            if tank_level < 30:
                inletvalve = 1
                pumpcmd = 0

            elif tank_level > 80:
                inletvalve = 0
                pumpcmd = 1

            else:
                inletvalve = 0
                pumpcmd = 0

            context[0].setValues(1, 1, [pumpcmd])
            context[0].setValues(1, 2, [inletvalve])

        if inletvalve == 1:
            tank_level += random.uniform(1, 3)

        if pumpcmd == 1:
            tank_level -= random.uniform(1, 4)

        tank_level = max(0, min(100, tank_level))

        context[0].setValues(3, 0, [int(tank_level)])

        print(
            f"Tank={int(tank_level)}% "
            f"Auto={automatic} "
            f"Pump={pumpcmd} "
            f"Valve={inletvalve}"
        )

        time.sleep(1)


thread = threading.Thread(target=update_data)
thread.daemon = True
thread.start()

print("Modbus TCP Running on 5020")

StartTcpServer(
    context,
    address=("0.0.0.0", 5020)
)
