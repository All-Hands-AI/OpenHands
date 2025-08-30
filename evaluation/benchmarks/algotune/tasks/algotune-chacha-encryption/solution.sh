#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305 as C

_cache = {}
_res = {}
_S1 = slice(None, -16)
_S2 = slice(-16, None)

class Solver:
    __slots__ = ()

    @staticmethod
    def solve(p, _cache=_cache, _res=_res, C=C, _S1=_S1, _S2=_S2):
        # Cache encrypt method per key
        key = p['key']
        e = _cache.get(key)
        if e is None:
            e = C(key).encrypt
            _cache[key] = e
        # Local references to reduce dict lookups
        n = p['nonce']; pt = p['plaintext']; aad = p['associated_data']
        # Perform encryption
        c = e(n, pt, aad)
        # Slice ciphertext and tag
        _res['ciphertext'] = c[_S1]
        _res['tag']        = c[_S2]
        return _res
EOF
