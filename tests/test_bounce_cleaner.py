import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bounce_cleaner import get_mx_server, verify_email_inbox_smtp

def test_valid_domain_mx():
    assert get_mx_server("gmail.com") is not None

def test_invalid_domain_mx():
    assert get_mx_server("fakeunexistingdomain123456789.com") is None

def test_empty_domain():
    assert get_mx_server("") is None

def test_verify_nonexistent_email_smtp():
    is_valid, reason = verify_email_inbox_smtp("nonexistentbarbershop999999@gmail.com")
    assert is_valid == False
    assert "550" in reason or "not found" in reason.lower() or "rejected" in reason.lower()
