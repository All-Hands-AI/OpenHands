from mnemonic import Mnemonic

from openhands.server.utils.crypto import generate_mnemonic


def test_generate_mnemonic_length():
    """Test that generated mnemonic has exactly 12 words"""
    mnemonic = generate_mnemonic()
    assert len(mnemonic.split()) == 12


def test_generate_mnemonic_words_in_wordlist():
    """Test that all generated words are in the BIP39 English wordlist"""
    mnemo = Mnemonic('english')
    mnemonic = generate_mnemonic()

    # Check each word is in the wordlist
    for word in mnemonic.split():
        assert word in mnemo.wordlist


def test_generate_mnemonic_uniqueness():
    """Test that multiple calls generate different mnemonics"""
    mnemonic1 = generate_mnemonic()
    mnemonic2 = generate_mnemonic()
    assert mnemonic1 != mnemonic2


def test_generate_mnemonic_validity():
    """Test that generated mnemonic is valid according to BIP39 standard"""
    mnemo = Mnemonic('english')
    mnemonic = generate_mnemonic()
    # Check if the mnemonic is valid according to BIP39
    assert mnemo.check(mnemonic) is True
