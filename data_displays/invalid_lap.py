"""
Invalid Lap Display Module

Handles the visual notification when a lap is invalidated.
"""

from datetime import datetime, timedelta
import ac


class InvalidLapDisplay:
    """
    Manages the on-screen notification for lap invalidations.
    """
    
    def __init__(self):
        """
        Initialize the invalid lap notification UI with its own app window
        """
        self.app = None
        self.label = None
        self.visible_until = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """
        Create and configure the UI elements in a dedicated app window
        """
        # Create a new app window for this display
        self.app = ac.newApp("pData_InvalidLap")
        ac.setSize(self.app, 300, 80)
        
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
        ac.setFontColor(self.label, 1.0, 0.2, 0.2, 1.0)  # Red color
        
        # Show but with empty text initially

        ac.setVisible(self.label, 1)
        ac.setText(self.label, "")
    
    def show(self, lap_number):
        """
        Display the lap invalidation notification
        
        Args:
            lap_number: The lap number that was invalidated
        """
        notification_text = "LAP {} INVALID".format(lap_number)
        ac.setText(self.label, notification_text)
        ac.setVisible(self.label, 1)
    
    def clear(self):
        """
        Clear the notification text
        """
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
