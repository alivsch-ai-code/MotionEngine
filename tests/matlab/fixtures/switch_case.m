function y = switch_case(mode, x)
% SWITCH_CASE Mode selection with numeric switch/case/otherwise.
switch mode
    case 1
        y = x;
    case {2, 3}
        y = -x;
    case 4
        y = x^2;
    otherwise
        y = 0;
end
