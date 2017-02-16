import argparse
import os
import sys
import time

import attr
import daff
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
    diff_matrix = attr.ib(default=attr.Factory(list), init=False)
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

    def set_files(self, files):
        self.files = files[:]

    def set_songs(self, songs):
        self.songs = songs[:]
        self.flat_songs = list(map(flatten.flatten, self.songs))

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
        from pprint import pprint

        self.diff_matrix = []

        yield ''
        yield 'Measures'
        yield '========'
        yield ''

        local, parent, remote, hashes = self.prepare_measure_tables()

        pprint(local)
        pprint(remote)
        flags = daff.CompareFlags()
        if parent is not None:
            flags.parent = parent
        align = daff.compareTables(local, remote, flags).align()

        print(list(map(astuple, align.meta.toOrder().getList())))
        print(list(map(astuple, align.toOrder().getList())))
        print(daff.diffAsAnsi(local, remote, flags))

        total_track_number = max(len(song.tracks) for song in self.songs)
        header = [' '] * total_track_number
        self.mark_columns(align, header)
        self.mark_rows(align, header)
        self.mark_cells(local, parent, remote, align)

    def prepare_measure_tables(self):
        hashes = {}
        tables = [self.hash_measures(s, fs, hashes) for s, fs in zip(self.songs, self.flat_songs)]
        if len(tables) == 3:
            local, parent, remote = tables
        else:
            remote, local = tables
            parent = None
        return local, parent, remote, hashes

    def hash_measures(self, song, flat_song, hashes):
        hashed_measures = [list(self.unique_track_names(song))]
        for track_wise in flat_song.measures:
            row = []
            for measure in track_wise:
                hashed_measure = hash(measure)
                hashes[hashed_measure] = measure
                row.append(hashed_measure)
            hashed_measures.append(row)
        return hashed_measures

    def unique_track_names(self, song):
        track_names = set()
        for track in song.tracks:
            name = track.name
            if name in track_names:
                name += ':{}'.format(hash(track))
            track_names.add(name)
            yield name

    def mark_columns(self, align, header):
        has_parent = align.reference is not None
        for col_unit in align.meta.toOrder().getList():
            if col_unit.p < 0 and col_unit.l < 0 and col_unit.r >= 0:
                # Track was added
                header[col_unit.r] = '+'
            if col_unit.p >= 0 or not has_parent and col_unit.l >= 0 and col_unit.r < 0:
                # Track was removed
                header[col_unit.l] = '!' if header[col_unit.l] == '+' else '-'

    def mark_rows(self, align, header):
        has_parent = align.reference is not None
        # Skip header and start from row 1
        inserted_measures = []
        for row_unit in align.toOrder().getList()[1:]:
            if row_unit.p < 0 and row_unit.l < 0 and row_unit.r >= 0:
                # Measure was inserted
                inserted_measures.append(['+' if c == ' ' else c for c in header])
            elif row_unit.p >= 0 or not has_parent and row_unit.l >= 0 and row_unit.r < 0:
                if inserted_measures:
                    # Mark previously inserted measures as replaced
                    inserted_measures = inserted_measures[1:]
                    self.diff_matrix.append(['!' if c == ' ' else c for c in header])
                else:
                    # Measure was removed
                    self.diff_matrix.append(['-' if c == ' ' else c for c in header])
            else:
                self.diff_matrix.extend(inserted_measures)
                inserted_measures = []
                self.diff_matrix.append(header[:])
        self.diff_matrix.extend(inserted_measures)

    def mark_cells(self, local, parent, remote, align):
        """Scan rows for differences."""
        for row_unit in align.toOrder().getList()[1:]:
            for col_number, col_unit in enumerate(align.meta.toOrder().getList()):
                pp = ll = rr = None
                if col_unit.p >= 0 and row_unit.p >= 0:
                    pp = parent[row_unit.p][col_unit.p]
                if col_unit.l >= 0 and row_unit.l >= 0:
                    ll = local[row_unit.l][col_unit.l]
                if col_unit.r >= 0 and row_unit.r >= 0:
                    rr = remote[row_unit.r][col_unit.r]

                print(astuple(row_unit), astuple(col_unit))
                print(ll, rr)

                if pp is not None:
                    if ll == pp != rr:
                        self.diff_matrix[row_unit.l-1][col_number] = '<'
                    elif ll != pp == rr:
                        self.diff_matrix[row_unit.l-1][col_number] = '>'
                    elif ll != pp != rr:
                        if ll == rr:
                            self.diff_matrix[row_unit.l-1][col_number] = '!'
                        else:
                            self.diff_matrix[row_unit.l-1][col_number] = 'x'
                elif ll is not None and rr is not None and ll != rr:
                    self.diff_matrix[row_unit.l-1][col_number] = '!'


def getmtime(fn):
    return time.ctime(os.path.getmtime(fn))


def astuple(hx_obj):
    return tuple(getattr(hx_obj, field) for field in hx_obj._hx_fields)


if __name__ == '__main__':
    main()
