import random
from copy import deepcopy

SAME_EX_1_1 = """The teacher scolded the shoe.
The naturalness score is 1 (there is no reason for a teacher to scold a shoe)"""

SAME_EX_1_2 = """The nurse brought the llama.
The naturalness score is 1 (why would a nurse bring a llama to an hospital)."""

SAME_EX_1_3 = """The policeman looked for the spaceship.
The naturalness score is 1 (why would a policeman look for a spaceship)"""

SAME_EX_1 = [SAME_EX_1_1, SAME_EX_1_2, SAME_EX_1_3]

SAME_EX_2_1 = """The teacher scolded the farmer.
The naturalness score is 2 (it is unlikely that a teacher would scold a farmer)"""

SAME_EX_2_2 = """The nurse brought the car.
The naturalness score is 2 (it is unlikely that a nurse would need to bring a car)"""

SAME_EX_2_3 = """The policeman looked for the dish.
The naturalness score is 2 (it is unlikely that a policeman would look for a dish)"""

SAME_EX_2 = [SAME_EX_2_1, SAME_EX_2_2, SAME_EX_2_3]

SAME_EX_3_1 = """The teacher scolded the cat.
The naturalness score is 3 (it is a somewhat unnatural/implausible situation)"""

SAME_EX_3_2 = """The nurse brought the chair.
The naturalness score is 3 (it is not the role of a nurse to bring a chair but it might happen)"""

SAME_EX_3_3 = """The policeman looked for the bicycle.
The naturalness score is 3 (it is a bit unlikely for a policeman to look for a bicycle but it might happen)"""

SAME_EX_3 = [SAME_EX_3_1, SAME_EX_3_2, SAME_EX_3_3]

SAME_EX_4_1 = """The teacher scolded the headmaster.
The naturalness score is 4 (it is a situation that might happen but is a bit unlikely)"""

SAME_EX_4_2 = """The nurse brought the food.
The naturalness score is 4 (it might be the role of the nurse to bring food but it's not their main task)"""

SAME_EX_4_3 = """The policeman looked for the bag.
The naturalness score is 4 (a policeman might look for a bag in a case but it does not happen often)"""

SAME_EX_4 = [SAME_EX_4_1, SAME_EX_4_2, SAME_EX_4_3]

SAME_EX_5_1 = """The teacher scolded the parents.
The naturalness score is 5 (it is a somewhat natural/plausible situation)"""

SAME_EX_5_2 = """The nurse brought the intern.
The naturalness score is 5 (it somewhat likely that a nurse would bring an intern)"""

SAME_EX_5_3 = """The policeman looked for the lawyer.
The naturalness score is 5 (it is somewhat likely that a policeman would look for a lawyer)"""

SAME_EX_5 = [SAME_EX_5_1, SAME_EX_5_2, SAME_EX_5_3]

SAME_EX_6_1 = """The teacher scolded the student.
The naturalness score is 6 (it is a natural/plausible situation)"""

SAME_EX_6_2 = """The nurse brought the doctor.
The naturalness score is 6 (it likely that a nurse would bring a doctor)"""

SAME_EX_6_3 = """The policeman looked for the victim.
The naturalness score is 6 (it is likely that a policeman would look for a victim)"""

SAME_EX_6 = [SAME_EX_6_1, SAME_EX_6_2, SAME_EX_6_3]

SAME_EX_7_1 = """The teacher scolded the troublemaker.
The naturalness score is 7 (it is a really natural/plausible situation)"""

SAME_EX_7_2 = """The nurse brought the medicine.
The naturalness score is 7 (it highly likely that a nurse would bring medicine to a patient)"""

SAME_EX_7_3 = """The policeman looked for the robber.
The naturalness score is 6 (it is highly likely that a policeman would look for a patient)"""

SAME_EX_7 = [SAME_EX_7_1, SAME_EX_7_2, SAME_EX_7_3]


DIFF_EX_1_1 = """The teacher scolded the shoe.
The naturalness score is 1 (it is really unnatural/implausible situation)"""

DIFF_EX_1_2 = """The fisherman dropped the plane.
The naturalness score is 1 (it is really unnatural situation for a fisherman to drop a plane)"""

DIFF_EX_1_3 = """The firefighter rescued the cellar.
The naturalness score is 1 (it is really implausible for a firefighter to save a cellar)"""

DIFF_EX_1 = [DIFF_EX_1_1, DIFF_EX_1_2, DIFF_EX_1_3]

DIFF_EX_2_1 = """The farmer bought a ski.
The naturalness score is 2 (it is an unnatural/implausible situation)"""

DIFF_EX_2_2 = """The doctor inspected the evidence.
The naturalness score is 2 (it is unnatural for a doctor to examine evidence)"""

DIFF_EX_2_3 = """The hunter observed the building.
The naturalness score is 2 (it is implausible for a hunter to observe a building)"""

DIFF_EX_2 = [DIFF_EX_2_1, DIFF_EX_2_2, DIFF_EX_2_3]

DIFF_EX_3_1 = """The handyman repaired the car.
The naturalness score is 3 (it is a somewhat unnatural/implausible situation)"""

DIFF_EX_3_2 = """The seller cleaned the vomit.
The naturalness score is 3 (it is somewhat unnatural for a seller to clean vomit)"""

DIFF_EX_3_3 = """The dentist scared the parent.
The naturalness score is 3 (it is somewhat implausible for a dentist to scare parents)"""

DIFF_EX_3 = [DIFF_EX_3_1, DIFF_EX_3_2, DIFF_EX_3_3]

DIFF_EX_4_1 = """The policeman stopped the plane.
The naturalness score is 4 (it is a situation that might happen but is a bit unlikely)"""

DIFF_EX_4_2 = """The cook prepared the cocktail.
The naturalness score is 4 (a cook might prepare a cocktail but it is a bit unlikely)"""

DIFF_EX_4_3 = """The gardener planted the watermelon.
The naturalness score is 4 (a gardener might plant a watermelon but it is a bit unlikely)"""

DIFF_EX_4 = [DIFF_EX_4_1, DIFF_EX_4_2, DIFF_EX_4_3]

DIFF_EX_5_1 = """The seller folded the socks.
The naturalness score is 5 (it is a somewhat natural/plausible situation)"""

DIFF_EX_5_2 = """The chef baked a cake.
The naturalness score is 5 (a chef might bake a cake even though it's not what they do generally)"""

DIFF_EX_5_3 = """The librarian ordered the audio book.
The naturalness score is 5 (a librarian might order an audio book but in general they order physical books)"""

DIFF_EX_5 = [DIFF_EX_5_1, DIFF_EX_5_2, DIFF_EX_5_3]

DIFF_EX_6_1 = """The waiter brought the drink.
The naturalness score is 6 (it is a natural/plausible situation)"""

DIFF_EX_6_2 = """The barista prepared the cappuccino.
The naturalness score is 6 (it is likely that a barista would prepare a cappuccino)"""

DIFF_EX_6_3 = """The soldier cleaned the rofle.
The naturalness score is 6 (part of a soldier's duties is to clean his weapon)"""

DIFF_EX_6 = [DIFF_EX_6_1, DIFF_EX_6_2, DIFF_EX_6_3]

DIFF_EX_7_1 = """The baker prepared the cake.
The naturalness score is 7 (it is a really plausible for a baker to prepare a cake)"""

DIFF_EX_7_2 = """The policemen caught the thief.
The naturalness score is 7 (it is highly likely that policemen would try and catch a thief)"""

DIFF_EX_7_3 = """The fisherman caught a fish.
The naturalness score is 7 (it is really plausible that a fisherman would catch a fish)"""

DIFF_EX_7 = [DIFF_EX_7_1, DIFF_EX_7_2, DIFF_EX_7_3]

SAME_EX = [SAME_EX_1, SAME_EX_2, SAME_EX_3, SAME_EX_4, SAME_EX_5, SAME_EX_6, SAME_EX_7]

DIFF_EX = [DIFF_EX_1, DIFF_EX_2, DIFF_EX_3, DIFF_EX_4, DIFF_EX_5, DIFF_EX_6, DIFF_EX_7]


def get_examples(num_ex: str, diff_sentence: str = 'yes'):

    all_examples = list()

    examples = DIFF_EX
    if diff_sentence != 'yes':
        examples = SAME_EX

    for orig in examples:
        temp_list = deepcopy(orig)
        if diff_sentence == 'yes':
            random.shuffle(temp_list)
        all_examples += temp_list[:int(num_ex)]

    random.shuffle(all_examples)

    return all_examples