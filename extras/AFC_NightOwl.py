class afcNightOwl:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')

        self.logo = 'Night Owl Ready'
        self.logo ='R  ,     ,\n'
        self.logo+='E  )\___/(\n'
        self.logo+='A {(@)v(@)}\n'
        self.logo+='D  {|~~~|}\n'
        self.logo+='Y  {/^^^\}\n'
        self.logo+='!   `m-m`\n'

        self.logo_error = 'Night Owl Not Ready\n'

def load_config(config):
    return afcNightOwl(config)