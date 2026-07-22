import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from send_outreach import get_template

def test_template_contains_free_trial():
    for cat in ["barber", "spa", "pilates", "cafe"]:
        template = get_template(cat)
        body = template["body"].format(business_name="Test Store", location="Dubai")
        assert "free trial" in body.lower()
        assert "https://t.me/filloappbot" in body.lower()

def test_template_explains_how_fillo_works():
    for cat in ["barber", "spa", "pilates", "general"]:
        template = get_template(cat)
        body = template["body"].format(business_name="Test Store", location="Dubai")
        assert "generates" in body.lower() or "creates" in body.lower()
        assert "qr code" in body.lower() or "booking link" in body.lower()

def test_subject_mentions_free():
    for cat in ["barber", "spa", "pilates", "general"]:
        template = get_template(cat)
        subject = template["subject"].format(business_name="Test Store")
        assert "free" in subject.lower()

def test_natural_tone_no_all_caps_marketing():
    for cat in ["barber", "spa", "pilates", "general"]:
        template = get_template(cat)
        body = template["body"].format(business_name="Test Store", location="Dubai")
        # Should not have aggressive all-caps marketing phrases
        assert "CLAIM YOUR" not in body
        assert "ACT NOW" not in body
