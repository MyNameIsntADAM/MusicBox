from sys import byteorder
from array import array
from struct import pack

import pyaudio
import wave
import sys, select, termios, tty, os, time

THRESHOLD = 100
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100
START = 12
LENGTH = 12

def is_silent(snd_data):
    return max(snd_data) < THRESHOLD

def normalize(snd_data):
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r

def trim(snd_data):

    def _trim(snd_data):
        snd_started = False
        r = array('h')

        for i in snd_data:
            if not snd_started and abs(i) > THRESHOLD:
                snd_started = True
                r.append(i)
            elif snd_started:
                r.append(i)
        return r

    snd_data = _trim(snd_data)

    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data

def keyPressed():
    i, o, e = select.select([sys.stdin], [], [], 0.0)
    for s in i:
        if s == sys.stdin:
            input = sys.stdin.readline()
            return True
    return False

def record():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
            input=True, output=True,
            frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False
    recording = True

    r = array('h')

    while 1:
        
        snd_data = array('h', stream.read(CHUNK_SIZE))
        
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)

        if keyPressed() == True:
            break

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True

        #if snd_started and num_silent > 30:
        #    print("Silence detected. Stopping recording and writing to file")
        #    break

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    return sample_width, r

def record_to_file(path):
    sample_width, data = record()
    data = pack('<' + ('h'*len(data)), *data)

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()

if __name__ == '__main__':
    while 1:
        print("RECORDING NEW AUDIO.")
        record_to_file('output.wav')
        print("Done. Written to output.wav")
        
        wf = wave.open('output.wav', mode='rb')
        p = pyaudio.PyAudio()
        chunk = 1024
        stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
                channels = wf.getnchannels(),
                rate = wf.getframerate(),
                output = True)

        #PLAYBACK
        data = wf.readframes(chunk)
        pos = wf.getnframes() - START*RATE
        if pos < 0:
            pos = 0
        wf.setpos(pos)
        n_frames = int(LENGTH*RATE)

        frames = wf.readframes(n_frames)
        stream.write(frames)
        
       # print("Press ENTER to record new audio.")
       # while 1:
       #     if keyPressed() == True:
       #         break

        print("Starting new audio recording.")
        
