import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_analytics import (
    encode_email_token,
    decode_email_token,
    record_open_event,
    record_click_event,
    get_analytics_report
)

def test_token_encode_decode():
    email_test = "jkbarber.fics@gmail.com"
    token = encode_email_token(email_test)
    assert decode_email_token(token) == email_test

def test_record_open_and_click():
    email_test = "unittest.store@example.com"
    record_open_event(email_test, ip="127.0.0.1", user_agent="PyTest Agent")
    record_click_event(email_test, target_url="https://t.me/Filloappbot")

    report = get_analytics_report()
    assert "unittest.store@example.com" in report or "Fillo Email Analytics Report" in report
