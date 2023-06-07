from typing import Callable, Dict, Iterable, Optional, Tuple
from functools import wraps, lru_cache as cache
from unittest.mock import _Call, call
from itertools import chain
from concurrent.futures import ThreadPoolExecutor

import logging

logger = logging.getLogger(__name__)


def func_call_str(func: Callable, call_obj: _Call) -> str:
    '''
    Returns a concatentation of the func's module, name, and call
    Useful for logging purposes.
    '''
    return f'{func.__module__}.{func.__name__}, {call_obj}'


class ParallelPreFetch():
    '''
    Object to register functions and their calls for parallel prefetching, 
    using ThreadPoolExecutor
    the namespace is a useful way to pre-register additional calls
    to avoid issues with circular imports
    The default namespace is an empty str `''`.
    '''

    def __init__(self, namespaces: Optional[Dict[str,  Iterable[_Call]]] = None):
        self.funcs_map: Dict[Callable, Tuple[Iterable[_Call], str]] = {}
        self.namespaces = namespaces or {'': []}


    def register_func(self, calls: Iterable[_Call], namespace: str = '') -> Callable:
        '''
        Register and func, calls, and calls within its namespace for prefetching
        '''
        def decorator(func: Callable) -> Callable:
            cached_func = cache(func)
            # @cache
            @wraps(func)
            def wrapper(*args, **kwargs):
                description = func_call_str(func, call(*args, **kwargs))
                return_value = cached_func(*args, **kwargs)
                logger.info(f'Cache hits: {description}: {cached_func.cache_info()}')
                return return_value
            self.funcs_map[wrapper] = (calls, namespace)
            return wrapper
        return decorator


    def register_func_v2(self, calls: Iterable[_Call], namespace: str = '') -> Callable:
        '''
        Register and func, calls, and calls within its namespace for prefetching
        '''
        # def decorator(func: Callable) -> Callable:
        #     '''
        #     Decorator to register a func
        #     '''
        #     cached_func = cache(func)
        #     self.funcs_map[cached_func] = (calls, namespace)
        #     return cached_func
        # return decorator

        return self.register_func(calls, namespace)


    def run_all_async(self) -> ThreadPoolExecutor:
        '''
        Runs each of the funcs and their calls in parallel and asynchronously,
         returns the used ThreadPoolExecutor
        '''
        executor = ThreadPoolExecutor()
        for func, (calls, namespace) in self.funcs_map.items():
            for call_obj in chain(calls, self.namespaces[namespace]):
                description = func_call_str(func, call_obj)
                logger.info(f'Prefetch running: {description}')
                future = executor.submit(func, *call_obj.args, **call_obj.kwargs)
                future.add_done_callback(
                    lambda _: logger.info(f'Prefetch finished: {description}')
                )
        return executor


    def run_all_until_complete(self) -> None:
        '''
        Runs each of the funcs and their calls in parallel and asynchronously,
         blocks until all are completed
        '''
        executor = self.run_all_async()
        executor.shutdown()


pre_fetcher = ParallelPreFetch()
