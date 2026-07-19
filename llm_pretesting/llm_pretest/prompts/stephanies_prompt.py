import random
from copy import deepcopy

STEPHS_1_1 = """The bag had been properly cured.
The plausibility score is 1 (bags are inanimate and don't need to be cured)."""

STEPHS_1_2 = """The sky had been completely repaired.
The plausibility score is 1 (the sky is not something you repair)."""

STEPHS_1_3 = """The child had been perfectly assembled.
The plausibility score is 1 (children are not assembled)."""

STEPHS_1 = [STEPHS_1_1, STEPHS_1_2, STEPHS_1_3]

STEPHS_2_1 = """The computer had been successfully took down.
The plausibility score is 2 (in general you don't take down a computer)."""

STEPHS_2_2 = """The headmaster forgot which teacher the students had taught.
The plausibility score is 2 (in general the teacher teaches the students, not the opposite)."""

STEPHS_2_3 = """The doctor noted which nurse the patient had treated.
The plausibility score is 2 (in general, the nurse treats the patient, not the opposite)."""

STEPHS_2 = [STEPHS_2_1, STEPHS_2_2, STEPHS_2_3]

STEPHS_3_1 = """The witness observed which policeman the robber had caught.
The plausibility score is 3 (in general, policemen catch robbers, not the other way around)."""

STEPHS_3_2 = """The salesman heard which father the children had scolded.
The plausibility score is 3 (in general fathers scold children, not the other way around)."""

STEPHS_3_3 = """The journalist revealed which politician the lobbyist had influenced.
The plausibility score is 3 (it can happen that politicians influence lobbyists but it's supposed to be the other way)."""

STEPHS_3 = [STEPHS_3_1, STEPHS_3_2, STEPHS_3_3]

STEPHS_4_1 = """The teacher remembered which principal the student had praised.
The plausibility score is 4 (it is relatively plausible that a student would like a principal but not that common)."""

STEPHS_4_2 = """The judge recalled which lawyer the assistant had called.
The plausibility score is 4 (this is a relatively plausible situation)."""

STEPHS_4_3 = """The detective identified which officer the suspect had recognized.
The plausibility score is 4 (suspects might know some police officer and recognize them)"""

STEPHS_4 = [STEPHS_4_1, STEPHS_4_2, STEPHS_4_3]

STEPHS_5_1 = """The doctor described which symptoms the patient had experienced.
 The plausibility score is 5 (it is relatively plausible that a doctor would describe symptoms a patient had)."""

STEPHS_5_2 = """The lawyer disclosed which client the judge had acquitted.
The plausibility score is 5 (it is relatively plausible that a lawyer would announce its client has been acquitted)."""

STEPHS_5_3 = """The tour guide guessed which landmark the visitor had photographed.
The plausibility score is 5 (it is relatively plausible that a tour guide might guess which landmark a tourist might photograph)."""

STEPHS_5 = [STEPHS_5_1, STEPHS_5_2, STEPHS_5_3]

STEPHS_6_1 = """The teacher guessed which student the headmaster had fired.
The plausibility score is 6 (it is plausible that a teacher would guess about the decision to fire a student)."""

STEPHS_6_2 = """The director recalled which scene the editor had cut.
The plausibility score is 6 (it is plausible that a director knows which scene has been cut from the movie)."""

STEPHS_6_3 = """The coach mentioned which player the scout had recruited.
The plausibility score is 6 (it is plausible that a coach would talk about the recruited players)."""

STEPHS_6 = [STEPHS_6_1, STEPHS_6_2, STEPHS_6_3]


def get_examples(num_ex: int):
    all_examples = list()

    for orig in [STEPHS_1, STEPHS_2, STEPHS_3, STEPHS_4, STEPHS_5, STEPHS_6]:
        temp_list = deepcopy(orig)
        random.shuffle(temp_list)
        all_examples += temp_list[:int(num_ex)]

    random.shuffle(all_examples)

    return all_examples