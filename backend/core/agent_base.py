from abc import ABC, abstractmethod
from typing import Dict, Any


class AgentBase(ABC):
    """
    ABSTRACT BASE CLASS FOR ALL AGENTS

    Every agent must:
    - Receive a shared state dictionary
    - Return the updated state dictionary
    """

    name: str = "base-agent"

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's logic.

        Args:
            state (Dict[str, Any]): Shared pipeline state

        Returns:
            Dict[str, Any]: Updated state
        """
        pass
