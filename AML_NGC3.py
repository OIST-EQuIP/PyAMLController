import pyvisa as visa
import time


class NGC3:
    # TODO set up connection and put in default setting values
    def __init__(self, rm, address, remote=True, filament=1, delay=True):
        self._remote = remote
        self._gauge_on = False
        self._current = 0
        self._filament = filament

        self.port = rm.open_resource(address)
        self.delay = delay # This pauses after every command to to allow the ion gauge to not miss commands
        self.remote = True # If false, can only send poll and status commands
        self._last_command = time.time()

    def __del__(self):
        self.port.close()

    @property
    def remote(self):
        return self._remote

    @remote.setter
    def remote(self, value):
        self._remote = value
        if value:
            self.write('*C0')
        else:
            self.write('*R0')

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = value
        if value == 0.5:
            self._gauge_on = True
            self.write('*i00')
        elif value == 5:
            self._gauge_on = True
            self.write('*i01')
        elif value == 0:
            self._gauge_on = False
            self._current = 0
            self.write('*o0')
        else:
            print("Invalid current value. Choose 0, 0.5, 5 mA.")

    @property
    def filament(self):
        return self._filament

    @filament.setter
    def filament(self, value):
        if value in {1, 2}:
            self._filament = value
            self.write('*j0{}'.format(value))
        else:
            print("Invalid filament number. Must be 1 or 2.")

    def poll(self):
        self.write('*P0')
        return self.read()

    def reset_error(self):
        self.write('*E0')

    def status(self):
        self.write('*S0')
        strings = [self.read().decode("utf-8") for _ in range(5)]
        strings[0] = strings[0][4:]
        strings = [string.rstrip('\r\n') for string in strings]
        values = []
        units = []
        for string in strings:
            if string == strings[-1]:
                values.append(int(string[:-1]))
                units.append(string[-1])
            else:
                if string[5:12]=="       ":
                    values.append('NA')
                    units.append('NA')
                    continue
                values.append(float(string[5:8])*10**float(string[9:12]))
                units.append(string[-2])
                if units[-1] == 'T':
                    units[-1] = 'Torr'
                if units[-1] == 'P':
                    units[-1] = 'Pascal'
                if units[-1] == 'M':
                    units[-1] = 'mBar'
        ion_gauge = ('Ion gauge', values[0], units[0])
        pirani_1 = ('Pirani 1', values[1], units[1])
        pirani_2 = ('Pirani 2', values[2], units[2])
        active_gauge = ('Active gauge', values[3], units[3])
        temp = ('Temperature', values[4], units[4])

        return [ion_gauge, pirani_1, pirani_2, active_gauge, temp]

    def gauge_off(self):
        self.current = 0

    def override_relay(self, relay):
        self.write('*O0{}'.format(relay))

    def inhibit_relay(self, relay):
        self.write('*I0{}'.format(relay))

    def bake(self, baking):
        if baking == True:
            self.write('*b01')
        if baking == False:
            self.write('*b00')

    ################
    # convert to byte and send through pyvisa commands
    ################
    def write(self, string):
        while time.time()-self._last_command < 0.1:
            time.sleep(0.01)
        self.port.write_raw(bytes(string, 'ascii'))
        self._last_command = time.time()

    def read(self):
        return self.port.read_raw()

if __name__ == '__main__':
    t0 = time.time()
    rm = visa.ResourceManager('@py')
    addr = rm.list_resources()[0]

    ig = NGC3(rm, addr)
    ig.filament = 1
    ig.status()
    print(ig.poll())

