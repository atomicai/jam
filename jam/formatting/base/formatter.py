import abc
import pathlib
from typing import Dict, Iterable, Union


class BaseFormatter(abc.ABC):
    @abc.abstractmethod
    def prepare(self, **kwargs):
        pass

    @abc.abstractmethod
    def format(self, data: Iterable[Dict], **kwargs) -> Iterable[Dict]:
        pass

    @abc.abstractmethod
    def save(self, save_dir: Union[pathlib.Path, str], filename: str = None, ext: str = ".json", **kwargs):
        pass
