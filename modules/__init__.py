import pathlib
from pkgutil import ModuleInfo, iter_modules

_ext: list[ModuleInfo] = []
_ext.extend(
    [
        module
        for module in iter_modules(__path__, prefix=__package__ + ".")
        if not module.name.rsplit(".")[-1].startswith("_")
    ]
)

private_path = pathlib.Path(__package__ + "/private")
if private_path.exists():
    _ext.extend(
        [
            module
            for module in iter_modules([str(private_path.absolute())], prefix=__package__ + ".private.")
            if not module.name.rsplit(".")[-1].startswith("_")
        ]
    )


EXTENSIONS = _ext
