from .base import HomeAssistantDomainHandler
<<<<<<< HEAD
=======
from .FanHandler import FanHandler  # noqa: F401
from .LightHandler import LightHandler
from .ClimateHandler import ClimateHandler
from .InputBooleanHandler import InputBooleanHandler
>>>>>>> 72e366971b55ac8eb3c9a8014386421bf5223c14

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
<<<<<<< HEAD
    return registry
=======
    return registry
>>>>>>> 72e366971b55ac8eb3c9a8014386421bf5223c14
