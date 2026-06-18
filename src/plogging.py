import ac
import datetime


def _ts():
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:10]


# TODO: Turn this into a class that gets init'ed with the module name
# [pData | {module_name}] {function_name}: {log}
def log(text, *args):
    ac.log("[pData] {}".format(text))


class pLogger:
    def __init__(self, module_name):
        self.module = module_name

    def log(self, *args):
        ac.log("[pData | {} | {}] | {}".format(_ts(), self.module, " | ".join([str(a) for a in list(args)])))

    def worker_log(self, *args):
        ac.log(
            "[pData | {} | worker | {}] | {}".format(_ts(), self.module, " | ".join([str(a) for a in list(args)]))
        )
