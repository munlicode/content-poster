# interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict


class IDataSource(ABC):
    """Interface for any data source."""

    @abstractmethod
    def get_data(self) -> List[Dict]:
        pass


class IProcessor(ABC):
    """Interface for any data processor."""

    @abstractmethod
    def process(self, data: List[Dict]) -> List[Dict]:
        pass


class IDestination(ABC):
    """Interface for any data destination."""

    @abstractmethod
    def post(self, content: Dict) -> bool:
        pass
