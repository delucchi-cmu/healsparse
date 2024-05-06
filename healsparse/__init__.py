try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    from importlib_metadata import PackageNotFoundError, version

try:
    __version__ = version("healsparse")
except PackageNotFoundError:
    # package is not installed
    pass

from . import geom
from .cat_healsparse_files import cat_healsparse_files
from .geom import Box, Circle, Ellipse, Polygon, realize_geom
from .healSparseCoverage import HealSparseCoverage
from .healSparseMap import HealSparseMap
from .healSparseRandoms import make_uniform_randoms, make_uniform_randoms_fast
from .operations import (
    and_intersection,
    and_union,
    divide_intersection,
    floor_divide_intersection,
    max_intersection,
    max_union,
    min_intersection,
    min_union,
    or_intersection,
    or_union,
    product_intersection,
    product_union,
    sum_intersection,
    sum_union,
    ufunc_intersection,
    ufunc_union,
    xor_intersection,
    xor_union,
)
from .utils import WIDE_MASK
