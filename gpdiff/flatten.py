import copy

import attr

import guitarpro as gp


def flatten(song):
    """Convert Song into list."""
    result = []
    song = map_attrs(hashable_attrs, song)
    result.extend(flat_obj(song, expand=['pageSetup'], skip=['tracks']))
    for track in song.tracks:
        result.extend(flat_obj(track, expand=['channel', 'settings'], skip=['measures']))
        for measure in track.measures:
            result.append(copy.copy(measure))
    return tuple(result)


def restore(sequence):
    """Restore Song from list."""
    song = None
    stack = []
    track_number = measure_number = 1
    until = None
    for e in sequence:
        if stack:
            top = stack[-1]
        if e is gp.Song:
            song = gp.Song(tracks=[], measureHeaders=[])
            stack.append(song)
        elif e is gp.PageSetup:
            page_setup = gp.PageSetup()
            song.pageSetup = page_setup
            stack.append(page_setup)
            until = len(attr.fields(gp.PageSetup))
        elif e is gp.Track:
            track = gp.Track(song, number=track_number, measures=[])
            song.tracks.append(track)
            stack.append(track)
            track_number += 1
            measure_number = 1
        elif e is gp.MidiChannel:
            channel = e()
            track.channel = channel
            stack.append(channel)
            until = len(attr.fields(gp.MidiChannel))
        elif e is gp.TrackSettings:
            settings = e()
            track.settings = settings
            stack.append(settings)
            until = len(attr.fields(gp.TrackSettings))
        elif isinstance(e, gp.Measure):
            e = restore_attrs(None, e)
            e.track = top
            e.number = measure_number
            e.track.measures.append(e)
            measure_number += 1
        else:
            attr_name, value = e
            attrib = getattr(type(top), attr_name)
            value = restore_attrs(attrib, value)
            setattr(top, attr_name, value)
            if until is not None:
                if until > 1:
                    until -= 1
                else:
                    until = None
                    stack.pop()
    return song


def flat_obj(obj, expand=[], skip=[]):
    """Convert *obj* into list consisting of *obj* class and *obj*
    attributes in form of tuples.

    >>> import guitarpro as gp
    >>> note = gp.Note()
    >>> flat_obj(note)
    [<class 'guitarpro.models.Note'>,
     ('value', 0), ('velocity', 95),
     ('string', 1),
     ('isTiedNote', False),
     ('effect', NoteEffect(...)),
     ('durationPercent', 1.0),
     ('swapAccidentals', False)]
    """
    cls = type(obj)
    yield cls
    for attrib in attr.fields(cls):
        if not attrib.cmp:
            continue
        attr_name = attrib.name
        if attr_name in skip:
            continue
        value = getattr(obj, attr_name)
        if attr_name in expand:
            yield from flat_obj(value)
            continue
        if isinstance(value, list):
            value = tuple(value)
        yield (attr_name, value)


def map_attrs(func, obj):
    fields = attr.fields(type(obj))
    for attrib in fields:
        value = getattr(obj, attrib.name)
        new_value = func(attrib, value)
        if value != new_value:
            obj = attr.assoc(obj, **{attrib.name: new_value})
    return obj


def hashable_attrs(attrib, value):
    if attrib is not None and not attrib.cmp:
        return value
    if isinstance(value, list):
        value = tuple(hashable_attrs(None, item) for item in value)
    elif attr.has(type(value)):
        value = map_attrs(hashable_attrs, value)
    return value


def restore_attrs(attrib, value):
    if attrib is not None and not attrib.cmp:
        return value
    if isinstance(value, tuple):
        value = [restore_attrs(None, item) for item in value]
    elif attr.has(type(value)):
        value = map_attrs(restore_attrs, value)
    return value
