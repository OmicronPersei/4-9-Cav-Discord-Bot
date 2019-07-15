from bot_command_service import BotCommandService
from asynctest import MagicMock, TestCase

class TestSetsUpCallbackWithDiscordService(TestCase):
    def setUp(self):
        self.mock_config = {  "command_keyword": "!roles" }
        self.mock_discord_service = MagicMock()
        self.mock_discord_service.create_listener_for_bot_command = MagicMock()

    def runTest(self):
        bot_command_service = BotCommandService(self.mock_config, self.mock_discord_service)

        self.mock_discord_service.create_listener_for_bot_command.assert_called_with("!roles", bot_command_service.bot_command_callback)


