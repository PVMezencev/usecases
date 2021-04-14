import os.path
import shutil
import sys
import time
from datetime import datetime

from watchdog.observers import Observer

from watchdog.events import FileSystemEventHandler


class CustomEventHandler(FileSystemEventHandler):
    def on_moved(self, event):
        super().on_moved(event)

        what = 'directory' if event.is_directory else 'file'
        print(
            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: Moved {what}: from {event.src_path} to {event.dest_path}")

    def on_created(self, event):
        super().on_created(event)

        what = 'directory' if event.is_directory else 'file'
        print(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: Created {what}: {event.src_path}")
        if str(event.src_path).endswith('~'):
            # Не обрабатываем временные файлы.
            return

        src = str(event.src_path)

        dst_dir = os.path.join(back_path, f"{datetime.utcnow().strftime('%Y-%m-%d')}")
        dst_base_name = os.path.basename(str(event.src_path))
        dst_base_name = f'{datetime.utcnow().timestamp()}-{dst_base_name}'
        dst = os.path.join(dst_dir, dst_base_name)

        copy_to_back(src=src, dst=dst)

    def on_deleted(self, event):
        super().on_deleted(event)

        what = 'directory' if event.is_directory else 'file'
        print(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: Deleted {what}: {event.src_path}")

    def on_modified(self, event):
        super().on_modified(event)

        what = 'directory' if event.is_directory else 'file'
        print(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: Modified {what}: {event.src_path}")
        if str(event.src_path).endswith('~') or what == 'directory':
            # Не обрабатываем временные файлы.
            return

        src = str(event.src_path)

        dst_dir = os.path.join(back_path, f"{datetime.utcnow().strftime('%Y-%m-%d')}")
        dst_base_name = os.path.basename(str(event.src_path))
        dst_base_name = f'{datetime.utcnow().timestamp()}-{dst_base_name}'
        dst = os.path.join(dst_dir, dst_base_name)

        copy_to_back(src=src, dst=dst)


def copy_to_back(src: str, dst: str) -> bool:
    dst_dir = os.path.dirname(dst)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir, mode=0o755, exist_ok=True)
    try:
        shutil.copyfile(src=src, dst=dst)
    except Exception as e:
        print(
            f"EXCEPTION {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}:\n\tshutil.move(src={src}, dst={dst}):\n\t{e}")
        return False
    return True


watch_path = rf'/home/user/watch_path'
back_path = rf'/home/user/back_path'

if len(sys.argv[1:]) < 2:
    print(f'укажите папку для слежения и папку для копирования, например: ./wath_change {watch_path} {back_path}')
    sys.exit(0)


watch_path = rf'{str(sys.argv[1]).strip()}'
back_path = rf'{str(sys.argv[2]).strip()}'

event_handler = CustomEventHandler()

observer = Observer()
observer.schedule(event_handler, watch_path, recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()
