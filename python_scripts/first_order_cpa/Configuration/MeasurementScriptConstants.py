# Picoscope
PICO_MAGIC_VALUE: int = 32512
PS6000_TRIGGER_AUX: int = 5  # Assuming 5 is the correct value for AUX based on the documentation
PS6000_RISING: int = 2  # Assuming 2 is the correct value for RISING based on the documentation

# JavaCard

# Apdu constants
SW1_SUCCESS: int = 0x90
SW2_SUCCESS: int = 0x00

#Instructions
BASIC_INS_CLASS: int = 0xB0
ZERO_INS_CLASS: int = 0x00
SELECT_APPLET_INS: int = 0xA4
SET_KEY_INS: int = 0x10
SET_NONCE_INS: int = 0x11
SET_PT_INS: int = 0x13
ENCRYPT_ASCON_INS: int = 0x61
DECRYPT_ASCON_INS: int = 0x62
ENCRYPT_AES_INS: int = 0x71
DECRYPT_AES_INS: int = 0x72
SCHEDULER_AES_INS: int = 0x73

# Other
MAX_BYTE: int = 0xFF