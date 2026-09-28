# LR3 local control research

## Current result

The proxy still relays Whisker traffic and publishes local MQTT status. It does
**not** generate or send local control commands. The optional packet capture is
the first step toward finding a valid command algorithm.

No packets from Fedor's robots have been analyzed yet. The command and checksum
fields below are based on [an earlier LR3 protocol investigation](https://github.com/mbafford/litter-robot-to-mqtt),
not on a confirmed local experiment.

This approach only applies if these specific robots use the older plaintext
UDP dispatch protocol. [A separate LR3 firmware investigation](https://www.elttam.com/blog/re-of-lr3)
found an AWS IoT/TLS variant. The HA integration's "Litter-Robot 3" model label
does not establish which network protocol a physical unit uses. An AdGuard DNS
record from the owner's `LR3-1` matches the AWS IoT endpoint in that
investigation. This proves the robot looked up that endpoint; it does **not**
rule out a separate UDP dispatch connection. Neither robot's UDP behavior has
been established. Before redirecting DNS, check whether each robot actually
queries `dispatch.prod.iothings.site` (or another legacy dispatch host) and
sends UDP traffic. Adam Thompson's proxy README does not state that AWS IoT
queries make a robot incompatible.

## Known packet shape and uncertainties

- A server command appears as `<COMMAND,LR3,DEVICE_ID,SEQUENCE,CHECKSUM`.
- A robot status appears as `>LR3,DEVICE_ID,...,SEQUENCE,CHECKSUM`.
- The earlier investigation reports that the robot rejects commands if the
  checksum is wrong or the command sequence does not advance.
- The command counter's relationship to robot status counters is unconfirmed.
- The checksum algorithm, byte order, framing bytes, and whether a keyed secret
  is involved are unconfirmed.
- The proxy's existing relay uses UDP port 2001 for robot traffic and sends
  server responses to robot port 2000. The server reply may arrive on either
  proxy socket because of NAT.

## Capture format

When `capture_packets: true`, the add-on records every datagram it handles to
`/data/captures/packets.jsonl`. Each JSON line has a UTC timestamp, direction,
ingress port, source and intended destination, byte length, `raw_hex`, decoded
text, and tentative parsed fields. `raw_hex` preserves the exact bytes, including
line endings and non-UTF-8 data. Files rotate at 20 MiB with five backups.

The add-on also writes `LR3_CAPTURE` log lines for server command packets, so
the first controlled experiment can be analyzed from copied add-on logs. Logs
and capture files contain device identifiers; review them before sharing.

Capture does not send extra network packets and does not change the relay.
Errors writing a capture are logged and do not stop packet forwarding.

## First experiment

1. Confirm the selected robot uses the legacy UDP dispatch host. Then run the
   updated proxy with `capture_packets: true` and keep Internet access
   so the Whisker app or HA integration can generate legitimate commands.
2. Confirm both robots continue reporting status and that the Whisker app still
   works.
3. On **one** robot, toggle only the night light ON and OFF several times,
   noting exact local times with timezone. Leave at least 10 seconds between
   changes. Do not trigger Cycle, Power, or Reset during this experiment.
4. Copy the add-on log section containing the `LR3_CAPTURE` lines. Make a CSV
   with `timestamp,label`, for example:

   ```csv
   timestamp,label
   2026-09-27T22:00:00-04:00,white robot night light on
   2026-09-27T22:00:15-04:00,white robot night light off
   ```

5. Analyze it locally:

   ```sh
   python3 capture_inspect.py app.log --annotations actions.csv
   ```

6. Compare repeated command IDs, sequence changes, checksums, and subsequent
   robot status. Treat an algorithm as a hypothesis until it predicts *held-out*
   captures from both night-light states and multiple sequence values.

## Next stages

- Build a checksum search tool driven by the real captured bytes, covering
  plausible CRC and non-CRC transforms and framing choices.
- Validate any candidate against new captures collected after it was proposed.
- Only after the generator is validated, add a guarded test sender limited to
  Night Light ON/OFF on a selected known robot and verify the status reply.
- Add MQTT controls for the remaining commands after local sending works.

## Observation log

| Date | Observation | Status |
| --- | --- | --- |
| 2026-09-27 | Fork cloned and capture code added; no robot packet sample yet. | Code only |
| 2026-09-27 | Owner's AdGuard log shows `LR3-1` queried an AWS IoT endpoint matching the published LR3 onboarding analysis. IP and full endpoint intentionally omitted here. | AWS DNS observed; UDP path unverified |
