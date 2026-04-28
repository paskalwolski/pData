import configparser

from src.plogging import pLogger

log = pLogger(__name__).log


class ConfigParser:
    def load(self, path):
        parser = configparser.ConfigParser()
        parser.read(path)
        for section in parser.sections():
            setattr(self, section, dict(parser[section]))
        log("Config loaded from {}".format(path))


app_config = ConfigParser()
