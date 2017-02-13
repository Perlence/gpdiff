# Copyright (C) 2002-2006 Stephen Kennedy <stevek@gnome.org>
# Copyright (C) 2009, 2012-2013 Kai Willadsen <kai.willadsen@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import guitarpro

from .myers import DiffChunk, MyersSequenceMatcher


opcode_reverse = {
    "replace": "replace",
    "insert": "delete",
    "delete": "insert",
    "conflict": "conflict",
    "equal": "equal"
}


class Differ(object):
    """Utility class to hold diff2 or diff3 chunks"""

    _matcher = MyersSequenceMatcher

    def __init__(self):
        # Internally, diffs are stored from text1 -> text0 and text1 -> text2.
        self.num_sequences = 0
        self.seqlength = [0, 0, 0]
        self.diffs = [[], []]
        self.conflicts = []
        self._old_merge_cache = set()
        self._changed_chunks = tuple()
        self._merge_cache = []
        self._line_cache = [[], [], []]
        self._initialised = False
        self._has_mergeable_changes = (False, False, False, False)

    def _update_merge_cache(self, texts):
        if self.num_sequences == 3:
            self._merge_cache = [c for c in self._merge_diffs(self.diffs[0],
                                                              self.diffs[1],
                                                              texts)]
        else:
            self._merge_cache = [(c, None) for c in self.diffs[0]]

        # Calculate chunks that were added (in the new but not the old merge
        # cache), removed (in the old but not the new merge cache) and changed
        # (where the edit actually occurred, *and* the chunk is still around).
        # This information is used by the inline highlighting mechanism to
        # avoid re-highlighting existing chunks.
        removed_chunks = self._old_merge_cache - set(self._merge_cache)
        modified_chunks = self._changed_chunks
        if modified_chunks in removed_chunks:
            modified_chunks = tuple()

        mergeable0, mergeable1 = False, False
        for (c0, c1) in self._merge_cache:
            mergeable0 = mergeable0 or (c0 is not None and c0.tag != 'conflict')
            mergeable1 = mergeable1 or (c1 is not None and c1.tag != 'conflict')
            if mergeable0 and mergeable1:
                break
        self._has_mergeable_changes = (False, mergeable0, mergeable1, False)

        # Conflicts can only occur when there are three panes, and will always
        # involve the middle pane.
        self.conflicts = []
        for i, (c1, c2) in enumerate(self._merge_cache):
            if (c1 is not None and c1.tag == 'conflict') or \
               (c2 is not None and c2.tag == 'conflict'):
                self.conflicts.append(i)

        self._update_line_cache()

    def _update_line_cache(self):
        """Cache a mapping from line index to per-pane chunk indices

        This cache exists so that the UI can quickly query for current,
        next and previous chunks when the current cursor line changes,
        enabling better action sensitivity feedback.
        """
        for i, l in enumerate(self.seqlength):
            # seqlength + 1 for after-last-line requests, which we do
            self._line_cache[i] = [(None, None, None)] * (l + 1)

        last_chunk = len(self._merge_cache)

        def find_next(diff, seq, current):
            next_chunk = None
            if seq == 1 and current + 1 < last_chunk:
                next_chunk = current + 1
            else:
                for j in range(current + 1, last_chunk):
                    if self._merge_cache[j][diff] is not None:
                        next_chunk = j
                        break
            return next_chunk

        prev = [None, None, None]
        next = [find_next(0, 0, -1), find_next(0, 1, -1), find_next(1, 2, -1)]
        old_end = [0, 0, 0]

        for i, c in enumerate(self._merge_cache):
            seq_params = ((0, 0, 3, 4), (0, 1, 1, 2), (1, 2, 3, 4))
            for (diff, seq, lo, hi) in seq_params:
                if c[diff] is None:
                    if seq == 1:
                        diff = 1
                    else:
                        continue

                start, end, last = c[diff][lo], c[diff][hi], old_end[seq]
                if (start > last):
                    chunk_ids = [(None, prev[seq], next[seq])] * (start - last)
                    self._line_cache[seq][last:start] = chunk_ids

                # For insert chunks, claim the subsequent line.
                if start == end:
                    end += 1

                next[seq] = find_next(diff, seq, i)
                chunk_ids = [(i, prev[seq], next[seq])] * (end - start)
                self._line_cache[seq][start:end] = chunk_ids
                prev[seq], old_end[seq] = i, end

        for seq in range(3):
            last, end = old_end[seq], len(self._line_cache[seq])
            if (last < end):
                chunk_ids = [(None, prev[seq], next[seq])] * (end - last)
                self._line_cache[seq][last:end] = chunk_ids

    def all_changes(self):
        return iter(self._merge_cache)

    def _merge_blocks(self, using):
        LO, HI = 1, 2
        lowc = min(using[0][0][LO], using[1][0][LO])
        highc = max(using[0][-1][HI], using[1][-1][HI])
        low = []
        high = []
        for i in (0, 1):
            d = using[i][0]
            low.append(lowc - d[LO] + d[2 + LO])
            d = using[i][-1]
            high.append(highc - d[HI] + d[2 + HI])
        return low[0], high[0], lowc, highc, low[1], high[1]

    def _auto_merge(self, using, texts):
        """Automatically merge two sequences of change blocks"""
        l0, h0, l1, h1, l2, h2 = self._merge_blocks(using)
        if h0 - l0 == h2 - l2 and texts[0][l0:h0] == texts[2][l2:h2]:
            if l1 != h1 and l0 == h0:
                tag = "delete"
            elif l1 != h1:
                tag = "replace"
            else:
                tag = "insert"
        elif all(isinstance(m, guitarpro.Measure) and m.isEmpty for m in texts[0][l0:h0]):
            if l1 != h1 and l2 == h2:
                tag = "delete"
            elif l1 != h1:
                tag = "replace"
            else:
                tag = "insert"
            yield None, (tag, l1, h1, l2, h2)
            if h2 - l2 < h0 - l0:
                yield None, ('insert', l1, h1, l0 + (h2 - l2), h0)
            return
        elif all(isinstance(m, guitarpro.Measure) and m.isEmpty for m in texts[2][l2:h2]):
            if l1 != h1 and l0 == h0:
                tag = "delete"
            elif l1 != h1:
                tag = "replace"
            else:
                tag = "insert"
            yield (tag, l1, h1, l0, h0), None
            if h0 - l0 < h2 - l2:
                yield None, ('insert', l1, h1, l2 + (h0 - l0), h2)
            return
        else:
            tag = "conflict"
        out0 = DiffChunk._make((tag, l1, h1, l0, h0))
        out1 = DiffChunk._make((tag, l1, h1, l2, h2))
        yield out0, out1

    def _merge_diffs(self, seq0, seq1, texts):
        seq0, seq1 = seq0[:], seq1[:]
        seq = seq0, seq1
        while len(seq0) or len(seq1):
            if not seq0:
                high_seq = 1
            elif not seq1:
                high_seq = 0
            else:
                high_seq = int(seq0[0].start_a > seq1[0].start_a)
                if seq0[0].start_a == seq1[0].start_a:
                    if seq0[0].tag == "insert":
                        high_seq = 0
                    elif seq1[0].tag == "insert":
                        high_seq = 1

            high_diff = seq[high_seq].pop(0)
            high_mark = high_diff.end_a
            other_seq = 0 if high_seq == 1 else 1

            using = [[], []]
            using[high_seq].append(high_diff)

            while seq[other_seq]:
                other_diff = seq[other_seq][0]
                if high_mark < other_diff.start_a:
                    break
                if high_mark == other_diff.start_a and \
                   not (high_diff.tag == other_diff.tag == "insert"):
                    break

                using[other_seq].append(other_diff)
                seq[other_seq].pop(0)

                if high_mark < other_diff.end_a:
                    high_seq, other_seq = other_seq, high_seq
                    high_mark = other_diff.end_a

            if len(using[0]) == 0:
                assert len(using[1]) == 1
                yield None, using[1][0]
            elif len(using[1]) == 0:
                assert len(using[0]) == 1
                yield using[0][0], None
            else:
                for c in self._auto_merge(using, texts):
                    yield c

    def set_sequences_iter(self, sequences):
        assert 0 <= len(sequences) <= 3
        self.diffs = [[], []]
        self.num_sequences = len(sequences)
        self.seqlength = [len(s) for s in sequences]

        for i in range(self.num_sequences - 1):
            matcher = self._matcher(None, sequences[1], sequences[i * 2])
            work = matcher.initialise()
            while next(work) is None:
                yield None
            self.diffs[i] = matcher.get_difference_opcodes()
        self._initialised = True
        self._update_merge_cache(sequences)
        yield 1
