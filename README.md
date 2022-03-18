# systemd-networkd-duid
This is a python script to calculate all the different type of DUID systemd-networkd may use --> DUID_LLT, DUID_EN, DUID_LL, DUID_UUID
DUID_EN is the default used by systemd-network

Usage: 
- Install python requirements | pip install -r requirements.txt
- Add your own interface mac address in the script line 7
- run python3 systemd_duid.py
