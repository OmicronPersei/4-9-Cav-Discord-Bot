from asynctest import TestCase, MagicMock, PropertyMock
from asyncio import Future

from user_reaction_report.user_reaction_mapper import map_message_to_user_reaction_dict

from user_reaction_report.test_utils import create_mock_user, AsyncIterator

# emoji_dict: dict of emoji: [user_obj]
def create_mock_message(emoji_dict):
    reactions = []
    for emoji,user_objs in emoji_dict.items():
        reaction = MagicMock()
        type(reaction).emoji = PropertyMock(return_value=emoji)
        reaction.users = MagicMock(return_value=AsyncIterator(user_objs))
        reactions.append(reaction)
    message = MagicMock()
    type(message).reactions = PropertyMock(return_value=reactions)
    return message

class TestUserReactionMapper(TestCase):
    def setUp(self):
        mock_reactions = dict()
        mock_reactions["👍"] = [ create_mock_user(id=1), create_mock_user(id=2) ]
        mock_reactions["👎"] = [ create_mock_user(id=3), create_mock_user(id=2) ]
        self.mock_message = create_mock_message(mock_reactions)

    async def runTest(self):
        actual = await map_message_to_user_reaction_dict(self.mock_message)
        # dict of user_id: [{"user": userobj, "emojis": [emojis]}]
        assert "1" in actual
        assert len(actual["1"]["emojis"]) == 1
        assert "👍" in actual["1"]["emojis"]

        assert "2" in actual
        assert len(actual["2"]["emojis"]) == 2
        assert "👍" in actual["2"]["emojis"]
        assert "👎" in actual["2"]["emojis"]

        assert "3" in actual
        assert len(actual["3"]["emojis"]) == 1
        assert "👎" in actual["3"]["emojis"]
