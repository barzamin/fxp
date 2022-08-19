from __future__ import annotations
import re
from typing import overload

class FxPOverflow(Exception):
    ...

FORMAT_RE = re.compile(r'^(\d+).(\d+)(s|u)$')
def _parse_format(fmt):
    if m := FORMAT_RE.match(fmt):
        n_integral, n_fractional, signedness = m.groups()
        n_integral = int(n_integral)
        n_fractional = int(n_fractional)

        if signedness == 'u':
            signed = False
        elif signedness == 's':
            signed = True
        else:
            raise Exception('unreachable!')

        return (n_integral, n_fractional, signed)

    else:
        raise ValueError('invalid format: FxP formats are of the form <n>.<m>(u|s)')

class FxPTy:
    def __init__(self, fmtstr: str = None, /, integral: int = None, fractional: int = None, signed: bool = False):
        if fmtstr is not None:
            if not isinstance(fmtstr, str):
                raise ValueError('fmtstr must be a `str`')

            self.integral, self.fractional, self.signed = _parse_format(fmtstr)
        else:
            self.integral = integral
            self.fractional = fractional
            self.signed = signed

        # todo: determine semantics
        assert self.integral >= 0
        assert self.fractional >= 0

        self._width = self.fractional + self.integral
        self._scale = 1 << self.fractional

        if self.signed:
            self._most_positive_ulps = (1 << (self.width-1)) - 1
            self._most_negative_ulps = -(1 << (self.width -1))
        else:
            self._most_positive_ulps = (1 << (self.width)) - 1
            self._most_negative_ulps = 0

    @property
    def width(self) -> int:
        return self._width

    @property
    def scale(self) -> int:
        return self._scale

    @property
    def ulp_size(self) -> float:
        return 1/self._scale

    def ulp(self) -> FxP:
        return FxP(1, fmt=self)

    def ulps(self, n: int) -> FxP:
        return FxP(n, fmt=self)

    def zero(self) -> FxP:
        return self.ulps(0)

    def one(self) -> FxP:
        return self.ulps(1 << self.fractional)

    def half(self) -> FxP:
        return self.ulps(1 << (self.fractional - 1))

    def most_positive(self) -> FxP:
        return self.ulps(self._most_positive_ulps)

    def most_negative(self) -> FxP:
        return self.ulps(self._most_negative_ulps)

    def representable(self, ulps: int) -> bool:
        return ulps >= self._most_negative_ulps and ulps <= self._most_positive_ulps


    def __repr__(self) -> str:
        return f"{self.integral}.{self.fractional}{'s' if self.signed else 'u'}"

    def desc(self) -> str:
        return f'''\
width: {self.width}, composed of {self.integral}.{self.fractional}
scale: {self.scale}
ulp size: {self.ulp_size}'''

class U(FxPTy):
    def __init__(self, /, integral: int = None, fractional: int = None):
        super().__init__(integral=integral, fractional=fractional, signed=False)

class S(FxPTy):
    def __init__(self, /, integral=None, fractional=None):
        super().__init__(integral=integral, fractional=fractional, signed=True)

class FxP:
    def __init__(self, ulps: int, fmt: FxPTy):
        self.ulps = ulps
        self.fmt = fmt

    def __repr__(self) -> str:
        return f'<FxP/{self.fmt!r} #{self.ulps} ≈ {self.asfloat()}>'

    @overload
    def astype(self, dtype: int) -> int: ...
    @overload
    def astype(self, dtype: float) -> float: ...

    def astype(self, dtype):
        if dtype is float:
            return self.ulps / self.fmt.scale
        elif dtype is int:
            # TODO(moon): rounding?
            return self.ulps // self.fmt._scale
        else:
            raise TypeError(f'cannot convert a FxP to {dtype}')

    def asfloat(self) -> float:
        return self.astype(float)
    def asint(self) -> int:
        return self.astype(int)

    def neg(self) -> FxP:
        if not self.fmt.signed:
            raise TypeError('cannot negate an unsigned type')

        if not self.fmt.representable(ulps := -self.ulps):
            raise FxPOverflow(f'negating {self} puts the result out of bounds for {self.fmt}')

        return FxP(-ulps, self.fmt)
