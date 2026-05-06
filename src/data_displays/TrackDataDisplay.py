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
_WINDOW_W = _MARGIN + _LABEL_W + 2 * _STATUS_W + _MARGIN
_WINDOW_H = _MARGIN + _HEADER_H + _MARGIN + (len(TrackDataState.value_ids) * _ROW_H) + _MARGIN + _BUTTON_H + _MARGIN 
_FULL_W = _WINDOW_W - 2 * _MARGIN

log = pLogger(__name__).log

class ACTION_STATE:
    WAITING = "WAITING"
    DISABLED = "DISABLED"
    READY = "READY"
    UPLOADING = "UPLOADING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class TrackDataDisplay:

    def __init__(self, on_upload):
        # type: (TrackDataDisplay, callable) -> None # type: ignore
        self._on_upload = on_upload
        self.rows = {} # type: dict[str, tuple[object, object, object]]
        self._setup_ui()

    def set_state(self, column, state):
        # type: (int, TrackDataState) -> None
        for id, row_state in state.items():
           self._set_row_state(id, column, row_state)
        if column == 1:
            # Trigger action change when we update the local state
            self._set_action_state(ACTION_STATE.READY if state.ready else ACTION_STATE.DISABLED)

    def set_uploading(self):
        self._set_action_state(ACTION_STATE.UPLOADING)

    def set_complete(self):
        self._set_action_state(ACTION_STATE.COMPLETE)

    def set_error(self):
        self._set_action_state(ACTION_STATE.ERROR)

    def _setup_ui(self):
        # type: () -> None
        self.app = ac.newApp("pData_TrackData")
        ac.setSize(self.app, _WINDOW_W, _WINDOW_H)
        ac.drawBackground(self.app, 0)
        ac.setTitle(self.app, " ")
        ac.drawBorder(self.app, 0)
        ac.setIconPosition(self.app, -10000, -10000)
        draw_y = _MARGIN 
        
        header_x = _MARGIN
        self._create_label("Track Data", draw_y, x=header_x, width=_LABEL_W, height=_HEADER_H, font_size=18, font_alignment="left")
        header_x += _LABEL_W
        self._create_label("Local", draw_y, x=header_x, width=_STATUS_W, height=_HEADER_H, font_size=12)
        header_x += _STATUS_W
        self._create_label("Remote", draw_y, x=header_x, width=_STATUS_W, height=_HEADER_H, font_size=12)
        draw_y += _HEADER_H + _MARGIN

        for id, label in TrackDataState.value_labels.items():
            self._add_row(draw_y, id, label)
            draw_y += _ROW_H
        draw_y += _MARGIN
        self._setup_action(draw_y)

    def _setup_action(self, y):
        waiting = self._create_label("Waiting for Track Data...", y)
        disabled = self._create_label("Track Upload not Available", y, color=RED)
        uploading = self._create_label("Upload in Progress", y)
        complete = self._create_label("Upload Complete", y, color=GREEN)
        error = self._create_label("Error Uploading", y, color=RED)
        # Create Upload Button
        ready = self.upload_btn = ac.addButton(self.app, "Upload")
        ac.setPosition(self.upload_btn, _MARGIN, y)
        ac.setSize(self.upload_btn, _FULL_W, _BUTTON_H)
        # Create closure function here, so we can correctly assign it to the button
        def on_upload_clicked(*_):
            self._on_upload()
        # Store it so it does not get cleaned
        self._upload_click_cb = on_upload_clicked
        ac.addOnClickedListener(self.upload_btn, self._upload_click_cb)

        self.actions = {
            ACTION_STATE.WAITING: waiting, 
            ACTION_STATE.DISABLED: disabled,
            ACTION_STATE.READY: ready,
            ACTION_STATE.UPLOADING: uploading, 
            ACTION_STATE.COMPLETE: complete,
            ACTION_STATE.ERROR: error,
        }


    # TODO: Consider yanking this
    def _create_label(self, text, y, *, x = _MARGIN, width = _FULL_W, height=_BUTTON_H, color = None, font_size = 14, font_alignment = 'center'):
        # type: (str, int, list, int, int, int, tuple[float, float, float, float] | None, int, str)-> object
        label = ac.addLabel(self.app, text)
        ac.setSize(label, width, height)
        ac.setFontSize(label, font_size)
        ac.setFontAlignment(label, font_alignment)
        ac.setPosition(label, x, y)
        if color:
            ac.setFontColor(label, *color)
        return label

    def _add_row(self, row_y, row_id, row_label_text, row_local_value=None):
        # type: (int, str, str, bool | None) -> None
        # Create friendly label
        row_label = self._create_label(row_label_text, row_y, x=_MARGIN, width=_LABEL_W, height=_ROW_H, font_size=14, font_alignment="left")
        
        # Create Local State Label
        local_col_x = _MARGIN + _LABEL_W
        status_label_local = self._create_label("-", row_y, x=local_col_x, width=_STATUS_W, height=_ROW_H)
        self._set_label_value(status_label_local, row_local_value)
        
        # Create Remote State Label
        row_col_x = local_col_x + _STATUS_W
        status_label_remote = self._create_label("-", row_y, x=row_col_x, width=_STATUS_W, height=_ROW_H)
        self._set_label_value(status_label_remote, None)

        # Register this label
        self.rows[row_id] = (row_label, status_label_local, status_label_remote,)

    def _set_row_state(self, row_id, column, row_value):
        # type: (str, int, bool | None) -> None
        row = self.rows.get(row_id, None)
        if row:
            self._set_label_value(row[column], row_value)


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
    

    def _set_action_state(self, state):
        # type: (str) -> None
        clean_state = getattr(ACTION_STATE, state, None)
        if not clean_state:
            clean_state = ACTION_STATE.WAITING
        log("Setting action state to {}".format(clean_state))
        for id, control in self.actions.items():
            ac.setVisible(control, id == clean_state)