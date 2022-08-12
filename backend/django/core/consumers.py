import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class SMARTConsumer(WebsocketConsumer):
    """Class for a client who joins the annotate page.

    A client can only do the following:
        * Connect to the project group
        * Disconnect from the project group
        * Recieve a message from SMART (which broadcasts to the group)
    """

    def connect(self):
        self.project = self.scope["url_route"]["kwargs"]["pk"]

        # Join project channel
        async_to_sync(self.channel_layer.group_add)(self.project, self.channel_name)

        self.accept()

    def disconnect(self, close_code):
        # Leave project channel
        async_to_sync(self.channel_layer.group_discard)(self.project, self.channel_name)

        # Potentially able to handle case when user leaves page here
        # When a user leaves the page, the browser disconnects from the websocket
        # This would be a good workaround for the beforeunload() issue
        # Uncomment this to test. Load up to an annotate page and exit the browser
        # print("user left page")

    # Receive message from project channel
    def timeout_message(self, event):
        message = event["message"]

        # Send message to client WebSocket
        self.send(
            text_data=json.dumps(
                {
                    "message": message,
                }
            )
        )
