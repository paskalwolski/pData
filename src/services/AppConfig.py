import configparser

from src.plogging import pLogger

log = pLogger(__name__).log


class ConfigParser:
    def load(self, path):
        parser = configparser.ConfigParser()
        parser.read(path)
        for section in parser.sections():
            opts = parser[section]
            for opt, val in opts.items():
                if val.startswith(";"):
                    continue
                input_val = val.split(";")[0]
                setattr(self, "{}.{}".format(section, opt).lower(), input_val)
                log("CONFIG | {}.{} {}".format(section, opt, input_val))
        log("Config loaded from {}".format(path))

    def __getitem__(self, key):
        return getattr(self, key.lower() if isinstance(key, str) else key, None)


app_config = ConfigParser()
