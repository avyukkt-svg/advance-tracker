from nse import NSE
import os

download_dir = os.path.join(os.getcwd(), 'downloads')
os.makedirs(download_dir, exist_ok=True)
nse_instance = NSE(download_folder=download_dir)

try:
    data = nse_instance.announcements()
    if isinstance(data, list) and len(data) > 0:
        print(data[0])
    elif isinstance(data, dict):
        print(list(data.keys()))
        if 'data' in data and len(data['data']) > 0:
            print("First item:", data['data'][0])
    else:
        print(data)
except Exception as e:
    print("Error:", e)
