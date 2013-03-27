import os
import copy

import guitarpro
import diffutil
import merge
import flatten

class GPDiffer(diffutil.Differ):

    def __init__(self, songs=[], *args, **kwds):
        '''Initialise Differ instance with given songs
        '''
        diffutil.Differ.__init__(self, *args, **kwds)
        self.songs = songs

    def _get_songs(self):
        songs = self._songs
        songs[0], songs[1] = self._songs[1], self._songs[0]
        return songs

    def _set_songs(self, songs):
        self._songs = songs
        self._songs[0], self._songs[1] = songs[1], songs[0]
        self._sequences = map(flatten.flatten, self._songs)
        for _ in self.set_sequences_iter(self._sequences): 
            pass

    songs = property(_get_songs, _set_songs)

    def _merge_sequences(self):
        '''Merge sequences using diff data of differ
        '''
        merger = merge.Merger()
        merger.differ = self
        merger.texts = self._sequences
        for result in merger.merge_3_files(mark_conflicts=False): 
            pass
        return result

    def merge(self):
        '''Merge sequences and restore tab
        '''
        assert len(self.songs) == 3
        merged_sequence = self._merge_sequences()
        return flatten.restore(merged_sequence)

    def get_tracknumber(self, sequence):
        tracks = filter(lambda x: x == guitarpro.Track, sequence)
        return len(tracks)

    def store_change(self, sequence, pane, index, action, replace_prefix='!'):
        prefix = dict(insert='+', delete='-', replace=replace_prefix, conflict='x', equal=' ')
        obj = sequence[index]
        if isinstance(obj, guitarpro.Measure):
            track_number = obj.track.number + self.tracknumber[pane] - 1
            self.measures[track_number][obj.number() - 1] = prefix[action]
        elif obj == guitarpro.Track:
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
                yield "{prefix} Track {number}: {attr} = {value}".format(prefix=prefix[action], 
                                                                         number=number + self.tracknumber[pane],
                                                                         attr=attr,
                                                                         value=str_value)
            else:
                yield "{prefix} Song: {attr} = {value}".format(prefix=prefix[action],
                                                               attr=attr,
                                                               value=str_value)

    def infodiff(self, change, pane):
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
        if tag == 'conflict' and pane == 0:
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
            else:
                for x in range(i1, i2):
                    self.store_change(a, pane, x, 'delete')
                for x in range(j1, j2):
                    self.store_change(b, pane, x, 'insert')
        if tag == 'delete':
            for x in range(i1, i2):
                self.store_change(a, pane, x, 'delete')
        if tag == 'insert':
            for x in range(j1, j2):
                self.store_change(b, pane, x, 'insert')
        if tag == 'conflict':
            for x in range(i1, i2):
                self.store_change(a, pane, x, 'conflict')

    def show(self):
        '''Output somewhat human-readible representation of diff between sequences
        '''
        self.measures = []
        self.tracknumber = [0, 0]
        for i in range(max(len(song.tracks) for song in self.songs)):
            track = []
            for j in range(max(len(song.tracks[0].measures) for song in self.songs)):
                track.append(' ')
            self.measures.append(track)
        
        # for change in self.all_changes():
        #     print change

        yield 'Attributes'
        yield '=========='
        yield ''

        for change in self.all_changes():
            if change[0] is not None:
                for line in self.infodiff(change, 0):
                    yield line
            if change[1] is not None:
                for line in self.infodiff(change, 1):
                    yield line

        yield ''
        yield 'Measures'
        yield '========'
        yield ''

        replace_prefix = '!'
        for change in self.all_changes():
            if change[0] is not None:
                if len(self._songs) == 3:
                    replace_prefix = '>'
                self.measurediff(change, 0, replace_prefix)
            if change[1] is not None:
                if len(self._songs) == 3:
                    replace_prefix = '<' 
                self.measurediff(change, 1, replace_prefix)

        # yield ' {}'.format(' '.join(map(str, range(1, len(self.measures) + 1))))
        yield ' ' + ' '.join([str(i) for i, _ in enumerate(self.measures, start=1)])
        for number, tracks in enumerate(zip(*self.measures)):
            yield '[{}] {}'.format('|'.join(map(str, tracks)),
                                  number + 1)
                                  



def main(args):
    '''Command line interface
    '''
    files = args.OLDFILE, args.MYFILE, args.YOURFILE
    # parse files
    songs = [guitarpro.parse(f) for f in files if f is not None]
    differ = GPDiffer(songs)
    if len(files) == 3:
        # if output is specified, try to merge
        if args.output is not None:
            result = differ.merge()
            guitarpro.write(result, args.output, format=args.format)
            if not len(differ.conflicts):
                return 0
    # print diff
    for line in differ.show():
        print line
    if len(files) == 2 or not differ.conflicts:
        return 0
    else:
        return 1

if __name__ == '__main__':
    import sys
    import argparse
    parser = argparse.ArgumentParser(description='Diff and merge Guitar Pro 3-5 files',
        epilog='''Returns 0 if diff or merge completed without conflicts,
            returns 1 if confilts occurred,
            returns 2 if error occurred''')
    parser.add_argument('OLDFILE')
    parser.add_argument('MYFILE')
    parser.add_argument('YOURFILE', nargs='?')
    parser.add_argument('-o', dest='output', metavar='OUTPUT', help='path to output merged file')
    parser.add_argument('-f', dest='format', choices=['gp3', 'gp4', 'gp5'], help='output file format')
    args = parser.parse_args()
    sys.exit(main(args))