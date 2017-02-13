# Copyright (C) 2009-2010 Piotr Piastucki <the_leech@users.berlios.de>
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

from . import diffutil


class Merger(diffutil.Differ):

    def __init__(self):
        self.differ = diffutil.Differ()
        self.differ.unresolved = []
        self.texts = []

    def _apply_change(self, text, change, mergedtext):
        LO, HI = 1, 2
        if change[0] == 'insert':
            for i in range(change[LO + 2], change[HI + 2]):
                mergedtext.append(text[i])
            return 0
        elif change[0] == 'replace':
            for i in range(change[LO + 2], change[HI + 2]):
                mergedtext.append(text[i])
            return change[HI] - change[LO]
        else:
            return change[HI] - change[LO]

    def merge_3_files(self):
        LO, HI = 1, 2
        self.unresolved = []
        lastline = 0
        mergedline = 0
        mergedtext = []
        for change in self.differ.all_changes():
            yield None
            low_mark = lastline
            if change[0] is not None:
                low_mark = change[0][LO]
            if change[1] is not None:
                if change[1][LO] > low_mark:
                    low_mark = change[1][LO]
            for i in range(lastline, low_mark, 1):
                mergedtext.append(self.texts[1][i])
            mergedline += low_mark - lastline
            lastline = low_mark
            if change[0] is not None:
                lastline += self._apply_change(self.texts[0], change[0], mergedtext)
                mergedline += change[0][HI + 2] - change[0][LO + 2]
            else:
                lastline += self._apply_change(self.texts[2], change[1], mergedtext)
                mergedline += change[1][HI + 2] - change[1][LO + 2]
        baselen = len(self.texts[1])
        for i in range(lastline, baselen, 1):
            mergedtext.append(self.texts[1][i])

        yield mergedtext
