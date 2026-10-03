import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from send_outreach import build_work_queue, has_replied, FOLLOWUP_GAPS_DAYS

DAY = 86400
NOW = 2_000_000_000.0


def lead(email, cat="Barber"):
    return {"Business": email.split("@")[0], "Email": email, "Category": cat, "Location": "Austin"}


def actions(queue):
    return [(l["Email"], a) for l, a in queue]


def test_new_lead_gets_the_first_email():
    q = build_work_queue([lead("a@x.com")], {}, NOW, 50)
    assert actions(q) == [("a@x.com", "initial")]


def test_first_followup_waits_the_gap():
    gap = FOLLOWUP_GAPS_DAYS[1]
    early = {"a@x.com": {"status": "sent", "sent_at": NOW - (gap - 1) * DAY, "followup_status": "none"}}
    due = {"a@x.com": {"status": "sent", "sent_at": NOW - gap * DAY, "followup_status": "none"}}
    assert build_work_queue([lead("a@x.com")], early, NOW, 50) == []
    assert actions(build_work_queue([lead("a@x.com")], due, NOW, 50)) == [("a@x.com", "followup1")]


def test_second_followup_waits_after_the_first():
    gap = FOLLOWUP_GAPS_DAYS[2]
    base = {"status": "sent", "sent_at": NOW - 30 * DAY, "followup_status": "sent"}
    early = {"a@x.com": dict(base, followup_sent_at=NOW - (gap - 1) * DAY)}
    due = {"a@x.com": dict(base, followup_sent_at=NOW - gap * DAY)}
    assert build_work_queue([lead("a@x.com")], early, NOW, 50) == []
    assert actions(build_work_queue([lead("a@x.com")], due, NOW, 50)) == [("a@x.com", "followup2")]


def test_nothing_after_the_second_followup():
    state = {"a@x.com": {"status": "sent", "sent_at": NOW - 60 * DAY,
                         "followup_status": "done", "followup_sent_at": NOW - 30 * DAY}}
    assert build_work_queue([lead("a@x.com")], state, NOW, 50) == []


def test_a_lead_who_replied_gets_no_followup():
    state = {"a@x.com": {"status": "sent", "sent_at": NOW - 10 * DAY, "followup_status": "none"}}
    q = build_work_queue([lead("a@x.com")], state, NOW, 50, replied=({"a@x.com"}, set()))
    assert q == []


def test_a_lead_marked_replied_in_state_gets_no_followup():
    state = {"a@x.com": {"status": "sent", "sent_at": NOW - 10 * DAY,
                         "followup_status": "none", "replied": True}}
    assert build_work_queue([lead("a@x.com")], state, NOW, 50) == []


def test_no_followups_when_the_inbox_could_not_be_checked():
    # Unknown replies: never risk chasing someone who already said no.
    state = {"a@x.com": {"status": "sent", "sent_at": NOW - 10 * DAY, "followup_status": "none"}}
    leads = [lead("a@x.com"), lead("new@x.com")]
    assert actions(build_work_queue(leads, state, NOW, 50, replied=None)) == [("new@x.com", "initial")]


def test_bounced_and_dead_leads_are_skipped():
    state = {"a@x.com": "bounced", "b@x.com": {"status": "email_not_found"}}
    assert build_work_queue([lead("a@x.com"), lead("b@x.com")], state, NOW, 50) == []


def test_followups_take_half_the_day_when_new_leads_wait():
    leads = [lead(f"new{i}@x.com") for i in range(10)] + [lead(f"old{i}@y.com") for i in range(10)]
    state = {f"old{i}@y.com": {"status": "sent", "sent_at": NOW - 10 * DAY, "followup_status": "none"}
             for i in range(10)}
    q = build_work_queue(leads, state, NOW, 10)
    kinds = [a for _, a in q]
    assert len(q) == 10
    assert kinds.count("initial") == 5
    assert kinds.count("followup1") == 5


def test_followups_fill_the_day_when_no_new_leads():
    leads = [lead(f"old{i}@y.com") for i in range(10)]
    state = {f"old{i}@y.com": {"status": "sent", "sent_at": NOW - 10 * DAY, "followup_status": "none"}
             for i in range(10)}
    assert len(build_work_queue(leads, state, NOW, 8)) == 8


def test_new_leads_fill_the_day_when_no_followups_are_due():
    leads = [lead(f"new{i}@x.com") for i in range(10)]
    assert len(build_work_queue(leads, {}, NOW, 8)) == 8


def test_has_replied_matches_the_address():
    assert has_replied("Info@Shop.com", {"info@shop.com"}, set())


def test_has_replied_matches_a_colleague_at_the_same_business_domain():
    assert has_replied("info@shop.com", set(), {"shop.com"})


def test_has_replied_ignores_shared_mail_providers():
    assert not has_replied("someone@gmail.com", set(), {"gmail.com"})
