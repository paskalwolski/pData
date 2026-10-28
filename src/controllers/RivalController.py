import ac

MARGIN = 10
HEADER_H = 30
FULL_W = 180
LABEL_W = 50
VALUE_W = 120
ROW_H = 25
RIVAL_SELECT_H = 150
WINDOW_W = MARGIN + FULL_W + MARGIN


SHOW_RIVALS = "Show Rivals"
HIDE_RIVALS = "Hide Rivals"


class RivalController:
    def __init__(self):
        self.slot_count = ac.getCarsCount()
        self.selected_rival = None
        self.rivals = {}
        self._displayed_rivals = []
        self.show_select = True

        self.window_h = 100

        self._init_window()
        self._refresh_rival_select()

    def trigger_update(self):
        """
        In-place for acUpdate, so that the RivalController can
        manage its own update lifecycle
        """
        return

    def _init_window(self):
        row_y = MARGIN

        self.app = ac.newApp("pData_RivalController")
        ac.drawBackground(self.app, 0)
        ac.setTitle(self.app, " ")
        ac.drawBorder(self.app, 0)
        ac.setIconPosition(self.app, -10000, -10000)
        ac.setSize(self.app, WINDOW_W, self.window_h)

        # Header Text
        header = ac.addLabel(self.app, "Rival Tracker")
        ac.setPosition(header, MARGIN, row_y)
        row_y += HEADER_H + MARGIN
        ac.setSize(header, FULL_W, HEADER_H)
        ac.setFontSize(header, 14)

        # Rival Display
        rival_label = ac.addLabel(self.app, "Selected Rival:")
        ac.setPosition(rival_label, MARGIN, row_y)
        ac.setSize(rival_label, LABEL_W, ROW_H)
        ac.setFontSize(rival_label, 12)

        self.rival_name = ac.addLabel(self.app, "None")
        ac.setPosition(self.rival_name, MARGIN + LABEL_W + MARGIN, row_y)
        ac.setSize(self.rival_name, VALUE_W, ROW_H)
        row_y += ROW_H + MARGIN

        # Rival Selector
        self.rival_toggle = ac.addButton(self.app, HIDE_RIVALS)
        ac.setPosition(self.rival_toggle, MARGIN, row_y)
        ac.setSize(self.rival_toggle, FULL_W, ROW_H)
        row_y += ROW_H + MARGIN

        # Toggle Closure
        def _toggle_rival_select(*_):
            # Update Label
            self.show_select = not self.show_select
            ac.setText(
                self.rival_toggle, HIDE_RIVALS if self.show_select else SHOW_RIVALS
            )

            # Populate the Rival Selector
            if self.show_select:
                self._refresh_rival_select()
            else:
                ac.setVisible(self.rival_select, 0)

            # Update Window Height
            self.window_h = (
                self.window_h + (RIVAL_SELECT_H)
                if self.show_select
                else self.window_h - (RIVAL_SELECT_H)
            )
            ac.setSize(self.app, WINDOW_W, self.window_h)

        self._toggle_rival_select = _toggle_rival_select

        ac.addOnClickedListener(self.rival_toggle, self._toggle_rival_select)

        self.rival_select = ac.addListBox(self.app, "Rival Select")
        ac.setSize(self.rival_select, FULL_W, RIVAL_SELECT_H)
        ac.setPosition(self.rival_select, MARGIN, row_y)
        row_y += RIVAL_SELECT_H + MARGIN

        # Selection Closures
        def _select_rival(NAME, _):
            self.selected_rival = self.rivals.get(NAME, None)
            self._update_rival_display()

        def _deselect_rival(*_):
            self.selected_rival = None
            self._update_rival_display()

        ac.addOnListBoxSelectionListener(self.rival_select, _select_rival)
        ac.addOnListBoxDeselectionListener(self.rival_select, _deselect_rival)

        self.window_h = row_y
        ac.setSize(self.app, WINDOW_W, self.window_h)

    def _update_rival_display(self):
        ac.setText(
            self.rival_name,
            self.selected_rival["name"] if self.selected_rival else "None",
        )

    def _init_rivals(self):
        # type: () -> dict[string, int]
        owner_name = ac.getDriverName(0)
        rivals = {}
        for i in range(self.slot_count):
            d_id = i + 1
            if ac.isConnected(d_id):
                name = ac.getDriverName(d_id)
                if name == owner_name:
                    continue
                rivals[name] = {"id": d_id, "name": name}
        self.rivals = rivals

    def _refresh_rival_select(self):
        self._clear_rival_select()
        self._init_rivals()
        # Popualate rival select
        for _, rival in self.rivals.values():
            rival_name = rival["name"]
            select_rival_id = ac.addItem(self.rival_select, rival_name)
            self._displayed_rivals.append({"id": select_rival_id, "name": rival_name})

    def _clear_rival_select(self):
        for r in self._displayed_rivals:
            ac.removeItem(self.rival_select, r["id"])
        self._displayed_rivals = []

        # TODO: Add onChange
