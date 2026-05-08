from prometheus_client import Counter

loans_created_total = Counter(
    "loans_created_total",
    "Total number of loans created",
)

loans_returned_total = Counter(
    "loans_returned_total",
    "Total number of loans returned",
)

loans_cancelled_total = Counter(
    "loans_cancelled_total",
    "Total number of loans cancelled",
)

loans_renewed_total = Counter(
    "loans_renewed_total",
    "Total number of loans renewed",
)

reservations_created_total = Counter(
    "reservations_created_total",
    "Total number of reservations created",
)

reservations_cancelled_total = Counter(
    "reservations_cancelled_total",
    "Total number of reservations cancelled",
)

notifications_sent_total = Counter(
    "notifications_sent_total",
    "Total number of notifications sent",
)