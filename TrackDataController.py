import base64
import configparser
import json
import os

from DataUploader import TrackDataUploader
from plogging import log


class TrackDataController:
    def __init__(self, circuit_name, track_name):
        self.track = track_name
        self.circuit = circuit_name
        self.track_data_uploader = TrackDataUploader(self.track_id)
        
        self.track_folder_path = os.path.join(os.getcwd(), "content", "tracks", self.circuit)

        # Read all stored ini files
        self.read_track_details()
        self.read_map_params()
        self.read_section_params()
        # TODO: Add the App Control init

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
                "margin":self.map_data['margin'],
                'image': self.map_data['image'],
            }
        }
    
    def trigger_upload(self):
        self.track_data_uploader.dispatch_track_data(self.track_data)
        
    def read_track_details(self):
        """Read basic UI-available data from the `ui_track.json` file"""
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
        """
        Read map data from the `map.ini` file. This expects to read data about the track image
        """
        
        try:
            # Read the track ini data
            track_path = self.track_folder_path if not self.track else os.path.join(self.track_folder_path, self.track)
            track_ini_path = os.path.join(track_path, 'data', "map.ini")
            cp = configparser.ConfigParser()
            cp.read(track_ini_path)
            track_params = cp['PARAMETERS']
            
            # Read the track image
            track_image_path = os.path.join(track_path, "map.png")
            log("[trackdata] check_track: Using map file {}".format(track_image_path))
            with open(track_image_path, 'rb') as f:
                img = f.read()

            track_details = {
                "trackId": self.track_id,
                "width": track_params["WIDTH"],
                "height": track_params["HEIGHT"],
                "xOffset": track_params["X_OFFSET"],
                "yOffset": track_params["Z_OFFSET"],
                "margin": track_params["MARGIN"],
                'image': base64.b64encode(img).decode('utf-8'),
            }

            self.map_data = track_details
            self.margin_aligned = track_details['margin'] == 10
        
        except Exception as e:
            log("[trackdata] error reading map data")
            log(e)
            self.map_data = {}

    def read_section_params(self):
        """Read the section data from `sections.ini`. This expects to contain track-unique sections with names, not S123 data"""
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
        except Exception as e:
            log('[trackdata] error reading section data')
            log(e)   

