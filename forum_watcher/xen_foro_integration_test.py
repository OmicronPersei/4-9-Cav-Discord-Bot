from asynctest import MagicMock, TestCase, main
from asyncio import Future

from forum_watcher.sql_wrapper import SQLWrapper
from forum_watcher.xen_foro.forum_thread_url_factory import ForumThreadURLFactory
from forum_watcher.new_message_dispatcher import NewMessageDispatcher
from forum_watcher.new_thread_detector import NewThreadDetector
from forum_watcher.xen_foro.request_factory import RequestFactory
from forum_watcher.xen_foro.thread_getter import ThreadGetter
from forum_watcher.forum_thread_data_storage import ForumThreadDataStorage
from discord_mention_factory import DiscordMentionFactory

mock_config = {
    "welcome_message": {
        "message": "the message",
        "channel": "welcome message channel",
        "enabled": True
    },
    "user_leave_notification": {
        "message": "the message",
        "channel": "user leave channel",
        "enabled": True
    },
    "db_filename": ":memory:",
    "xen_foro_integration": {
        "forum_name": "my_unique_prefix",
        "base_url": "https://myforum.xyz/",
        "update_period": "60",
        "forums": [
            {
                "forum_id": "234",
                "target_discord_channel": "forum posts",
                "message_template": "A new forum post has appeared! {thread_url}",
                "discord_message_reactions": [ "👍", "👎" ]
            }
        ]
    }
}

mock_secrets = {
    "xen_foro_integration_api_token": "imsecret"
}

mock_threads_from_forum_API = [ {
    "forum_id": "234",
    "thread_id": "111",
    "title": "my_thread_title"
}]

class MockSQLWrapper(SQLWrapper):
    def __init__(self, config, mock_sql):
        self.mock_sql = mock_sql
        super().__init__(config)

    def _get_db_connection(self, db_filename):
        return self.mock_sql

class XenForoIntegrationTest(TestCase):
    def setUp(self):
        self.setUpAPIs()
        self.setUpObjectsForTest()

    def setUpAPIs(self):
        self.mock_sql = MagicMock()
        self.mock_sql.execute = MagicMock()
        self.mock_sql.commit = MagicMock()

        self.thread_getter = MagicMock()
        self.thread_getter.get_threads = MagicMock(return_value = mock_threads_from_forum_API)
        
        self.discord_service = MagicMock()
        self.mock_sent_message = MagicMock()

        self.discord_service.send_channel_message = MagicMock(return_value=Future())
        self.discord_service.send_channel_message.return_value.set_result(self.mock_sent_message)

        self.discord_service.set_reactions_for_message = MagicMock(return_value=Future())
        self.discord_service.set_reactions_for_message.return_value.set_result(None)

    def setUpObjectsForTest(self):
        self.mock_sql_wrapper = MockSQLWrapper(mock_config, self.mock_sql)

        self.forum_url_factory = ForumThreadURLFactory()

        self.request_factory = RequestFactory()

        self.forum_data_storage = ForumThreadDataStorage(self.mock_sql_wrapper)

        xen_forum_config = mock_config["xen_foro_integration"]
        xen_forum_api_token = mock_secrets["xen_foro_integration_api_token"]
        self.new_thread_detector = NewThreadDetector(self.thread_getter, self.forum_data_storage, xen_forum_config, xen_forum_api_token)

        self.discord_mention_factory = DiscordMentionFactory(self.discord_service)

        self.new_thread_dispatcher = NewMessageDispatcher(self.new_thread_detector, self.discord_service, self.discord_mention_factory, self.forum_data_storage, self.forum_url_factory, xen_forum_config)

    async def runTest(self):
        #simulate the callback from ClockSignal
        await self.new_thread_dispatcher._check_for_new_threads()

        self.thread_getter.get_threads.assert_called_with("https://myforum.xyz/", "imsecret", "234")

        self.discord_service.send_channel_message.assert_called_with("A new forum post has appeared! https://myforum.xyz/threads/my_thread_title", "forum posts")

        self.discord_service.set_reactions_for_message.assert_called_with(self.mock_sent_message, [ "👍", "👎" ])
        
        expected_sql_insert = """insert into ForumMessageHistory (forum_name, forum_id, thread_id)
        values ('{}', '{}', '{}')""".format(
            "my_unique_prefix",
            "234",
            "111"
        )
        self.mock_sql.execute.assert_called_with(expected_sql_insert)
        self.mock_sql.commit.assert_any_call()