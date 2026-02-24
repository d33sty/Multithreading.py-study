from collections.abc import Callable
from typing import Any

# импортируйте необходимое


class ConcurrentExecutor:
    ...

    def concurrent_run(self, func: Callable) -> Callable: ...

    def get_results(self, timeout=None) -> dict[str, Any]: ...
