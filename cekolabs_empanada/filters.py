

def tolower(literal):
    return unicode(literal).lower()

def toupper(literal):
    return unicode(literal).upper()

def reverse(literal):
    return literal[::-1]

FilterMap = {
    'tolower': tolower,
    'toupper': toupper,
    'reverse': reverse
}