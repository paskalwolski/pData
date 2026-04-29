import ac

RED = (
    1.0,
    0.2,
    0.2,
    1.0,
)

BLUE = (
    0.2,
    0.5,
    1.0,
    1.0,
)


class LapStatus:

    def __init__(self):
        self.current_lap = None
        self.is_pit = False
        self.is_invalid = False

        self._setup_ui()

    def register_lap(self, lap_number):
        # type: (int) -> None
        """Clear the current registered lap info, and point it to the new one"""
        # TODO: Add current lap state to the lap display queue
        self.current_lap = lap_number
        self.is_invalid = False
        self.is_pit = False

    def set_state(self, lap_number, is_pit, is_invalid):
        # type: (int, bool, bool) -> None
        if not self.current_lap == lap_number:
            return
        self.is_pit = is_pit or self.is_pit
        self.is_invalid = is_invalid or self.is_invalid
        self._update_display()

    def _setup_ui(self):
        """
        Create and configure the UI elements in a dedicated app window
        """
        # Create a new app window for this display
        self.app = ac.newApp("pData_LapState")
        ac.setSize(self.app, 300, 80)
        ac.setBackgroundOpacity(self.app, 0)
        ac.setTitle(self.app, " ")  # Empty title so it's not distracting

        # Position the window on screen
        ac.setPosition(self.app, 200, 100)

        # Hide the title bar and background
        ac.drawBorder(self.app, 0)
        ac.setIconPosition(self.app, -10000, -10000)

        # Create text label
        self.label = ac.addLabel(self.app, "AWAITING LAP INFO")
        ac.setPosition(self.label, 0, 0)
        ac.setSize(self.label, 300, 80)
        ac.setFontAlignment(self.label, "center")
        ac.setFontSize(self.label, 36)

        ac.setVisible(self.label, 1)

    def _set_text(self, text, color=None):
        # type: (str, tuple[float, float, float, float] | None) -> None
        ac.setText(self.label, text)
        if color:
            ac.setFontColor(self.label, *color)

    def _update_display(self):
        """
        Update the display based on current state (pit takes priority)
        """
        if self.is_pit:
            notification_text = "LAP {} PIT".format(self.current_lap)
            self._set_text(notification_text, BLUE)
        elif self.is_invalid:
            notification_text = "LAP {} INVALID".format(self.current_lap)
            self._set_text(notification_text, RED)


lap_status_display = LapStatus()
