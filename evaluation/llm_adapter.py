from __future__ import annotations

from typing import Any, List, Optional

from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult


def _to_litellm_messages(messages: List[BaseMessage]) -> list[dict]:
    result = []
    for m in messages:
        if isinstance(m, SystemMessage):
            result.append({"role": "system", "content": m.content})
        elif isinstance(m, HumanMessage):
            result.append({"role": "user", "content": m.content})
        else:
            result.append({"role": "assistant", "content": m.content})
    return result


class LiteLLMChatAdapter(BaseChatModel):
    """Thin LangChain BaseChatModel backed by litellm.

    Used exclusively to provide a RAGAS-compatible LLM judge via
    LangchainLLMWrapper — not used in the production serving path.
    """

    model: str
    max_tokens: int = 1024
    temperature: float = 0.0

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        import litellm

        response = litellm.completion(
            model=self.model,
            messages=_to_litellm_messages(messages),
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        content = response.choices[0].message.content or ""
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        import litellm

        response = await litellm.acompletion(
            model=self.model,
            messages=_to_litellm_messages(messages),
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        content = response.choices[0].message.content or ""
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    @property
    def _llm_type(self) -> str:
        return "litellm"
