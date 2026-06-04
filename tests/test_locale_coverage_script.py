from scripts.check_locale_coverage import build_locale_report


def test_locale_coverage_report_contains_supported_languages():
    report = "\n".join(build_locale_report())

    assert "English baseline keys" in report
    assert "uk:" in report
    assert "no:" in report
