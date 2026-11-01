"""Minimal dependency injection container.

    container = Container()
    container.register("trajectory_planner", lambda c: create_component("trajectory_planner/werling"))
    container.register_instance("vehicle", vehicle_config)
    planner = container.resolve("trajectory_planner")

Factories receive the container, so dependencies are resolved recursively. Singletons
are created once per container; scopes (child containers) override registrations,
e.g. for one batch run with a different controller.
"""

from __future__ import annotations


class Container:
    def __init__(self, parent=None):
        self.parent = parent
        self._factories = {}
        self._singletons = {}
        self._instances = {}
        self._resolving = set()

    def register(self, key, factory, singleton=True):
        self._factories[key] = (factory, singleton)
        self._singletons.pop(key, None)
        return self

    def register_instance(self, key, instance):
        self._instances[key] = instance
        return self

    def has(self, key):
        return key in self._instances or key in self._factories or (self.parent is not None and self.parent.has(key))

    def resolve(self, key):
        if key in self._instances:
            return self._instances[key]
        if key in self._singletons:
            return self._singletons[key]
        if key in self._factories:
            if key in self._resolving:
                raise RuntimeError(f"circular dependency while resolving '{key}'")
            factory, singleton = self._factories[key]
            self._resolving.add(key)
            try:
                obj = factory(self)
            finally:
                self._resolving.discard(key)
            if singleton:
                self._singletons[key] = obj
            return obj
        if self.parent is not None:
            return self.parent.resolve(key)
        raise KeyError(f"nothing registered for '{key}'")

    def scope(self):
        # child container: own registrations, falls back to this one
        return Container(parent=self)

    def keys(self):
        own = set(self._instances) | set(self._factories)
        return own | (self.parent.keys() if self.parent else set())
