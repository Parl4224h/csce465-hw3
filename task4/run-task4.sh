#!/usr/bin/env bash
set -u

PARSER="/opt/agentsec/legacy_log_parser"
PAYLOAD="/opt/agentsec/payloads/exploit.bin"
MARKERS="/opt/agentsec/markers"

echo "=== Task 4: AppArmor Confinement Test ==="

echo
echo "[1] Checking account"
id agentlab

echo
echo "[2] Checking AppArmor profile"
sudo aa-status | grep -F "$PARSER" || true

echo
echo "[3] Checking payload access"
sudo -u agentlab test -r "$PAYLOAD"
echo "Payload access exit code: $?"

echo
echo "[4] Clearing previous marker output"
sudo find "$MARKERS" -mindepth 1 -maxdepth 1 \
    -type f -delete

echo
echo "[5] Recording start time"
START="$(date --iso-8601=seconds)"
echo "$START" | tee task4-start-time.txt

echo
echo "[6] Running exploit as agentlab"

set +e
sudo -u agentlab -- "$PARSER" "$PAYLOAD" \
    > task4-exploit-stdout.txt \
    2> task4-exploit-stderr.txt
STATUS=$?
set -e

echo "Parser exit code: $STATUS" \
    | tee task4-exit-status.txt

echo
echo "[7] Capturing AppArmor denial logs"

sudo journalctl -k --since "$START" \
    --no-pager -o short-iso \
    | grep -E 'apparmor="DENIED".*legacy_log_parser|profile="/opt/agentsec/legacy_log_parser".*apparmor="DENIED"' \
    > task4-denials.txt || true

echo
echo "[8] Capturing marker directory contents"
sudo ls -la "$MARKERS" \
    > task4-marker-results.txt

echo
echo "[9] Displaying results"
cat task4-exit-status.txt
cat task4-exploit-stdout.txt
cat task4-exploit-stderr.txt

echo
echo "AppArmor denial events:"
cat task4-denials.txt

echo
echo "Marker directory:"
cat task4-marker-results.txt

echo
echo "Evidence files saved."
