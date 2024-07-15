if __package__ is None or __package__ == '':
    from search.search_manage import SearchManager
else:
    from .search.search_manage import SearchManager

__all__ = ['SearchManager']