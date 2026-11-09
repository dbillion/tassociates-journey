import subprocess
import os

ASSETS = '/home/deeone/tassociates-journey/assets'
VID = f'{ASSETS}/vid'
WORK = '/tmp/tassociates-clips'
os.makedirs(VID, exist_ok=True)
os.makedirs(WORK, exist_ok=True)

FPS = 24
DIVE_SEC = 6
DIVE_FRAMES = DIVE_SEC * FPS # 144 frames
CONN_SEC = 3
CONN_FRAMES = CONN_SEC * FPS # 72 frames

def run(cmd):
    print('Running:', ' '.join(cmd[:6]) + '...')
    subprocess.check_call(cmd)

print('--- Generating Dives ---')

# Dive 1: Table - slow cinematic push-in
run([
    'ffmpeg', '-v', 'error', '-y',
    '-loop', '1', '-i', f'{ASSETS}/table.webp',
    '-vf', f'zoompan=z=\'min(zoom+0.0012,1.20)\':x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':d={DIVE_FRAMES}:s=1920x1080:fps={FPS}',
    '-t', str(DIVE_SEC),
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    f'{WORK}/dive_table.mp4'
])

# Dive 2: Hands - macro focus push-in
run([
    'ffmpeg', '-v', 'error', '-y',
    '-loop', '1', '-i', f'{ASSETS}/hands.webp',
    '-vf', f'zoompan=z=\'min(zoom+0.0013,1.22)\':x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':d={DIVE_FRAMES}:s=1920x1080:fps={FPS}',
    '-t', str(DIVE_SEC),
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    f'{WORK}/dive_hands.mp4'
])

# Dive 3: Door - walking forward into warm sunlight
run([
    'ffmpeg', '-v', 'error', '-y',
    '-loop', '1', '-i', f'{ASSETS}/door.webp',
    '-vf', f'zoompan=z=\'min(zoom+0.0015,1.25)\':x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':d={DIVE_FRAMES}:s=1920x1080:fps={FPS}',
    '-t', str(DIVE_SEC),
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    f'{WORK}/dive_door.mp4'
])

print('--- Extracting Seam Boundary Frames ---')
run(['ffmpeg', '-v', 'error', '-y', '-sseof', '-0.1', '-i', f'{WORK}/dive_table.mp4', '-frames:v', '1', f'{WORK}/last_table.png'])
run(['ffmpeg', '-v', 'error', '-y', '-ss', '0', '-i', f'{WORK}/dive_hands.mp4', '-frames:v', '1', f'{WORK}/first_hands.png'])
run(['ffmpeg', '-v', 'error', '-y', '-sseof', '-0.1', '-i', f'{WORK}/dive_hands.mp4', '-frames:v', '1', f'{WORK}/last_hands.png'])
run(['ffmpeg', '-v', 'error', '-y', '-ss', '0', '-i', f'{WORK}/dive_door.mp4', '-frames:v', '1', f'{WORK}/first_door.png'])

print('--- Generating Frame-Locked Connectors ---')
# Connector 1: from last_table to first_hands with smooth zoom transition
run([
    'ffmpeg', '-v', 'error', '-y',
    '-loop', '1', '-t', str(CONN_SEC), '-i', f'{WORK}/last_table.png',
    '-loop', '1', '-t', str(CONN_SEC), '-i', f'{WORK}/first_hands.png',
    '-filter_complex', f'[0][1]xfade=transition=fade:duration=1.2:offset=0.9,format=yuv420p',
    '-c:v', 'libx264',
    f'{WORK}/conn_1.mp4'
])

# Connector 2: from last_hands to first_door with smooth zoom transition
run([
    'ffmpeg', '-v', 'error', '-y',
    '-loop', '1', '-t', str(CONN_SEC), '-i', f'{WORK}/last_hands.png',
    '-loop', '1', '-t', str(CONN_SEC), '-i', f'{WORK}/first_door.png',
    '-filter_complex', f'[0][1]xfade=transition=fade:duration=1.2:offset=0.9,format=yuv420p',
    '-c:v', 'libx264',
    f'{WORK}/conn_2.mp4'
])

print('--- Encoding Final Desktop Clips (1080p, GOP 8, faststart) ---')
clips = [
    (f'{WORK}/dive_table.mp4', f'{VID}/table.mp4'),
    (f'{WORK}/conn_1.mp4', f'{VID}/conn1.mp4'),
    (f'{WORK}/dive_hands.mp4', f'{VID}/hands.mp4'),
    (f'{WORK}/conn_2.mp4', f'{VID}/conn2.mp4'),
    (f'{WORK}/dive_door.mp4', f'{VID}/door.mp4'),
]

for src, dst in clips:
    run([
        'ffmpeg', '-v', 'error', '-y', '-i', src,
        '-an', '-vf', 'unsharp=5:5:0.8:5:5:0.0',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p',
        '-g', '8', '-keyint_min', '8', '-sc_threshold', '0',
        '-movflags', '+faststart', dst
    ])
    print(f'Encoded {dst} ({os.path.getsize(dst)} bytes)')

print('--- Encoding Final Mobile Clips (720p, GOP 4, faststart) ---')
mobile_clips = [
    (f'{WORK}/dive_table.mp4', f'{VID}/table-m.mp4'),
    (f'{WORK}/conn_1.mp4', f'{VID}/conn1-m.mp4'),
    (f'{WORK}/dive_hands.mp4', f'{VID}/hands-m.mp4'),
    (f'{WORK}/conn_2.mp4', f'{VID}/conn2-m.mp4'),
    (f'{WORK}/dive_door.mp4', f'{VID}/door-m.mp4'),
]

for src, dst in mobile_clips:
    run([
        'ffmpeg', '-v', 'error', '-y', '-i', src,
        '-an', '-vf', 'scale=-2:720,unsharp=5:5:0.6:5:5:0.0',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p',
        '-g', '4', '-keyint_min', '4', '-sc_threshold', '0',
        '-movflags', '+faststart', dst
    ])
    print(f'Encoded {dst} ({os.path.getsize(dst)} bytes)')

print('ALL CLIPS GENERATED SUCCESSFULLY.')
