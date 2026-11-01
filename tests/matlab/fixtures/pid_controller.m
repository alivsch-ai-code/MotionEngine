function [u, integ_out] = pid_controller(r, y, kp, ki, kd, dt, u_min, u_max)
% PID_CONTROLLER Discrete PID controller with conditional integration
% (anti-windup); integrator and previous error are persistent states.
persistent integ e_prev
if isempty(integ)
    integ = 0;
    e_prev = 0;
end
e = r - y;                         % control error
d = (e - e_prev) / dt;             % backward difference of the error
u_unsat = kp*e + ki*integ + kd*d;  % PID control law
u = min(max(u_unsat, u_min), u_max);
if u == u_unsat                    % integrate only when not saturated
    integ = integ + e*dt;
end
e_prev = e;
integ_out = integ;
