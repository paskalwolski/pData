"""
Lap State Display Module

Handles the visual notification for lap state (invalid/pit).
"""

from datetime import datetime, timedelta
import ac


class InvalidLapDisplay:
    """
    Manages the on-screen notification for lap state (invalid and pit).
    """
    
    def __init__(self):
        """
        Initialize the lap state notification UI with its own app window
        """
        self.app = None
        self.label = None
        self.visible_until = None
        self.is_invalid = False
        self.is_pit = False
        self.current_lap = 0
        
        self._setup_ui()
    
    def _setup_ui(self):
        """
        Create and configure the UI elements in a dedicated app window
        """
        # Create a new app window for this display
        self.app = ac.newApp("pData_LapState")
        ac.setSize(self.app, 300, 80)
        ac.setTitle(self.app, " ") # Empty title so it's not distracting
        
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
        ac.setFontColor(self.label, 1.0, 0.2, 0.2, 1.0)  # Red color (default for invalid)
        
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
            ac.setFontColor(self.label, 0.2, 0.5, 1.0, 1.0)  # Blue color
        elif self.is_invalid:
            # Show red invalid message
            notification_text = "LAP {} INVALID".format(self.current_lap)
            ac.setText(self.label, notification_text)
            ac.setFontColor(self.label, 1.0, 0.2, 0.2, 1.0)  # Red color
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
    
    def update(self):
        """
        Update the display state. 
        Note: This method is kept for compatibility but no longer manages auto-hide.
        The display now persists until explicitly cleared.
        """
        pass
    
    def configure(self, x=None, y=None, width=None, height=None, 
                  font_size=None, color=None, duration=None):
        """
        Reconfigure the display appearance
        
        Args:
            x: X position on screen for the app window
            y: Y position on screen for the app window
            width: Width of the notification
            height: Height of the notification
            font_size: Font size for text
            color: RGB tuple for text color (r, g, b) values 0-1
            duration: Default duration in seconds
        """
        if x is not None and y is not None:
            ac.setPosition(self.app, x, y)
        
        if width is not None and height is not None:
            ac.setSize(self.app, width, height)
            ac.setSize(self.label, width, height)
        
        if font_size is not None:
            ac.setFontSize(self.label, font_size)
        
        if color is not None and len(color) == 3:
            ac.setFontColor(self.label, color[0], color[1], color[2], 1.0)
