"""Compatibility fallback for a policy-blocked optional ujson wheel.

FastAPI imports ``ujson`` when a package with that name is present.  The local
wheel cannot load under this Windows application-control policy, so this small
drop-in uses the standard-library JSON implementation instead.  It keeps the
API available without changing response semantics.
"""

from json import dumps, loads

