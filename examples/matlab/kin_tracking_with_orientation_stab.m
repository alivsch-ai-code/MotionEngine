% KIN_TRACKING_WITH_ORIENTATION_STAB Lyapunov-based tracking controller with
% orientation stabilization for the kinematic single-track model
% (Werling 2011, Sec. 4.2.3, Theorem 4).
%
% Transcribed from: M. Werling, "Ein neues Konzept fuer die Trajektorien-
% generierung und -stabilisierung in zeitkritischen Verkehrsszenarien",
% KIT Scientific Publishing, 2011, Appendix A.5 ("Beispielprogramm: Regelung
% des kinematischen Einspurmodells"). Code and comments follow the printed
% listing; the helper normalize_angle is used there but not printed and is
% added as a subfunction at the end of this file.
function [delta_dot, F_l] = kin_tracking_with_orientation_stab( ...
    y1_d, y2_d, theta_d, kappa_d, kappa_d_dot, v_d, v_d_dot, varsigma, ...
    y1, y2, psi, v, delta, ...
    l_v, l_h, m, J, gam,...
    k1, k2, k3, k4 );
% y1_d, ..., varsigma: desired values in rear axle coordinates
% y1, ..., delta: measured states
% l_v, ..., gam: vehicular parameters
% k1, ..., k4: control design parameters
l = l_v + l_h; % wheel base
% State transformations
e_t = ( y1-y1_d ) * cos(theta_d) + ( y2-y2_d ) * sin(theta_d); % (4.9)
e_n = ( y1-y1_d ) * (-sin(theta_d)) + ( y2-y2_d ) * cos(theta_d); % (4.9)
e_psi = normalize_angle( psi - theta_d ); % Normalize to -pi..pi (4.9)
kappa_delta = tan(delta)/l; % (4.9)
% Transformed time derivatives
e_t_dot = v *cos(e_psi) - v_d *( 1- kappa_d*e_n ); % (4.10a)
e_n_dot = v *sin(e_psi) - v_d *kappa_d*e_t; % (4.10b)
e_psi_dot = v*kappa_delta - v_d*kappa_d; % (4.10c)
% Taylor approximations for control law
cos_approx = -1/2 *e_psi + 1/24*e_psi^3 - 1/720*e_psi^5; % (A.10)
sin_approx = 1 - 1/6*e_psi^2 + 1/120*e_psi^4 - 1/5040*e_psi^6; % (A.11)
dcos_approx = -0.5 + 1/8*e_psi^2 - 1/144*e_psi^4 + 1/5760*e_psi^6; % (A.12)
dsin_approx = -1/3*e_psi + 1/30*e_psi^3 - 1/840*e_psi^5; % (A.13)
% Fictitious and virtual control laws
xi1 = kappa_d - k1*( e_t*cos_approx + e_n*sin_approx ) ...
    - varsigma*k2*e_psi; % (4.11)
e_v = v - v_d;
w2 = v_d_dot - k1*e_t - k3*e_v + varsigma*k2*e_psi^2 ...
    - e_psi * kappa_d;
% (4.12)
% Back-stepping
xi1_dot = kappa_d_dot - k1*( e_t_dot*cos_approx ...
    + e_t*e_psi_dot*dcos_approx + e_n_dot*sin_approx ...
    + e_n*e_psi_dot*dsin_approx) - varsigma*k2*e_psi_dot; % (4.18)
e_delta = kappa_delta - xi1; % (4.16)
w1 = -e_psi*v + xi1_dot - k4*e_delta; % (4.17)
% Lateral input resubstitution
u1 = l*w1*cos(delta)^2; % (4.15)
% Longitudinal input resubstitution
M = (m*l_h^2 + J)/l^2;
u2 = 1/(1+gam*(1/cos(delta) - 1))*(w2*(m+M*tan(delta)^2) ...
    + 2*M*v*tan(delta)/cos(delta)^2*u1 ); % (4.7)
% Output results
delta_dot = u1;
F_l = u2;


function a = normalize_angle(a)
% Wrap an angle to the interval [-pi, pi) (not printed in Werling 2011, A.5).
a = mod(a + pi, 2*pi) - pi;
