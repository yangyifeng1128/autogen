import sys
from typing import Dict, List, Optional, Union

from autogen import Agent, ConversableAgent, GroupChat


class GroupChatManagerWeb(ConversableAgent):

    def __init__(
        self,
        groupchat: GroupChat,
        name: Optional[str] = "chat_manager",
        # unlimited consecutive auto reply by default
        max_consecutive_auto_reply: Optional[int] = sys.maxsize,
        human_input_mode: Optional[str] = "NEVER",
        system_message: Optional[str] = "Group chat manager.",
        # seed: Optional[int] = 4,
        **kwargs,
    ):
        super().__init__(
            name=name,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            human_input_mode=human_input_mode,
            system_message=system_message,
            **kwargs,
        )

        self.register_reply(
            Agent,
            GroupChatManagerWeb.run_chat,
            config=groupchat,
            reset_config=GroupChat.reset,
        )

    async def run_chat(
        self,
        messages: Optional[List[Dict]] = None,
        sender: Optional[Agent] = None,
        config: Optional[GroupChat] = None,
    ) -> Union[str, Dict, None]:
        if messages is None:
            messages = self._oai_messages[sender]
        message = messages[-1]
        speaker = sender
        group_chat = config

        for i in range(group_chat.max_round):
            # set the name to speaker's name if the role is not function
            if message["role"] != "function":
                message["name"] = speaker.name
            group_chat.messages.append(message)
            # broadcast the message to all agents except the speaker
            for agent in group_chat.agents:
                if agent != speaker:
                    self.send(message, agent, request_reply=False, silent=True)
            if i == group_chat.max_round - 1:
                # the last round
                break
            try:
                # select the next speaker
                speaker = group_chat.select_speaker(speaker, self)
                # let the speaker speak
                reply = await speaker.a_generate_reply(sender=self)
            except KeyboardInterrupt:
                # let the admin agent speak if interrupted
                if group_chat.admin_name in group_chat.agent_names:
                    # admin agent is one of the participants
                    speaker = group_chat.agent_by_name(group_chat.admin_name)
                    reply = await speaker.a_generate_reply(sender=self)
                else:
                    # admin agent is not found in the participants
                    raise
            if reply is None:
                break
            # The speaker sends the message without requesting a reply
            speaker.send(reply, self, request_reply=False)
            message = self.last_message(speaker)

        return True, None
