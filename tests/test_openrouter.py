import unittest
from unittest.mock import patch, MagicMock
import sys
import types
import ai_assistant

class OpenRouterTests(unittest.TestCase):
    def test_free_model_default(self):
        self.assertEqual(ai_assistant.DEFAULT_MODEL, "openrouter/free")

    def test_request_uses_openrouter(self):
        response = MagicMock()
        response.choices[0].message.content = "Demo answer"
        with patch.object(ai_assistant, "get_api_key", return_value="test-key"), \
             patch.object(ai_assistant, "build_database_context", return_value="Synthetic login event"), \
             patch.dict(sys.modules, {"openai": types.SimpleNamespace(OpenAI=MagicMock())}):
            client_type = sys.modules["openai"].OpenAI
            client_type.return_value.chat.completions.create.return_value = response
            self.assertEqual(ai_assistant.ask_ai("What happened?"), "Demo answer")
            self.assertEqual(client_type.call_args.kwargs["base_url"], "https://openrouter.ai/api/v1")
            kwargs = client_type.return_value.chat.completions.create.call_args.kwargs
            self.assertEqual(kwargs["model"], "openrouter/free")
            self.assertEqual(kwargs["messages"][0]["role"], "system")

if __name__ == "__main__":
    unittest.main()
