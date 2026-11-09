import subprocess
import os

ASSETS = '/home/deeone/tassociates-journey/assets'
VID = f'{ASSETS}/vid'
WORK = '/tmp/tassociates-chain'

os.makedirs(VID, exist_ok=True)
os.makedirs(WORK, exist_ok=True)

# Standard dimensions for crisp 16:9 playback
WIDTH = 1280
HEIGHT = 720
FPS = 24

def run(cmd):
    print("Running:", " ".join(cmd[:8]))
    subprocess.check_call(cmd)

print("=== 1. Normalizing Dives to Standard 720p 24fps ===")
for name in ['table', 'hands', 'door']:
    src = f'{ASSETS}/{name}.mp4'
    dst = f'{WORK}/dive_{name}.mp4'
    # Scale to 1280x720 without distorting aspect ratio, ensure 24fps
    run([
        'ffmpeg', '-v', 'error', '-y', '-i', src,
        '-an',
        '-vf', f'scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}',
        '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p',
        dst
    ])
    print(f"Normalized dive_{name}.mp4")

print("=== 2. Extracting Still Posters & Boundary Frames ===")
# Poster stills
run(['ffmpeg', '-v', 'error', '-y', '-ss', '0', '-i', f'{WORK}/dive_table.mp4', '-frames:v', '1', '-c:v', 'libwebp', '-quality', '90', f'{ASSETS}/table.webp'])
run(['ffmpeg', '-v', 'error', '-y', '-ss', '0', '-i', f'{WORK}/dive_hands.mp4', '-frames:v', '1', '-c:v', 'libwebp', '-quality', '90', f'{ASSETS}/hands.webp'])
run(['ffmpeg', '-v', 'error', '-y', '-ss', '0', '-i', f'{WORK}/dive_door.mp4', '-frames:v', '1', '-c:v', 'libwebp', '-quality', '90', f'{ASSETS}/door.webp'])

# Seam boundary frames
run(['ffmpeg', '-v', 'error', '-y', '-sseof', '-0.08', '-i', f'{WORK}/dive_table.mp4', '-frames:v', '1', f'{WORK}/last_table.png'])
run(['ffmpeg', '-v', 'error', '-y', '-ss', '0', '-i', f'{WORK}/dive_hands.mp4', '-frames:v', '1', f'{WORK}/first_hands.png'])
run(['ffmpeg', '-v', 'error', '-y', '-sseof', '-0.08', '-i', f'{WORK}/dive_hands.mp4', '-frames:v', '1', f'{WORK}/last_hands.png'])
run(['ffmpeg', '-v', 'error', '-y', '-ss', '0', '-i', f'{WORK}/dive_door.mp4', '-frames:v', '1', f'{WORK}/first_door.png'])

print("=== 3. Creating Frame-Locked Seamless Connectors ===")
CONN_DUR = 2.5
XFADE_DUR = 1.0
OFFSET = CONN_DUR - XFADE_DUR

# Connector 1: table -> hands
run([
    'ffmpeg', '-v', 'error', '-y',
    '-loop', '1', '-t', str(CONN_DUR), '-i', f'{WORK}/last_table.png',
    '-loop', '1', '-t', str(CONN_DUR), '-i', f'{WORK}/first_hands.png',
    '-filter_complex', f'[0:v][1:v]xfade=transition=fade:duration={XFADE_DUR}:offset={OFFSET},format=yuv420p',
    '-c:v', 'libx264', '-crf', '19',
    f'{WORK}/conn_1.mp4'
])

# Connector 2: hands -> door
run([
    'ffmpeg', '-v', 'error', '-y',
    '-loop', '1', '-t', str(CONN_DUR), '-i', f'{WORK}/last_hands.png',
    '-loop', '1', '-t', str(CONN_DUR), '-i', f'{WORK}/first_door.png',
    '-filter_complex', f'[0:v][1:v]xfade=transition=fade:duration={XFADE_DUR}:offset={OFFSET},format=yuv420p',
    '-c:v', 'libx264', '-crf', '19',
    f'{WORK}/conn_2.mp4'
])

print("=== 4. Final Scrub Encoding for Desktop (GOP 8, faststart) ===")
chain = [
    (f'{WORK}/dive_table.mp4', f'{VID}/table.mp4'),
    (f'{WORK}/conn_1.mp4', f'{VID}/conn1.mp4'),
    (f'{WORK}/dive_hands.mp4', f'{VID}/hands.mp4'),
    (f'{WORK}/conn_2.mp4', f'{VID}/conn2.mp4'),
    (f'{WORK}/dive_door.mp4', f'{VID}/door.mp4'),
]

for src, dst in chain:
    run([
        'ffmpeg', '-v', 'error', '-y', '-i', src,
        '-an', '-vf', 'unsharp=5:5:0.6:5:5:0.0',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '21', '-pix_fmt', 'yuv420p',
        '-g', '8', '-keyint_min', '8', '-sc_threshold', '0',
        '-movflags', '+faststart', dst
    ])
    print(f"Encoded {dst} ({os.path.getsize(dst)} bytes)")

print("=== 5. Final Scrub Encoding for Mobile (GOP 4, 720p, faststart) ===")
mobile_chain = [
    (f'{WORK}/dive_table.mp4', f'{VID}/table-m.mp4'),
    (f'{WORK}/conn_1.mp4', f'{VID}/conn1-m.mp4'),
    (f'{WORK}/dive_hands.mp4', f'{VID}/hands-m.mp4'),
    (f'{WORK}/conn_2.mp4', f'{VID}/conn2-m.mp4'),
    (f'{WORK}/dive_door.mp4', f'{VID}/door-m.mp4'),
]

for src, dst in mobile_chain:
    run([
        'ffmpeg', '-v', 'error', '-y', '-i', src,
        '-an', '-vf', 'scale=960:540,unsharp=5:5:0.5:5:5:0.0',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p',
        '-g', '4', '-keyint_min', '4', '-sc_threshold', '0',
        '-movflags', '+faststart', dst
    ])
    print(f"Encoded mobile {dst} ({os.path.getsize(dst)} bytes)")

print("=== PIPELINE INTEGRATION COMPLETE ===")
