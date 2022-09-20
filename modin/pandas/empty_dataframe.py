import pandas

from modin.utils import try_cast_to_pandas

from .dataframe import DataFrame
from .series import Series


def decorate_all_functions(function_decorator):
    def decorator(cls):
        exclude_names = ["__init__", "_default_to_pandas", "_to_pandas"]
        for name, obj in vars(cls).items():
            if name not in exclude_names and callable(obj):
                print(name, "added")
                setattr(cls, name, function_decorator(obj, name))
            else:
                print(name, "not added")
        return cls

    return decorator


from functools import wraps


def empty_dataframe_default(func, name):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        return self._default_to_pandas(func, *args, **kwargs)

    return wrapper


@decorate_all_functions(empty_dataframe_default)
class EmptyDataFrame(DataFrame):
    """
    Special Modin class to handle empty dataframe operations.
    Inherit from DataFrame class (__repr__ method would be the same).
    All operations will be defaulted to pandas.
    """

    def __init__(
        self,
        data=None,
        index=None,
        columns=None,
        dtype=None,
        copy=None,
        query_compiler=None,
    ):
        # Initialize parameters according to expected parameters for pandas
        # Ex. Series object in pandas has attribute codes
        # May have to add specific index and dtype parameters (see concat below)
        if query_compiler is None:
            self._dataframe = pandas.DataFrame(data, index, columns, dtype, copy)
        else:
            self._dataframe = query_compiler.to_pandas()

    def default_to_pandas(self, pandas_op, *args, **kwargs):
        args = try_cast_to_pandas(args)
        kwargs = try_cast_to_pandas(kwargs)

        result = pandas_op(self._dataframe, *args, **kwargs)
        if isinstance(result, pandas.Series) and not result.empty:
            return Series(result)
        if isinstance(result, pandas.DataFrame) and not result.empty:
            return DataFrame(result)

        return result

    def _to_pandas(self):
        return self._dataframe
