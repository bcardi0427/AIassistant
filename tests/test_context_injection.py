import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ha-config-ai-agent', 'src')))

from agents.agent_system import AgentSystem

class TestContextInjection(unittest.TestCase):
    def setUp(self):
        self.mock_config_manager = MagicMock()
        self.mock_config_manager.config_dir = "mock_config"

    def test_context_loading(self):
        """Test that AgentSystem loads HA_CONTEXT.md if it exists."""
        
        # We need to mock the file existence check and open
        # But actually, since HA_CONTEXT.md exists on disk in the real environment, 
        # we can just test the real logic!
        
        # Initialize AgentSystem
        agent = AgentSystem(self.mock_config_manager)
        
        # Check if system prompt contains the specific header from HA_CONTEXT.md
        self.assertIn("Home Assistant Context & Best Practices", agent.system_prompt)
        self.assertIn("Critical Behavioral Guidelines", agent.system_prompt)
        print("\nSUCCESS: System prompt contains context!")
        print(f"Prompt length: {len(agent.system_prompt)}")

if __name__ == '__main__':
    unittest.main()
