import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bounce_cleaner import check_mx_record

def test_valid_domain_mx():
    assert check_mx_record("gmail.com") == True

def test_invalid_domain_mx():
    assert check_mx_record("fakeunexistingdomain123456789.com") == False

def test_empty_domain():
    assert check_mx_record("") == False
