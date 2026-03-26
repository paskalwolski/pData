import ac

# TODO: Turn this into a class that gets init'ed with the module name
# [pData | {module_name}] {function_name}: {log}
def log(text: str, *args):
    ac.log("[pData] {}".format(text))