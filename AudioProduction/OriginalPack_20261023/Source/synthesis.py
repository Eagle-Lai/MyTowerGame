"""Original Freedom Tower instruments and 24-bit audio utilities. No audio samples."""
from __future__ import annotations
import hashlib
import json
import math
import subprocess
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / '.dependencies'))
import numpy as np
from scipy import signal
import imageio_ffmpeg

SR = 48000
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def rng_for(key: str):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'little'))


def hz(note):
    return 440.0 * 2.0 ** ((np.asarray(note) - 69.0) / 12.0)


def clock(duration):
    return np.arange(max(1, round(duration * SR)), dtype=np.float64) / SR


def edge(x, attack=.003, release=.03):
    y = np.array(x, dtype=np.float32, copy=True)
    a, r = min(len(y), round(attack * SR)), min(len(y), round(release * SR))
    if a:
        ramp = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
        y[:a] *= ramp[:, None] if y.ndim == 2 else ramp
    if r:
        ramp = np.sin(np.linspace(np.pi / 2, 0, r)) ** 2
        y[-r:] *= ramp[:, None] if y.ndim == 2 else ramp
    return y


def filtered(x, low=None, high=None):
    if low and high:
        sos = signal.butter(3, [low, high], btype='bandpass', fs=SR, output='sos')
    elif low:
        sos = signal.butter(3, low, btype='highpass', fs=SR, output='sos')
    else:
        sos = signal.butter(3, high, btype='lowpass', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=0).astype(np.float32)


def instrument(kind, note, duration, strength=1.0, key=''):
    """Finite envelopes: every event, including its release, can wrap over a loop."""
    rng = rng_for(f'{kind}:{note}:{duration}:{key}')
    tail = {'pad': .48, 'lead': .20, 'bell': .8, 'pluck': .3, 'bass': .06}.get(kind, .05)
    t = clock(duration + tail)
    f = float(hz(note))
    phase = 2 * np.pi * f * t
    release = np.minimum(1, np.maximum(0, (duration + tail - t) / tail)) ** 2
    if kind == 'pad':
        y = np.zeros(len(t))
        for harmonic, level in [(1, .49), (2, .16), (3, .09), (4, .035)]:
            for detune in [-.0018, .0018]:
                y += level * .5 * np.sin(phase * harmonic * (1 + detune) + .06 * np.sin(2*np.pi*.31*t))
        env = (1 - np.exp(-t / .23)) * release
        y *= env * (.94 + .06*np.sin(2*np.pi*.17*t))
    elif kind == 'pluck':
        y = sum(a * np.sin(phase*k + .25/k) * np.exp(-t*(2.3 + k*.7))
                for k, a in [(1,.65),(2,.22),(3,.13),(4,.065),(6,.025)])
        y += .045 * filtered(rng.normal(size=len(t)), high=2600) * np.exp(-t*90)
        y *= release
    elif kind == 'bell':
        y = sum(a*np.sin(phase*k)*np.exp(-t*d)
                for k,a,d in [(1,.55,2.8),(2,.17,4.0),(3,.065,6.0),(4.01,.04,8.0)])
        y *= release
    elif kind == 'lead':
        vibrato = .019*np.sin(2*np.pi*4.7*t)*np.minimum(t/.2, 1)
        y = (.65*np.sin(phase+vibrato) + .14*np.sin(2*phase+vibrato)
             + .075*np.sin(3*phase) + .025*np.sin(5*phase))
        y *= (1-np.exp(-t/.014)) * (.66+.34*np.exp(-t*5)) * release
    elif kind == 'bass':
        y = (.78*np.sin(phase)+.13*np.sin(2*phase)+.065*np.sin(3*phase))
        y *= np.exp(-t*1.6) * release
    else:
        raise ValueError(kind)
    return edge(y * strength, .006 if kind != 'pad' else .04, .012)


def percussion(kind, strength=1., key=''):
    rng = rng_for(f'drum:{kind}:{key}')
    duration = {'kick':.36,'snare':.23,'hat':.095,'openhat':.28,'tom':.3,'shaker':.12}[kind]
    t = clock(duration)
    noise = rng.normal(size=len(t))
    if kind == 'kick':
        phase = 2*np.pi*(45*t + (115-45)*.022*(1-np.exp(-t/.022)))
        y = np.sin(phase)*np.exp(-t*14)+.08*filtered(noise,high=1600)*np.exp(-t*180)
    elif kind == 'snare':
        y = (.38*np.sin(2*np.pi*185*t)*np.exp(-t*26)
             + .47*filtered(noise,low=850,high=6200)*np.exp(-t*25))
    elif kind in ('hat','openhat','shaker'):
        y = filtered(noise, low=4200, high=12500)*np.exp(-t*(38 if kind=='hat' else 16))*.52
    else:
        phase = 2*np.pi*(86*t+55*.04*(1-np.exp(-t/.04)))
        y = np.sin(phase)*np.exp(-t*17) + .03*filtered(noise,high=2500)*np.exp(-t*40)
    return edge(y*strength,.001,.02)


def add(dest, mono, at, gain=1., pan=0., circular=False):
    start = round(at*SR)
    x = np.asarray(mono, dtype=np.float32)
    if dest.ndim == 2 and x.ndim == 1:
        p = np.clip(pan,-1,1)
        x = x[:,None]*np.array([np.cos((p+1)*np.pi/4),np.sin((p+1)*np.pi/4)],dtype=np.float32)
    elif dest.ndim == 1 and x.ndim == 2:
        x = x.mean(axis=1)
    if circular:
        offset = 0
        while offset < len(x):
            s = (start+offset) % len(dest)
            n = min(len(dest)-s,len(x)-offset)
            dest[s:s+n] += x[offset:offset+n]*gain
            offset += n
    else:
        skip = max(0,-start)
        start = max(0,start)
        n = min(len(dest)-start,len(x)-skip)
        if n>0:
            dest[start:start+n] += x[skip:skip+n]*gain


def ambience(x, amount=.17, circular=False):
    """Sparse, damped stereo room. No convolution recordings or external IRs."""
    y = np.array(x,copy=True)
    for sec,gain in [(.071,.44),(.113,.35),(.173,.29),(.239,.22),(.337,.15),(.479,.10)]:
        d = round(sec*SR)
        if circular:
            wet = np.roll(x,d,axis=0)
        else:
            wet = np.zeros_like(x)
            wet[d:] = x[:-d]
        if x.ndim==2:
            wet = wet[:,::-1]
        # Stable filter state at circular boundary.
        if circular:
            wet = filtered(np.concatenate([wet[-SR:],wet]),high=4300)[SR:]
        else:
            wet = filtered(wet,high=4300)
        y += wet*(amount*gain)
    return y


def write_wav(path, x):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    y = np.asarray(x)
    if y.ndim==1:
        y=y[:,None]
    # Deterministic TPDF dither at the 24-bit quantizer, with no extra audio samples.
    rng = rng_for(path.stem+':dither')
    flat = y.reshape(-1)
    with wave.open(str(path),'wb') as out:
        out.setnchannels(y.shape[1]); out.setsampwidth(3); out.setframerate(SR)
        for start in range(0,len(flat),SR*4):
            a=flat[start:start+SR*4]
            d=(rng.random(len(a))-rng.random(len(a))) / 8388608.
            q=np.rint(np.clip(a+d,-1,1-1/8388608)*8388608).astype(np.int32)
            b=np.empty((len(q),3),np.uint8)
            b[:,0]=q&255; b[:,1]=(q>>8)&255; b[:,2]=(q>>16)&255
            out.writeframes(b.tobytes())


def read_wav(path):
    with wave.open(str(path),'rb') as f:
        rate,channels,width=f.getframerate(),f.getnchannels(),f.getsampwidth()
        raw=f.readframes(f.getnframes())
    if width!=3 or rate!=SR:
        raise ValueError(f'Unexpected WAV format: {path}')
    u=np.frombuffer(raw,np.uint8).reshape(-1,3).astype(np.int32)
    q=u[:,0] | (u[:,1]<<8) | (u[:,2]<<16)
    q=(q^0x800000)-0x800000
    return (q.astype(np.float32)/8388608).reshape(-1,channels)


def loudness(path):
    cmd=[FFMPEG,'-hide_banner','-nostats','-i',str(path),'-af',
         'loudnorm=I=-17:TP=-1:LRA=11:print_format=json','-f','null','-']
    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    text=r.stderr.decode('utf-8',errors='replace')
    data=json.loads(text[text.rfind('{'):text.rfind('}')+1])
    return {k:float(v) for k,v in data.items() if k != 'normalization_type'}


def master_music(x,path,target=-17.2):
    # Gentle bus saturation before transparent, static loudness gain.
    x=x.astype(np.float32)
    x-=x.mean(axis=0)
    x=np.tanh(x*1.15)
    work=HERE/'_work'/f'{Path(path).stem}_measurement.wav'
    write_wav(work,x/max(1.,float(np.max(np.abs(x)))/.85))
    m=loudness(work)
    y=read_wav(work)
    gain=min(target-m['input_i'],-1.35-m['input_tp'])
    y *= 10**(gain/20)
    write_wav(path,y)
    work.unlink()
    return {'measured_before_gain':m,'gain_db':gain}


def master_sfx(x,peak_db=-5.,loop=False):
    x=np.asarray(x,dtype=np.float32)
    x-=x.mean(axis=0)
    if not loop:
        x=filtered(x,low=25)
    x=np.tanh(x*1.1)
    if not loop:
        x=edge(x,.001,.025)
    true_peak=float(np.max(np.abs(signal.resample_poly(x,4,1,axis=0))))
    if true_peak>1e-9:
        x *= 10**(peak_db/20)/true_peak
    return x


def encode_mp3(source,target,quality='3'):
    Path(target).parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([FFMPEG,'-v','error','-y','-i',str(source),'-codec:a','libmp3lame',
                    '-q:a',str(quality),str(target)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
