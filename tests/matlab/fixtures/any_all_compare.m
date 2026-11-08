function [p, q, r] = any_all_compare(v, c)
% ANY_ALL_COMPARE Regression: any/all/logical over a comparison must not become a chained comparison.
%#type v: vector(3)
%#type c: double
p = any(v > c);
q = all(v >= c);
r = sum(logical(v > c));
end
