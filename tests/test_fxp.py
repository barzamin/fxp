import pytest
from fxp import S, U, FxPTy, FxP, FxPOverflow
from fxp.num import _parse_format

def test_parse_format():
    for n in range(1, 32):
        for m in range(1, 32):
            for signed in [False, True]:
                signedness = 's' if signed else 'u'
                fmtstr = f'{n}.{m}{signedness}'

                assert _parse_format(fmtstr) == (n, m, signed)

def test_format_roundtrip():
    for n in range(1, 32):
        for m in range(1, 32):
            for signed in [False, True]:
                signedness = 's' if signed else 'u'
                fmtstr = f'{n}.{m}{signedness}'

                ty = FxPTy(fmtstr)
                assert repr(ty) == fmtstr

def test_basic():
    ty = S(1,31)
    zero = ty.zero()
    one = ty.one()
    half = ty.half()

    print(f'''\
        zero: {ty.zero()},
        one:  {ty.one()},
        1/2:  {ty.half()}
        ---
        most_positive: {ty.most_positive()}
        most_negative: {ty.most_negative()}''')

    # assert False

def test_impossible_to_negate_most_negative():
    with pytest.raises(FxPOverflow):
        S(1,31).most_negative().neg()

def test_possible_to_negate_most_positive():
    S(1,31).most_positive().neg()

def test_negation_busted_on_unsigned():
    with pytest.raises(TypeError):
        U(1,7).ulps(5).neg()
