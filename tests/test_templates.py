import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from send_outreach import get_template, FOLLOWUPS, email_footer, render_email

CATEGORIES = ["Barber", "Salon/Spa", "Clinic", "Pilates", "Restaurant/Cafe", "Bar", "Car Wash"]


def all_emails():
    """Every email a lead can receive, filled in for a sample business."""
    out = []
    for cat in CATEGORIES:
        t = get_template(cat)
        out.append((t["subject"].format(business_name="Test Store"),
                    t["body"].format(business_name="Test Store", location="Austin")))
    for step in (1, 2):
        t = FOLLOWUPS[step]
        out.append((t["subject"].format(business_name="Test Store"),
                    t["body"].format(business_name="Test Store", location="Austin")))
    return out


def test_every_email_asks_for_a_reply_by_email():
    for subject, body in all_emails():
        assert "reply" in body.lower(), body


def test_no_email_sends_people_to_telegram_or_a_link():
    for subject, body in all_emails():
        text = (subject + body).lower()
        assert "telegram" not in text
        assert "t.me" not in text
        assert "http" not in text


def test_signed_by_the_team_not_a_person():
    for subject, body in all_emails():
        assert body.rstrip().endswith("The Fillo Team")
        for name in ("racem", "amine", "i'm the founder", "founder"):
            assert name not in body.lower()


def test_first_emails_are_short():
    for cat in CATEGORIES:
        body = get_template(cat)["body"].format(business_name="Test Store", location="Austin")
        assert len(body.split()) <= 110, f"{cat}: {len(body.split())} words"


def test_food_and_drink_places_get_the_quiet_hours_pitch():
    for cat in ("Restaurant/Cafe", "Bar", "Coffee Shop", "Pub"):
        assert get_template(cat) is get_template("Restaurant/Cafe")
        assert "quiet" in get_template(cat)["body"].lower()


def test_appointment_businesses_get_the_cancellation_pitch():
    for cat in ("Barber", "Salon/Spa", "Clinic"):
        assert "cancel" in get_template(cat)["body"].lower()


def test_any_other_business_still_gets_an_email():
    body = get_template("Car Wash")["body"].format(business_name="Test Store", location="Austin")
    assert "Test Store" in body


def test_footer_offers_opt_out_in_team_voice():
    footer = email_footer().lower()
    assert "no thanks" in footer
    assert "we won't write again" in footer


def test_footer_names_instagram_under_the_signature_without_a_link():
    footer = email_footer()
    assert footer.startswith("\nInstagram: @joinfillo\n")
    assert "http" not in footer


def test_render_email_picks_followup_by_step():
    lead = {"Business": "Test Store", "Category": "Barber", "Location": "Austin"}
    s0, _ = render_email(lead, "initial")
    s1, _ = render_email(lead, "followup1")
    s2, _ = render_email(lead, "followup2")
    assert len({s0, s1, s2}) == 3
