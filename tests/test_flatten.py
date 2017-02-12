import attr
import guitarpro

from gpdiff.flatten import map_attrs, hashable_attrs, restore_attrs, flat_obj, flatten, restore


@attr.s
class A:
    a = attr.ib()
    b = attr.ib()
    c = attr.ib()


def test_hashable_attrs():
    table = [
        (A(1, 2, 3), A(1, 2, 3)),
        (A(1, 2, [3]), A(1, 2, (3,))),
        (A(1, 2, A(3, 4, 5)), A(1, 2, A(3, 4, 5))),
        (A(1, 2, A(3, 4, [5, 6, 7])), A(1, 2, A(3, 4, (5, 6, 7)))),
        (A(1, 2, A(3, 4, A(5, 6, [7, 8]))), A(1, 2, A(3, 4, A(5, 6, (7, 8))))),
    ]
    for source, expected in table:
        hashable = map_attrs(hashable_attrs, source)
        assert hashable == expected
        hash(hashable)

    song = guitarpro.Song()
    hashable_song = map_attrs(hashable_attrs, song)
    hash(hashable_song)


def test_restore_attrs():
    table = [
        (A(1, 2, 3), A(1, 2, 3)),
        (A(1, 2, (3,)), A(1, 2, [3])),
        (A(1, 2, A(3, 4, 5)), A(1, 2, A(3, 4, 5))),
        (A(1, 2, A(3, 4, (5, 6, 7))), A(1, 2, A(3, 4, [5, 6, 7]))),
        (A(1, 2, A(3, 4, A(5, 6, (7, 8)))), A(1, 2, A(3, 4, A(5, 6, [7, 8])))),
    ]
    for source, expected in table:
        hashable = map_attrs(restore_attrs, source)
        assert hashable == expected

    song = guitarpro.Song()
    hashable_song = map_attrs(hashable_attrs, song)
    restored_song = map_attrs(restore_attrs, hashable_song)
    assert song == restored_song


def test_flat_obj():
    table = [
        (A(1, 2, 3), {}, [A, ('a', 1), ('b', 2), ('c', 3)]),
        (A(1, 2, 3), {'skip': ['b']}, [A, ('a', 1), ('c', 3)]),
        (A(1, 2, A(3, 4, 5)), {'expand': ['c']}, [A, ('a', 1), ('b', 2), A, ('a', 3), ('b', 4), ('c', 5)]),
    ]
    for source, kwargs, expected in table:
        flat = list(flat_obj(source, **kwargs))
        assert flat == expected


def test_flatten():
    song = guitarpro.Song()
    flat = flatten(song)
    hash(flat)


def test_restore():
    song = guitarpro.Song()
    flat_song = flatten(song)
    restored_song = restore(flat_song)
    assert song == restored_song
