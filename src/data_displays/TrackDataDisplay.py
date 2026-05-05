import ac  # type: ignore
from src.models import TrackDataState
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
_WINDOW_H = _MARGIN + _HEADER_H + (len(TrackDataState.value_ids) * _ROW_H) + _MARGIN + 2 * (_BUTTON_H + _MARGIN) 

log = pLogger(__name__).log


class TrackDataDisplay:

    def __init__(self, on_upload):
        # type: (TrackDataDisplay, callable) -> None # type: ignore
        self._on_upload = on_upload
        self.rows = {} # type: dict[str, tuple[str, object]]
        self._setup_ui()

    def set_state(self, state):
        # type: (TrackDataState) -> None
        for id, row_state in state.items():
           self._set_row_state(id, row_state)
        self._flag_local_data(state)

    def _setup_ui(self):
        # type: () -> None
        self.app = ac.newApp("pData_TrackData")
        ac.setSize(self.app, _WINDOW_W, _WINDOW_H)
        ac.drawBackground(self.app, 0)
        ac.setTitle(self.app, " ")
        ac.drawBorder(self.app, 0)
        ac.setIconPosition(self.app, -10000, -10000)
        draw_y = _MARGIN 

        header = ac.addLabel(self.app, "Track Data")
        ac.setPosition(header, _MARGIN, draw_y)
        draw_y += _HEADER_H
        ac.setSize(header, _LABEL_W + _STATUS_W, _HEADER_H)
        ac.setFontSize(header, 18)
        ac.setFontColor(header, 1.0, 1.0, 1.0, 1.0)
        draw_y += _MARGIN

        for id, label in TrackDataState.value_labels.items():
            draw_y = self._add_row(draw_y, id, label)
        draw_y += _MARGIN
        
        self.upload_btn = ac.addButton(self.app, "Upload")
        ac.setPosition(self.upload_btn, _MARGIN, draw_y)
        draw_y += _BUTTON_H
        ac.setSize(self.upload_btn, _LABEL_W + _MARGIN + _STATUS_W, _BUTTON_H)
        # Create closure function here, so we can correctly assign it to the button
        def on_upload_clicked(*_):
            self._on_upload()
        # Store it so it does not get cleaned
        self._upload_click_cb = on_upload_clicked
        
        ac.addOnClickedListener(self.upload_btn, self._upload_click_cb)
        draw_y += _MARGIN

        self.warning_label = ac.addLabel(self.app, 'Track Data Upload not available')
        ac.setPosition(self.warning_label, _MARGIN, draw_y)
        ac.setSize(self.warning_label, _WINDOW_W, _ROW_H)
        draw_y += _ROW_H
        ac.setFontSize(self.warning_label, 14)
        ac.setFontAlignment(self.warning_label, 'center')
        ac.setFontColor(self.warning_label, *RED)

    def _add_row(self, row_y, row_id, row_label_text, row_local_value=None):
        # type: (int, str, str, bool | None) -> int
        # Create friendly label
        row_label = ac.addLabel(self.app, row_label_text)
        ac.setPosition(row_label, _MARGIN, row_y)
        ac.setSize(row_label, _LABEL_W, _ROW_H)
        ac.setFontSize(row_label, 14)
        
        # Create Local State Label
        local_col_x = 2 * _MARGIN + _LABEL_W
        status_label_local = ac.addLabel(self.app, "-")
        self._set_label_value(status_label_local, row_local_value)
        ac.setPosition(status_label_local, local_col_x, row_y)
        ac.setSize(status_label_local, _STATUS_W, _ROW_H)
        ac.setFontSize(status_label_local, 14)
        ac.setFontAlignment(status_label_local, "center")

        # Register this label
        self.rows[row_id] = (row_label, status_label_local,)
        # Shift drawing
        return (row_y + _ROW_H)

    def _set_row_state(self, row_id, row_value):
        # type: (str, bool | None) -> None
        row = self.rows.get(row_id, None)
        if row:
            self._set_label_value(row[1], row_value)


    def _set_label_value(self, label, val):
        # type: (object, bool | None) -> None
        if val == None:
            text, col = "-", (1.0, 1.0, 1.0, 1.0,)
        elif val:
            text, col = "OK", GREEN
        else:
            text, col = 'KO', RED
        ac.setText(label, text)
        ac.setFontColor(label, *col)
    
    
    def _flag_local_data(self, state):
        # type: (TrackDataState) -> None
        ac.setVisible(self.warning_label, not state.ready)