import abc
from typing import Dict, List, Optional, Union

from jam.ir.document_store import base


class IR(abc.ABC):
    def __init__(self, store: base.BaseDocStore) -> None:
        self.store = store

    @abc.abstractmethod
    def retrieve_top_k(
        self, query_batch: List[Dict], index: Optional[str] = "document", top_k: Optional[int] = 5, **kwargs
    ) -> List[Union[Dict, base.Document]]:
        pass
