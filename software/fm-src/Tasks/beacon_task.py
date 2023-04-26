"""
IARU assigned frequency = 437.40 MHz --> TODO: Set in pycubed.py
"""
import cdh
from Tasks.template_task import Task

class task(Task):
    priority = 1
    frequency = 1/300 # once every 5 mins, for listening for cmds TODO: 
    name = "beacon"
    color = "teal"

    schedule_later = True

    # 4-byte password for commands
    super_secret_code = b"p\xba\xb8A"

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
        self.cubesat.radio1.destination = 0xAB # target's ID

    async def main_task(self):
        """
        TODO: If you've attached an antenna,
        set the cubesat.antenna_attached variable to True in main.py
        to actually send the beacon packet
        """
        if self.cubesat.antenna_attached:
            self.debug("Sending beacon")
            self.cubesat.radio1.send("KE8VDKHello World!\0", destination = 0xFF, keep_listening = True)

            self.debug("Listening 10s for response (non-blocking)")
            heard_something = await self.cubesat.radio1.await_rx(timeout = 10)

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
                        if not self.cubesat.antenna_attached:
                            self.debug("Antenna not attached. Skipping over-the-air command handling")
                        else:
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
                                        self.cubesat.radio1.send(str(e).encode())
                                else:
                                    self.debug("invalid command!")
                                    self.cubesat.radio1.send(b"invalid cmd" + response[4:])
            else:
                self.debug("no messages")
                self.cubesat.radio1.sleep()
                self.debug("finished")
        else:
            # Fake beacon since we don't know if an antenna is attached
            print()
            self.debug("[WARNING]")
            self.debug("NOT sending beacon (unknown antenna state)", 2)
            self.debug("If you've attached an antenna, edit '/Tasks/beacon_task.py' to actually beacon", 2)
            print()