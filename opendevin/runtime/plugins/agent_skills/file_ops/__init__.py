from ..utils.dependency import import_functions
from .file_ops import __all__

import_functions(package=__name__ + '.file_ops', function_names=__all__)
