import os

import attr
import guitarpro

from gpdiff.flatten import as_dict_items, flatten, restore


DIRNAME = os.path.dirname(__file__)


@attr.s
class A:
    a = attr.ib()
    b = attr.ib()
    c = attr.ib()


def test_as_dict_items():
    table = [
        (A(1, 2, 3), {}, [('a', 1), ('b', 2), ('c', 3)]),
        (A(1, 2, 3), {'skip': ['b']}, [('a', 1), ('c', 3)]),
    ]
    for source, kwargs, expected in table:
        flat = list(as_dict_items(source, **kwargs))
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

    song = guitarpro.parse(os.path.join(DIRNAME, 'tabs', 'Effects.gp5'))
    flat_song = flatten(song)
    restored_song = restore(flat_song)
    assert song == restored_song


def diff_song(song_a, song_b):
    import difflib
    import textwrap

    song_a_str = textwrap.wrap(str(song_a))
    song_b_str = textwrap.wrap(str(song_b))
    for line in difflib.context_diff(song_a_str, song_b_str):
        print(line)
