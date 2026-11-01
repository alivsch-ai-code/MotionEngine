function u = pure_feedback(r, y, y_dot, kp, kd, u_max)
% PURE_FEEDBACK PD controller with pure feedback (no feedforward).
e = r - y;                    % control error
u = kp*e - kd*y_dot;          % feedback only
u = max(min(u, u_max), -u_max);
