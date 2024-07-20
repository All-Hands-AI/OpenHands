if __package__ is None or __package__ == '':
    from manager import SearchManager
else:
    from .manager import SearchManager

__all__ = ['SearchManager']
