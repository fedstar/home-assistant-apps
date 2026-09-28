"""Lossless, opt-in UDP packet capture for LR3 protocol research.

The decoded fields are tentative. ``raw_hex`` is the authoritative packet data.
Capture failures must never interfere with the proxy's forwarding path.
"""

import datetime
import json
import os


CAPTURE_DIR = "/data/captures"
CAPTURE_FILE = os.path.join(CAPTURE_DIR, "packets.jsonl")
MAX_FILE_BYTES = 20 * 1024 * 1024
BACKUP_COUNT = 5


def parse_packet(payload):
    """Extract visible LR3 fields without changing the original payload."""
    text = payload.rstrip(b"\r\n").decode("utf-8", errors="replace")
    parts = text.split(",")
    fields = {"kind": "unknown", "field_count": len(parts)}

    if len(parts) == 5 and parts[0].startswith("<") and parts[1] == "LR3":
        fields.update(
            kind="command",
            command=parts[0],
            model=parts[1],
            device_id=parts[2],
            sequence=parts[3],
            checksum=parts[4],
        )
    elif len(parts) == 2 and parts[0] in ("AOK", "NOK"):
        fields.update(kind="ack", ack=parts[0], device_id=parts[1])
    elif len(parts) == 12 and parts[0].startswith(">LR3"):
        fields.update(
            kind="status",
            model=parts[0],
            device_id=parts[1],
            status=parts[4],
            wait=parts[5],
            night_light=parts[6],
            panel_lock=parts[8],
            sequence=parts[10],
            checksum=parts[11],
        )

    return fields


class PacketCapture:
    def __init__(self, enabled=False, path=CAPTURE_FILE,
                 max_file_bytes=MAX_FILE_BYTES, backup_count=BACKUP_COUNT):
        self.enabled = enabled
        self.path = path
        self.max_file_bytes = max_file_bytes
        self.backup_count = backup_count

    def record(self, direction, payload, source, destination, ingress_port):
        """Append one complete UDP datagram as JSONL; return the record."""
        if not self.enabled:
            return None

        record = {
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "direction": direction,
            "ingress_port": ingress_port,
            "source": {"ip": source[0], "port": source[1]},
            "destination": (
                {"ip": destination[0], "port": destination[1]}
                if destination else None
            ),
            "length": len(payload),
            "raw_hex": payload.hex(),
            "decoded_text": payload.decode("utf-8", errors="replace"),
            "fields": parse_packet(payload),
        }
        line = (json.dumps(record, separators=(",", ":")) + "\n").encode("utf-8")

        directory = os.path.dirname(self.path)
        os.makedirs(directory, mode=0o700, exist_ok=True)
        os.chmod(directory, 0o700)
        if os.path.exists(self.path) and os.path.getsize(self.path) + len(line) > self.max_file_bytes:
            self._rotate()

        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.fchmod(fd, 0o600)
            view = memoryview(line)
            while view:
                view = view[os.write(fd, view):]
        finally:
            os.close(fd)
        return record

    def _rotate(self):
        if self.backup_count < 1:
            os.remove(self.path)
            return
        oldest = "%s.%d" % (self.path, self.backup_count)
        if os.path.exists(oldest):
            os.remove(oldest)
        for index in range(self.backup_count - 1, 0, -1):
            source = "%s.%d" % (self.path, index)
            if os.path.exists(source):
                os.replace(source, "%s.%d" % (self.path, index + 1))
        os.replace(self.path, self.path + ".1")
