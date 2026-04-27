import ac


# TODO: Turn this into a class that gets init'ed with the module name
# [pData | {module_name}] {function_name}: {log}
def log(text: str, *args):
    ac.log("[pData] {}".format(text))


class pLogger:
    def __init__(self, module_name):
        self.module = module_name

    def log(self, *args):
        ac.log("[pData | {}] | {}".format(self.module, " | ".join(list(args))))

    def worker_log(self, *args):
        self.log(
            "[pData | worker | {}] | {}".format(self.module, " | ".join(list(args)))
        )
