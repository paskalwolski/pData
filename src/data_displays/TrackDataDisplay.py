import ac  # type: ignore
from src.plogging import pLogger

RED = (1.0, 0.2, 0.2, 1.0)
GREEN = (0.2, 1.0, 0.2, 1.0)

_MARGIN = 10
_LABEL_W = 180
_STATUS_W = 60
_ROW_H = 25
_HEADER_H = 30
_BUTTON_H = 30
_WINDOW_W = _MARGIN + _LABEL_W + _MARGIN + _STATUS_W + _MARGIN
_WINDOW_H = _MARGIN + _HEADER_H + (4 * _ROW_H) + _MARGIN + _BUTTON_H + _MARGIN

_ROW_LABELS = ["Track Name", "Map Details", "Margin 10px", "Map Present"]

log = pLogger(__name__).log


class TrackDataDisplay:

    def __init__(self, on_upload):
        self._on_upload = on_upload
        self._status_labels = []
        self._setup_ui()

    def _setup_ui(self):
        self.app = ac.newApp("pData_TrackData")
        ac.setSize(self.app, _WINDOW_W, _WINDOW_H)
        ac.drawBackground(self.app, 0)
        ac.setTitle(self.app, " ")
        ac.drawBorder(self.app, 0)
        ac.setIconPosition(self.app, -10000, -10000)

        header = ac.addLabel(self.app, "Track Data")
        ac.setPosition(header, _MARGIN, _MARGIN)
        ac.setSize(header, _LABEL_W + _STATUS_W, _HEADER_H)
        ac.setFontSize(header, 18)
        ac.setFontColor(header, 1.0, 1.0, 1.0, 1.0)

        status_col_x = _MARGIN + _LABEL_W + _MARGIN

        for i, row_label_text in enumerate(_ROW_LABELS):
            row_y = _MARGIN + _HEADER_H + (i * _ROW_H)

            label = ac.addLabel(self.app, row_label_text)
            ac.setPosition(label, _MARGIN, row_y)
            ac.setSize(label, _LABEL_W, _ROW_H)
            ac.setFontSize(label, 14)
            ac.setFontColor(label, 1.0, 1.0, 1.0, 1.0)

            status = ac.addLabel(self.app, "KO")
            ac.setPosition(status, status_col_x, row_y)
            ac.setSize(status, _STATUS_W, _ROW_H)
            ac.setFontSize(status, 14)
            ac.setFontAlignment(status, "center")
            ac.setFontColor(status, *RED)
            self._status_labels.append(status)

        button_y = _MARGIN + _HEADER_H + (len(_ROW_LABELS) * _ROW_H) + _MARGIN
        self.upload_btn = ac.addButton(self.app, "Upload")
        ac.setPosition(self.upload_btn, _MARGIN, button_y)
        ac.setSize(self.upload_btn, _LABEL_W + _MARGIN + _STATUS_W, _BUTTON_H)
        ac.addOnClickedListener(self.upload_btn, self._on_upload_clicked)

    def _set_indicator(self, index, ok):
        # type: (int, bool) -> None
        label = self._status_labels[index]
        if ok:
            ac.setText(label, "OK")
            ac.setFontColor(label, *GREEN)
        else:
            ac.setText(label, "KO")
            ac.setFontColor(label, *RED)

    def _on_upload_clicked(self, *args):
        self._on_upload()
