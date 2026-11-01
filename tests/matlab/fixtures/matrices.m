function [y, nrm, tr, c] = matrices(x, theta)
% MATRICES Rotation of a 2-D column vector, norms and matrix products.
%#type x: vector(2)
R = [cos(theta), -sin(theta); sin(theta) cos(theta)];   % rotation matrix
y = R * x;
A = R' * R + 0.5 * eye(2);
tr = A(1,1) + A(2,2);
nrm = norm(y) + sum(abs(x)) + numel(x);
c = [y; tr];
c(end) = c(end) * 2;
c(1) = c(1) - y(2) .* x(1);
