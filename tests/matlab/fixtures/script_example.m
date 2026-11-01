% SCRIPT_EXAMPLE Script with a local function, block comment and printing.
%{
  This block comment is ignored by the parser.
  %{ nested %}
%}
gain = 2;
vals = [1, 2, ...
        3, 4];
total = 0;
for v = vals
    total = total + scale(v, gain);
end
fprintf('total = %d\n', total);

function y = scale(x, k)
    y = k * x;
end
