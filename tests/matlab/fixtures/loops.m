function [s, p, n_iter, v] = loops(n, x0)
% LOOPS For and while loops: sum of squares, odd factorial, Newton iteration.
%#type v: row
s = 0;
for k = 1:n
    s = s + k^2;            % sum of squares
end
p = 1;
for k = n:-2:1
    p = p * k;
end
% Newton iteration for sqrt(x0)
x = x0; n_iter = 0;
while abs(x*x - x0) > 1e-12 && n_iter < 50
    x = 0.5*(x + x0/x);
    n_iter = n_iter + 1;
    if n_iter > 100, break; end
end
v = zeros(1, n);
for k = 1:n
    if mod(k, 2) == 0
        continue
    end
    v(k) = k / 2 + x;
end
