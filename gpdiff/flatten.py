from collections import OrderedDict

import attr

import guitarpro as gp


@attr.s
class FlatSong:
    song_attrs = attr.ib()
    song_attr_count = attr.ib()
    page_setup_attrs = attr.ib()
    page_setup_attr_count = attr.ib()
    measure_headers = attr.ib()
    track_attrs = attr.ib()
    track_attr_count = attr.ib()
    track_channel_attrs = attr.ib()
    track_channel_attr_count = attr.ib()
    track_settings_attrs = attr.ib()
    track_settings_attr_count = attr.ib()
    measures = attr.ib()


def flatten(song):
    """Convert Song into a tuple."""
    song_attrs = tuple(as_dict_items(song, skip=['pageSetup', 'tracks']))
    page_setup_attrs = tuple(as_dict_items(song.pageSetup))
    measure_headers = tuple(measure.header for measure in song.tracks[0].measures)
    track_attrs = []
    track_channel_attrs = []
    track_settings_attrs = []
    measures = []
    for track in song.tracks:
        track_attrs.extend(as_dict_items(track, skip=['channel', 'settings', 'measures']))
        track_channel_attrs.extend(as_dict_items(track.channel))
        track_settings_attrs.extend(as_dict_items(track.settings))
        measures.extend(track.measures)
    return FlatSong(song_attrs, len(song_attrs),
                    page_setup_attrs, len(page_setup_attrs),
                    measure_headers,
                    tuple(track_attrs), len(track_attrs) // len(song.tracks),
                    tuple(track_channel_attrs), len(track_channel_attrs) // len(song.tracks),
                    tuple(track_settings_attrs), len(track_settings_attrs) // len(song.tracks),
                    tuple(measures))


def restore(flat_song):
    """Restore Song from FlatSong instance."""
    fs = flat_song
    [page_setup] = from_dict_items(gp.PageSetup, fs.page_setup_attr_count, fs.page_setup_attrs)
    [song] = from_dict_items(gp.Song, fs.song_attr_count, fs.song_attrs,
                             pageSetup=page_setup,
                             measureHeaders=list(fs.measure_headers),
                             tracks=())

    song.tracks = list(from_dict_items(gp.Track, fs.track_attr_count, fs.track_attrs, song=song, measures=()))
    track_channels = from_dict_items(gp.MidiChannel, fs.track_channel_attr_count, fs.track_channel_attrs)
    track_settings = from_dict_items(gp.TrackSettings, fs.track_settings_attr_count, fs.track_settings_attrs)
    track_measures = restore_track_measures(fs.measure_headers, fs.measures)

    for number, (track, channel, settings) in enumerate(zip(song.tracks, track_channels, track_settings), start=1):
        track.number = number
        track.channel = channel
        track.settings = settings

    for track, measures in zip(song.tracks, track_measures):
        track.measures = list(measures)

    return song


def from_dict_items(cls, attr_count, attrs, **kwargs):
    while attrs:
        single_obj_attrs = attrs[:attr_count]
        for k, v in single_obj_attrs:
            if isinstance(v, tuple):
                v = list(v)
            kwargs[k] = v
        yield cls(**kwargs)
        attrs = attrs[attr_count:]


def restore_track_measures(headers, all_measures):
    while all_measures:
        track_measures = all_measures[:len(headers)]
        for header, measure in zip(headers, track_measures):
            measure.header = header
        yield track_measures
        all_measures = all_measures[len(headers):]


def as_dict_items(obj, skip=[]):
    """Convert *obj* into list consisting of *obj* class and *obj*
    attributes in form of tuples.

    >>> import guitarpro as gp
    >>> note = gp.Note()
    >>> list(as_dict_items(note))
    [('value', 0), ('velocity', 95),
     ('string', 1),
     ('isTiedNote', False),
     ('effect', NoteEffect(...)),
     ('durationPercent', 1.0),
     ('swapAccidentals', False)]
    """
    def filter_(attrib, value):
        if not attrib.hash:
            return False
        if attrib.name in skip:
            return False
        return True

    dictionary = attr.asdict(obj, recurse=False, filter=filter_, dict_factory=OrderedDict)
    for k, v in dictionary.items():
        if isinstance(v, list):
            v = tuple(v)
        yield k, v
