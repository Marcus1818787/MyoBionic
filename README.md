# MyoBionic
Open source project aiming to develop a low-cost, actuated, prosthetic hand for transradial amputees controlled through EMG technology.

raspberry Pi setup:
sudo apt-get purge python python3 python-pip python3-pip
sudo apt autoremove
sudo apt-get install python3 python3-pip pigpio git libatlas-base-dev
sudo apt-get update
sudo apt-get upgrade
sudo pip install RPi.GPIO Adafruit_GPIO Adafruit_MCP3008 pyomyo pigpio
sudo pigpiod
git clone --branch main https://github.com/Marcus1818787/MyoBionic.git
