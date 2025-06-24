#!/usr/bin/env python3
import time
from datetime import UTC
from datetime import datetime


now = datetime.now(UTC)
print(f"Current system time: {now}")
print(f"Current timestamp: {int(time.time())}")
print(f"Timezone: {time.tzname}")
