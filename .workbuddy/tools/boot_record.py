"""Record actual Android startup and extract time-labelled evidence frames."""
import argparse
import subprocess
import time
from pathlib import Path
import imageio_ffmpeg
from PIL import Image, ImageDraw
from boot_validation import ADB, Device, EVIDENCE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', required=True)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    device = Device(args.serial)
    directory = EVIDENCE / args.name
    directory.mkdir(exist_ok=True)
    remote = '/sdcard/' + args.name + '.mp4'
    record = subprocess.Popen([str(ADB), '-s', args.serial, 'shell', 'screenrecord',
                               '--time-limit', '14', '--bit-rate', '4000000', remote],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(.4)
    result = device.scenario(args.name, '[BootSequence] GameReady', 45)
    out, error = record.communicate(timeout=25)
    if record.returncode:
        raise RuntimeError(error.decode('utf-8', 'replace'))
    video = directory / 'startup.mp4'
    device.adb('pull', remote, video)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    timestamps = [2.8, 3.2, 3.6, 4, 4.4, 4.8, 5.2, 5.6, 6, 6.4, 7, 8]
    sheet = Image.new('RGB', (1600, 750), '#101720')
    draw = ImageDraw.Draw(sheet)
    for index, stamp in enumerate(timestamps):
        frame = directory / ('frame-' + str(stamp) + '.png')
        subprocess.run([ffmpeg, '-loglevel', 'error', '-y', '-ss', str(stamp), '-i', str(video),
                        '-frames:v', '1', str(frame)], check=True)
        if frame.exists():
            with Image.open(frame) as picture:
                picture.thumbnail((400, 225))
                sheet.paste(picture, ((index % 4) * 400, (index // 4) * 250))
            draw.text(((index % 4) * 400 + 8, (index // 4) * 250 + 226), str(stamp) + ' seconds', fill='white')
    sheet.save(directory / 'contact-sheet.png')
    assert result['matched'] and not result['issues'], result


if __name__ == '__main__':
    main()
