import pytest

from app.agents.checklists import checklist_for


def test_structure_flags_missing_soil_report_and_system():
    result = checklist_for('structure', 'سوله ۲۵×۶۰ متر با ارتفاع ۳ متر')
    assert 'گزارش خاک' in result['missing']
    assert 'سیستم سازه' in result['missing']
    assert 'ارتفاع' in result['present']


def test_persian_digits_are_recognised_as_dimensions():
    result = checklist_for('cost', 'متره ۲۵×۶۰ متر با ارتفاع ۳ متر')
    assert 'ابعاد برای متره' in result['present']
    assert 'ارتفاع برای دیوار' in result['present']


def test_nothing_is_invented_for_an_empty_brief():
    result = checklist_for('fire_safety', '')
    assert result['present'] == []
    assert len(result['missing']) == 3
    assert result['completeness'] == 0.0


def test_unknown_discipline_is_rejected():
    with pytest.raises(KeyError):
        checklist_for('astrology', 'anything')
