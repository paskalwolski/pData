import ac  # type: ignore
from src.data_displays.DataSectionDisplay import DataSectionDisplay
from src.data_displays.layout import MARGIN, ROW_H, WINDOW_W, FULL_W
from src.plogging import pLogger

log = pLogger(__name__).log

_WAITING_H = MARGIN + ROW_H + MARGIN


class DataControllerDisplay:
    def __init__(self, on_upload):
        self.app = ac.newApp("pData_DataController")
        ac.drawBackground(self.app, 0)
        ac.setTitle(self.app, " ")
        ac.drawBorder(self.app, 0)
        ac.setIconPosition(self.app, -10000, -10000)
        ac.setSize(self.app, WINDOW_W, _WAITING_H)

        self._waiting_label = ac.addLabel(self.app, "Waiting for data registry...")
        ac.setPosition(self._waiting_label, MARGIN, MARGIN)
        ac.setSize(self._waiting_label, FULL_W, ROW_H)
        ac.setFontSize(self._waiting_label, 14)
        ac.setFontAlignment(self._waiting_label, "center")

        self.track_display = DataSectionDisplay(self.app, on_upload, "Track Data")
        self.car_display = DataSectionDisplay(self.app, lambda: None, "Car Data")

    def register_track_row(self, key, label, required=True):
        if required:
            self.track_display.register_required_row(key, label)
        else:
            self.track_display.register_optional_row(key, label)

    def register_car_row(self, key, label, required=True):
        if required:
            self.car_display.register_required_row(key, label)
        else:
            self.car_display.register_optional_row(key, label)

    def build(self):
        ac.setVisible(self._waiting_label, 0)
        track_section_h = self.track_display.section_h
        car_section_h = self.car_display.section_h
        ac.setSize(self.app, WINDOW_W, track_section_h + car_section_h)
        self.track_display.build(0)
        self.car_display.build(track_section_h)

    def set_values(self, column, values):
        self.track_display.set_values(column, values)

    def set_uploading(self):
        self.track_display.set_uploading()

    def set_complete(self):
        self.track_display.set_complete()

    def set_error(self):
        self.track_display.set_error()
