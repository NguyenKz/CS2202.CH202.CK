import random
from copy import deepcopy

TALS_1_1 = """The zoologist noted which lion the antelopes had hunted.
The plausibility score is 1 (lions hunts antelopes, not the other way around)."""

TALS_1_2 = """The captain understood which iceberg the boat had sunk.
The plausibility score is 1 (icebergs sunk boats, a boat cannot sink an iceberg)."""

TALS_1_3 = """The zookeeper observed which caretaker the animals had fed.
The plausibility score is 1 (caretakers feed animals, not the other way around)."""

TALS_1 = [TALS_1_1, TALS_1_2, TALS_1_3]

TALS_2_1 = """The pilote remembered which plane the airline had represented.
The plausibility score is 2 (planes represent airlines in general, not the opposite)."""

TALS_2_2 = """The headmaster forgot which teacher the students had taught.
The plausibility score is 2 (in general the teacher teaches the students, not the opposite)."""

TALS_2_3 = """The doctor noted which nurse the patient had treated.
The plausibility score is 2 (in general, the nurse treats the patient, not the opposite)."""

TALS_2 = [TALS_2_1, TALS_2_2, TALS_2_3]

TALS_3_1 = """The witness observed which policeman the robber had caught.
The plausibility score is 3 (in general, policemen catch robbers, not the other way around)."""

TALS_3_2 = """The salesman heard which father the children had scolded.
The plausibility score is 3 (in general fathers scold children, not the other way around)."""

TALS_3_3 = """The journalist revealed which politician the lobbyist had influenced.
The plausibility score is 3 (it can happen that politicians influence lobbyists but it's supposed to be the other way)."""

TALS_3 = [TALS_3_1, TALS_3_2, TALS_3_3]

TALS_4_1 = """The teacher remembered which principal the student had praised.
The plausibility score is 4 (it is relatively plausible that a student would like a principal but not that common)."""

TALS_4_2 = """The judge recalled which lawyer the assistant had called.
The plausibility score is 4 (this is a relatively plausible situation)."""

TALS_4_3 = """The detective identified which officer the suspect had recognized.
The plausibility score is 4 (suspects might know some police officer and recognize them)"""

TALS_4 = [TALS_4_1, TALS_4_2, TALS_4_3]

TALS_5_1 = """The doctor described which symptoms the patient had experienced.
 The plausibility score is 5 (it is relatively plausible that a doctor would describe symptoms a patient had)."""

TALS_5_2 = """The lawyer disclosed which client the judge had acquitted.
The plausibility score is 5 (it is relatively plausible that a lawyer would announce its client has been acquitted)."""

TALS_5_3 = """The tour guide guessed which landmark the visitor had photographed.
The plausibility score is 5 (it is relatively plausible that a tour guide might guess which landmark a tourist might photograph)."""

TALS_5 = [TALS_5_1, TALS_5_2, TALS_5_3]

TALS_6_1 = """The teacher guessed which student the headmaster had fired.
The plausibility score is 6 (it is plausible that a teacher would guess about the decision to fire a student)."""

TALS_6_2 = """The director recalled which scene the editor had cut.
The plausibility score is 6 (it is plausible that a director knows which scene has been cut from the movie)."""

TALS_6_3 = """The coach mentioned which player the scout had recruited.
The plausibility score is 6 (it is plausible that a coach would talk about the recruited players)."""

TALS_6 = [TALS_6_1, TALS_6_2, TALS_6_3]

TALS_7_1 = """The accountant knew which employee the CEO had promoted.
The plausibility score is 7 (it is highly plausible that an accountant would know who got promoted since he handles the money)."""

TALS_7_2 = """The librarian mentioned which book the student had borrowed.
The plausibility score is 7 (it is highly plausible that a librarian would talk about borrowed books)."""

TALS_7_3 = """The musician remembered which song the producer had mixed.
The plausibility score is 7 (it is highly plausible that a musician would remember which song a producer mixed)."""

TALS_7 = [TALS_7_1, TALS_7_2, TALS_7_3]


def get_examples(num_ex: int):
    all_examples = list()

    for orig in [TALS_1, TALS_2, TALS_3, TALS_4, TALS_5, TALS_6, TALS_7]:
        temp_list = deepcopy(orig)
        random.shuffle(temp_list)
        all_examples += temp_list[:int(num_ex)]

    random.shuffle(all_examples)

    return all_examples