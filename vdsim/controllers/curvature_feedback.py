"""Feedback correction: estimates the curvature error and corrects the desired curvature."""


class CurvatureCorrection:
    # Estimates the factor g = k_measured / k_expected and sends k_des / g.
    # k_expected is the sent curvature passed through a model of the latency chain,
    # so that commanded and measured curvature are aligned in time.
    # The estimate is a sliding least-squares fit and is frozen while there is
    # hardly any curvature (nothing to learn from).
    def __init__(self, dt, time_constant=0.5, min_curvature=3e-5, gain_limits=(0.5, 2.0)):
        self.alpha = dt / time_constant
        self.min_energy = min_curvature**2
        self.gain_limits = gain_limits
        self.num = 0.0
        self.den = 0.0
        self.gain = 1.0

    def update(self, k_expected, k_meas):
        self.num += self.alpha * (k_expected * k_meas - self.num)
        self.den += self.alpha * (k_expected**2 - self.den)
        if self.den > self.min_energy:
            low, high = self.gain_limits
            self.gain = min(max(self.num / self.den, low), high)
        return self.gain

    def correct(self, k_des):
        return k_des / self.gain
