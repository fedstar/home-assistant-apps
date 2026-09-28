# Changelog

# 1.3.0

- Added opt-in lossless UDP capture of robot and server packets in `/data/captures/packets.jsonl` for LR3 protocol analysis. Capture does not transmit commands or change the existing relay.
- Capture records UTC timestamps, source and destination, exact payload hex, decoded text, and tentative command, device ID, sequence, and checksum fields.

# 1.2.5
- Added additional error code states

# 1.2.4
- Added app icon

# 1.2.3
- Fixed a flaw in the local AOK response that was causing the litter robot's memory to overflow after a few hours

# 1.2.2
- Adjust script so that server responses are properly routed

# 1.2.1
- Added logging for local and Whisker server responses
