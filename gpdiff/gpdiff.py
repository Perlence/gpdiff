import os
import copy

import guitarpro
import diffutil
import merge
import flatten

class MuseDiffer(diffutil.Differ):

    def __init__(self, songs=[], *args, **kwds):
        '''Initialise Differ instance with given songs
        '''
        diffutil.Differ.__init__(self, *args, **kwds)
        self.songs = songs

    def _get_songs(self):
        return self._songs

    def _set_songs(self, songs):
        self._songs = songs
        self._sequences = map(flatten.flatten, songs)
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
        # copy base file to store merged elements
        base = self.songs[1]
        merged_sequence = self._merge_sequences()
        return flatten.restore(merged_sequence)

    def show(self):
        '''Output somewhat human-readible representation of diff between sequences
        '''
        for change in self.all_changes():
            yield '===='

            if change[0] is not None:
                tag, i1, i2, j1, j2 = change[0]
                yield '1:%d,%dc' % (i1, i2)
                for e in self._sequences[0][i1:i2]:
                    yield '%s' %  e

            if change[0] is not None:
                tag, i1, i2, j1, j2 = change[0]
                yield '2:%d,%dc' % (j1, j2)
                for e in self._sequences[1][i1:i2]:
                    yield '%s' %  e
            else:
                tag, i1, i2, j1, j2 = change[1]
                yield '2:%d,%dc' % (j1, j2)
                for e in self._sequences[1][i1:i2]:
                    yield '%s' %  e

            if len(self._sequences) == 3:
                if change[1] is not None:
                    tag, i1, i2, j1, j2 = change[1]
                    yield '3:%d,%dc' % (i1, i2)
                    for e in self._sequences[2][i1:i2]:
                        yield '%s' %  e


def main(args):
    '''Command line interface
    '''
    files = args.MYFILE, args.OLDFILE, args.YOURFILE
    # parse files
    songs = [guitarpro.parse(f) for f in files if f is not None]
    differ = MuseDiffer(songs)
    if len(files) == 3:
        # if output is specified, try to merge
        if args.output is not None:
            result = differ.merge()
            gpfile = guitarpro.open(args.output, 'wb', format=args.format)
            gpfile.write(result)
            if not len(differ.conflicts):
                return 0
    # print diff
    for line in differ.show():
        print line
    if len(files) == 2:
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
    parser.add_argument('MYFILE')
    parser.add_argument('OLDFILE')
    parser.add_argument('YOURFILE', nargs='?')
    parser.add_argument('-o', dest='output', metavar='OUTPUT', help='path to output merged file')
    parser.add_argument('-f', dest='format', choices=['gp3', 'gp4', 'gp5'], help='output file format')
    args = parser.parse_args()
    sys.exit(main(args))