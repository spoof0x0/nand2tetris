


load HalfAdder.hdl,
compare-to HalfAdder.cmp,
output-list a b sum carry;

set a 0,
set b 0,
eval,
output;

set a 0,
set b 1,
eval,
output;

set a 1,
set b 0,
eval,
output;

set a 1,
set b 1,
eval,
output;