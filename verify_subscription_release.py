"""Read-only release check. Run beside run.py before doctor or maintenance.

No app import, database access, PayPal calls, or file modifications.
Line-ending differences from Windows downloads are accepted.
"""
from pathlib import Path
import hashlib
import sys

EXPECTED = {'app/credit_routes.py': 'c60bc774406e9ee47609073517caf74b04b9bc5ff2d6d5ca80323b510791f9a8', 'app/subscription_checkout.py': '51f46b0376edc7173e9e32d072227934841732ffbefc8d6a39ad4d38bba1f374', 'app/subscription_credits.py': '7e785c8720f04016b28563c331ac22770649f55d911459c184db1808c09a3b6c', 'app/subscription_maintenance.py': 'fc9820f4ad0ce14db5bce8831201313bce8eff7f84f44642d4c033dcb5d4a408', 'app/views.py': '896c23f3a0d2a0fa288069e1158e27dcf6b5906aaa5ad0fd317174d65a49c2f6', 'schedule_subscription_maintenance.py': '1a9bcfaf013f69abfcd07a7d9c83eef762d5623e49bae16c28e3b302cc1cf3bf'}


def main():
    root = Path(__file__).resolve().parent
    mismatches = []
    for name, expected in EXPECTED.items():
        path = root / name
        try:
            actual = hashlib.sha256(path.read_text(encoding='utf-8-sig').encode('utf-8')).hexdigest()
        except (OSError, UnicodeError):
            mismatches.append(name + ' (missing or unreadable)')
            continue
        if actual != expected:
            mismatches.append(name + ' (different contents)')
    if mismatches:
        print('Release verification FAILED. Compare these files before running maintenance:')
        for name in mismatches:
            print('  ' + name)
        return 1
    print('Release 20261009 verified: all 6 application files match the tested package.')
    print('This verifies file contents only. Run credits doctor next; live webhook and scheduler checks are separate.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
