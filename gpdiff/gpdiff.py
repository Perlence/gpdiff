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
class GPDiffer(diffutil.Differ):
    """A Differ instance with given songs.

    :param files: list of 2 or 3 file names: [A, O, B] or [A, O].
    :param songs: list of 2 or 3 parsed tabs.
    """
    files = attr.ib(default=attr.Factory(list))
    songs = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        super().__init__()
        self.files = self.files[:]
        self.songs = self.songs[:]
        self._sequences = list(map(flatten.flatten, self.songs))
        self.set_sequences_iter(self._sequences)

    def _merge_sequences(self):
        """Merge sequences using diff data of differ."""
        merger = merge.Merger()
        merger.differ = self
        merger.texts = self._sequences
        return merger.merge_3_files()

    def merge(self):
        """Merge sequences and restore tab."""
        assert len(self.songs) == 3
        merged_sequence = self._merge_sequences()
        return flatten.restore(merged_sequence)

    def get_tracknumber(self, sequence):
        tracks = [x for x in sequence if x is guitarpro.Track]
        return len(tracks)

    def store_change(self, sequence, pane, index, action, replace_prefix='!'):
        prefix = dict(insert='+', delete='-', replace=replace_prefix, conflict='x', equal=' ')
        obj = sequence[index]
        if isinstance(obj, guitarpro.Measure):
            measure = obj
            track_number = measure.track.number + self.tracknumber[pane] - 1
            self.measures[track_number][measure.number - 1] = prefix[action]
        elif obj is guitarpro.Track:
            if action == 'insert':
                self.tracknumber[1 - pane] += 1

    def print_info(self, sequence, pane, index, action, replace_prefix='!'):
        prefix = dict(insert='+', delete='-', replace=replace_prefix, conflict='x', equal=' ')
        obj = sequence[index]
        if isinstance(obj, tuple):
            attr, value = obj
            number = self.get_tracknumber(sequence[:index])
            if isinstance(value, tuple):
                if attr == 'strings':
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
                yield ("{prefix} Track {number}: {attr} = {value}"
                       .format(prefix=prefix[action],
                               number=number + self.tracknumber[pane],
                               attr=attr,
                               value=str_value))
            else:
                yield ("{prefix} Song: {attr} = {value}"
                       .format(prefix=prefix[action],
                               attr=attr,
                               value=str_value))

    def infodiff(self, change, pane, replace_prefix='!'):
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

    def measurediff(self, change, pane, replace_prefix='!'):
        a, b = self._sequences[1], self._sequences[pane * 2]
        tag, i1, i2, j1, j2 = change[pane]
        if tag == 'replace':
            if i2 - i1 == j2 - j1:
                for x in range(i1, i2):
                    self.store_change(a, pane, x, 'replace', replace_prefix)
            elif i2 - i1 < j2 - j1:
                for x in range(j1, j1 + i2 - i1):
                    self.store_change(b, pane, x, 'replace', replace_prefix)
                for x in range(j1 + i2 - i1, j2):
                    self.store_change(b, pane, x, 'insert')
            else:
                for x in range(i1, i1 + j2 - j1):
                    self.store_change(a, pane, x, 'replace', replace_prefix)
                for x in range(i1 + j2 - j1, i2):
                    self.store_change(a, pane, x, 'delete')
        if tag == 'delete':
            for x in range(i1, i2):
                self.store_change(a, pane, x, 'delete')
        if tag == 'insert':
            for x in range(j1, j2):
                self.store_change(b, pane, x, 'insert')
        if tag == 'conflict':
            if i2 - i1 == 0:
                for x in range(j1, j2):
                    self.store_change(b, pane, x, 'conflict')
            else:
                for x in range(i1, i2):
                    self.store_change(a, pane, x, 'conflict')

    def show(self):
        """Output somewhat human-readable representation of diff between
        sequences."""
        self.measures = []
        self.tracknumber = [0, 0]
        for i in range(max(len(song.tracks) for song in self.songs)):
            track = []
            for j in range(max(len(song.tracks[0].measures) for song in self.songs)):
                track.append(' ')
            self.measures.append(track)

        if len(self.songs) == 3:
            replace_prefix = '><'
        else:
            replace_prefix = '!!'

        def getmtime(fn):
            return time.ctime(os.path.getmtime(fn))

        yield 'OLDFILE:  %s\t%s' % (self.files[1], getmtime(self.files[1]))
        yield 'MYFILE:   %s\t%s' % (self.files[0], getmtime(self.files[0]))
        if len(self.songs) > 2:
            yield 'YOURFILE: %s\t%s' % (self.files[2], getmtime(self.files[2]))

        yield ''
        yield 'Attributes'
        yield '=========='
        yield ''

        for change in self.all_changes():
            if change[0] is not None:
                for line in self.infodiff(change, 0, replace_prefix[0]):
                    yield line
            if change[1] is not None:
                for line in self.infodiff(change, 1, replace_prefix[1]):
                    yield line

        yield ''
        yield 'Measures'
        yield '========'
        yield ''

        for change in self.all_changes():
            if change[0] is not None:
                self.measurediff(change, 0, replace_prefix[0])
            if change[1] is not None:
                self.measurediff(change, 1, replace_prefix[1])

        block = False

        yield ' ' + ' '.join([str(i) for i, _ in enumerate(self.measures, start=1)])
        for number, tracks in enumerate(zip(*self.measures)):
            if any(x != ' ' for x in tracks):
                yield '[{}] {}'.format('|'.join(map(str, tracks)),
                                       number + 1)
                block = True
            else:
                if block:
                    yield ''
                block = False


if __name__ == '__main__':
    main()
