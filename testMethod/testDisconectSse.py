import sseclient
import requests

url = "http://localhost:3000/petstore/sse"
response = requests.get(url, stream=True)
client = sseclient.SSEClient(response)

for event in client.events():
    print(event.data)
    if "some_condition_to_stop" in event.data:
        break

# Ngắt stream:
response.close()