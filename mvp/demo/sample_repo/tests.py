"""The gate's test command runs this. Exit 0 = pass, exit 1 = fail.

Pure stdlib so the demo needs no test framework. This is the real, executable
acceptance check the reliability gate enforces.
"""
import sys

from validator import validate_login

CASES = [
    (("alice", "pw"), True),       # normal valid login
    (("bob", "secret"), True),
    (("", "pw"), False),           # empty username must be rejected
    (("   ", "pw"), False),        # whitespace-only username must be rejected
    (("alice", ""), False),        # empty password must be rejected
    ((None, "pw"), False),         # non-string input must be rejected
]


def main() -> int:
    failures = []
    for args, expected in CASES:
        try:
            got = validate_login(*args)
        except Exception as exc:  # a crash is a failure
            got = f"EXC:{type(exc).__name__}"
        if got != expected:
            failures.append((args, expected, got))

    if failures:
        print(f"FAILED {len(failures)}/{len(CASES)} cases")
        for args, exp, got in failures:
            print(f"  validate_login{args!r}: expected {exp}, got {got}")
        return 1
    print(f"PASSED {len(CASES)}/{len(CASES)} cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
