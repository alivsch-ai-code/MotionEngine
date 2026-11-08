"""Multilayer perceptron in NumPy: y = W_L tanh(... tanh(W_1 x + b_1) ...) + b_L.

Inputs and outputs are standardized with the training statistics. Training minimizes the mean
squared error of the standardized outputs with Adam (Kingma & Ba 2015) on mini-batches, with
Xavier initialization (Glorot & Bengio 2010) and early stopping on a validation split.
"""

from __future__ import annotations

import io
import json

import numpy as np


class MLP:
    def __init__(self, n_in, n_out, hidden=(64, 64), seed=0):
        rng = np.random.default_rng(seed)
        sizes = [n_in, *hidden, n_out]
        self.W = [rng.normal(0.0, np.sqrt(2.0 / (a + b)), size=(a, b)) for a, b in zip(sizes[:-1], sizes[1:])]
        self.b = [np.zeros(b) for b in sizes[1:]]
        self.x_mean, self.x_std = np.zeros(n_in), np.ones(n_in)
        self.y_mean, self.y_std = np.zeros(n_out), np.ones(n_out)
        self.hidden = tuple(hidden)

    # ------------------------------------------------------------------ inference
    def _forward(self, xn):
        acts = [xn]
        h = xn
        for k, (W, b) in enumerate(zip(self.W, self.b)):
            z = h @ W + b
            h = np.tanh(z) if k < len(self.W) - 1 else z
            acts.append(h)
        return acts

    def predict(self, x):
        x = np.atleast_2d(np.asarray(x, dtype=float))
        out = self._forward((x - self.x_mean) / self.x_std)[-1]
        return out * self.y_std + self.y_mean

    # ------------------------------------------------------------------ training
    def fit(self, x, y, epochs=200, batch=256, lr=2e-3, val_split=0.15, patience=25, seed=0, progress=None,
            should_stop=None):
        x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
        rng = np.random.default_rng(seed)
        idx = rng.permutation(len(x))
        n_val = max(int(len(x) * val_split), 1)
        val, tr = idx[:n_val], idx[n_val:]
        self.x_mean, self.x_std = x[tr].mean(0), x[tr].std(0) + 1e-12
        self.y_mean, self.y_std = y[tr].mean(0), y[tr].std(0) + 1e-12
        xn, yn = (x - self.x_mean) / self.x_std, (y - self.y_mean) / self.y_std
        params = self.W + self.b
        m = [np.zeros_like(p) for p in params]
        v = [np.zeros_like(p) for p in params]
        beta1, beta2, eps, step = 0.9, 0.999, 1e-8, 0
        history, best, best_state, wait = [], np.inf, None, 0
        for epoch in range(epochs):
            order = rng.permutation(tr)
            for k in range(0, len(order), batch):
                bi = order[k:k + batch]
                grads = self._gradients(xn[bi], yn[bi])
                step += 1
                for p, g, mi, vi in zip(params, grads, m, v):
                    mi *= beta1
                    mi += (1 - beta1) * g
                    vi *= beta2
                    vi += (1 - beta2) * g * g
                    p -= lr * (mi / (1 - beta1 ** step)) / (np.sqrt(vi / (1 - beta2 ** step)) + eps)
            train_loss = float(np.mean((self._forward(xn[tr])[-1] - yn[tr]) ** 2))
            val_loss = float(np.mean((self._forward(xn[val])[-1] - yn[val]) ** 2))
            history.append({"epoch": epoch + 1, "train": train_loss, "val": val_loss})
            if progress:
                progress(epoch + 1, epochs, train_loss, val_loss)
            if val_loss < best - 1e-9:
                best, wait = val_loss, 0
                best_state = ([w.copy() for w in self.W], [b.copy() for b in self.b])
            else:
                wait += 1
                if wait >= patience:
                    break
            if should_stop and should_stop():
                break
        if best_state is not None:
            self.W, self.b = best_state
        return history

    def _gradients(self, xb, yb):
        acts = self._forward(xb)
        n = len(xb)
        delta = 2.0 * (acts[-1] - yb) / (n * yb.shape[1])
        gW, gb = [None] * len(self.W), [None] * len(self.b)
        for k in range(len(self.W) - 1, -1, -1):
            gW[k] = acts[k].T @ delta
            gb[k] = delta.sum(0)
            if k:
                delta = (delta @ self.W[k].T) * (1.0 - acts[k] ** 2)
        return gW + gb

    # ------------------------------------------------------------------ persistence
    def to_bytes(self):
        buf = io.BytesIO()
        arrays = {f"W{i}": w for i, w in enumerate(self.W)} | {f"b{i}": b for i, b in enumerate(self.b)}
        np.savez(buf, x_mean=self.x_mean, x_std=self.x_std, y_mean=self.y_mean, y_std=self.y_std,
                 meta=np.array(json.dumps({"hidden": list(self.hidden), "layers": len(self.W)})), **arrays)
        return buf.getvalue()

    @classmethod
    def from_bytes(cls, data):
        with np.load(io.BytesIO(data), allow_pickle=False) as z:
            meta = json.loads(str(z["meta"]))
            n = meta["layers"]
            W = [z[f"W{i}"] for i in range(n)]
            net = cls(W[0].shape[0], W[-1].shape[1], tuple(meta["hidden"]))
            net.W, net.b = W, [z[f"b{i}"] for i in range(n)]
            net.x_mean, net.x_std, net.y_mean, net.y_std = z["x_mean"], z["x_std"], z["y_mean"], z["y_std"]
        return net
