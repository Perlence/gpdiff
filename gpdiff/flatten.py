import copy
import guitarpro as gp

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
    return result

def restore(sequence):
    song = None
    for e in sequence:
        if isinstance(e, gp.Song):
            song = e
        elif isinstance(e, gp.Track):
            song.tracks.append(e)
        elif isinstance(e, gp.Measure):
            song.tracks[-1].measures.append(e)
    song.measureHeaders = [measure.header for measure in song.tracks[0].measures]
    return song
