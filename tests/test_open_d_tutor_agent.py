# tests/test_open_d_tutor_agent.py

import unittest
from opendevin.controller.state.state import State
from opendevin.llm.llm import LLM
from agenthub.open_d_tutor.agent import OpenDTutorAgent
from opendevin.events.action import MessageAction

class MockLLM(LLM):
    def completion(self, messages, stop, temperature):
        return "This is a mock response."

class TestOpenDTutorAgent(unittest.TestCase):
    def setUp(self):
        self.llm = MockLLM()
        self.agent = OpenDTutorAgent(self.llm)
        self.state = State()

    def test_step(self):
        action = self.agent.step(self.state)
        self.assertIsInstance(action, MessageAction)
        self.assertEqual(action.content, "This is a mock response.")

    def test_reset(self):
        self.agent.reset()
        self.assertFalse(self.agent.complete)

if __name__ == '__main__':
    unittest.main()