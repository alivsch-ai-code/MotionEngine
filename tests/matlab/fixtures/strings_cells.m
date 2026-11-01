function [msg, n, s] = strings_cells(name, x)
% STRINGS_CELLS Strings, cells, structs and anonymous functions (interpreter only).
c = {1, 'two', [3 4]};
n = numel(c) + numel(c{3});
s.name = name;
s.value = x * 2;
msg = sprintf('%s: %.2f', s.name, s.value);
f = @(t) t.^2 + 1;
n = n + f(2);
