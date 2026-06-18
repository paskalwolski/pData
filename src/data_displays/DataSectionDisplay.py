import ac  # type: ignore
from src.plogging import pLogger
from src.data_displays.layout import MARGIN, LABEL_W, STATUS_W, ROW_H, HEADER_H, BUTTON_H, WINDOW_W, FULL_W

RED = (1.0, 0.2, 0.2, 1.0)
ORANGE = (1.0, 0.6, 0.0, 1.0)
GREEN = (0.2, 1.0, 0.2, 1.0)

_SEPARATOR_H = 10
_SEPARATOR_COLOR = (0.5, 0.5, 0.5, 1.0)

log = pLogger(__name__).log


class ACTION_STATE:
    WAITING = "WAITING"
    DISABLED = "DISABLED"
    READY = "READY"
    UPLOADING = "UPLOADING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class DataSectionDisplay:

    def __init__(self, app, on_upload, title):
        self._app = app
        self._y_offset = 0
        self._on_upload = on_upload
        self._title = title
        self._required_rows = []
        self._optional_rows = []
        self.rows = {}
        self.actions = {}
        self._upload_click_cb = lambda: None

    @property
    def section_h(self):
        row_count = len(self._required_rows) + len(self._optional_rows)
        sep_h = _SEPARATOR_H if (self._required_rows and self._optional_rows) else 0
        return MARGIN + HEADER_H + MARGIN + (row_count * ROW_H) + sep_h + MARGIN + BUTTON_H + MARGIN

    def register_required_row(self, key, label):
        self._required_rows.append((key, label))

    def register_optional_row(self, key, label):
        self._optional_rows.append((key, label))

    def build(self, y_offset=0):
        self._y_offset = y_offset
        draw_y = self._y_offset + MARGIN

        header_x = MARGIN
        self._create_label(
            self._title,
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

        for key, label in self._required_rows:
            self._add_row(draw_y, key, label, RED)
            draw_y += ROW_H

        if self._required_rows and self._optional_rows:
            self._add_separator(draw_y)
            draw_y += _SEPARATOR_H

        for key, label in self._optional_rows:
            self._add_row(draw_y, key, label, ORANGE)
            draw_y += ROW_H
        draw_y += MARGIN
        self._setup_action(draw_y)

    def set_values(self, column, values):
        for row_id, row_value in values.items():
            self._set_row_state(row_id, column, row_value)
        if column == 1:
            is_ready = all(values.get(k) for k, _ in self._required_rows)
            self._set_action_state(
                ACTION_STATE.READY if is_ready else ACTION_STATE.DISABLED
            )

    def set_uploading(self):
        self._set_action_state(ACTION_STATE.UPLOADING)

    def set_complete(self):
        self._set_action_state(ACTION_STATE.COMPLETE)

    def set_error(self):
        self._set_action_state(ACTION_STATE.ERROR)

    def _setup_action(self, y):
        waiting = self._create_label("Waiting for {}...".format(self._title), y)
        disabled = self._create_label("{} Upload not Available".format(self._title), y, color=RED)
        uploading = self._create_label("Upload in Progress", y)
        complete = self._create_label("Upload Complete", y, color=GREEN)
        error = self._create_label("Error Uploading", y, color=RED)
        ready = ac.addButton(self._app, "Upload")
        ac.setPosition(ready, MARGIN, y)
        ac.setSize(ready, FULL_W, BUTTON_H)

        # Store closure so it is not garbage collected
        def on_upload_clicked(*_):
            self._on_upload()

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
        self._set_action_state(ACTION_STATE.WAITING)

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
        label = ac.addLabel(self._app, text)
        ac.setSize(label, width, height)
        ac.setFontSize(label, font_size)
        ac.setFontAlignment(label, font_alignment)
        ac.setPosition(label, x, y)
        if color:
            ac.setFontColor(label, *color)
        return label

    def _add_separator(self, y):
        sep = self._create_label(
            "-" * 150,
            y,
            width=FULL_W,
            height=_SEPARATOR_H,
            font_size=5,
            color=_SEPARATOR_COLOR,
        )
        return sep

    def _add_row(self, row_y, row_id, row_label_text, ko_color=RED):
        row_label = self._create_label(
            row_label_text,
            row_y,
            x=MARGIN,
            width=LABEL_W,
            height=ROW_H,
            font_size=14,
            font_alignment="left",
        )

        local_col_x = MARGIN + LABEL_W
        status_label_local = self._create_label(
            "-", row_y, x=local_col_x, width=STATUS_W, height=ROW_H
        )
        self._set_label_value(status_label_local, None, ko_color)

        row_col_x = local_col_x + STATUS_W
        status_label_remote = self._create_label(
            "-", row_y, x=row_col_x, width=STATUS_W, height=ROW_H
        )
        self._set_label_value(status_label_remote, None, ko_color)

        self.rows[row_id] = (row_label, status_label_local, status_label_remote, ko_color)

    def _set_row_state(self, row_id, column, row_value):
        row = self.rows.get(row_id, None)
        if row:
            self._set_label_value(row[column], row_value, row[3])

    def _set_label_value(self, label, val, ko_color=RED):
        if val is None:
            text, col = "-", (1.0, 1.0, 1.0, 1.0)
        elif val:
            text, col = "OK", GREEN
        else:
            text, col = "KO", ko_color
        ac.setText(label, text)
        ac.setFontColor(label, *col)

    def _set_action_state(self, state):
        clean_state = getattr(ACTION_STATE, state, None)
        if not clean_state:
            clean_state = ACTION_STATE.WAITING
        log("Setting action state to {}".format(clean_state))
        for action_id, control in self.actions.items():
            ac.setVisible(control, action_id == clean_state)
