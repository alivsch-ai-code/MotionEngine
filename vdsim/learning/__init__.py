"""Neural networks in MotionEngine: train a surrogate of the vehicle dynamics or connect an external model.

mlp        NumPy multilayer perceptron (tanh, Adam, standardization, early stopping) - no ML framework needed
dataset    supervised data from a physics model (Monte Carlo over the driving envelope)
backends   trained MLP, ONNX file (optional onnxruntime), HTTP endpoint
vehicle    NeuralVehicleModel: exact planar kinematics + learned accelerations, usable in every simulation
store      model registry on disk (MOTIONENGINE_MODEL_DIR)
training   train / evaluate pipeline with metrics against the physics model (offline and closed loop)
trajectory learned trajectory planner: imitation of the Werling planner, proposal + verified local search
"""

from .backends import HTTPBackend, MLPBackend, ONNXBackend, load_backend
from .dataset import FEATURES, TARGETS, sample_dataset
from .mlp import MLP
from .store import ModelStore
from .training import evaluate_closed_loop, train_surrogate
from .trajectory import LearnedPlanner, compare_closed_loop, evaluate_planner, sample_situation, train_planner
from .vehicle import NeuralVehicleModel, register_neural_model

__all__ = [
    "MLP",
    "MLPBackend",
    "ONNXBackend",
    "HTTPBackend",
    "load_backend",
    "FEATURES",
    "TARGETS",
    "sample_dataset",
    "ModelStore",
    "train_surrogate",
    "evaluate_closed_loop",
    "NeuralVehicleModel",
    "register_neural_model",
    "LearnedPlanner",
    "train_planner",
    "evaluate_planner",
    "compare_closed_loop",
    "sample_situation",
]
