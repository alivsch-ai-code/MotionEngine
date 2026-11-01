function [r, s] = subfunctions(a, b)
% SUBFUNCTIONS Main function calling local functions (end-terminated file).
r = add_scaled(a, b, 2);
s = sat(r, -1, 1) + helper2(a);
end

function y = add_scaled(a, b, k)
% weighted sum
y = a + k*b;
end

function y = sat(x, lo, hi)
% saturation
y = min(max(x, lo), hi);
end

function y = helper2(x)
y = add_scaled(x, x, 0.5);
end
