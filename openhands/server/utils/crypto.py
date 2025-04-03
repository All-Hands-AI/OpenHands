from mnemonic import Mnemonic


def generate_mnemonic() -> str:
    """
    Generate a 12-word mnemonic phrase using BIP39 standard.

    Returns:
        str: A space-separated string of 12 random words that form a mnemonic phrase
    """
    mnemo = Mnemonic('english')
    # Generate a 128-bit entropy which will give us a 12-word mnemonic
    mnemonic = mnemo.generate(128)  # 128 bits = 12 words
    return mnemonic
