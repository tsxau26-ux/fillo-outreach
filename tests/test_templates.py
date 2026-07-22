import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from send_outreach import get_template

def test_template_contains_free_trial():
    for cat in ["barber", "spa", "pilates", "cafe"]:
        template = get_template(cat)
        body = template["body"].format(business_name="Test Store", location="Dubai")
        assert "1-month free trial" in body.lower() or "1 month free trial" in body.lower()
        assert "telegram" in body.lower()
        assert "benefit" in body.lower() or "recover" in body.lower() or "fill" in body.lower()

def test_template_explains_ad_generation():
    for cat in ["barber", "spa", "pilates", "general"]:
        template = get_template(cat)
        body = template["body"].format(business_name="Test Store", location="Dubai")
        assert "generate" in body.lower() or "promo" in body.lower() or "ad" in body.lower()
