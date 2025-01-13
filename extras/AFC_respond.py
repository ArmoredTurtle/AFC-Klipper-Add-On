
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

    # Displaying a full example prompt with options
    def display_example_prompt(self):
        self.prompt_begin("My Prompt")
        self.prompt_text("This is an example of a prompt")

        # Adding buttons with various styles
        self.p_button("primary", "G28", "primary")
        self.p_button("secondary", "RESPOND MSG=test", "secondary")
        self.p_button("info", "RESPOND MSG=test #2", "info")
        self.p_button("warning", "RESPOND MSG=test #3", "warning")
        
        # Showing the prompt
        self.p_show()

    # Example of grouped buttons
    def display_grouped_buttons(self):
        self.p_begin("Grouped Buttons Example")
        self.p_text("These buttons are grouped:")

        self.p_button_group_start()
        self.p_button("Button 1", "CMD_1", "primary")
        self.p_button("Button 2", "CMD_2", "secondary")
        self.p_button_group_end()

        self.p_button("Stand-alone Button", "CMD_3", "info")
        self.p_show()

    # Method to create a custom prompt
    def create_custom_p(self, prompt_name, text=None, buttons=None, Cancel=False, footer_buttons=None):
        self.p_begin(prompt_name)
        if text != None:
            self.p_text(text)

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
        
        if Cancel:
            self.p_cancel_button()

        self.p_show()

def load_config(config):
    return AFCPrompt(config)