import random
from copy import deepcopy

BRIAN_1_1 = """The boy flew.
The plausibility score is 1 (humans can't fly)."""

BRIAN_1_2 = """The mechanic fixed the problematic cars with his eyes closed.
The plausibility score is 1 (it is highly unlikely that a mechanic can fix cars without seeing)."""

BRIAN_1_3 = """Ever since the husband left, the plane refused to go to school.
The plausibility score is 1 (planes don't have desires and they don't go to school)."""

BRIAN_EX_1 = [BRIAN_1_1, BRIAN_1_2, BRIAN_1_3]

BRIAN_2_1 = """The baby was granted the rooster.
The plausibility score is 2 (why would a baby be granted a rooster)."""

BRIAN_2_2 = """The policeman showed that the cow was guilty of murder.
The plausibility score is 2 (it is unlikely that a cow would murder someone)."""

BRIAN_2_3 = """The firefighter who was denied the transplant went to the moon.
The plausibility score is 2 (people really rarely go to the moon)."""

BRIAN_EX_2 = [BRIAN_2_1, BRIAN_2_2, BRIAN_2_3]

BRIAN_3_1 = """After the judge called, the lawyer dropped the case almost immediately.
The plausibility score is 3 (it is somewhat unlikely that a judge would lead a lawyer to drop a case)."""

BRIAN_3_2 = """The fish ate the sponge.
The plausibility score is 3 (it is somewhat unlikely that a fish would eat a sponge but it might happen)."""

BRIAN_3_3 = """The surgeon was brought the towel.
The plausibility score is 3 (towels rarely find their place in an operating room)."""

BRIAN_EX_3 = [BRIAN_3_1, BRIAN_3_2, BRIAN_3_3]

BRIAN_4_1 = """The prison guard, which the inmate despised, robbed a bank.
The plausibility score is 4 (a prison guard robbing a bank might happen but is unlikely)."""

BRIAN_4_2 = """He felt very hungry after eating a 300g steak.
The plausibility score is 4 (a 300g steak is quite heavy, eating one and still being very hungry is unlikely)."""

BRIAN_4_3 = """The trainer told that the tiger was completely trained.
The plausibility score is 4 (in general, trainers train dogs not tiger)."""

BRIAN_EX_4 = [BRIAN_4_1, BRIAN_4_2, BRIAN_4_3]

BRIAN_5_1 = """The lawyer who was hired by the suspect convinced all the jurors.
The plausibility score is 5 (it might happen that a lawyer convinces all the members of the jury)."""

BRIAN_5_2 = """After sending the mail, he needed a bottle of coke.
The plausibility score is 5 (it is a somewhat plausible situation, maybe he was thirsty)."""

BRIAN_5_3 = """The teacher left.
The plausibility score is 5 (it is a somewhat plausible situation, maybe the class is over)."""

BRIAN_EX_5 = [BRIAN_5_1, BRIAN_5_2, BRIAN_5_3]

BRIAN_6_1 = """The waiter brought the drink.
The plausibility score is 6 (it is plausible that a waiter would bring a drink to a client)."""

BRIAN_6_2 = """The sick patient was brought his medicine.
The plausibility score is 6 (it is plausible that someone would bring medicine to someone sick)."""

BRIAN_6_3 = """The scientist showed that the invention worked well.
The plausibility score is 6 (it is plausible that a scientist would show the efficiency of an invention)."""

BRIAN_EX_6 = [BRIAN_6_1, BRIAN_6_2, BRIAN_6_3]

BRIAN_7_1 = """The baker prepared the cake.
The plausibility score is 7 (it is a really plausible situation, the role of the baker is to prepare cakes)."""

BRIAN_7_2 = """The firefighters put out the fire.
The plausibility score is 7 (it is really plausible, the role of firefighters is to put out fires)."""

BRIAN_7_3 = """She recommended him not to spend his entire savings on a big car.
The plausibility score is 7 (it is a sensible advice not to spend everything on a car)."""

BRIAN_EX_7 = [BRIAN_7_1, BRIAN_7_2, BRIAN_7_3]

def get_examples(num_ex: int):

    all_examples = list()

    for orig in [BRIAN_EX_1, BRIAN_EX_2, BRIAN_EX_3, BRIAN_EX_4, BRIAN_EX_5, BRIAN_EX_6, BRIAN_EX_7]:
        temp_list = deepcopy(orig)
        random.shuffle(temp_list)
        all_examples += temp_list[:int(num_ex)]

    random.shuffle(all_examples)

    return all_examples