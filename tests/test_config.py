import pytest

from receptor_satellite.worker import Config
from fake_logger import FakeLogger

ERROR_HANDLING_TEST_CASES = [
    (
        {},
        {
            "text_updates": Config.Defaults.TEXT_UPDATES,
            "text_update_interval": Config.Defaults.TEXT_UPDATE_INTERVAL,
            "text_update_full": Config.Defaults.TEXT_UPDATE_FULL,
        },
        [],
    ),
    (
        {"text_updates": 27, "text_update_interval": -13, "text_update_full": []},
        {
            "text_updates": Config.Defaults.TEXT_UPDATES,
            "text_update_interval": Config.Defaults.TEXT_UPDATE_INTERVAL,
            "text_update_full": Config.Defaults.TEXT_UPDATE_FULL,
        },
        [
            "Expected the value of text_updates '27' to be a boolean",
            "Expected the value of text_update_full '[]' to be a boolean",
            "Expected the value of text_update_interval '-13' to be an integer greater or equal than 5000",
        ],
    ),
    (
        {
            "text_updates": True,
            "text_update_interval": 10000,
            "text_update_full": False,
        },
        {
            "text_updates": True,
            "text_update_interval": 10000,
            "text_update_full": False,
        },
        [],
    ),
]


@pytest.fixture(scope="module", params=ERROR_HANDLING_TEST_CASES)
def scenario(request):
    logger = FakeLogger()
    config, expected, warnings = request.param
    yield (config, expected, warnings, logger)


def test_error_handling(scenario):
    config, expected, warnings, logger = scenario
    validated = Config.validate_input(config, logger)
    assert validated == expected
    assert logger.warnings() == warnings
