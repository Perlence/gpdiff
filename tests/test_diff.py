import os

import guitarpro
import pytest

import gpdiff.gpdiff


DIRNAME = os.path.dirname(__file__)


@pytest.mark.parametrize('file_a, file_b, expected_diff_matrix', [
    ('1-track.gp5',
     '1-track-modified-1.gp5',
     [[' '],
      ['!']]),
    ('1-track.gp5',
     '1-track-modified-2.gp5',
     [[' '],
      ['!'],
      ['+']]),
    ('1-track.gp5',
     '1-track-modified-3.gp5',
     [[' '],
      ['-']]),
    ('1-track.gp5',
     '1-track-modified-4.gp5',
     [[' '],
      [' '],
      ['+']]),
    ('1-track.gp5',
     '1-track-modified-5.gp5',
     [['!'],
      ['-']]),

    ('1-track.gp5',
     '2-track.gp5',
     [[' ', '+'],
      [' ', '+']]),

    ('2-track.gp5',
     '3-track.gp5',
     [[' ', '+', ' '],
      [' ', '+', ' ']]),
    ('2-track.gp5',
     '3-track-modified-1.gp5',
     [[' ', '+', ' '],
      [' ', '+', '!']]),
    ('3-track-modified-1.gp5',
     '2-track.gp5',
     [[' ', '-', ' '],
      [' ', '-', '!']]),

    ('2-track.gp5',
     '4-track.gp5',
     [[' ', '+', ' ', '+'],
      [' ', '+', ' ', '+']]),
    ('2-track-modified-1.gp5',
     '4-track.gp5',
     [[' ', '+', ' ', '+'],
      [' ', '+', '!', '+']]),
    ('4-track.gp5',
     '2-track-modified-1.gp5',
     [[' ', '-', ' ', '-'],
      [' ', '-', '!', '-']]),
])
def test_replace_measures(file_a, file_b, expected_diff_matrix):
    song_a = guitarpro.parse(os.path.join(DIRNAME, 'tabs', file_a))
    song_b = guitarpro.parse(os.path.join(DIRNAME, 'tabs', file_b))
    differ = gpdiff.GPDiffer([file_b, file_a], [song_b, song_a])
    for _ in differ.show_measure_diff():
        pass
    assert differ.diff_matrix == expected_diff_matrix
