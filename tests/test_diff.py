import os

import guitarpro
import pytest

import gpdiff.gpdiff


DIRNAME = os.path.dirname(__file__)


TABLE_REPLACE_MEASURES = [
    # Add one track
    ('1-track.gp5', '2-track.gp5',
     [list(' +'),
      list(' +')]),
    ('2-track.gp5', '3-track.gp5',
     [list(' + '),
      list(' + ')]),
    ('2-track.gp5', '4-track.gp5',
     [list(' + +'),
      list(' + +')]),
    # Remove one track
    ('2-track.gp5', '1-track.gp5',
     [list(' -'),
      list(' -')]),
    ('3-track.gp5', '2-track.gp5',
     [list(' - '),
      list(' - ')]),
    ('4-track.gp5', '2-track.gp5',
     [list(' - -'),
      list(' - -')]),

    ('1-track.gp5', '1-track-modified-1.gp5',
     [list(' '),
      list('!')]),
    ('1-track.gp5', '1-track-modified-2.gp5',
     [list(' '),
      list('!'),
      list('+')]),
    ('1-track.gp5', '1-track-modified-3.gp5',
     [list(' '),
      list('-')]),
    ('1-track.gp5', '1-track-modified-4.gp5',
     [list(' '),
      list(' '),
      list('+')]),
    ('1-track.gp5', '1-track-modified-5.gp5',
     [list('!'),
      list('-')]),
    ('1-track-modified-6.gp5', '1-track-modified-7.gp5',
     [list(' '),
      list('-'),
      list(' '),
      list('!')]),
    ('1-track.gp5', '1-track-modified-9.gp5',
     [list('!'),
      list('!'),
      list('!'),
      list('!')]),

    ('2-track.gp5', '3-track-modified-1.gp5',
     [list(' + '),
      list(' +!')]),
    ('3-track-modified-1.gp5', '2-track.gp5',
     [list(' - '),
      list(' -!')]),
    ('3-track-modified-3.gp5', '3-track-modified-4.gp5',
     [list(' - +'),
      list(' - +'),
      list(' - +'),
      list(' - +')]),

    ('2-track-modified-1.gp5', '4-track.gp5',
     [list(' + +'),
      list(' +!+')]),
    ('4-track.gp5', '2-track-modified-1.gp5',
     [list(' - -'),
      list(' -!-')]),
    ('4-track-modified-1.gp5', '3-track.gp5',
     [list('   -'),
      list('   -'),
      list('----'),
      list('----')]),
    ('4-track-modified-1.gp5', '3-track-modified-2.gp5',
     [list('   -'),
      list('+++-'),
      list('   -'),
      list('----'),
      list('----')]),
    ('3-track-modified-2.gp5', '4-track-modified-1.gp5',
     [list('   +'),
      list('---+'),
      list('   +'),
      list('++++'),
      list('++++')]),
    ('4-track-modified-2.gp5', '4-track-modified-3.gp5',
     [list('!!!!'),
      list('!+++'),
      list('!+++'),
      list('!+++'),
      list('!+++'),
      list('!+++'),
      list('!+++'),
      list('!+++'),
      list('!+++'),
      list('!   '),
      list('!   '),
      list('!   '),
      list('!!  '),
      list('!!  '),
      list('!!  '),
      list('!!  '),
      list('!!  '),
      list('!!  '),
      list('!!  '),
      list('!!  '),
      list('!!  '),
      list('!!!!'),
      list('!!!!'),
      list('!!!!'),
      list('!!! '),
      list('!!!!'),
      list('!!!!'),
      list('!!!!')]),
]


@pytest.mark.parametrize('file_l, file_r, expected_diff_matrix', TABLE_REPLACE_MEASURES)
def test_diff_matrix(file_l, file_r, expected_diff_matrix):
    song_l = guitarpro.parse(os.path.join(DIRNAME, 'tabs', file_l))
    song_r = guitarpro.parse(os.path.join(DIRNAME, 'tabs', file_r))
    differ = gpdiff.GPDiffer([file_r, file_l], [song_r, song_l])
    for line in differ.show_measure_diff():
        print(line)
    assert differ.diff_matrix == expected_diff_matrix


TABLE_MARK_ROWS = [
    ('4-track-modified-1.gp5', '3-track.gp5',
     [(1, 1),
      (2, 2),
      (3, None),
      (4, None)]),
    ('4-track-modified-1.gp5', '3-track-modified-2.gp5',
     [(1, 1),
      (None, 2),
      (2, 3),
      (3, None),
      (4, None)]),
    ('3-track-modified-2.gp5', '4-track-modified-1.gp5',
     [(1, 1),
      (2, None),
      (3, 2),
      (None, 3),
      (None, 4)]),
    ('4-track-modified-2.gp5', '4-track-modified-3.gp5',
     [(1, 1),
      (None, 2),
      (None, 3),
      (None, 4),
      (None, 5),
      (None, 6),
      (None, 7),
      (None, 8),
      (None, 9),
      (2, 10),
      (3, 11),
      (4, 12),
      (5, 13),
      (6, 14),
      (7, 15),
      (8, 16),
      (9, 17),
      (10, 18),
      (11, 19),
      (12, 20),
      (13, 21),
      (14, 22),
      (15, 23),
      (16, 24),
      (17, 25),
      (18, 26),
      (19, 27),
      (20, 28)]),
]


@pytest.mark.parametrize('file_l, file_r, expected_measure_numbers', TABLE_MARK_ROWS)
def test_mark_rows(file_l, file_r, expected_measure_numbers):
    song_l = guitarpro.parse(os.path.join(DIRNAME, 'tabs', file_l))
    song_r = guitarpro.parse(os.path.join(DIRNAME, 'tabs', file_r))
    differ = gpdiff.GPDiffer([file_r, file_l], [song_r, song_l])
    for line in differ.show_measure_diff():
        print(line)
    assert differ.measure_numbers == expected_measure_numbers


TABLE_MERGE = [
    ('1-track.gp5', '1-track-modified-1.gp5', '1-track-modified-2.gp5',
     [list(' '),
      list('+'),
      list('+'),
      list(' ')]),
    ('1-track.gp5', '1-track-modified-4.gp5', '1-track-modified-2.gp5',
     [list(' '),
      list('<'),
      list('+'),
      list(' ')]),
    ('1-track-modified-6.gp5', '2-track-modified-2.gp5', '2-track-modified-3.gp5',
     [list(' + '),
      list(' + '),
      list(' + '),
      list('<+!')]),
    ('1-track-modified-6.gp5', '2-track-modified-4.gp5', '2-track-modified-5.gp5',
     [list(' + '),
      list('!+ '),
      list(' + '),
      list('<+!')]),
]


@pytest.mark.parametrize('file_p, file_l, file_r, expected_diff_matrix', TABLE_MERGE)
def test_merge(file_p, file_l, file_r, expected_diff_matrix):
    song_p = guitarpro.parse(os.path.join(DIRNAME, 'tabs', file_p))
    song_l = guitarpro.parse(os.path.join(DIRNAME, 'tabs', file_l))
    song_r = guitarpro.parse(os.path.join(DIRNAME, 'tabs', file_r))
    differ = gpdiff.GPDiffer([file_l, file_p, file_r], [song_l, song_p, song_r])
    for line in differ.show_measure_diff():
        print(line)
    assert differ.diff_matrix == expected_diff_matrix
