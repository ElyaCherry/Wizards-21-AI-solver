from Card import Card
from predict import load_trained_model_and_predict, load_reinforced_model_and_predict
from random import choice, choices


class Column:
    cards: list
    current_sum: int

    def __init__(self):
        self.cards = []
        self.current_sum = 0

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
    acceptable_modes = ["ML", "algorithm", "play", "train"]

    def __init__(self, mode: str):
        self.columns = [Column(), Column(), Column(), Column()]
        self.busts = 0
        self.score = 0
        self.combo = 0
        self.last52 = [-1] * 52
        self.card = -1
        if mode not in self.acceptable_modes:
            raise ValueError(f"No such mode. Available modes are: {', '.join(self.acceptable_modes)}.")
        else:
            self.mode = mode

    def get_sums(self):
        return [column.current_sum for column in self.columns]

    def add(self, card, column):
        if not any(column == index for index in range(4)):
            raise IndexError("Invalid column index")

        res = self.columns[column].add(card)
        if res == 1:
            self.combo = 0
            self.busts += 1
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
        return res

    def find_pair(self):
        sums = self.get_sums()
        seen = []
        for i, cur in enumerate(sums):
            if cur not in seen:
                seen.append(cur)
            else:  # found a pair of columns with same values
                pair = [seen.index(cur), i]
                return pair
        else:
            return None

    def make_moves(self, col=None):
        while True:
            if self.mode == "play" or self.mode == "reinforce":
                c = self.generate_next_card()
            else:
                c = input("\nEnter next card: ").rstrip()

            if c == "0" or c == "wild" or c == "w":
                self.card = Card.WILD
            elif c == "2":
                self.card = Card.TWO
            elif c == "3":
                self.card = Card.THREE
            elif c == "4":
                self.card = Card.FOUR
            elif c == "5":
                self.card = Card.FIVE
            elif c == "6":
                self.card = Card.SIX
            elif c == "7":
                self.card = Card.SEVEN
            elif c == "8":
                self.card = Card.EIGHT
            elif c == "9":
                self.card = Card.NINE
            elif c == "10":
                self.card = Card.TEN
            elif c == "J" or c == "j":
                self.card = Card.JACK
            elif c == "Q" or c == "q":
                self.card = Card.QUEEN
            elif c == "K" or c == "k":
                self.card = Card.KING
            elif c == "A" or c == "a" or c == "1":
                self.card = Card.ACE

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

            if self.mode == "train":
                col = int(input("Propose the best move: ")) - 1
                self.record_train_data(col)
            elif self.mode == "play":
                col = int(input("Enter the column number: ")) - 1
            elif self.mode == "ML":
                col = self.calculate_best_move_with_ml()
                print(f"\n{col + 1}")
            elif self.mode == "algorithm":
                col = self.calculate_best_move(self.card)
                print(f"\n{col + 1}")
            elif self.mode == "reinforce":
                yield self.dump_to_list()
                col = col

            self.last52.append(self.card)
            self.last52.pop(0)

            res = self.add(self.card, col)
            self.card = -1

            if self.mode == "reinforce":
                return res
            if res == 1 and self.busts == 3:
                print(f"Game over. Score: {self.score}")
                return

    def calculate_best_move(self, card):
        sums = self.get_sums()
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
            pair = self.find_pair()
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
                pair = self.find_pair()
                if pair is not None:
                    col = pair[0 if len(self.columns[pair[0]]) < len(self.columns[pair[1]]) else 1]
                    return col
                return sums.index(max(sums))

            candidates = list(filter(lambda j: sums[j] + 10 not in sums, candidates_))
            if len(candidates) == 0:  # we get a bust anyway - use it to eliminate duplicates
                pair = self.find_pair()
                if pair is not None:
                    col = pair[0 if len(self.columns[pair[0]]) < len(self.columns[pair[1]]) else 1]
                    return col
                return sums.index(max(sums))
            elif len(candidates) == 1:
                return candidates[0]
            else:
                pair = self.find_pair()
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
                pair = self.find_pair()
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

    def dump_to_list(self):
        # Scalar features
        current_score = self.score
        num_busts = self.busts
        current_combo = self.combo

        # Last 52 cards
        last_52_cards = [int(c) for c in self.last52[::-1]]  # Take the last 52 cards or fewer

        # Columns
        column_features = []
        for column in self.columns:
            # Pad columns with placeholders (-1) if needed
            padded_column = [int(c) for c in column.cards] + [-1] * (5 - len(column.cards))
            column_features.extend(padded_column)
            # Include the current sum of the column
            column_features.append(column.current_sum)

        # Combine all features into a single input array
        input_features = [int(self.card), current_score, num_busts, current_combo] + column_features + last_52_cards

        return input_features  # len 80

    def record_train_data(self, col):
        with open('training_input.py', 'a') as file:
            file.write(f"{self.dump_to_list()},\n")
        formatted = [int(bool(i == col)) for i in range(4)]
        with open('training_output.py', 'a') as file:
            file.write(f"{formatted},\n")

    def calculate_best_move_with_ml(self):
        # predicted_column = load_trained_model_and_predict(self.preprocess_input(card))
        predicted_column = load_reinforced_model_and_predict(self.dump_to_list())
        return predicted_column

    @staticmethod
    def generate_next_card():
        normal_cards = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "j", "q", "k", "a"]
        card_choice = choice(normal_cards)
        wild_card_bias = 52  # 1 wild card per this many normal cards
        card_choice = choices([card_choice, "w"], weights=[wild_card_bias, 1])
        return card_choice
