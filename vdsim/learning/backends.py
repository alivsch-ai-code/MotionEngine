"""Inference backends with one interface: predict(x: (n, n_in)) -> (n, n_out).

    MLPBackend   network trained in MotionEngine (vdsim.learning.mlp)
    ONNXBackend  any framework exported to ONNX (PyTorch, TensorFlow, JAX, ...); needs `onnxruntime`
    HTTPBackend  model served elsewhere: POST {"inputs": [[...], ...]} -> {"outputs": [[...], ...]}
"""

from __future__ import annotations

import json
import urllib.request

import numpy as np

from .mlp import MLP


class MLPBackend:
    kind = "mlp"

    def __init__(self, net):
        self.net = net

    def predict(self, x):
        return self.net.predict(x)


class ONNXBackend:
    kind = "onnx"

    def __init__(self, data):
        try:
            import onnxruntime as ort
        except ImportError as exc:  # optional dependency
            raise RuntimeError("ONNX models need the optional package onnxruntime (pip install onnxruntime)") from exc
        self.session = ort.InferenceSession(data, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    def predict(self, x):
        x = np.atleast_2d(np.asarray(x, dtype=np.float32))
        return np.asarray(self.session.run(None, {self.input_name: x})[0], dtype=float)


class HTTPBackend:
    kind = "http"

    def __init__(self, url, timeout=2.0, headers=None):
        self.url, self.timeout, self.headers = url, timeout, dict(headers or {})

    def predict(self, x):
        body = json.dumps({"inputs": np.atleast_2d(x).tolist()}).encode()
        req = urllib.request.Request(self.url, data=body, method="POST",
                                     headers={"Content-Type": "application/json", **self.headers})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 (URL checked by the store)
            out = json.loads(resp.read())["outputs"]
        return np.atleast_2d(np.asarray(out, dtype=float))


def load_backend(meta, blob=None):
    kind = meta["backend"]
    if kind == "mlp":
        return MLPBackend(MLP.from_bytes(blob))
    if kind == "onnx":
        return ONNXBackend(blob)
    if kind == "http":
        return HTTPBackend(meta["url"], meta.get("timeout", 2.0))
    raise ValueError(f"unknown backend '{kind}'")
