from typing import Tuple, Iterable
from asyncapi import Message, Channel, Operation, Components

from . import failure_task_name, SagaErrorPayload, success_task_name


def message_to_channel(message: Message,
                       response: Message = None,
                       publish_made_first=False,
                       description: str = None) -> Tuple[str, Channel]:
    if publish_made_first:
        first_action, second_action = 'publish', 'subscribe'
    else:
        first_action, second_action = 'subscribe', 'publish'

    channel_kwargs = {'description': description,
                      first_action: Operation(message=message)}

    if response:
        channel_kwargs[second_action] = Operation(message=response)

    return message.name, Channel(**channel_kwargs)


def message_to_component(message: Message) -> Tuple[str, Message]:
    return message.name, message


def asyncapi_components_from_asyncapi_channels(channels: Iterable[Channel]):
    messages = list()
    for channel in channels:
        if channel.publish and channel.publish.message:
            messages.append(channel.publish.message)
        if channel.subscribe and channel.subscribe.message:
            messages.append(channel.subscribe.message)

    components = [message_to_component(message) for message in messages]

    return Components(messages=dict(components))


def asyncapi_message_for_success_response(base_task_name: str,
                                          title: str = None,
                                          summary: str = None,
                                          payload_dataclass: object = None):
    return Message(name=success_task_name(base_task_name),
                   title=title,
                   summary=summary,
                   payload=payload_dataclass)


def asyncapi_message_for_failure_response(base_task_name: str,
                                          title: str = None,
                                          summary: str = None,
                                          payload_dataclass: type = SagaErrorPayload):
    return Message(name=failure_task_name(base_task_name),
                   title=title,
                   summary=summary,
                   payload=payload_dataclass)
