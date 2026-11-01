"""Perception layer: object sensor model (range, field of view, occlusion, noise, latency) and ground truth."""

from ..framework.plugins import component
from .sensor import GroundTruthPerception, ObjectSensor, ObjectSensorParams, visibility

component(ObjectSensor)
component(GroundTruthPerception)

__all__ = ["ObjectSensor", "ObjectSensorParams", "GroundTruthPerception", "visibility"]
