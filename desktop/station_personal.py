from station_app import launch_station
from station_config import SERVER_URL, PERSONAL_KEY


if __name__ == '__main__':
    launch_station(SERVER_URL, 'personal', PERSONAL_KEY)
