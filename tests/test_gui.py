import pytest

from msi_monitor import i18n
from msi_monitor.profile import PROFILES


@pytest.mark.parametrize("lang", i18n.LANGUAGES)
def test_every_feature_has_a_label_and_tooltip(lang):
    for profile in PROFILES:
        for name in profile.features:
            assert i18n.label(lang, name) != name, (lang, name)
            assert i18n.tip(lang, name), (lang, name)


def test_ui_strings_exist_in_every_language():
    for lang in i18n.LANGUAGES:
        assert set(i18n.UI[lang]) == set(i18n.UI["en"]), lang


def test_unknown_language_falls_back_to_english():
    assert i18n.ui("xx", "reload") == "Reload"
    assert i18n.label("xx", "brightness") == "Brightness"


def test_every_feature_is_placed_in_a_tab():
    gui = pytest.importorskip("msi_monitor.gui", exc_type=ImportError)
    placed = {name for _, names in gui.TABS for name in names}
    for profile in PROFILES:
        assert set(profile.features) <= placed, profile.slug
