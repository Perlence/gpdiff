import argparse
import os
import sys
import time

import attr
import guitarpro

from . import flatten
from . import diffutil
from . import merge


def main():
    sys.exit(cli(sys.argv[1:]))


def cli(argv):
    """Command line interface."""
    args = parser.parse_args(argv)
    files = [args.MYFILE, args.OLDFILE, args.YOURFILE]
    # Parse files
    songs = [guitarpro.parse(f) for f in files if f is not None]
    differ = GPDiffer(files, songs)
    if len(files) == 3:
        # If output is specified, try to merge
        if args.output is not None:
            result = differ.merge()
            max_version = max(song.versionTuple for song in songs)
            guitarpro.write(result, args.output, version=max_version)
            if not len(differ.conflicts):
                return 0
    for line in differ.show():
        print(line)
    if len(files) == 2 or not differ.conflicts:
        return 0
    else:
        return 1


legend = ('Measure diff legend:\n'
          '  +  inserted measure\n'
          '  -  removed measure\n'
          '  !  changed measure in 2-file mode\n'
          '  >  changed measure of first descendant\n'
          '  <  changed measure of second descendant\n'
          '  x  conflict')
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Diff and merge Guitar Pro 3-5 files\n\n' + legend,
    epilog='Returns 0 if diff or merge completed without conflicts\n'
           'Returns 1 if conflicts occurred\n'
           'Returns 2 if error occurred')
parser.add_argument('OLDFILE')
parser.add_argument('MYFILE')
parser.add_argument('YOURFILE', nargs='?')
parser.add_argument('-o', dest='output', metavar='OUTPUT', help='path to output merged file')


@attr.s
class GPDiffer:
    """A Differ instance with given songs.

    :param files: list of 2 or 3 file names: [A, O, B] or [A, O].
    :param songs: list of 2 or 3 parsed tabs.
    """
    Differ = diffutil.Differ
    Merger = merge.Merger

    files = attr.ib(default=attr.Factory(list))
    songs = attr.ib(default=attr.Factory(list))

    flat_songs = attr.ib(init=False)
    replace_prefixes = attr.ib(init=False)
    diff_matrix = attr.ib(init=False)
    conflicts = attr.ib(init=False)
    _sequences = attr.ib(init=False)

    def __attrs_post_init__(self):
        super().__init__()
        self.set_files(self.files)
        self.set_songs(self.songs)

        if len(self.songs) == 3:
            self.replace_prefixes = '><'
        else:
            self.replace_prefixes = '!!'

        self.init_diff_matrix()

    def set_files(self, files):
        self.files = files[:]

    def set_songs(self, songs):
        self.songs = songs[:]
        self.flat_songs = list(map(flatten.flatten, self.songs))

    def init_diff_matrix(self):
        self.diff_matrix = []
        for _ in range(max(len(song.tracks[0].measures) for song in self.songs)):
            row = []
            for _ in range(max(len(song.tracks) for song in self.songs)):
                row.append(' ')
            self.diff_matrix.append(row)

    def merge(self):
        """Merge sequences and restore tab."""
        assert len(self.songs) == 3
        merged_sequence = self._merge_sequences()
        return flatten.restore(merged_sequence)

    def _merge_sequences(self):
        """Merge sequences using diff data of differ."""
        merger = self.Merger()
        merger.differ = self
        merger.texts = self._sequences
        return merger.merge_3_files()

    def show(self):
        """Output somewhat human-readable representation of diff between
        sequences."""
        yield from self.show_file_info()
        yield from self.show_attr_diff('Song information', [fs.song_attrs for fs in self.flat_songs])
        yield from self.show_measure_diff()

    def show_file_info(self):
        yield 'OLDFILE:  %s\t%s' % (self.files[1], getmtime(self.files[1]))
        yield 'MYFILE:   %s\t%s' % (self.files[0], getmtime(self.files[0]))
        if len(self.songs) > 2:
            yield 'YOURFILE: %s\t%s' % (self.files[2], getmtime(self.files[2]))

    def show_attr_diff(self, section_name, attrs):
        differ = self.Differ()
        self._sequences = attrs
        differ.set_sequences_iter(self._sequences)
        all_changes = list(differ.all_changes())
        if not all_changes:
            return

        yield ''
        yield section_name
        yield '=' * len(section_name)
        yield ''

        for change in all_changes:
            if change[0] is not None:
                for line in self.infodiff(change, 0, self.replace_prefixes[0]):
                    yield line
            if change[1] is not None:
                for line in self.infodiff(change, 1, self.replace_prefixes[1]):
                    yield line

    def infodiff(self, change, pane, replace_prefix):
        a, b = self._sequences[1], self._sequences[pane * 2]
        tag, i1, i2, j1, j2 = change[pane]
        if tag == 'replace':
            for x in range(i1, i2):
                for line in self.print_info(a, pane, x, 'delete'):
                    yield line
            for x in range(j1, j2):
                for line in self.print_info(b, pane, x, 'insert'):
                    yield line
        if tag == 'delete':
            for x in range(i1, i2):
                for line in self.print_info(a, pane, x, 'delete'):
                    yield line
        if tag == 'insert':
            for x in range(j1, j2):
                for line in self.print_info(b, pane, x, 'insert'):
                    yield line
        if tag == 'conflict':
            yield replace_prefix * 8
            if i2 - i1 == 0:
                for x in range(j1, j2):
                    for line in self.print_info(b, pane, x, 'conflict'):
                        yield line
            else:
                for x in range(i1, i2):
                    for line in self.print_info(a, pane, x, 'conflict'):
                        yield line

    def print_info(self, sequence, pane, index, action, replace_prefix='!'):
        prefix = {'insert': '+', 'delete': '-', 'replace': replace_prefix, 'conflict': 'x', 'equal': ' '}
        obj = sequence[index]
        if isinstance(obj, tuple):
            attr_name, value = obj
            number = self.get_tracknumber(sequence[:index])
            if isinstance(value, tuple):
                if attr_name == 'strings':
                    value = reversed(value)
                    str_value = '({})'.format(', '.join(map(str, value)))
                else:
                    str_value = str(value)
            elif isinstance(value, str):
                str_value = repr(value)
            elif isinstance(value, guitarpro.Lyrics):
                str_value = repr(str(value))
            else:
                str_value = str(value)
            if number > 0:
                yield ("{prefix} Track {number}: {attr_name} = {value}"
                       .format(prefix=prefix[action],
                               # number=number + self.tracknumber[pane],
                               number=number,
                               attr_name=attr_name,
                               value=str_value))
            else:
                yield ("{prefix} Song: {attr_name} = {value}"
                       .format(prefix=prefix[action],
                               attr_name=attr_name,
                               value=str_value))

    def get_tracknumber(self, sequence):
        tracks = [x for x in sequence if x is guitarpro.Track]
        return len(tracks)

    def show_measure_diff(self):
        self._sequences = [fs.measures for fs in self.flat_songs]
        differ = self.Differ()
        differ.set_sequences_iter(self._sequences)
        all_changes = list(differ.all_changes())
        if not all_changes:
            return

        # import difflib
        # from .myers import DiffChunk

        # def isjunk(measure):
        #     return measure.isEmpty

        # sm = difflib.SequenceMatcher(isjunk=isjunk, autojunk=False)
        # sm.set_seqs(*reversed(self._sequences))
        # all_changes = [(DiffChunk(*chunk), None) for chunk in sm.get_opcodes() if chunk[0] != 'equal']

        yield ''
        yield 'Measures'
        yield '========'
        yield ''

        for change in all_changes:
            if change[0] is not None:
                self.diff_measures(change, 0, self.replace_prefixes[0])
            if change[1] is not None:
                self.diff_measures(change, 1, self.replace_prefixes[1])

        block = False

        yield ' ' + ' '.join([str(i) for i, _ in enumerate(self.diff_matrix[0], start=1)])
        for number, tracks in enumerate(self.diff_matrix):
            if any(x != ' ' for x in tracks):
                yield '[{}] {}'.format('|'.join(map(str, tracks)), number + 1)
                block = True
            else:
                if block:
                    yield ''
                block = False

    def diff_measures(self, change, pane, replace_prefix='!'):
        a, b = self._sequences[1], self._sequences[pane * 2]
        tag, i1, i2, j1, j2 = change[pane]
        if tag == 'replace':
            if i2 - i1 == j2 - j1:
                if i1 > j1:
                    for x in range(i1, i2):
                        self.store_change(a, x, 'replace', replace_prefix)
                else:
                    for x in range(j1, j2):
                        self.store_change(b, x, 'replace', replace_prefix)
            elif i2 - i1 < j2 - j1:
                for x in range(j1, j1 + i2 - i1):
                    self.store_change(b, x, 'replace', replace_prefix)
                for x in range(j1 + i2 - i1, j2):
                    self.store_change(b, x, 'insert')
            else:
                for x in range(i1, i1 + j2 - j1):
                    self.store_change(a, x, 'replace', replace_prefix)
                for x in range(i1 + j2 - j1, i2):
                    self.store_change(a, x, 'delete')
        elif tag == 'delete':
            for x in range(i1, i2):
                self.store_change(a, x, 'delete')
        elif tag == 'insert':
            for x in range(j1, j2):
                self.store_change(b, x, 'insert')
        elif tag == 'conflict':
            if i2 - i1 == 0:
                for x in range(j1, j2):
                    self.store_change(b, x, 'conflict')
            else:
                for x in range(i1, i2):
                    self.store_change(a, x, 'conflict')

    def store_change(self, sequence, index, action, replace_prefix='!'):
        prefix = {'insert': '+', 'delete': '-', 'replace': replace_prefix, 'conflict': 'x', 'equal': ' '}
        measure = sequence[index]
        track_number = measure.track.number - 1
        self.diff_matrix[measure.number - 1][track_number] = prefix[action]


def getmtime(fn):
    return time.ctime(os.path.getmtime(fn))


if __name__ == '__main__':
    main()
