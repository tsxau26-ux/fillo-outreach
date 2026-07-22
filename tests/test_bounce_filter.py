import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_replies import is_real_human_reply

def test_filters_mailer_daemon():
    assert is_real_human_reply("Mail Delivery Subsystem <mailer-daemon@googlemail.com>", "Delivery Status Notification (Failure)") == False

def test_filters_auto_reply():
    assert is_real_human_reply("info@barber.com", "Out of office") == False

def test_filters_google_alerts():
    assert is_real_human_reply("Google <no-reply@accounts.google.com>", "Security alert") == False

def test_allows_human_reply():
    assert is_real_human_reply("Jittakorn Pakjant <jkbarber.fics@gmail.com>", "Re: question about empty slots at JK Barber FICS31") == True
