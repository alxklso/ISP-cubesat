import os
import time
import cdh
import microcontroller
from Tasks.template_task import Task

class task(Task):
    priority = 3
    testing_frequency = 1/10 # once every 5 mins, for listening for cmds
    frequency = 1/(60*40) # once every 40 mins, for listening for cmds
    name = "beacon"
    color = "teal"

    schedule_later = True

    # 4-byte password for commands
    super_secret_code = b"p\xba\xb8A" # TODO: CHANGE CODE

    cmd_dispatch = {
        "no-op":        cdh.noop,
        "hreset":       cdh.hreset,
        "shutdown":     cdh.shutdown,
        "query":        cdh.query,
        "exec_cmd":     cdh.exec_cmd,
    }

    def __init__(self,satellite):
        super().__init__(satellite)
        # set our radiohead node ID so we can get ACKs
        self.cubesat.radio1.node = 0xFA # our ID
        self.cubesat.radio1.destination = 0xFF # target's ID

    async def main_task(self):
        """
        TODO: If you've attached an antenna,
        set the cubesat.antenna_attached variable to True in pycubed.py
        to actually send the beacon packet
        """
        if self.cubesat.antenna_attached:
            self.debug("Sending beacon")
            self.cubesat.radio_send(
                f"vlt: {self.cubesat.battery_voltage} temp: {microcontroller.cpu.temperature}",
                destination = 0xFF)
            
            self.transmit_cw_data()

            self.debug("Listening for response (non-blocking)")
            self.cubesat.radio1.listen()
            listen_timeout = 2400
            if self.cubesat.benchtop_testing:
                listen_timeout = 60
            heard_something = await self.cubesat.radio1.await_rx(timeout = listen_timeout)

            if heard_something:
                # retrieve response but don't ACK back unless an antenna is attached
                response = self.cubesat.radio1.receive(keep_listening = True, with_ack = self.cubesat.antenna_attached)
                if response is not None:
                    self.debug("Packet received")
                    self.debug(f"msg: {response}, RSSI: {self.cubesat.radio1.last_rssi-137}", 2)
                    self.cubesat.c_gs_resp += 1

                    """
                    ########### ADVANCED ###########
                    Over-the-air commands
                    See beep-sat guide for more details
                    """
                    if len(response) >= 6:
                        if response[:4] == self.super_secret_code:
                            cmd=bytes(response[4:6]) # [pass-code(4 bytes)] [cmd 2 bytes] [args]
                            cmd_args=None
                            if len(response) > 6:
                                self.debug("command with args", 2)
                                try:
                                    cmd_args = response[6:] # arguments are everything after
                                    self.debug(f"cmd args: {cmd_args}", 2)
                                except Exception as e:
                                    self.debug(f"arg decoding error: {e}", 2)
                            if cmd in cdh.commands:
                                try:
                                    if cmd_args is None:
                                        self.debug(f"running {cdh.commands[cmd]} (no args)")
                                        self.cmd_dispatch[cdh.commands[cmd]](self)
                                    else:
                                        self.debug(f"running {cdh.commands[cmd]} (with args: {cmd_args})")
                                        self.cmd_dispatch[cdh.commands[cmd]](self, cmd_args)
                                except Exception as e:
                                    self.debug(f"something went wrong: {e}")
                                    self.cubesat.radio_send(str(e).encode())
                            else:
                                self.debug("invalid command!")
                                self.cubesat.radio_send(b"invalid cmd" + response[4:])
            else:
                self.debug("no messages")
                self.cubesat.radio1.sleep()
                self.debug("finished")
        else:
            # Fake beacon since we don't know if an antenna is attached
            print()
            self.debug("[WARNING]")
            self.debug("NOT sending beacon (unknown antenna state)", 2)
            self.debug("If you've attached an antenna, edit '/pycubed.py' to actually beacon", 2)
            print()
    
    def transmit_cw_data(self):
        if self.cubesat.hardware["SDcard"]:
            files = []
            try:
                files = [f"/sd/cw/{f}" for f in os.listdir("/sd/cw")]
            except:
                pass
            files.sort()

            start_time = time.monotonic()
            end_time = start_time + (60*10) # run for 10 mins at max

            self.debug(f"Send CW data file")
            for file in files:
                with open(file, "rb") as f:
                    chunk = f.read(32) # Each reading is 32 bytes when encoded
                    while chunk:
                        # We could send bigger chunks, radio packet can take 252 bytes
                        self.cubesat.radio_send(chunk)
                        chunk = f.read(32)
                # Move to read directory when we have sent it
                try:
                    os.rename(file, file.replace("cw", "cw_read"))
                except OSError:
                    try:
                        os.mkdir("/sd/cw_read")
                    except:
                        break
                # If we time out let's stop reading
                if time.monotonic() > end_time:
                    break