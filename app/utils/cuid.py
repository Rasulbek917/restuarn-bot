"""
Prisma'ning `@default(cuid())` bilan bir xil formatdagi ID generator.

Mavjud Neon database'da allaqachon cuid() orqali yaratilgan qatorlar bor
(masalan `User.id`, `Order.id`). Python tomonida yangi qatorlar ham xuddi
shunday formatdagi (kichik harf + raqamlardan iborat, ~25 belgili) unique
string ID olishi kerak — shunda ikkala til ham bir xil ustunga yozadi va
formatlar mos keladi.

Bu klassik cuid v1 algoritmining soddalashtirilgan implementatsiyasi:
timestamp (base36) + counter (base36) + fingerprint + random.
Kriptografik jihatdan cuid bilan bit-baravar emas, lekin collision-resistant
va formatga (harf bilan boshlanadigan, faqat [a-z0-9]) to'liq mos string beradi.
"""
from __future__ import annotations

import os
import random
import socket
import threading
import time

_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
_counter_lock = threading.Lock()
_counter = random.randint(0, 456_976)  # 36^3


def _base36(number: int, pad: int = 0) -> str:
    if number == 0:
        digits = "0"
    else:
        digits = ""
        n = number
        while n > 0:
            n, rem = divmod(n, 36)
            digits = _ALPHABET[rem] + digits
    return digits.rjust(pad, "0")


def _fingerprint() -> str:
    host = socket.gethostname()
    pid = os.getpid()
    value = sum(ord(c) for c in host) + pid
    return _base36(value % (36**4), 4)


_FINGERPRINT = _fingerprint()


def cuid() -> str:
    global _counter
    with _counter_lock:
        _counter = (_counter + 1) % 1_679_616  # 36^4
        counter_part = _base36(_counter, 4)

    timestamp_part = _base36(int(time.time() * 1000))
    random_part = _base36(random.randint(0, 36**8), 8)

    return f"c{timestamp_part}{counter_part}{_FINGERPRINT}{random_part}"[:25]
