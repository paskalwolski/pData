import ac  # type: ignore
from src.models import TrackDataState
from src.plogging import pLogger
from src.data_displays.layout import MARGIN, LABEL_W, STATUS_W, ROW_H, HEADER_H, BUTTON_H, WINDOW_W, FULL_W

RED = (1.0, 0.2, 0.2, 1.0)
GREEN = (0.2, 1.0, 0.2, 1.0)

SECTION_H = (
    MARGIN
    + HEADER_H
    + MARGIN
    + (len(TrackDataState.value_ids) * ROW_H)
    + MARGIN
    + BUTTON_H
    + MARGIN
)

log = pLogger(__name__).log


class ACTION_STATE:
    WAITING = "WAITING"
    DISABLED = "DISABLED"
    READY = "READY"
    UPLOADING = "UPLOADING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class TrackDataDisplay:

    def __init__(self, app, y_offset, on_upload):
        self._app = app
        self._y_offset = y_offset
        self._on_upload = on_upload
        self.rows = {}  # type: dict[str, tuple[object, object, object]]
        self.actions = {}
        self._upload_click_cb = lambda: None
        self._setup_ui()

    def set_state(self, column, state):
        # type: (int, TrackDataState) -> None
        for row_id, row_state in state.items():
            self._set_row_state(row_id, column, row_state)
        if column == 1:
            # Trigger action change when we update the local state
            self._set_action_state(
                ACTION_STATE.READY if state.ready else ACTION_STATE.DISABLED
            )

    def set_uploading(self):
        self._set_action_state(ACTION_STATE.UPLOADING)

    def set_complete(self):
        self._set_action_state(ACTION_STATE.COMPLETE)

    def set_error(self):
        self._set_action_state(ACTION_STATE.ERROR)

    def _setup_ui(self):
        # type: () -> None
        draw_y = self._y_offset + MARGIN

        header_x = MARGIN
        self._create_label(
            "Track Data",
            draw_y,
            x=header_x,
            width=LABEL_W,
            height=HEADER_H,
            font_size=18,
            font_alignment="left",
        )
        header_x += LABEL_W
        self._create_label(
            "Local", draw_y, x=header_x, width=STATUS_W, height=HEADER_H, font_size=12
        )
        header_x += STATUS_W
        self._create_label(
            "Remote",
            draw_y,
            x=header_x,
            width=STATUS_W,
            height=HEADER_H,
            font_size=12,
        )
        draw_y += HEADER_H + MARGIN

        for row_id, label in TrackDataState.value_labels.items():
            self._add_row(draw_y, row_id, label)
            draw_y += ROW_H
        draw_y += MARGIN
        self._setup_action(draw_y)

    def _setup_action(self, y):
        waiting = self._create_label("Waiting for Track Data...", y)
        disabled = self._create_label("Track Upload not Available", y, color=RED)
        uploading = self._create_label("Upload in Progress", y)
        complete = self._create_label("Upload Complete", y, color=GREEN)
        error = self._create_label("Error Uploading", y, color=RED)
        # Create Upload Button
        ready = ac.addButton(self._app, "Upload")
        ac.setPosition(ready, MARGIN, y)
        ac.setSize(ready, FULL_W, BUTTON_H)

        # Create closure function here, so we can correctly assign it to the button
        def on_upload_clicked(*_):
            self._on_upload()

        # Store it so it does not get cleaned
        self._upload_click_cb = on_upload_clicked
        ac.addOnClickedListener(ready, self._upload_click_cb)

        self.actions = {
            ACTION_STATE.WAITING: waiting,
            ACTION_STATE.DISABLED: disabled,
            ACTION_STATE.READY: ready,
            ACTION_STATE.UPLOADING: uploading,
            ACTION_STATE.COMPLETE: complete,
            ACTION_STATE.ERROR: error,
        }

    # TODO: Consider yanking this
    def _create_label(
        self,
        text,
        y,
        *,
        x=MARGIN,
        width=FULL_W,
        height=BUTTON_H,
        color=None,
        font_size=14,
        font_alignment="center"
    ):
        # type: (str, int, list, int, int, int, tuple[float, float, float, float] | None, int, str)-> object
        label = ac.addLabel(self._app, text)
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
        row_label = self._create_label(
            row_label_text,
            row_y,
            x=MARGIN,
            width=LABEL_W,
            height=ROW_H,
            font_size=14,
            font_alignment="left",
        )

        # Create Local State Label
        local_col_x = MARGIN + LABEL_W
        status_label_local = self._create_label(
            "-", row_y, x=local_col_x, width=STATUS_W, height=ROW_H
        )
        self._set_label_value(status_label_local, row_local_value)

        # Create Remote State Label
        row_col_x = local_col_x + STATUS_W
        status_label_remote = self._create_label(
            "-", row_y, x=row_col_x, width=STATUS_W, height=ROW_H
        )
        self._set_label_value(status_label_remote, None)

        # Register this label
        self.rows[row_id] = (
            row_label,
            status_label_local,
            status_label_remote,
        )

    def _set_row_state(self, row_id, column, row_value):
        # type: (str, int, bool | None) -> None
        row = self.rows.get(row_id, None)
        if row:
            self._set_label_value(row[column], row_value)

    def _set_label_value(self, label, val):
        # type: (object, bool | None) -> None
        if val is None:
            text, col = "-", (
                1.0,
                1.0,
                1.0,
                1.0,
            )
        elif val:
            text, col = "OK", GREEN
        else:
            text, col = "KO", RED
        ac.setText(label, text)
        ac.setFontColor(label, *col)

    def _set_action_state(self, state):
        # type: (str) -> None
        clean_state = getattr(ACTION_STATE, state, None)
        if not clean_state:
            clean_state = ACTION_STATE.WAITING
        log("Setting action state to {}".format(clean_state))
        for action_id, control in self.actions.items():
            ac.setVisible(control, action_id == clean_state)
