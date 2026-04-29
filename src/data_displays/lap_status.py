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
        self.current_lap = 0
        self.is_pit = False
        self.is_invalid = False

        self._setup_ui()

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
        self.label = ac.addLabel(self.app, "")
        ac.setPosition(self.label, 0, 0)
        ac.setSize(self.label, 300, 80)

        # Set text styling
        ac.setFontSize(self.label, 36)
        ac.setFontAlignment(self.label, "center")
        ac.setFontColor(self.label, *RED)

        # Show but with empty text initially
        ac.setVisible(self.label, 1)
        ac.setText(self.label, "")

    def show(self, lap_number):
        """
        Display the lap invalidation notification

        Args:
            lap_number: The lap number that was invalidated
        """
        self.is_invalid = True
        self.current_lap = lap_number
        self._update_display()

    def set_pit(self, lap_number, in_pit):
        """
        Update the pit state

        Args:
            lap_number: The current lap number
            in_pit: Boolean indicating if currently in pit
        """
        self.is_pit = in_pit
        self.current_lap = lap_number
        self._update_display()

    def _update_display(self):
        """
        Update the display based on current state (pit takes priority)
        """
        if self.is_pit:
            # Show blue pit message
            notification_text = "LAP {} PIT".format(self.current_lap)
            ac.setText(self.label, notification_text)
            ac.setFontColor(self.label, *BLUE)
        elif self.is_invalid:
            # Show red invalid message
            notification_text = "LAP {} INVALID".format(self.current_lap)
            ac.setText(self.label, notification_text)
            ac.setFontColor(self.label, *RED)
        else:
            # Clear the display
            ac.setText(self.label, "")

    def clear(self):
        """
        Clear the notification state (called when a new lap starts)
        """
        self.is_invalid = False
        self.is_pit = False
        self.current_lap = 0
        if self.label:
            ac.setText(self.label, "")


lap_status_display = LapStatus()
