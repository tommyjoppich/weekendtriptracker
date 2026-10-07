"""Destinations tracked from ORD.

tier "top"   = one of ~50 of United's biggest US stations (hubs + major cities)
tier "state" = added so every state United serves has at least one airport

Edit freely: add a line to track another airport, delete a line to drop one.
Illinois is skipped (it's home). Delaware has no United service, so Philadelphia
(PHL) covers it. If United turns out not to serve an airport, the report lists it
under "No United flights found" so you can swap it for a nearby one.
"""

AIRPORTS = [
    # code, city, state, tier
    # ---- United hubs
    ("DEN", "Denver", "CO", "top"),
    ("IAH", "Houston", "TX", "top"),
    ("EWR", "Newark / New York", "NJ", "top"),
    ("SFO", "San Francisco", "CA", "top"),
    ("IAD", "Washington Dulles", "VA", "top"),
    ("LAX", "Los Angeles", "CA", "top"),
    # ---- big United markets
    ("LGA", "New York LaGuardia", "NY", "top"),
    ("DCA", "Washington National", "VA", "top"),
    ("BOS", "Boston", "MA", "top"),
    ("LAS", "Las Vegas", "NV", "top"),
    ("MCO", "Orlando", "FL", "top"),
    ("SEA", "Seattle", "WA", "top"),
    ("PHX", "Phoenix", "AZ", "top"),
    ("SAN", "San Diego", "CA", "top"),
    ("AUS", "Austin", "TX", "top"),
    ("DFW", "Dallas", "TX", "top"),
    ("ATL", "Atlanta", "GA", "top"),
    ("MSP", "Minneapolis", "MN", "top"),
    ("DTW", "Detroit", "MI", "top"),
    ("PHL", "Philadelphia", "PA", "top"),
    ("TPA", "Tampa", "FL", "top"),
    ("FLL", "Fort Lauderdale", "FL", "top"),
    ("MIA", "Miami", "FL", "top"),
    ("SNA", "Orange County", "CA", "top"),
    ("PDX", "Portland", "OR", "top"),
    ("SLC", "Salt Lake City", "UT", "top"),
    ("MSY", "New Orleans", "LA", "top"),
    ("BNA", "Nashville", "TN", "top"),
    ("RDU", "Raleigh-Durham", "NC", "top"),
    ("CLT", "Charlotte", "NC", "top"),
    ("PIT", "Pittsburgh", "PA", "top"),
    ("CLE", "Cleveland", "OH", "top"),
    ("CMH", "Columbus", "OH", "top"),
    ("IND", "Indianapolis", "IN", "top"),
    ("STL", "St. Louis", "MO", "top"),
    ("MCI", "Kansas City", "MO", "top"),
    ("SAT", "San Antonio", "TX", "top"),
    ("SMF", "Sacramento", "CA", "top"),
    ("SJC", "San Jose", "CA", "top"),
    ("HNL", "Honolulu", "HI", "top"),
    ("OGG", "Maui", "HI", "top"),
    ("ANC", "Anchorage", "AK", "top"),
    ("RSW", "Fort Myers", "FL", "top"),
    ("PBI", "West Palm Beach", "FL", "top"),
    ("JAX", "Jacksonville", "FL", "top"),
    ("BWI", "Baltimore", "MD", "top"),
    ("BDL", "Hartford", "CT", "top"),
    ("PSP", "Palm Springs", "CA", "top"),
    ("BZN", "Bozeman", "MT", "top"),
    ("COS", "Colorado Springs", "CO", "top"),
    # ---- one per remaining state United serves
    ("BHM", "Birmingham", "AL", "state"),
    ("XNA", "Northwest Arkansas", "AR", "state"),
    ("BOI", "Boise", "ID", "state"),
    ("DSM", "Des Moines", "IA", "state"),
    ("ICT", "Wichita", "KS", "state"),
    ("SDF", "Louisville", "KY", "state"),
    ("PWM", "Portland", "ME", "state"),
    ("JAN", "Jackson", "MS", "state"),
    ("OMA", "Omaha", "NE", "state"),
    ("MHT", "Manchester", "NH", "state"),
    ("ABQ", "Albuquerque", "NM", "state"),
    ("FAR", "Fargo", "ND", "state"),
    ("OKC", "Oklahoma City", "OK", "state"),
    ("PVD", "Providence", "RI", "state"),
    ("CHS", "Charleston", "SC", "state"),
    ("RAP", "Rapid City", "SD", "state"),
    ("BTV", "Burlington", "VT", "state"),
    ("CRW", "Charleston", "WV", "state"),
    ("MKE", "Milwaukee", "WI", "state"),
    ("JAC", "Jackson Hole", "WY", "state"),
]
