import time

"""
Satellite command & data handling functions.

- no-op: Simple acknowledgement.
- hreset: Hard reset the satellite.
- shutdown: Shut down satellite forever.
- query: Querying satellite. 
- exec_cmd: Execute specific command.

"""
commands = {
    b'\x8eb': 'no-op',
    b'\xd4\x9f': 'hreset',
    b'\x12\x06': 'shutdown',
    b'8\x93': 'query',
    b'\x96\xa2': 'exec_cmd',
}

########### Commands without arguments ###########
def noop(self):
    self.debug('no-op')
    pass

def hreset(self):
    self.debug('Resetting')
    try:
        self.cubesat.radio_send(b'resetting')
        self.cubesat.micro.on_next_reset(self.cubesat.micro.RunMode.NORMAL)
        self.cubesat.micro.reset()
    except:
        pass

########### Commands with arguments ###########

def shutdown(self, args):
    # make shutdown require yet another pass-code
    if args == b'\x0b\xfdI\xec':
        self.debug('Valid shutdown command received')
        # set shutdown NVM bit flag
        self.cubesat.f_shtdwn = True
        # stop all tasks
        for t in self.cubesat.scheduled_tasks:
            self.cubesat.scheduled_tasks[t].stop()
        self.cubesat.powermode('minimum')

        while True:
            time.sleep(100000)

def query(self,args):
    self.debug(f'query: {args}')
    self.cubesat.radio_send(str(eval(args)))

def exec_cmd(self,args):
    self.debug(f'exec: {args}')
    exec(args)