import time

from neurosity import NeurositySDK
import os
from dotenv import load_dotenv

load_dotenv()

neurosity = NeurositySDK({
    "device_id": os.getenv("NEUROSITY_DEVICE_ID")
})

neurosity.login({
    "email": os.getenv("NEUROSITY_EMAIL"),
    "password": os.getenv("NEUROSITY_PASSWORD")
})

# Tester différentes méthodes
info = neurosity.get_info()
print("Device Info:", info)

# Essayer de récupérer le status
def test_callback(data):
    print("Status callback:", data)

unsub = neurosity.status(test_callback)
time.sleep(5)
unsub()