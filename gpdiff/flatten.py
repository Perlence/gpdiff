import copy
import guitarpro as gp

def flat_obj(obj, skip_attrs=[]):
    '''Convert obj into list consisting of obj class and obj attributes in form of tuples
    
    >>> import guitarpro as gp
    >>> note = gp.Note()
    >>> flat_obj(note) #doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    [<class 'guitarpro.base.Note'>, 
     ('value', 0), ('velocity', 95), 
     ('string', 1), 
     ('isTiedNote', False), 
     ('effect', <guitarpro.base.NoteEffect object at 0x...>), 
     ('durationPercent', 1.0), 
     ('swapAccidentals', False)]
    '''
    result = []
    result.append(obj.__class__)
    for attr in obj.__attr__:
        value = getattr(obj, attr)
        if attr not in skip_attrs:
            if isinstance(value, list):
                value = tuple(value)
            result.append((attr, value))
    return result

def flatten(song):
    '''Convert Song into list
    '''
    result = []
    result += flat_obj(song, ['tracks'])
    for track in song.tracks:
        result += flat_obj(track, ['measures'])
        for measure in track.measures:
            result.append(copy.copy(measure))
    return result

def restore(sequence):
    '''Restore Song from list
    '''
    song = None
    last = None
    tracknumber = 1
    measurenumber = 1
    for e in sequence:
        if e == gp.Song:
            song = e()
            song.tracks = []
            song.measureHeaders = []
            last = song
        elif e == gp.Track:
            track = e()
            track.number = tracknumber
            track.measures = []
            song.tracks.append(track)
            last = track
            tracknumber += 1
            measurenumber = 0
        elif isinstance(e, gp.Measure):
            if last.number == 1:
                song.measureHeaders.append(e.header)
            e.number = measurenumber
            last.measures.append(e)
            measurenumber += 1
        else:
            attr, value = e
            if isinstance(value, tuple):
                value = list(value)
            setattr(last, attr, value)
    return song
