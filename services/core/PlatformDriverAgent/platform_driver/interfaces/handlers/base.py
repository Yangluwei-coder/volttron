from abc import ABC, abstractmethod

class HomeAssistantDomainHandler(ABC):
    def __init__(self, config=None):
        self.config = config

    @abstractmethod
    def validate(self, entity_point, value):
        """subclass must implement validation logic for the value to be set on the entity point"""
        pass

    @abstractmethod
    def build_operation(self, entity_id, entity_point, value):
        pass