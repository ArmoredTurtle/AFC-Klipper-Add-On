
class AFCPrompt:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        self.AFC = self.printer.lookup_object('AFC')

    # Prompt begin action
    def p_begin(self, prompt_name):
        self.AFC.gcode.respond_raw("// action:prompt_begin {}".format(prompt_name))

    # Prompt text action
    def p_text(self, text):
        self.AFC.gcode.respond_raw("// action:prompt_text {}".format(text))

    # Prompt button action (with style options)
    def p_button(self, label, command, style=None):
        if style:
            self.AFC.gcode.respond_raw("// action:prompt_button {}|{}|{}".format(label, command, style))
        else:
            self.AFC.gcode.respond_raw("// action:prompt_button {}|{}".format(label, command))

    # Prompt footer button action (4 max allowed)
    def p_footer_button(self, label, command, style=None):
        if style:
            self.AFC.gcode.respond_raw("// action:prompt_footer_button {}|{}|{}".format(label, command, style))
        else:
            self.AFC.gcode.respond_raw("// action:prompt_footer_button {}|{}".format(label, command))

    def p_cancel_button(self):
        self.p_footer_button('Cancel', "RESPOND TYPE=command MSG=action:prompt_end", 'warning')

    # Show prompt action
    def p_show(self):
        self.AFC.gcode.respond_raw("// action:prompt_show")

    # Close prompt action
    def p_end(self):
        self.AFC.gcode.respond_raw("// action:prompt_end")

    # Button group start
    def p_button_group_start(self):
        self.AFC.gcode.respond_raw("// action:prompt_button_group_start")

    # Button group end
    def p_button_group_end(self):
        self.AFC.gcode.respond_raw("// action:prompt_button_group_end")

    # Method to create a custom prompt
    def create_custom_p(self, prompt_name, text=None, buttons=None, cancel=False, groups=None, footer_buttons=None):
        self.p_begin(prompt_name)
        if text != None:
            self.p_text(text)

        # Add group bottons
        if groups != None:
            for group in groups:
                self.p_button_group_start()
                for button in group:
                    label, command, style = button
                    self.p_button(label, command, style)
                self.p_button_group_end()

        # Add main buttons
        if buttons != None:
            for button in buttons:
                label, command, style = button
                self.p_button(label, command, style)

        # Add footer buttons (if any)
        if footer_buttons != None:
            for footer_button in footer_buttons:
                label, command, style = footer_button
                self.p_footer_button(label, command, style)
        
        if cancel:
            self.p_cancel_button()

        self.p_show()

    # template to be used to create prompts with groups of buttons
    def example_prompt(self, items):
        buttons = []
        group_buttons = []
        title = 'Prompt title'
        text = 'Prompt text'

        # Loop to group buttons
        for index, key in enumerate(items):
            # Create a button for each lane
            button_label = "{}".format(key)
            button_command = "CALIBRATE_AFC BOWDEN={}".format(key)
            button_style = "primary" if index % 2 == 0 else "secondary"
            group_buttons.append((button_label, button_command, button_style))

            # Add group to buttons list after every 4 keys
            if (index + 1) % 4 == 0 or index == len(items) - 1:
                buttons.append(group_buttons)
                group_buttons = []

        back = [('Back', '<Prompt to go back to>', 'info')]
        self.AFC.prompt.create_custom_p(title, 
                                        text,
                                        None,
                                        True,
                                        buttons,
                                        back)

def load_config(config):
    return AFCPrompt(config)