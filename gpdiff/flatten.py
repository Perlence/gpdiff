import copy

def flatten(song):
    result = []
    tracks, song.tracks = song.tracks, []
    newSong = copy.copy(song)
    song.tracks = tracks
    result.append(newSong)
    for track in tracks:
        measures, track.measures = track.measures, []
        newTrack = copy.copy(track)
        track.measures = measures
        result.append(newTrack)
        for measure in measures:
            newMeasure = copy.copy(measure)
            result.append(newMeasure)
        result.append('end')
    result.append('end')
    
    return result