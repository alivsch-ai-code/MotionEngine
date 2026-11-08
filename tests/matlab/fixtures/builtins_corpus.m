function [s, v, m] = builtins_corpus(a, b)
% BUILTINS_CORPUS Exercises numeric builtins; interpreter and generated Python must agree bitwise.
%#type a: double
%#type b: double
x = linspace(a, a + abs(b) + 1, 7);
y = [x(1) x(3) x(5)];
s = abs(b) + round(a) + sign(b) + mod(a, 3) + rem(b, 2) + atan2(a, b + 2);
s = s + floor(a) + ceil(b) + fix(a) + sqrt(abs(a)) + exp(-abs(b)) + log(abs(a) + 1);
s = s + log10(abs(b) + 1) + log2(abs(a) + 2) + hypot(a, b) + sin(a) + cos(b) + tan(a / 10);
s = s + asin(a / 10) + acos(b / 10) + atan(a) + sinh(a / 5) + cosh(b / 5) + tanh(a);
s = s + deg2rad(a) + rad2deg(b) / 1000 + wrapToPi(a * 3);
s = s + sum(x) + prod(y) / 100 + mean(x) + median(x) + std(x) + var(x);
s = s + max(x) + min(x) + numel(x) + length(y) + norm(y) + dot(y, y);
s = s + any(x > 100) + all(x >= a) + isempty(x) + isscalar(a);
s = s + sum(cumsum(y)) + sum(cumprod(y)) / 1000 + sum(diff(x)) + sum(sort(-y));
s = s + sum(fliplr(y)) + interp1(x, x .^ 2, a + 0.5);
s = s + polyval([1 2 3], a) + xor(a > 0, b > 0) + double(isfinite(a)) + double(isnan(b));
M = [a b; b - 1 a + 2];
m = det(M) + trace(M) + sum(sum(inv(M + 5 * eye(2)))) + sum(sum(eye(2) + ones(2) + zeros(2)));
m = m + sum(sum(repmat(y, 2, 1))) + sum(reshape(M, 1, 4));
m = m + sum(sum(M')) + sum(sum(M .* M)) + sum(sum(M ^ 2)) + sum(cross([1 0 0], [0 1 0]));
m = m + numel(size(M)) + sum(abs(flipud(M(:, 1))));
v = [s; m; hypot(s, m)];
end
