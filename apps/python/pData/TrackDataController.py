import base64
import configparser
import json
import os

import ac
from DataUploader import TrackDataUploader
from plogging import log


class TrackDataController:
    def __init__(self, circuit_name, track_name):
        self.track = track_name
        self.circuit = circuit_name
        self.track_folder_path = os.path.join(os.getcwd(), "content", "tracks", self.circuit)

        self.friendly_name = None
        self.map_data = {}
        self.section_data = []

        self.read_track_details()
        self.read_map_params()
        self.read_section_params()

        self.init_app()

        self.track_data_uploader = TrackDataUploader(self.track_id, check_callback=self.on_check_result)

    @property
    def track_id(self):
        if self.track:
            return self.circuit + "_" + self.track
        else:
            return self.circuit

    @property
    def track_data(self):
        return {
            'trackId': self.track_id,
            'trackData': {
                'trackName': self.friendly_name if self.friendly_name else self.track_id,
                'sectionData': self.section_data,
                "width": self.map_data['width'],
                "height": self.map_data['height'],
                "xOffset": self.map_data['xOffset'],
                "yOffset": self.map_data['yOffset'],
                "margin": self.map_data['margin'],
                'image': self.map_data['image'],
            }
        }

    def trigger_upload(self):
        self.track_data_uploader.dispatch_track_data(self.track_data)

    def read_track_details(self):
        track_ui_path = os.path.join(self.track_folder_path, 'ui') if not self.track else os.path.join(self.track_folder_path, "ui", self.track)
        ui_ini_path = os.path.join(track_ui_path, 'ui_track.json')
        try:
            with open(ui_ini_path, 'r') as ui_file:
                data = ui_file.read()
                track_details = json.loads(data)
                self.friendly_name = track_details['name']
        except Exception as e:
            log('[trackdata] error reading track UI data')
            log(e)

    def read_map_params(self):
        try:
            track_path = self.track_folder_path if not self.track else os.path.join(self.track_folder_path, self.track)
            track_ini_path = os.path.join(track_path, 'data', "map.ini")
            cp = configparser.ConfigParser()
            cp.read(track_ini_path)
            track_params = cp['PARAMETERS']

            track_image_path = os.path.join(track_path, "map.png")
            log("[trackdata] check_track: Using map file {}".format(track_image_path))
            with open(track_image_path, 'rb') as f:
                img = f.read()

            self.map_data = {
                "trackId": self.track_id,
                "width": track_params["WIDTH"],
                "height": track_params["HEIGHT"],
                "xOffset": track_params["X_OFFSET"],
                "yOffset": track_params["Z_OFFSET"],
                "margin": track_params["MARGIN"],
                'image': base64.b64encode(img).decode('utf-8'),
            }

        except Exception as e:
            log("[trackdata] error reading map data")
            log(e)
            self.map_data = {}

    def read_section_params(self):
        track_path = self.track_folder_path if not self.track else os.path.join(self.track_folder_path, self.track)
        section_ini_path = os.path.join(track_path, 'data', "sections.ini")
        try:
            cp = configparser.ConfigParser()
            cp.read(section_ini_path)
            sections = []
            for section in cp.sections():
                log('[trackdata] Reading section {}'.format(section))
                section_data = cp[section]
                section_details = {
                    'name': section_data['NAME'],
                    'start': section_data['IN'],
                    'end': section_data['OUT'],
                }
                sections.append(section_details)
            self.section_data = sections
        except Exception as e:
            log('[trackdata] error reading section data')
            log(e)
            self.section_data = []

    def init_app(self):
        self.app = ac.newApp("pData_TrackData")
        ac.setSize(self.app, 265, 215)
        ac.setTitle(self.app, " ")
        ac.setIconPosition(self.app, -10000, -10000)

        self._status_label = ac.addLabel(self.app, "Checking...")
        ac.setPosition(self._status_label, 10, 30)
        ac.setSize(self._status_label, 245, 20)
        ac.setFontSize(self._status_label, 14)
        ac.setFontColor(self._status_label, 0.8, 0.8, 0.8, 1.0)

        remote_header = ac.addLabel(self.app, "Remote")
        ac.setPosition(remote_header, 140, 55)
        ac.setSize(remote_header, 55, 18)
        ac.setFontSize(remote_header, 12)
        ac.setFontColor(remote_header, 0.6, 0.6, 0.6, 1.0)

        local_header = ac.addLabel(self.app, "Local")
        ac.setPosition(local_header, 200, 55)
        ac.setSize(local_header, 55, 18)
        ac.setFontSize(local_header, 12)
        ac.setFontColor(local_header, 0.6, 0.6, 0.6, 1.0)

        self._remote_labels = {}
        self._local_labels = {}
        rows = [
            ('trackName',   'Track Name'),
            ('mapData',     'Map Data'),
            ('sectionData', 'Sections'),
            ('margin',      'Margin = 10'),
        ]
        for i, (key, display) in enumerate(rows):
            y = 75 + i * 22

            row_lbl = ac.addLabel(self.app, display)
            ac.setPosition(row_lbl, 10, y)
            ac.setSize(row_lbl, 130, 18)
            ac.setFontSize(row_lbl, 13)
            ac.setFontColor(row_lbl, 0.8, 0.8, 0.8, 1.0)

            remote_lbl = ac.addLabel(self.app, "-")
            ac.setPosition(remote_lbl, 140, y)
            ac.setSize(remote_lbl, 55, 18)
            ac.setFontSize(remote_lbl, 13)
            ac.setFontColor(remote_lbl, 0.6, 0.6, 0.6, 1.0)

            local_lbl = ac.addLabel(self.app, "-")
            ac.setPosition(local_lbl, 200, y)
            ac.setSize(local_lbl, 55, 18)
            ac.setFontSize(local_lbl, 13)
            ac.setFontColor(local_lbl, 0.5, 0.5, 0.5, 1.0)

            self._remote_labels[key] = remote_lbl
            self._local_labels[key] = local_lbl

        self._upload_btn = ac.addButton(self.app, "Upload Track Data")
        ac.setPosition(self._upload_btn, 10, 185)
        ac.setSize(self._upload_btn, 180, 25)
        ac.addOnClickedListener(self._upload_btn, self._on_upload_clicked)

    def _set_indicator(self, label, value):
        if value:
            ac.setText(label, "Yes")
            ac.setFontColor(label, 0.2, 1.0, 0.2, 1.0)
        else:
            ac.setText(label, "No")
            ac.setFontColor(label, 1.0, 0.4, 0.4, 1.0)

    def on_check_result(self, result):
        exists = result.get('exists', False) if result else False

        if exists:
            ac.setText(self._status_label, "Track: in DB")
            ac.setFontColor(self._status_label, 0.2, 1.0, 0.2, 1.0)
        else:
            ac.setText(self._status_label, "Track: not in DB")
            ac.setFontColor(self._status_label, 1.0, 0.4, 0.4, 1.0)
            self.track_data_uploader.dispatch_track_data({'trackId': self.track_id})

        remote_trackName   = bool(result.get('trackName'))           if result else False
        remote_mapData     = bool(result.get('width'))               if result else False
        remote_sectionData = bool(result.get('sections'))            if result else False
        remote_margin      = str(result.get('margin', '')) == '10'   if result else False

        self._set_indicator(self._remote_labels['trackName'],   remote_trackName)
        self._set_indicator(self._remote_labels['mapData'],     remote_mapData)
        self._set_indicator(self._remote_labels['sectionData'], remote_sectionData)
        self._set_indicator(self._remote_labels['margin'],      remote_margin)

    def _on_upload_clicked(self, *_):
        log("[trackdata] upload button clicked")
        ac.setText(self._status_label, "Sending...")
        ac.setFontColor(self._status_label, 0.8, 0.8, 0.8, 1.0)
        self.trigger_upload()
