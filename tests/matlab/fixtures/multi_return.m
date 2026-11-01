function [mn, mx, idx, avg, q] = multi_return(v)
% MULTI_RETURN Statistics of a vector with multiple outputs.
%#type v: vector(5)
[mx, idx] = max(v);
mn = min(v);
avg = mean(v);
[q, ~] = divmod(mx, 3);

function [q, r] = divmod(a, b)
% integer division with remainder
q = floor(a/b);
r = a - q*b;
