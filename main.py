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


class Column:
    cards = []
    current_sum = 0

    def __len__(self):
        return len(self.cards)

    def clear(self):
        self.cards.clear()
        self.current_sum = 0

    def add(self, card):
        if card == Card.WILD:
            self.clear()
            return 4  # win by wildcard

        self.cards.append(card)
        self.current_sum += card
        if self.current_sum > 21:
            for i, c in enumerate(self.cards):
                if c == Card.ACE:
                    self.cards[i] = Card.DETERMINED_ACE
                    self.current_sum -= 10
                    break

        if (self.current_sum <= 21) and len(self.cards) == 5:
            self.clear()
            return 5  # win by 5 cards
        elif self.current_sum == 21 and len(self.cards) == 2:
            self.clear()
            return 2  # win by blackjack
        elif self.current_sum == 21:
            self.clear()
            return 3  # normal win
        elif self.current_sum > 21:
            self.clear()
            return 1  # bust
        elif self.current_sum < 21:
            return 0  # normal append


class GameState:
    columns = [Column(), Column(), Column(), Column()]
    busts = 0
    score = 0
    combo = 0
    last52 = []

    def GetSums(self):
        return [column.current_sum for column in self.columns]

    def Add(self, card, column):
        if not any(column == index for index in range(4)):
            raise IndexError("Invalid column index")

        res = self.columns[column].add(card)
        if res == 1:
            self.combo = 0
            self.busts += 1
            if self.busts == 3:
                return 1
        elif res == 0:
            self.combo = 0
        else:
            if res == 2:
                self.score += 400
            elif res == 3:
                self.score += 150
            elif res == 4:
                self.score += 200
            elif res == 5:
                self.score += 600

            combo_bonus = 300 * int(self.combo >= 1) + 300 * int(self.combo >= 2)
            self.score += combo_bonus
            self.combo += 1

    def FindPair(self):
        sums = self.GetSums()
        seen = []
        for i, cur in enumerate(sums):
            if cur not in seen:
                seen.append(cur)
            else:  # found a pair of columns with same values
                pair = [seen.index(cur), i]
                return pair
        else:
            return None

    def MakeMoves(self):
        card: int
        while True:
            c = input("\nEnter next card: ").rstrip()
            if c == "0" or c == "wild" or c == "w":
                card = Card.WILD
            elif c == "2":
                card = Card.TWO
            elif c == "3":
                card = Card.THREE
            elif c == "4":
                card = Card.FOUR
            elif c == "5":
                card = Card.FIVE
            elif c == "6":
                card = Card.SIX
            elif c == "7":
                card = Card.SEVEN
            elif c == "8":
                card = Card.EIGHT
            elif c == "9":
                card = Card.NINE
            elif c == "10":
                card = Card.TEN
            elif c == "J" or c == "j":
                card = Card.JACK
            elif c == "Q" or c == "q":
                card = Card.QUEEN
            elif c == "K" or c == "k":
                card = Card.KING
            elif c == "A" or c == "a":
                card = Card.ACE

            elif c == "deck" or c == "d":
                print(self.last52)
                continue
            elif c == "stop" or c == "quit" or c == "exit":
                return
            elif c == "state":
                print(self.columns)
                print(self.score)
                print(self.combo)
                print(self.busts)
                continue
            else:
                raise ValueError("Invalid card")

            self.last52.append(card)
            if len(self.last52) == 53:
                self.last52.pop(0)

            col = self.CalculateBestMove(card)
            print(f"\n{col + 1}")
            res = self.Add(card, col)
            if res == 1:
                print(f"Game over. Score: {self.score}")
                return

    def CalculateBestMove(self, card):
        sums = self.GetSums()
        if card == Card.ACE:
            for i in range(4):
                if sums[i] == 20:  # complete the 20-column
                    return i
            for i in range(4):
                if len(self.columns[i]) == 4:  # complete the 5-card column
                    return i
            if 0 in sums:
                return sums.index(0)  # prepare blackjack  # 400 guaranteed + spare 10-card
            if 10 in sums:
                return sums.index(10)  # form blackjack or 21  # 400 or 150 points  # priority over ^?
            candidates = []
            for i in range(4):
                if 10 <= sums[i] < 20 and len(self.columns[i]) >= 3:  # prioritise columns with 3+ cards
                    if sums[i] + 1 not in sums:  # prioritise not forming duplicates
                        candidates.insert(0, i)
                    candidates.append(i)
            if candidates:
                return candidates[0]  # TODO: also prioritise columns with sums closer to 15-17
            for i in range(4):
                if sums[i] + 1 not in sums:
                    candidates.append(i)
            if 1 <= len(candidates) <= 3:
                return candidates.index(min(candidates))
            for i in range(4):
                if sums[i] < 10:
                    return i
            pass  # TODO: multifactorial decision
            return 0
        elif card == Card.WILD:
            pair = self.FindPair()
            if pair is not None:
                col = pair[0 if len(self.columns[pair[0]]) < len(self.columns[pair[1]]) else 1]
                return col  # eliminate the one with fewer cards
            else:
                col = sums.index(max(sums))  # eliminates first of 20, 19, 18, etc.
                return col
            # TODO: if there's a column with 4 cards and sum 18 or less (or 19 and no 2s recently),
            #  the wild card must skip it

        elif any(card == c for c in [Card.TEN, Card.JACK, Card.QUEEN, Card.KING]):  # value 10
            if 11 in sums:
                return sums.index(11)
            elif 20 not in sums:
                if 10 in sums:
                    return sums.index(10)
                elif 0 in sums:
                    return sums.index(0)
            # if we already have 20 or can't form it from 0 or 10:
            candidates_ = list(filter(lambda j: sums[j] + card <= 21, range(4)))
            if len(candidates_) == 0:
                pair = self.FindPair()
                if pair is not None:
                    col = pair[0 if len(self.columns[pair[0]]) < len(self.columns[pair[1]]) else 1]
                    return col
                return sums.index(max(sums))

            candidates = list(filter(lambda j: sums[j] + 10 not in sums, candidates_))
            if len(candidates) == 0:  # we get a bust anyway - use it to eliminate duplicates
                pair = self.FindPair()
                if pair is not None:
                    col = pair[0 if len(self.columns[pair[0]]) < len(self.columns[pair[1]]) else 1]
                    return col
                return sums.index(max(sums))
            elif len(candidates) == 1:
                return candidates[0]
            else:
                pair = self.FindPair()
                if pair is not None:
                    col = pair[0 if len(self.columns[pair[0]]) < len(self.columns[pair[1]]) else 1]
                    # the one with fewer cards
                    return col

                new_candidates = list(filter(lambda j: sums[j] + card not in sums, candidates))
                if len(new_candidates) == 0:
                    return candidates[0]
                else:
                    return new_candidates[0]
                # is that all?

        else:  # 2 3 4 5 6 7 8 9
            for i in range(4):
                if 21 - sums[i] == card:  # complete 21
                    return i
            for i in range(4):
                if 11 - sums[i] == card:  # form 11
                    return i
            for i in range(4):
                if len(self.columns[i]) == 4 and sums[i] + card <= 21:  # complete the 5-card column
                    return i

            candidates_ = list(filter(lambda j: sums[j] + card <= 21, range(4)))
            if len(candidates_) == 0:
                pair = self.FindPair()
                if pair is not None:
                    col = pair[0 if len(self.columns[pair[0]]) < len(self.columns[pair[1]]) else 1]
                    return col
                return sums.index(max(sums))

            candidates = list(filter(lambda j: sums[j] + card != 20
                                     and sums[j] + card not in sums
                                     and sums[j] + card != 10, candidates_))
            if candidates:
                candidates.sort(key=lambda j: sums[j] + card)
                return candidates[0]  # TODO: this may destroy an ace column

            candidates = list(filter(lambda j: sums[j] + card != 20
                                     and sums[j] + card not in sums, candidates_))
            if candidates:
                candidates.sort(key=lambda j: sums[j] + card)
                return candidates[0]

            candidates = list(filter(lambda j: sums[j] + card != 10
                                     and sums[j] + card not in sums, candidates_))
            if candidates:
                candidates.sort(key=lambda j: sums[j] + card)
                return candidates[0]

            candidates = list(filter(lambda j: sums[j] + card not in sums, candidates_))
            if candidates:
                candidates.sort(key=lambda j: sums[j] + card)
                return candidates[0]

            return 0
            # TODO: multifactorial decision
            # try not to form too many of 19, 18, 17 because all the small cards are needed for 5-column


if __name__ == '__main__':
    game = GameState()
    game.MakeMoves()
