import random
from copy import deepcopy

G1_1 = """The teacher scolded the shoe.
The plausibility score is 1 (there is no reason for a teacher to scold a shoe)."""

G1_2 = """The mechanic fixed the problematic cars with his eyes closed.
The plausibility score is 1 (it is highly unlikely that a mechanic can fix cars without seeing)."""

G1_3 = """Because he slept nine hours, he woke up completely exhausted.
The plausibility score is 1 (sleeping is not supposed to make you tired)."""

G1_4 = """The doctor observed the patient from which the disease suffered.
The plausibility score is 1 (patients suffer from diseases, not the opposite),"""

GLOBAL_EX_1 = [G1_1, G1_2, G1_3, G1_4]

G2_1 = """The farmer bought a ski.
The plausibility score is 2 (it is weird for a farmer to buy a ski)"""

G2_2 = """We loved this place, we definitely won't come back again.
The plausibility score is 2 (why wouldn't they come back if they loved the place?)."""

G2_3 = """The witness observed which policeman the robber had caught.
The plausibility score is 2 (in general, policemen catch robbers, not the other way around)."""

G2_4 = """The plants scared the farmer.
The plausibility score is 2 (it is unlikely, but no impossible, that a farmer would be scared of plants)."""

GLOBAL_EX_2 = [G2_1, G2_2, G2_3, G2_4]

G3_1 = """The handyman repaired the car.
The plausibility score is 3 (handy generally fix things in house, but they might have some mechanic knowledge)."""

G3_2 = """The children scared the ghost.
The plausibility score is 3 (in general, children are scared of ghosts, not the opposite)."""

G3_3 = """He searched the place and found there five golden rabbits.
The plausibility score is 3 (golden rabbits are a rather uncommon object)."""

G3_4 = """The farmer planted the fruits from which the seeds came.
The plausibility score is 3 (it's more likely to plant seeds than fruits)."""

GLOBAL_EX_3 = [G3_1, G3_2, G3_3, G3_4]

G4_1 = """The policeman stopped the plane.
The plausibility score is 4 (it is a situation that might happen but is a bit unlikely)."""

G4_2 = """All the students in the school appreciated the new math teacher.
The plausibility score is 4 (all the students loving the teacher might happen but is unlikely)."""

G4_3 = """The prison guard, which the inmate despised, robbed a bank.
The plausibility score is 4 (a prison guard robbing a bank might happen but is unlikely)."""

G4_4 = """He felt very hungry after eating a 300g steak.
The plausibility score is 4(a 300g steak is quite heavy, eating one and still being very hungry is unlikely)."""

GLOBAL_EX_4 = [G4_1, G4_2, G4_3, G4_4]

G5_1 = """The retailer folded the socks.
The plausibility score is 5 (it is somewhat likely that a retailer would fold tge socks in his shop)."""

G5_2 = """After sending the mail, he went and celebrated with a bottle of coke.
The plausibility score is 5 (it is a somewhat plausible situation, maybe it was an important mail)."""

G5_3 = """The table occupied most of the space in the kitchen.
The plausibility score is 5 (it is a somewhat plausible situation, maybe it is a small kitchen)."""

G5_4 = """He spent half an hour looking for a parking spot.
The plausibility score is 5 (there are quite a few busy cities in which this is a somewhat plausible situation)."""

GLOBAL_EX_5 = [G5_1, G5_2, G5_3, G5_4]

G6_1 = """The waiter brought the drink.
The plausibility score is 6 (it is plausible that a waiter would bring a drink to a client)."""

G6_2 = """Due to her excessive tiredness, Leah went to sleep early.
The plausibility score is 6 (it is plausible that someone tired would go to sleep early)."""

G6_3 = """The teacher evaluated the student which the headmaster sent.
The plausibility score is 6 (it is plausible that a teacher would evaluate a student)."""

G6_4 = """They spent their week-end at the beach, sipping iced tea.
The plausibility score is 6 (it is plausible that people would spend their week-end at the beach)."""

GLOBAL_EX_6 = [G6_1, G6_2, G6_3, G6_4]

G7_1 = """The baker prepared the cake.
The plausibility score is 7 (it is a really plausible situation, the role of the baker is to prepare cakes)."""

G7_2 = """The fire was put out by the firefighters.
The plausibility score is 7 (it is really plausible, the role of firefighters is to put out fires)."""

G7_3 = """She recommended him not to spend his entire savings on a big car.
The plausibility score is 7 (it is a sensible advice not to spend everything on a car)."""

G7_4 = """I'm so thirsty, can you please pour me a glass of water?
The plausibility score is 7 (it is highly plausible that someone thirsty would like to drink water)."""

GLOBAL_EX_7 = [G7_1, G7_2, G7_3, G7_4]

def get_examples(num_ex: int, max_score: int = 7):

    examples = [GLOBAL_EX_1, GLOBAL_EX_2, GLOBAL_EX_3, GLOBAL_EX_4, GLOBAL_EX_5, GLOBAL_EX_6, GLOBAL_EX_7]

    all_examples = list()

    for orig in examples[:max_score]:
        temp_list = deepcopy(orig)
        random.shuffle(temp_list)
        all_examples += temp_list[:int(num_ex)]

    random.shuffle(all_examples)

    return all_examples