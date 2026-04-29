import os
import zipfile

INCLUDE_FILES = [
    "pData.py",
    "readme.md",
    "pData.ini",
    "pData_defaults.ini",
]

INCLUDE_DIRS = [
    "src",
    "deps",
]

ZIP_PREFIX = "apps/python/pData"
OUTPUT = "pData.zip"


def build():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output = os.path.join(root, OUTPUT)

    if os.path.exists(output):
        os.remove(output)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in INCLUDE_FILES:
            src = os.path.join(root, filename)
            arc = "{}/{}".format(ZIP_PREFIX, filename)
            zf.write(src, arc)
            print("  {}".format(arc))

        for dirname in INCLUDE_DIRS:
            src_dir = os.path.join(root, dirname)
            for dirpath, dirnames, filenames in os.walk(src_dir):
                dirnames[:] = [d for d in dirnames if d != "__pycache__"]
                for filename in filenames:
                    if filename.endswith(".pyc"):
                        continue
                    filepath = os.path.join(dirpath, filename)
                    rel = os.path.relpath(filepath, root).replace("\\", "/")
                    arc = "{}/{}".format(ZIP_PREFIX, rel)
                    zf.write(filepath, arc)
            print("  {}/{}/".format(ZIP_PREFIX, dirname))

    print("Built {}".format(output))


if __name__ == "__main__":
    build()
