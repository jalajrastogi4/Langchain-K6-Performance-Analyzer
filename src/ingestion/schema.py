# Raw Metrics we care about from K6 output
metrics_of_interest = [
    "http_req_duration",
    "http_req_blocked",
    "http_req_connecting",
    "http_req_tls_handshaking",
    "http_req_sending",
    "http_req_waiting",
    "http_req_receiving",
    "http_req_failed",
    "http_reqs",
]

# Raw metrics renames to schema names
rename_map = {
    "http_req_duration": "response_time_ms",
    "http_req_blocked": "blocked_ms",
    "http_req_connecting": "connecting_ms",
    "http_req_tls_handshaking": "tls_handshake_ms",
    "http_req_sending": "sending_ms",
    "http_req_waiting": "waiting_ms",
    "http_req_receiving": "receiving_ms",
}

# Map k6 endpoint names to URLs
url_mappings = {
    "home": "https://test.k6.io/",
    "news": "https://test.k6.io/news.php",
    "contact": "https://test.k6.io/contact.php",
    "login": "https://test.k6.io/login.php",
} 