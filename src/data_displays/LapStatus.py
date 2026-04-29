import ac

RED = (
    1.0,
    0.2,
    0.2,
)

GREEN = (
    0.2,
    0.1,
    0.2,
)

BLUE = (
    0.2,
    0.5,
    1.0,
)


class LAP_STATE:
    ok = "OK"
    pit = "PIT"
    invalid = "INVALID"


LAP_STATE_COLORS = {LAP_STATE.ok: GREEN, LAP_STATE.pit: BLUE, LAP_STATE.invalid: RED}


class LapStatus:

    def __init__(self):
        self.current_lap = None
        self.is_pit = False
        self.is_invalid = False

        # Lap History Tracking
        self.lap_history_data = []  # type: list[str | None]
        self._setup_ui()

    def register_lap(self, lap_number):
        # type: (int) -> None
        """Clear the current registered lap info, and point it to the new one"""

        if self.current_lap:
            self._track_lap()

        self.current_lap = lap_number
        self.is_invalid = False
        self.is_pit = False

    def register_session(self):
        self.current_lap = None
        self.is_invalid = False
        self.is_pit = False

        self._clear_lap_history()

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
        ac.setSize(self.app, 300, 90)
        ac.drawBackground(self.app, 0)
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

        # Create the Lap History row
        self.lap_history_row = [ac.addLabel(self.app, " ") for _ in range(5)]
        start_pos = 0
        width = 60
        height = 10
        for lap_block in self.lap_history_row:
            ac.setPosition(lap_block, start_pos, 80)
            ac.setSize(lap_block, width, height)
            ac.setBackgroundColor(lap_block, *GREEN)

    def _clear_lap_history(self):
        self.lap_history_data = [None for _ in range(5)]
        self._update_history_display()

    def _track_lap(self):
        lap_state = (
            LAP_STATE.invalid
            if self.is_invalid
            else LAP_STATE.pit if self.is_pit else LAP_STATE.ok
        )
        self.lap_history_data.append(lap_state)
        # Clamp to 5 items
        if len(self.lap_history_data) > 5:
            self.lap_history_data = self.lap_history_data[-5:]
        self._update_history_display()

    def _update_display(self):
        """
        Trigger an update to the display when the state changes,
        including when a new lap is registered
        """
        if self.is_pit:
            notification_text = "LAP {} PIT".format(self.current_lap)
            self._set_text(notification_text, BLUE)
        elif self.is_invalid:
            notification_text = "LAP {} INVALID".format(self.current_lap)
            self._set_text(notification_text, RED)
        else:
            self._set_text("")

    def _update_history_display(self):
        for i, lap_block in enumerate(self.lap_history_row):
            lap_state = self.lap_history_data[i]
            if lap_state:
                ac.setBackgroundOpacity(lap_block, 1)
                ac.setBackgroundColor(lap_block, *LAP_STATE_COLORS[lap_state])
            else:
                ac.setBackgroundOpacity(lap_block, 0)

    def _set_text(self, text, color=None, opacity=1.0):
        # type: (str, tuple[float, float, float] | None, float) -> None
        ac.setText(self.label, text)
        if color:
            ac.setFontColor(self.label, *color, opacity)


lap_status_display = LapStatus()
