"""Component framework of the automated-driving platform (Clean Architecture core).

    types       signal data types exchanged between components (+ flat codecs for native nodes)
    component   Component base class: typed ports, parameters, version, documentation metadata
    layers      abstract layer contracts (Perception ... VehiclePlant)
    plugins     versioned plugin registry and component factory ("kind/name@version", "python:...", ...)
    container   dependency injection container
    context     RunContext handed to components (time step, seeds, vehicle, road, logger)
    knowledge   traceability decorators and documentation metadata (ComponentDoc)

Nothing in this package depends on the GUI, the runtime or concrete algorithms.
"""

from .component import Component, Port
from .context import RunContext
from .knowledge import ComponentDoc, trace
from .plugins import available_components, component, create_component, get_component

__all__ = ["Component", "Port", "RunContext", "ComponentDoc", "trace", "component", "create_component",
           "get_component", "available_components"]
