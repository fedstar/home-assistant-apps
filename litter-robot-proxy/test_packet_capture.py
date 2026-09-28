import json
import os
import tempfile
import unittest

from packet_capture import PacketCapture, parse_packet
from capture_inspect import read_records


class PacketCaptureTests(unittest.TestCase):
    def test_parses_command_and_preserves_exact_bytes(self):
        payload = b"<N1,LR3,example-device,06EB,7AE2E42F\r\n"
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "capture", "packets.jsonl")
            capture = PacketCapture(enabled=True, path=path)
            capture.record("server_to_robot", payload, ("203.0.113.1", 2001),
                           ("192.0.2.5", 2000), 2001)
            with open(path, encoding="utf-8") as stream:
                saved = json.loads(stream.readline())

            self.assertEqual(bytes.fromhex(saved["raw_hex"]), payload)
            self.assertEqual(saved["length"], len(payload))
            self.assertEqual(saved["source"], {"ip": "203.0.113.1", "port": 2001})
            self.assertEqual(saved["destination"], {"ip": "192.0.2.5", "port": 2000})
            self.assertEqual(saved["ingress_port"], 2001)
            self.assertEqual(saved["fields"]["command"], "<N1")
            self.assertEqual(saved["fields"]["sequence"], "06EB")
            self.assertEqual(saved["fields"]["checksum"], "7AE2E42F")
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)

    def test_parses_status_and_ack(self):
        status = b">LR3,device,H,AC,Rdy,W7,NL1,SM0,PL0,CS0100,38FA,8A23DAFE\r\n"
        fields = parse_packet(status)
        self.assertEqual(fields["kind"], "status")
        self.assertEqual(fields["sequence"], "38FA")
        self.assertEqual(fields["night_light"], "NL1")
        self.assertEqual(parse_packet(b"AOK,device\r\n")["kind"], "ack")
        self.assertEqual(parse_packet(b"\xff\x00")["kind"], "unknown")

    def test_disabled_capture_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "packets.jsonl")
            capture = PacketCapture(enabled=False, path=path)
            self.assertIsNone(capture.record("server_to_robot", b"data", ("a", 1), None, 2000))
            self.assertFalse(os.path.exists(path))

    def test_rotation_and_log_inspector(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "packets.jsonl")
            capture = PacketCapture(enabled=True, path=path, max_file_bytes=1, backup_count=2)
            first = capture.record("server_to_robot", b"<N1,LR3,id,0001,abcd", ("a", 1), None, 2000)
            capture.record("server_to_robot", b"<N0,LR3,id,0002,efgh", ("a", 1), None, 2000)
            self.assertTrue(os.path.exists(path + ".1"))
            self.assertEqual(len(list(read_records([path, path + ".1"]))), 2)

            log_path = os.path.join(directory, "app.log")
            with open(log_path, "w", encoding="utf-8") as stream:
                stream.write("INFO LR3_CAPTURE " + json.dumps(first) + "\n")
            self.assertEqual(len(list(read_records([log_path]))), 1)


if __name__ == "__main__":
    unittest.main()
