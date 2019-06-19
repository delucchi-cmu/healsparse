import numpy as np
import healsparse


def test_circle_smoke():
    """
    just test we can make a circle and a map from it
    """
    ra, dec = 200.0, 0.0
    radius = 30.0/3600.0
    nside = 2**17
    circle = healsparse.Circle(
        ra=ra,
        dec=dec,
        radius=radius,
        value=2**4,
    )
    pixels = circle.get_pixels(nside=nside)  # noqa

    smap = circle.get_map(nside=nside, dtype=np.int16)  # noqa


def atbound(longitude, minval, maxval):
    w, = np.where(longitude < minval)
    while w.size > 0:
        longitude[w] += 360.0
        w, = np.where(longitude < minval)

    w, = np.where(longitude > maxval)
    while w.size > 0:
        longitude[w] -= 360.0
        w, = np.where(longitude > maxval)

    return


def _randcap(rng, nrand, ra, dec, rad, get_radius=False):
    """
    Generate random points in a sherical cap

    parameters
    ----------

    nrand:
        The number of random points
    ra,dec:
        The center of the cap in degrees.  The ra should be within [0,360) and
        dec from [-90,90]
    rad:
        radius of the cap, same units as ra,dec

    get_radius: bool, optional
        if true, return radius of each point in radians
    """
    # generate uniformly in r**2
    rand_r = rng.uniform(size=nrand)
    rand_r = np.sqrt(rand_r)*rad

    # put in degrees
    np.deg2rad(rand_r, rand_r)

    # generate position angle uniformly 0,2*PI
    rand_posangle = rng.uniform(nrand)*2*np.pi

    theta = np.array(dec, dtype='f8', ndmin=1, copy=True)
    phi = np.array(ra, dtype='f8', ndmin=1, copy=True)
    theta += 90

    np.deg2rad(theta, theta)
    np.deg2rad(phi, phi)

    sintheta = np.sin(theta)
    costheta = np.cos(theta)
    # sinphi = np.sin(phi)
    # cosphi = np.cos(phi)

    sinr = np.sin(rand_r)
    cosr = np.cos(rand_r)

    cospsi = np.cos(rand_posangle)
    costheta2 = costheta*cosr + sintheta*sinr*cospsi

    np.clip(costheta2, -1, 1, costheta2)

    # gives [0,pi)
    theta2 = np.arccos(costheta2)
    sintheta2 = np.sin(theta2)

    cosDphi = (cosr - costheta*costheta2)/(sintheta*sintheta2)

    np.clip(cosDphi, -1, 1, cosDphi)
    Dphi = np.arccos(cosDphi)

    # note fancy usage of where
    phi2 = np.where(rand_posangle > np.pi, phi+Dphi, phi-Dphi)

    np.rad2deg(phi2, phi2)
    np.rad2deg(theta2, theta2)
    rand_ra = phi2
    rand_dec = theta2-90.0

    atbound(rand_ra, 0.0, 360.0)

    if get_radius:
        np.rad2deg(rand_r, rand_r)
        return rand_ra, rand_dec, rand_r
    else:
        return rand_ra, rand_dec


def test_circle_values():
    """
    make sure we get out the value we used for the map

    Note however that we do not use inclusive intersections, we we will test
    values from a slightly smaller circle
    """

    rng = np.random.RandomState(7812)
    nside = 2**17

    ra, dec = 200.0, 0.0
    radius = 30.0/3600.0
    circle = healsparse.Circle(
        ra=ra,
        dec=dec,
        radius=radius,
        value=2**4,
    )

    smap = circle.get_map(nside=nside, dtype=np.int16)

    # test points we expect to be inside
    smallrad = radius*0.95
    nrand = 10000
    rra, rdec = _randcap(rng, nrand, ra, dec, smallrad)

    vals = smap.getValueRaDec(rra, rdec)  # noqa

    assert np.all(vals == circle.value)

    # test points we expect to be outside
    bigrad = radius*2
    nrand = 10000
    rra, rdec, rrand = _randcap(
        rng,
        nrand,
        ra,
        dec,
        bigrad,
        get_radius=True,
    )
    w, = np.where(rrand > 1.1*radius)

    vals = smap.getValueRaDec(rra[w], rdec[w])  # noqa

    assert np.all(vals == 0)


def test_polygon_smoke():
    """
    just test we can make a polygon and a map from it
    """
    nside = 2**15

    # counter clockwise
    ra = [200.0, 200.2, 200.3, 200.2, 200.1]
    dec = [0.0,     0.1,   0.2,   0.25, 0.13]
    poly = healsparse.Polygon(
        ra=ra,
        dec=dec,
        value=64,
    )

    smap = poly.get_map(nside=nside, dtype=np.int16)

    ra = np.array([200.1, 200.15])
    dec = np.array([0.05, 0.015])
    vals = smap.getValueRaDec(ra, dec)  # noqa


def test_polygon_values():
    """
    make sure we get out the value we used for the map

    Use a box so "truth" is easy to calculate.  Note however
    that we do not use inclusive intersections, we we will
    test values from a slightly smaller box
    """
    nside = 2**15
    rng = np.random.RandomState(8312)
    nrand = 10000

    # make a box
    ra_range = 200.0, 200.1
    dec_range = 0.1, 0.2

    ra = [ra_range[0], ra_range[1], ra_range[1], ra_range[0]]
    dec = [dec_range[0], dec_range[0], dec_range[1], dec_range[1]]
    poly = healsparse.Polygon(
        ra=ra,
        dec=dec,
        value=64,
    )

    smap = poly.get_map(nside=nside, dtype=np.int16)

    rad = 0.1*(ra_range[1] - ra_range[0])
    decd = 0.1*(dec_range[1] - dec_range[0])

    rra = rng.uniform(
        low=ra_range[0]+rad,
        high=ra_range[1]-rad,
        size=nrand,
    )
    rdec = rng.uniform(
        low=dec_range[0]+decd,
        high=dec_range[1]-decd,
        size=nrand,
    )

    vals = smap.getValueRaDec(rra, rdec)  # noqa

    assert np.all(vals == poly.value)


def test_or_geom_values():
    """
    test "or"ing two geom objects
    """
    nside = 2**17
    dtype = np.int16

    radius1 = 0.075
    radius2 = 0.075
    ra1, dec1 = 200.0, 0.0
    ra2, dec2 = 200.1, 0.0
    value1 = 2**2
    value2 = 2**4

    circle1 = healsparse.Circle(
        ra=ra1,
        dec=dec1,
        radius=radius1,
        value=value1,
    )
    circle2 = healsparse.Circle(
        ra=ra2,
        dec=dec2,
        radius=radius2,
        value=value2,
    )

    smap = healsparse.HealSparseMap.makeEmpty(
        nsideCoverage=32,
        nsideSparse=nside,
        dtype=dtype,
        sentinel=0,
    )
    healsparse.or_geom([circle1, circle2], smap)

    out_ra, out_dec = 190.0, 25.0
    in1_ra, in1_dec = 200.02, 0.0
    in2_ra, in2_dec = 200.095, 0.0
    both_ra, both_dec = 200.05, 0.0

    out_vals = smap.getValueRaDec(out_ra, out_dec)
    in1_vals = smap.getValueRaDec(in1_ra, in1_dec)
    in2_vals = smap.getValueRaDec(in2_ra, in2_dec)
    both_vals = smap.getValueRaDec(both_ra, both_dec)

    assert np.all(out_vals == 0)
    assert np.all(in1_vals == value1)
    assert np.all(in2_vals == value2)
    assert np.all(both_vals == (value1 | value2))
