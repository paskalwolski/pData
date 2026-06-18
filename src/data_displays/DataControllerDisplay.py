import ac  # type: ignore
from src.data_displays.TrackDataDisplay import TrackDataDisplay
from src.data_displays.layout import MARGIN, LABEL_W, HEADER_H, ROW_H, WINDOW_W, FULL_W
from src.plogging import pLogger

_CAR_H = MARGIN + HEADER_H + ROW_H + MARGIN

log = pLogger(__name__).log


class DataControllerDisplay:
    def __init__(self, on_upload):
        self.app = ac.newApp("pData_DataController")
        ac.drawBackground(self.app, 0)
        ac.setTitle(self.app, " ")
        ac.drawBorder(self.app, 0)
        ac.setIconPosition(self.app, -10000, -10000)

        self.track_display = TrackDataDisplay(self.app, 0, on_upload)

    def build(self):
        section_h = self.track_display.section_h
        ac.setSize(self.app, WINDOW_W, section_h + _CAR_H)
        self.track_display.build()
        self._build_car_section(section_h)

    def _build_car_section(self, y):
        header = ac.addLabel(self.app, "Car Data")
        ac.setPosition(header, MARGIN, y + MARGIN)
        ac.setSize(header, LABEL_W, HEADER_H)
        ac.setFontSize(header, 18)
        ac.setFontAlignment(header, "left")

        placeholder = ac.addLabel(self.app, "Waiting for Car Data Init...")
        ac.setPosition(placeholder, MARGIN, y + MARGIN + HEADER_H)
        ac.setSize(placeholder, FULL_W, ROW_H)
        ac.setFontSize(placeholder, 14)
        ac.setFontAlignment(placeholder, "center")

    def set_values(self, column, values):
        self.track_display.set_values(column, values)

    def set_uploading(self):
        self.track_display.set_uploading()

    def set_complete(self):
        self.track_display.set_complete()

    def set_error(self):
        self.track_display.set_error()
