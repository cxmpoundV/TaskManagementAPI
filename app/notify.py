import pusher

pusher_client = pusher.Pusher(
  app_id='',
  key='',
  secret='',
  cluster='ap2',
  ssl=True
)

def push_notifications(channel : str, event : str, message : dict):
  pusher_client.trigger(channel, event, message)