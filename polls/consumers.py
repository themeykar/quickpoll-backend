import json

from channels.generic.websocket import AsyncWebsocketConsumer


class PollConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live poll updates.

    Clients connect to ws/polls/{poll_id}/ and receive JSON messages
    whenever a vote is cast or the poll is closed.
    """

    async def connect(self):
        self.poll_id = self.scope['url_route']['kwargs']['poll_id']
        self.group_name = f'poll_{self.poll_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name, self.channel_name
        )

    async def poll_update(self, event):
        """
        Handler for messages of type "poll_update" sent to this group.
        Forwards the poll data down to the WebSocket client as JSON.
        """
        await self.send(text_data=json.dumps(event['data']))
