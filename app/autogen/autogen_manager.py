import asyncio
import os

from dotenv import find_dotenv, load_dotenv
from fastapi import WebSocket

from autogen import ConversableAgent, GroupChat, GroupChatManager

from .user_proxy_web_agent import UserProxyWebAgent

_ = load_dotenv(find_dotenv())

llm_config = {
    "config_list": [
        {
            "model": os.environ["AZURE_OPENAI_MODEL"],
            "api_type": os.environ["AZURE_OPENAI_API_TYPE"],
            "api_key": os.environ["AZURE_OPENAI_API_KEY"],
            "base_url": os.environ["AZURE_OPENAI_BASE_URL"],
            "api_version": os.environ["AZURE_OPENAI_VERSION"],
        }
    ]
}

question_agent_description = """
负责与用户互动、提出问题、收集回复，并将其传递给Analysis Agent。完成每个主题后，等待Scoring Agent的评分，确保整体对话流畅。
"""
question_agent_system_message = """
你是心理学专家，负责与用户互动、提出问题、收集回复，并将其传递给Analysis Agent。你还要在每个主题结束后，等待Scoring Agent的评分。

**任务**:
- 向用户问好，然后开始提问并收集回复。
- 将每次用户回复发送给Analysis Agent。
- 在每个主题完成后，等待Scoring Agent的评分。
- 问完所有问题后，感谢用户并告别。

**问题**:
1. 社交活动：请问你最后一次参加的社交活动是什么时候？请描述一下这个活动的情况，你做了什么，与谁交谈，以及整体的气氛如何？
2. 情感表达：你通常如何表达你的思想和情感呢？分享一个最近你交流或表达情感的例子。并解释你是如何做到的以及你在这次互动中的感觉。
3. 团队参与：你在团队或小组工作情境中通常扮演怎样的角色？描述一个你在团队中工作的经历，你的具体角色，你是如何与他人互动的，以及你对团队合作的整体看法。

**限制**:
- 不讨论任何与评分有关的内容。
- 全程使用中文。
- 一次只提一个问题，等待回复后再继续。

**互动**:
- 与Analysis Agent沟通，以确定是否需要追问。
- 与Scoring Agent合作，在每个主题结束后得到评分。
"""

analysis_agent_description = """
负责分析每个用户回复，判断是否需要追问，并在必要时提供追问问题。与Scoring Agent协作，确保每个主题得到准确评分。
"""
analysis_agent_system_message = """
你是Analysis Agent，负责分析用户的每个回复，确定是否需要追问。即使不需要追问，也要解释原因。每个主题最多追问两次。

**任务**:
- 分析来自Question Agent的用户回复。
- 决定是否需要追问，解释原因。
- 建议追问问题，每个主题最多两次。
- 与Scoring Agent协调，确保准确评分。

**输出格式**:
```json
{
  "analysis_summary": "概括用户的回复，提供洞察或背景信息。",
  "follow_up_suggestion": {
    "needed": true,  # 或false，视分析结果而定
    "reason": "解释需要追问或不需要的原因。",
    "suggested_follow_up": "若需要，提供追问问题。"
  }
}

**互动**:
- 与Question Agent沟通，建议追问问题。
- 与Scoring Agent合作，确保准确评分。
"""

scoring_agent_description = """
负责对用户回复进行评分。每个主题结束后进行评分，并在Question Agent问完所有问题并说再见后提供最终的外向性评分。与Analysis Agent和Question Agent协作，确保评分准确。
"""
scoring_agent_system_message = """
你是Scoring Agent，负责评分，评估外向性。评分范围是1到10，精确到小数点后一位。

**任务**:
- 根据Analysis Agent的数据进行评分。
- 每个主题结束后，提供评分。
- 在Question Agent问完所有主题并说再见后后，提供最终评分。

**输出格式**:
```json
{
  "topic": "XX",
  "score": XX,
  "score_explanation": "解释评分原因。"

  "scores": {
    "social_activities": XX,
    "emotional_expression": XX,
    "team_participation": XX
  },
  "final_score": XX,
  "score_explanation": "最终评分的简要解释。"
}

**互动**:
- 与Analysis Agent协调，接收评分数据。
- 与Question Agent合作，提供每个主题的评分。
- 在Question Agent问完所有问题并说再见后，提供最终评分。
"""

user_proxy_description = """
用户本人，提供对话中的回复和互动内容。
"""
user_proxy_system_message = """
用户本人，提供对话中的回复和互动内容。
"""


class AutogenManager:

    def __init__(self, socket: WebSocket = None, chat_id: str = None):
        self.socket = socket
        self.chat_id = chat_id
        self.client_sent_queue = asyncio.Queue()
        self.client_receive_queue = asyncio.Queue()

        self.question_agent = ConversableAgent(
            name="question_agent",
            description=question_agent_description,
            system_message=question_agent_system_message,
            is_termination_msg=lambda msg: "再见" in msg["content"].lower(),
            human_input_mode="NEVER",
            llm_config=llm_config,
        )

        self.analysis_agent = ConversableAgent(
            name="analysis_agent",
            description=analysis_agent_description,
            system_message=analysis_agent_system_message,
            human_input_mode="NEVER",
            llm_config=llm_config,
        )

        self.scoring_agent = ConversableAgent(
            name="scoring_agent",
            description=scoring_agent_description,
            system_message=scoring_agent_system_message,
            human_input_mode="NEVER",
            llm_config=llm_config,
        )

        self.user_proxy = UserProxyWebAgent(
            name="user_proxy",
            description=user_proxy_description,
            system_message=user_proxy_system_message,
            human_input_mode="ALWAYS",
            is_termination_msg=lambda x: x.get("content", "")
            and x.get("content", "").rstrip().endswith("TERMINATE"),
            max_consecutive_auto_reply=5,
            code_execution_config=False,
        )

        # add the queues to communicate
        self.user_proxy.set_queues(self.client_sent_queue, self.client_receive_queue)

        self.group_chat = GroupChat(
            agents=[
                self.question_agent,
                self.analysis_agent,
                self.scoring_agent,
                self.user_proxy,
            ],
            messages=[],
            max_round=50,
            send_introductions=True,
            speaker_selection_method="auto",
        )

        self.group_chat_manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config=llm_config,
        )

    async def start(self, message: str):
        await self.user_proxy.a_initiate_chat(
            self.group_chat_manager,
            message=message,
            summary_method="reflection_with_llm",
        )
