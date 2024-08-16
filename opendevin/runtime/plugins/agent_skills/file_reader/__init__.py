from ..utils.dependency import import_functions
from . import file_readers

import_functions(
    module=file_readers, function_names=file_readers.__all__, target_globals=globals()
)
__all__ = file_readers.__all__
