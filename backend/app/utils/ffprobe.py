import subprocess
import json
from pathlib import Path
from ..utils.logger import logger


def get_metadata(file_path: str) -> dict:
    """Return metadata dict with keys like 'duration' and 'tags'. Requires ffprobe installed."""
    p = Path(file_path)
    if not p.exists():
        return {}
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        str(p),
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        data = json.loads(out)
        fmt = data.get('format', {})
        duration = fmt.get('duration')
        tags = fmt.get('tags', {})
        return {'duration': float(duration) if duration else None, 'tags': tags}
    except FileNotFoundError:
        logger.warning('ffprobe not found on PATH; metadata extraction disabled')
        return {}
    except Exception:
        logger.exception('ffprobe error')
        return {}
