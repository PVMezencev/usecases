import asyncio
import queue
import sys

import numpy as np
import sounddevice as sd

q = queue.Queue()

SAID = False
ITER = 500
COUNTER = 0


async def record_buffer(buffer, **kwargs):
    def callback(indata, frame_count, time_info, status):
        if status:
            print(status)
        volume_norm = np.linalg.norm(indata) * 10
        global ITER
        global SAID
        if SAID:
            if ITER > 0:
                ITER -= 1
            else:
                SAID = False
        else:
            ITER = 500
        if int(volume_norm) > 60:
            print(int(volume_norm))
            asyncio.run(voice())

    stream = sd.InputStream(callback=callback, dtype=buffer.dtype,
                            channels=buffer.shape[1], **kwargs)

    with stream:
        global SAID
        while True:
            q.get()


async def voice():
    global SAID
    global COUNTER
    if SAID:
        return
    COUNTER += 1
    if COUNTER % 2 == 0:
        cmd = 'echo "Я спрашиваю кто тут?" | RHVoice-client -s Pavel  | aplay'
    else:
        cmd = 'echo "Кто тут?" | RHVoice-client -s Pavel  | aplay'
    print(f'COUNTER: {COUNTER}')
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    SAID = True


async def main(frames=150_000, channels=1, dtype='float32', **kwargs):
    buffer = np.empty((frames, channels), dtype=dtype)
    print('recording buffer ...')
    await record_buffer(buffer, **kwargs)
    print('done')


if __name__ == "__main__":
    SAID = False
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit('\nInterrupted by user')
