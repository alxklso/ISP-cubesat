from lib.pycubed import cubesat

cubesat.radio1.node = 0xFA # our ID
cubesat.radio1.destination = 0xFF # target's ID

async def main_task():
    antenna_attached = False
    print("Started listening for messages")
    if antenna_attached:
        while True:
            cubesat.radio1.listen()        
            listen_timeout = 60
            heard_something = await cubesat.radio1.await_rx(timeout = listen_timeout)
            if heard_something:
                response = cubesat.radio1.receive(keep_listening = True, with_ack = True)
                if response is not None:
                    print(f"Response: {response}")
            else:
                print("No messages")
            cubesat.radio1.sleep()

schedule = cubesat.tasko.schedule
cubesat.scheduled_tasks["beacon"]=schedule(1/60, main_task, 1)
cubesat.tasko.run()