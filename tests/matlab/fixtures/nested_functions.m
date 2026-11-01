function y = nested_functions(x)
% NESTED_FUNCTIONS Nested function sharing a variable with its parent.
acc = 0;
add(x);
add(2*x);
y = acc;
    function add(v)
        acc = acc + v;
    end
end
