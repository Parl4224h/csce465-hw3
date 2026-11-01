
#!/usr/bin/env python3

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARSER = ROOT / "legacy_log_parser_fixed"
EXPLOIT = ROOT / "exploit.bin"


def run_test(name, path, should_accept, expected_size=None):
    result = subprocess.run(
        [str(PARSER), str(path)],
        capture_output=True,
        timeout=5,
        check=False,
    )

    accepted = result.returncode == 0
    passed = accepted == should_accept

    if expected_size is not None and should_accept:
        expected = f"[INFO] Read {expected_size} bytes"
        passed &= expected.encode() in result.stdout

    # Ensure the exploit did not reach win().
    if b"[WIN]" in result.stdout:
        passed = False

    status = "PASS" if passed else "FAIL"

    print(f"[{status}] {name}")
    print(f"  Exit code: {result.returncode}")
    print(f"  Expected: {'accept' if should_accept else 'reject'}")
    print(f"  Actual: {'accepted' if accepted else 'rejected'}")

    if result.stderr:
        print(
            "  stderr:",
            result.stderr.decode(errors="replace").strip(),
        )

    if not passed and result.stdout:
        print(
            "  stdout:",
            result.stdout.decode(errors="replace").strip(),
        )

    return passed


def main():
    if not PARSER.is_file():
        raise SystemExit(f"Missing parser: {PARSER}")

    if not EXPLOIT.is_file():
        raise SystemExit(f"Missing exploit payload: {EXPLOIT}")

    results = []

    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)

        # Test 1: Valid short input.
        short = directory / "short.log"
        short.write_bytes(b"INFO: Valid log entry\n")
        results.append(
            run_test(
                "Valid short input",
                short,
                True,
                short.stat().st_size,
            )
        )

        # Test 2: Exactly 128 bytes.
        maximum = directory / "maximum.log"
        maximum.write_bytes(b"A" * 128)
        results.append(
            run_test(
                "Exactly 128 bytes",
                maximum,
                True,
                128,
            )
        )

        # Test 3: One byte over the limit.
        oversized = directory / "oversized.log"
        oversized.write_bytes(b"B" * 129)
        results.append(
            run_test(
                "129 bytes (one over limit)",
                oversized,
                False,
            )
        )

        # Test 4: Missing file.
        missing = directory / "nonexistent.log"
        results.append(
            run_test(
                "Missing file",
                missing,
                False,
            )
        )

    # Test 5: Original exploit payload.
    exploit_size = EXPLOIT.stat().st_size
    print(f"\nOriginal exploit payload: {exploit_size} bytes")

    marker = ROOT / "markers" / "ret2win.txt"

    # Remove any marker left by the original vulnerable program.
    if marker.exists():
        marker.unlink()

    results.append(
        run_test(
            "Original exploit payload",
            EXPLOIT,
            False,
        )
        and not marker.exists()
    )

    if marker.exists():
        print("[FAIL] Exploit created the win() marker")

    passed = sum(results)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
