"""passlib.handlers.sha1_crypt
"""

#=========================================================
#imports
#=========================================================

#core
from hmac import new as hmac
from hashlib import sha1
import re
import logging; log = logging.getLogger(__name__)
from warnings import warn
#site
#libs
from passlib.utils import h64, handlers as uh, safe_os_crypt, classproperty, \
    to_native_str, to_unicode, bytes, b
from passlib.utils.compat import unicode
from passlib.utils.pbkdf2 import hmac_sha1
from passlib.utils.compat import u
#pkg
#local
__all__ = [
]
#=========================================================
#sha1-crypt
#=========================================================
class sha1_crypt(uh.HasManyBackends, uh.HasRounds, uh.HasSalt, uh.GenericHandler):
    """This class implements the SHA1-Crypt password hash, and follows the :ref:`password-hash-api`.

    It supports a variable-length salt, and a variable number of rounds.

    The :meth:`encrypt()` and :meth:`genconfig` methods accept the following optional keywords:

    :param salt:
        Optional salt string.
        If not specified, an 8 character one will be autogenerated (this is recommended).
        If specified, it must be 0-64 characters, drawn from the regexp range ``[./0-9A-Za-z]``.

    :param salt_size:
        Optional number of bytes to use when autogenerating new salts.
        Defaults to 8 bytes, but can be any value between 0 and 64.

    :param rounds:
        Optional number of rounds to use.
        Defaults to 40000, must be between 1 and 4294967295, inclusive.

    It will use the first available of two possible backends:

    * stdlib :func:`crypt()`, if the host OS supports sha1-crypt (NetBSD).
    * a pure python implementation of sha1-crypt

    You can see which backend is in use by calling the :meth:`get_backend()` method.
    """

    #=========================================================
    #class attrs
    #=========================================================
    #--GenericHandler--
    name = "sha1_crypt"
    setting_kwds = ("salt", "salt_size", "rounds")
    ident = u("$sha1$")
    checksum_size = 28
    checksum_chars = uh.HASH64_CHARS

    #--HasSalt--
    default_salt_size = 8
    min_salt_size = 0
    max_salt_size = 64
    salt_chars = uh.HASH64_CHARS

    #--HasRounds--
    default_rounds = 40000 #current passlib default
    min_rounds = 1 #really, this should be higher.
    max_rounds = 4294967295 # 32-bit integer limit
    rounds_cost = "linear"

    #=========================================================
    #formatting
    #=========================================================

    @classmethod
    def from_string(cls, hash):
        rounds, salt, chk = uh.parse_mc3(hash, cls.ident, cls.name)
        if rounds.startswith("0"):
            raise ValueError("invalid sha1-crypt hash (zero-padded rounds)")
        return cls(
            rounds=int(rounds),
            salt=salt,
            checksum=chk,
            strict=bool(chk),
        )

    def to_string(self, native=True):
        out = u("$sha1$%d$%s") % (self.rounds, self.salt)
        if self.checksum:
            out += u("$") + self.checksum
        return to_native_str(out) if native else out

    #=========================================================
    #backend
    #=========================================================
    backends = ("os_crypt", "builtin")

    _has_backend_builtin = True

    @classproperty
    def _has_backend_os_crypt(cls):
        h = u('$sha1$1$Wq3GL2Vp$C8U25GvfHS8qGHimExLaiSFlGkAe')
        return bool(safe_os_crypt and safe_os_crypt(u("test"),h)[1]==h)

    def _calc_checksum_builtin(self, secret):
        if isinstance(secret, unicode):
            secret = secret.encode("utf-8")
        rounds = self.rounds
            #NOTE: this uses a different format than the hash...
        result = u("%s$sha1$%s") % (self.salt, rounds)
        result = result.encode("ascii")
        r = 0
        while r < rounds:
            result = hmac_sha1(secret, result)
            r += 1
        return h64.encode_transposed_bytes(result, self._chk_offsets).decode("ascii")

    _chk_offsets = [
        2,1,0,
        5,4,3,
        8,7,6,
        11,10,9,
        14,13,12,
        17,16,15,
        0,19,18,
    ]

    def _calc_checksum_os_crypt(self, secret):
        ok, hash = safe_os_crypt(secret, self.to_string(native=False))
        if ok:
            return hash[hash.rindex("$")+1:]
        else:
            return self._calc_checksum_builtin(secret)

    #=========================================================
    #eoc
    #=========================================================

#=========================================================
#eof
#=========================================================
