"""Money uses integer hundredths; floats are display-only projections."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN


def cents(value):
    if isinstance(value, bool):
        raise ValueError('Valor monetário inválido.')
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0:
            raise ValueError('Valor monetário inválido.')
        return int((number * 100).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN))
    except (InvalidOperation, TypeError, OverflowError) as exc:
        raise ValueError('Valor monetário inválido.') from exc


def set_balance(state, value):
    return set_cents(state, cents(value))


def set_cents(state, value):
    if type(value) is not int or value < 0:
        raise ValueError('Saldo inválido.')
    state['moedas_centavos'] = value
    state['moedas'] = value / 100
    return value


def balance(state):
    return state['moedas_centavos']


def credit(state, value):
    set_cents(state, balance(state) + value)


def can_buy(state, price):
    return balance(state) >= cents(price)


def debit(state, price):
    amount = cents(price)
    if balance(state) < amount:
        return False
    set_cents(state, balance(state) - amount)
    return True


def reward(base, boat):
    """Round each event once, using decimal half-even, before crediting."""
    return cents(Decimal(str(base)) * (Decimal('1') + Decimal('0.2') * boat))
