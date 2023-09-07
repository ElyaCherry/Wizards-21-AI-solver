from aenum import NamedConstant


class Card(NamedConstant):
    DETERMINED_ACE = 1
    ACE = 11  # sum 21 or 31 = win, no other way to get 31
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 10
    QUEEN = 10
    KING = 10
    WILD = 0

