"""Settings for the weekend-trip tracker. Edit these to change what it looks for."""

ORIGIN = "ORD"
AIRLINE_CODE = "UA"
AIRLINE_NAME = "United"

# Weekdays: 0=Mon 1=Tue 2=Wed 3=Thu 4=Fri 5=Sat 6=Sun
# Outbound window: Thursday 6 PM → Friday 5:59 PM (leaving ORD).
# Each entry is (weekday, earliest departure hour, latest departure hour).
# None = no limit. Hours are 0–23; latest 17 means departures up to 5:59 PM.
DEPART_WINDOWS = [
    (3, 18, None),   # Thursday, 6 PM or later
    (4, None, 17),   # Friday, before 6 PM
]

# Return: Sunday, any departure time, landing at ORD by 10 PM.
RETURN_WEEKDAY = 6
RETURN_LATEST_ARRIVAL_HOUR = 21   # arrive by 9:59 PM (i.e. back by 10 PM)

WEEKENDS_AHEAD = 10          # track the next 10 weekends, rolling forward

ADULTS = 1
SEAT = "economy"
EXCLUDE_BASIC_ECONOMY = True # regular Economy only (what Chase Travel sells)
CURRENCY = "USD"
TIMEZONE = "America/Chicago"

# Pause between searches so Google doesn't block the bot (seconds, random range)
DELAY_RANGE = (1.0, 2.5)

# A "deal" = a fare at least this far below that destination's own typical price
DEAL_THRESHOLD = 0.20        # 20% below typical
DEAL_MIN_CHECKS = 4          # need this many runs of history before calling deals
# Only email deals under this price (None = any price)
DEAL_MAX_PRICE = None
