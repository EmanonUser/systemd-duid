#!/usr/bin/env python3

import hmac
import hashlib
from csiphash24 import siphash24

mac_address: str = "ff:ff:ff:ff:ff:ff"                          # Your NIC Mac Address | YOU NEED TO ADD YOUR OWN
hash_key_uuid: str = "80118cc2fe4a03ee3ed60c6f363914090a"       # From https://github.com/systemd/systemd/blob/a420d71793bcbc1539a63be60f83cdc14373ea4a/src/libsystemd-network/dhcp-identifier.c#L20
application_id_uuid: str = "a50ad112bf604577a2fb741ab1955b03"   # From https://github.com/systemd/systemd/blob/a420d71793bcbc1539a63be60f83cdc14373ea4a/src/libsystemd-network/dhcp-identifier.c#L21

def add_duid_colons(func):
	def inner(*args, **kwargs) -> str:
		res: str = func(*args, **kwargs)
		res: str = ":".join([ a+b for a,b in zip(res[::2], res[1::2])])
		return res
	return inner

@add_duid_colons
def generate_duid_llt(mac_address: str) -> str:
    """ DUID_LLT is the same as DUID_LL but we add a time source avoiding collision
    The default time added for systemd-networkd is 2000-01-01 00:00:00 UTC, see man networkd.conf """
    duid_type_llt: str = '0001'
    duid_hw_type_ethernet: str = '0001'                 # Assume Ethernet as arp_type see https://www.iana.org/assignments/arp-parameters/arp-parameters.xhtml
    duid_systemd_default_time = '00000000'              # Assume default time 2000-01-01 00:00:00 UTC

    mac_address = mac_address.replace(":", "")
    return duid_type_llt + duid_hw_type_ethernet + duid_systemd_default_time + mac_address

@add_duid_colons
def generate_duid_en(machine_id: str, app_id: str) -> str:
    """ DUID_EN seems to be the same as DUID_UUID but using different hashing
    algorithm siphash24 """
    duid_type_en: str = '0002'
    systemd_entreprise_id: str = '0000ab11'         # From https://github.com/systemd/systemd/blob/a420d71793bcbc1539a63be60f83cdc14373ea4a/src/libsystemd-network/dhcp-identifier.h#L11

    machine_id: bytes = bytes.fromhex(machine_id)
    app_id: bytes = bytes.fromhex(app_id)

    myhash: bytes = siphash24(app_id, machine_id)   # From https://github.com/systemd/systemd/blob/a420d71793bcbc1539a63be60f83cdc14373ea4a/src/libsystemd-network/dhcp-identifier.c#L134
    inverted_hash: bytes = myhash[::-1]             # Reverse string from Big Endian to Little Endian, assume recent amd64 CPU
    res: str = duid_type_en + systemd_entreprise_id + inverted_hash.hex()
    return res

@add_duid_colons
def generate_duid_ll(mac_address: str) -> str:
    """ DUID_LL is generated using your mac addr (without the ':') 
    even if its based on a single interface it may be used on multiple interface """
    duid_type_ll: str = '0003'
    duid_arp_type_ethernet: str = '0001'                # Assume Ethernet as arp_type see https://www.iana.org/assignments/arp-parameters/arp-parameters.xhtml

    mac_address = mac_address.replace(":", "")
    return duid_type_ll + duid_arp_type_ethernet + mac_address

@add_duid_colons
def generate_duid_uuid(machine_id: str, application_id_uuid: str) -> str:
    """ DUID_UUID is generated using a combination of your machine-id plus an application-id
    both are supposed to be stable and feed into an hmac function see man sd_id128_get_machine_app_specific
    I suppose its done to hide the machine-id some bytes are swapped too """
    duid_type_uuid: str = '0004'

    machine_id = bytes.fromhex(machine_id)
    application_id_uuid = bytes.fromhex(application_id_uuid)
    res: hmac.HMAC = hmac.new(machine_id, application_id_uuid, digestmod=hashlib.sha256) # From https://github.com/systemd/systemd/blob/a420d71793bcbc1539a63be60f83cdc14373ea4a/src/libsystemd/sd-id128/sd-id128.c#L279
    res: str = res.hexdigest()[:32]
    res: bytearray = bytearray.fromhex(res)

    res[6]: bytearray = (res[6] & 0x0f) | 0x40                 # From https://github.com/systemd/systemd/blob/a420d71793bcbc1539a63be60f83cdc14373ea4a/src/libsystemd/sd-id128/id128-util.c#L196
    res[8]: bytearray = (res[8] & 0x3F) | 0x80
    return duid_type_uuid + res.hex()

def get_machine_id(machine_id_path='/etc/machine-id') -> str:
    with open(machine_id_path, 'r', encoding='utf8') as machine_id_file:
        return machine_id_file.read()

machine_id = get_machine_id()
print(f'systemd-netwokd DUID_LLT:   { generate_duid_llt(mac_address) }')
print(f'systemd-netwokd DUID_EN:    { generate_duid_en(machine_id, hash_key_uuid )}')
print(f'systemd-netwokd DUID_LL:    { generate_duid_ll(mac_address) }')
print(f'systemd-netwokd DUID_UUID:  { generate_duid_uuid(machine_id, application_id_uuid) }')
