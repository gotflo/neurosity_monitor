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

# Obtenir les infos du device
info = neurosity.get_info()
print("Device Info:", info)

# Callback pour le status
def status_callback(data):
    print("Status callback:", data)

# Callback pour la qualité du signal
def signal_quality_callback(data):
    print("Signal Quality:", data)

# Souscription aux deux flux
unsub_status = neurosity.status(status_callback)
unsub_signal = neurosity.signal_quality(signal_quality_callback)

# Attente de réception de données
time.sleep(10)

# Se désabonner des flux
unsub_status()
unsub_signal()
