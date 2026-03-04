from .base import HomeAssistantDomainHandler
from .FanHandler import FanHandler  # noqa: F401

def get_handler_registry(config=None):
    """
    get handler registry for home assistant domains
        - key: domain name, e.g. light, switch, input_boolean
    """
    registry = {}
    for cls in HomeAssistantDomainHandler.__subclasses__():
        # get domain key by removing 'Handler' suffix and converting to lowercase
        domain_key = cls.__name__.replace('Handler', '').lower()
        if domain_key == 'inputboolean':
            domain_key = 'input_boolean'
        
        registry[domain_key] = cls(config)
    return registry