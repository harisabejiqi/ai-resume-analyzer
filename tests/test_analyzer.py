"""Tests for work-experience parsing in app/services/analyzer.py."""

import pytest

from app.services.analyzer import extract_work_experience

LONG_TITLE_CV = """Work experience
Gjirafa Inc – Data Engineer
January 2024 - Present
• Collaborated with product and engineering teams to turn reporting outputs.
Gjirafa Inc – Quality Assurance Automation Engineer
February 2023 - December 2023
• Validated application behavior and data accuracy through
API and database testing.
• Resolved defects with developers.
"""


def test_long_line_above_a_date_line_is_a_title():
    roles = extract_work_experience(LONG_TITLE_CV)
    assert [(r["title"], r["company"]) for r in roles] == [
        ("Data Engineer", "Gjirafa Inc"),
        ("Quality Assurance Automation Engineer", "Gjirafa Inc"),
    ]
    assert len(roles[0]["bullets"]) == 1


def test_wrapped_marked_bullet_is_rejoined_even_after_a_capital():
    roles = extract_work_experience(LONG_TITLE_CV)
    assert roles[1]["bullets"] == [
        "Validated application behavior and data accuracy through API and database testing.",
        "Resolved defects with developers.",
    ]


def test_title_after_unpunctuated_bullet_is_not_swallowed():
    cv = """Experience
Junior Backend Developer, Nexa Web Studio
Jun 2023 - Present
- Added unit tests with pytest for the payments module
Intern, Nexa Web Studio
Jan 2023 - May 2023
- Built an internal admin page
"""
    roles = extract_work_experience(cv)
    assert roles[0]["bullets"] == ["Added unit tests with pytest for the payments module"]
    assert (roles[1]["title"], roles[1]["company"]) == ("Intern", "Nexa Web Studio")


def test_unmarked_lines_are_not_glued_together():
    cv = """Experience
Backend Developer, Acme
2020 - 2022
Built the billing service in Python and Django for the payments team
Migrated reporting jobs from cron to Airflow with alerting on failures
"""
    roles = extract_work_experience(cv)
    assert roles[0]["bullets"] == [
        "Built the billing service in Python and Django for the payments team",
        "Migrated reporting jobs from cron to Airflow with alerting on failures",
    ]


def _roles(cv):
    return [(r["title"], r["company"], r["start"], r["end"], len(r["bullets"]))
            for r in extract_work_experience(cv)]


@pytest.mark.parametrize("dates", ["Since 2020", "From 2020", "2020 -", "2020 –"])
def test_open_ended_dates_mean_present(dates):
    cv = f"""Experience
Backend Developer, Acme
{dates}
- Built APIs in Python
"""
    assert _roles(cv) == [("Backend Developer", "Acme", "2020", "Present", 1)]


def test_since_inside_a_sentence_does_not_open_a_role():
    cv = """Experience
Backend Developer, Acme
Jan 2018 - Dec 2019
Maintained the payment services that have been running in production since 2015.
"""
    assert len(extract_work_experience(cv)) == 1


def test_dates_above_title_and_company():
    cv = """Experience
Jan 2020 - Present
Backend Developer
Acme Corp
- Built APIs
"""
    assert _roles(cv) == [("Backend Developer", "Acme Corp", "Jan 2020", "Present", 1)]


@pytest.mark.parametrize("first, second", [
    ("Acme Corp", "Backend Developer"),
    ("Backend Developer", "Acme Corp"),
])
def test_title_and_company_on_two_lines_in_either_order(first, second):
    cv = f"""Experience
{first}
{second}
Jan 2020 - Present
- Built APIs
"""
    assert _roles(cv) == [("Backend Developer", "Acme Corp", "Jan 2020", "Present", 1)]


def test_promotion_inherits_the_company():
    cv = """Experience
Acme Corp
Senior Developer
Jan 2022 - Present
- Led the payments team
Developer
Jan 2020 - Dec 2021
- Built APIs
"""
    assert [(r["title"], r["company"]) for r in extract_work_experience(cv)] == [
        ("Senior Developer", "Acme Corp"), ("Developer", "Acme Corp"),
    ]


def test_company_is_not_inherited_from_a_one_line_header():
    cv = """Experience
Senior Developer, Acme Corp
Jan 2022 - Present
- Led the payments team
Developer
Jan 2020 - Dec 2021
- Built APIs
"""
    assert extract_work_experience(cv)[1]["company"] is None


def test_unrecognised_section_heading_is_not_taken_as_company():
    cv = """Përvoja e punës
Backend Developer, Acme
Jan 2020 - Present
- Built APIs
"""
    assert _roles(cv) == [("Backend Developer", "Acme", "Jan 2020", "Present", 1)]
