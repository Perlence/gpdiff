import copy
import guitarpro as gp

def flat_obj(obj, expand=[], skip=[]):
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
        value = getattr(obj, attr, None)
        if attr in expand:
            result += flat_obj(value)
        elif attr not in skip:
            if isinstance(value, list):
                value = tuple(value)
            result.append((attr, value))
    return result

def flatten(song):
    '''Convert Song into list
    '''
    result = []
    result += flat_obj(song, expand=['pageSetup'], skip=['tracks'])
    for track in song.tracks:
        result += flat_obj(track, expand=['channel', 'settings'], skip=['measures'])
        for measure in track.measures:
            result.append(copy.copy(measure))
    return result

def restore(sequence):
    '''Restore Song from list
    '''
    song = None
    stack = []
    tracknumber = 1
    measurenumber = 1
    until = None
    for e in sequence:
        if e == gp.Song:
            song = e()
            song.tracks = []
            song.measureHeaders = []
            stack.append(song)
        elif e == gp.PageSetup:
            pageSetup = e()
            song.pageSetup = pageSetup
            stack.append(pageSetup)
            until = len(gp.PageSetup.__attr__)
        elif e == gp.Track:
            track = e()
            track.number = tracknumber
            track.measures = []
            song.tracks.append(track)
            stack.append(track)
            tracknumber += 1
            measurenumber = 1
        elif e == gp.MidiChannel:
            channel = e()
            track.channel = channel
            stack.append(channel)
            until = len(gp.MidiChannel.__attr__)
        elif e == gp.TrackSettings:
            settings = e()
            track.settings = settings
            stack.append(settings)
            until = len(gp.TrackSettings.__attr__)
        elif isinstance(e, gp.Measure):
            e.header.number = measurenumber
            if stack[-1].number == 1:
                song.measureHeaders.append(e.header)
            stack[-1].measures.append(e)
            measurenumber += 1
        else:
            attr, value = e
            if isinstance(value, tuple):
                value = list(value)
            setattr(stack[-1], attr, value)
            if until is not None:
                if until > 1:
                    until -= 1
                else:
                    until = None
                    stack.pop()
    return song
