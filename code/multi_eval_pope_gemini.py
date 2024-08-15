import os
import json
import random
from agent_gemini import Agent
import tqdm
import sys

google_api_key = '' # add your api_key

NAME_LIST = [
    "Affirmative side",
    "Negative side",
    "Judge",
]


class DebatePlayer(Agent):
    # initialization DebatePlayer
    def __init__(self, model_name: str, name: str, temperature: float, google_api_key: str, sleep_time: float) -> None:
        super(DebatePlayer, self).__init__(model_name, name, temperature, sleep_time)
        self.google_api_key = google_api_key


class Debate:
    def __init__(self,
                 model_name: str = 'gemini-pro-vision',
                 temperature: float = 0,
                 num_players: int = 3,
                 google_api_key: str = None,
                 config: dict = None,
                 max_round: int = 3,
                 sleep_time: float = 0,
                 img: str = None,
                 discussion_process: str = None
                 ) -> None:

        self.model_name = model_name
        self.temperature = temperature
        self.num_players = num_players
        self.google_api_key = google_api_key
        self.config = config
        self.max_round = max_round
        self.sleep_time = sleep_time
        self.img = img
        self.discussion_process = discussion_process

        self.init_prompt()

        # creat&init agents
        self.creat_agents()
        self.init_agents()

    def init_prompt(self):
        def prompt_replace(key):
            self.config[key] = self.config[key].replace("##debate_topic##", self.config["debate_topic"])

        prompt_replace("player_meta_prompt")
        prompt_replace("affirmative_prompt")
        prompt_replace("negative_prompt")

    def creat_agents(self):
        # creates players
        self.players = [
            DebatePlayer(model_name=self.model_name, name=name, temperature=self.temperature,
                         google_api_key=self.google_api_key, sleep_time=self.sleep_time) for name in NAME_LIST
        ]
        self.affirmative = self.players[0]
        self.negative = self.players[1]
        self.judge_player = self.players[2]

    def init_agents(self):
        # set meta prompt
        self.affirmative.set_meta_prompt(self.config['player_meta_prompt'])
        self.negative.set_meta_prompt(self.config['player_meta_prompt'])

        # start first round debate
        print(f"===== Debate Round-1 =====\n")
        self.discussion_process += "===== Debate Round-1 =====\n" # add to the discussion_process
        source = self.affirmative.memory_lst
        self.affirmative.memory_lst = self.affirmative.memory_lst + self.config['affirmative_prompt']
        self.aff_ans = self.affirmative.ask(self.img).lstrip()
        q1_ans_start = self.aff_ans.find("Question1: ")
        q1_ans_end = self.aff_ans.find("\nQuestion2: ")
        q1_ans = self.aff_ans[q1_ans_start + 11:q1_ans_end]

        self.dict_aff_ans = {}
        self.dict_aff_ans['Answer'] = q1_ans

        q2_ans_start = self.aff_ans.find("Question2: ")
        q2_ans_end = len(self.aff_ans)
        q2_ans = self.aff_ans[q2_ans_start + 11:q2_ans_end]

        self.dict_aff_ans['Reason'] = q2_ans

        print(f"----- Affirmative side -----\n{self.aff_ans}\n")
        print(self.affirmative.memory_lst)
        self.discussion_process += f"----- Affirmative side -----\n{self.aff_ans}\n"
        self.config['base_answer'] = self.dict_aff_ans['Answer']
        self.affirmative.memory_lst = source

        source = self.negative.memory_lst
        self.negative.memory_lst = self.negative.memory_lst + self.config['negative_prompt'].replace('##oppo_ans##',
                                                                                                     self.dict_aff_ans[
                                                                                                         'Answer'])

        self.neg_ans = self.negative.ask(self.img).lstrip()
        q1_ans_start = self.neg_ans.find("Question1: ")
        q1_ans_end = self.neg_ans.find("\nQuestion2: ")
        q1_ans = self.neg_ans[q1_ans_start + 11:q1_ans_end]

        self.dict_neg_ans = {}
        self.dict_neg_ans['Answer'] = q1_ans

        q2_ans_start = self.neg_ans.find("Question2: ")
        q2_ans_end = len(self.neg_ans)
        q2_ans = self.neg_ans[q2_ans_start + 11:q2_ans_end]

        self.dict_neg_ans['Reason'] = q2_ans

        print(f"----- Negative side -----\n{self.neg_ans}\n")
        self.discussion_process += f"----- Negative side -----\n{self.neg_ans}\n"
        print(self.negative.memory_lst)
        self.negative.memory_lst = source

    def round_dct(self, num: int):
        dct = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth', 6: 'sixth', 7: 'seventh', 8: 'eighth',
            9: 'ninth', 10: 'tenth'
        }
        return dct[num]

    def print_answer(self):
        print("\n\n===== Debate Done! =====")
        print("\n----- Debate Topic -----")
        print(self.config["debate_topic"])
        print("\n----- Base Answer -----")
        print(self.config["base_answer"])
        print("\n----- Debate Answer -----")
        print(self.config["debateAnswer"])
        print("\n----- Debate Reason -----")
        print(self.config["Reason"])

        # add to the discussion_process
        self.discussion_process += "\n\n===== Debate Done! ====="
        self.discussion_process += "\n----- Debate Topic -----"
        self.discussion_process += self.config["debate_topic"]
        self.discussion_process += "\n----- Base Answer -----"
        self.discussion_process += self.config["base_answer"]
        self.discussion_process += "\n----- Debate Answer -----"
        self.discussion_process += self.config["debateAnswer"]
        self.discussion_process += "\n----- Debate Reason -----"
        self.discussion_process += self.config["Reason"]


    def run(self):
        for round in range(self.max_round - 1):
            # judge whether consensus has been reached
            if self.dict_aff_ans['Answer'] == self.dict_neg_ans['Answer'] or (self.dict_aff_ans['Answer'].find('No')!= -1 and self.dict_neg_ans['Answer'].find('No')!= -1) or (self.dict_aff_ans['Answer'].find('Yes')!= -1 and self.dict_neg_ans['Answer'].find('Yes')!= -1):
                # Reaching consensus, discussion ends
                self.config["debateAnswer"] = self.dict_aff_ans['Answer']
                self.config["Reason"] = "A argue: " + self.dict_aff_ans['Reason'] + "\nB argue: " + self.dict_neg_ans[
                    'Reason'] + "\nThey reached a consensus."
                self.config['success'] = True
                break
            else:
                # No consensus, discussion continues
                if self.dict_aff_ans['Answer'] == 'Yes':
                    self.say_yes_side = self.affirmative
                    self.say_yes_ans = self.aff_ans
                    self.say_yes_dict_ans = self.dict_aff_ans

                    self.say_no_side = self.negative
                    self.say_no_ans = self.neg_ans
                    self.say_no_dict_ans = self.dict_neg_ans
                else:
                    self.say_yes_side = self.negative
                    self.say_yes_ans = self.neg_ans
                    self.say_yes_dict_ans = self.dict_neg_ans

                    self.say_no_side = self.affirmative
                    self.say_no_ans = self.aff_ans
                    self.say_no_dict_ans = self.dict_aff_ans

                # Perform self reflection on the debater that said Yes in the previous round
                source = self.say_yes_side.memory_lst
                if self.config['object'] == 'person':
                    self.config['say_yes_side_probe1'] = self.config['say_yes_side_probe1'].replace(
                        "Question1: What color is this ##object## in the picture?",
                        "Question1: What color is the clothing this ##object## is wearing?")
                self.say_yes_side.memory_lst = self.say_yes_side.memory_lst + self.config[
                    'say_yes_side_probe1'].replace('##Your_answer##', self.say_yes_dict_ans['Answer']).replace(
                    "##Your_reason##", self.say_yes_dict_ans['Reason']).replace('##object##', self.config['object'])
                self.say_yes_ans = self.say_yes_side.ask(self.img).lstrip()

                q1_ans_start = self.say_yes_ans.find("Question1: ")
                q1_ans_end = self.say_yes_ans.find("\nQuestion2: ")
                q1_ans = self.say_yes_ans[q1_ans_start + 11:q1_ans_end]

                q2_ans_start = self.say_yes_ans.find("Question2: ")
                q2_ans_end = self.say_yes_ans.find("\nQuestion3: ")
                q2_ans = self.say_yes_ans[q2_ans_start + 11:q2_ans_end]

                q3_ans_start = self.say_yes_ans.find("Question3: ")
                q3_ans_end = self.say_yes_ans.find("\nQuestion4: ")
                q3_ans = self.say_yes_ans[q3_ans_start + 11:q3_ans_end]

                q4_ans_start = self.say_yes_ans.find("Question4: ")
                q4_ans_end = self.say_yes_ans.find("\nQuestion5: ")
                q4_ans = self.say_yes_ans[q4_ans_start + 11:q4_ans_end]

                q5_ans_start = self.say_yes_ans.find("Question5: ")
                q5_ans_end = self.say_yes_ans.find("\nQuestion6: ")
                q5_ans = self.say_yes_ans[q5_ans_start + 11:q5_ans_end]

                q6_ans_start = self.say_yes_ans.find("Question6: ")
                q6_ans_end = len(self.say_yes_ans)
                q6_ans = self.say_yes_ans[q6_ans_start + 11:q6_ans_end]

                self.say_yes_side.color = q1_ans.lower()
                self.say_yes_side.absolute_area = q2_ans.lower()
                self.say_yes_side.above = q3_ans.lower()
                if self.say_yes_side.above == 'nothing' or self.say_yes_side.above == 'no' or self.say_yes_side.above == 'none' or self.say_yes_side.above == 'n/a' or self.say_yes_side.above.find('not') != -1:
                    self.config['say_no_side_probe1'] = self.config['say_no_side_probe1'].replace(" beneath ##below##,",
                                                                                                  "")
                    self.config['say_yes_side_probe2'] = self.config['say_yes_side_probe2'].replace(
                        " beneath ##below##,", "")
                    self.config['judge_side'] = self.config['judge_side'].replace(" beneath ##below##,", "")
                self.say_yes_side.below = q4_ans.lower()
                if self.say_yes_side.below == 'nothing' or self.say_yes_side.below == 'no' or self.say_yes_side.below == 'none' or self.say_yes_side.below == 'n/a' or self.say_yes_side.below.find('not') != -1:
                    self.config['say_no_side_probe1'] = self.config['say_no_side_probe1'].replace(" above ##above##,",
                                                                                                  "")
                    self.config['say_yes_side_probe2'] = self.config['say_yes_side_probe2'].replace(" above ##above##,",
                                                                                                    "")
                    self.config['judge_side'] = self.config['judge_side'].replace(" above ##above##,", "")
                self.say_yes_side.right_side = q5_ans.lower()
                if self.say_yes_side.right_side == 'nothing' or self.say_yes_side.right_side == 'no' or self.say_yes_side.right_side == 'none' or self.say_yes_side.right_side == 'n/a' or self.say_yes_side.right_side.find('not') != -1:
                    self.config['say_no_side_probe1'] = self.config['say_no_side_probe1'].replace(
                        " to the left of ##left_side##,", "")
                    self.config['say_yes_side_probe2'] = self.config['say_yes_side_probe2'].replace(
                        " to the left of ##left_side##,", "")
                    self.config['judge_side'] = self.config['judge_side'].replace(" to the left of ##left_side##,", "")
                self.say_yes_side.left_side = q6_ans.lower()
                if self.say_yes_side.left_side == 'nothing' or self.say_yes_side.left_side == 'no' or self.say_yes_side.left_side == 'none' or self.say_yes_side.left_side == 'n/a' or self.say_yes_side.left_side.find('not') != -1:
                    self.config['say_no_side_probe1'] = self.config['say_no_side_probe1'].replace(
                        " to the right of ##right_side##,", "")
                    self.config['say_yes_side_probe2'] = self.config['say_yes_side_probe2'].replace(
                        " to the right of ##right_side##,", "")
                    self.config['judge_side'] = self.config['judge_side'].replace(" to the right of ##right_side##,",
                                                                                  "")

                print(f"----- say yes side probe1 -----\n{self.say_yes_ans}\n")
                self.discussion_process += f"----- say yes side probe1 -----\n{self.say_yes_ans}\n"
                print(self.say_yes_side.memory_lst)
                self.say_yes_side.memory_lst = source

                print(f"===== Debate Round-{round + 2} =====\n")
                self.discussion_process += f"===== Debate Round-{round + 2} =====\n"

                # Based on the information above, ask for the opinion of Debater who says No
                source = self.say_no_side.memory_lst
                self.say_no_side.memory_lst = self.say_no_side.memory_lst + self.config[
                    'say_no_side_probe1'].replace('##Your_answer##', self.say_no_dict_ans['Answer']).replace(
                    "##Your_reason##", self.say_no_dict_ans['Reason']).replace('##object##',
                                                                               self.config['object']).replace(
                    '##Other_answer##', 'Yes').replace('##color##', self.say_yes_side.color).replace(
                    '##absolute_area##', self.say_yes_side.absolute_area).replace('##above##',
                                                                                  self.say_yes_side.below).replace(
                    '##below##', self.say_yes_side.above).replace('##left_side##',
                                                                  self.say_yes_side.right_side).replace(
                    '##right_side##', self.say_yes_side.left_side)
                self.say_no_ans = self.say_no_side.ask(self.img).lstrip()
                while self.say_no_ans.find("Question2: Not") != -1:
                    self.say_no_ans = self.say_no_side.ask(self.img).lstrip()

                q1_ans_start = self.say_no_ans.find("Question1: ")
                q1_ans_end = self.say_no_ans.find("\nQuestion2: ")
                q1_ans = self.say_no_ans[q1_ans_start + 11:q1_ans_end]

                self.say_no_dict_ans = {}
                self.say_no_dict_ans['Have found the object'] = q1_ans

                q2_ans_start = self.say_no_ans.find("Question2: ")
                q2_ans_end = self.say_no_ans.find("\nQuestion3: ")
                q2_ans = self.say_no_ans[q2_ans_start + 11:q2_ans_end].replace("It's a ","").replace("It's an ","")

                self.say_no_dict_ans['What is it'] = q2_ans.lower()

                q3_ans_start = self.say_no_ans.find("Question3: ")
                q3_ans_end = len(self.say_no_ans)
                q3_ans = self.say_no_ans[q3_ans_start + 11:q3_ans_end]

                self.say_no_dict_ans['Reason'] = q3_ans

                print(f"----- say no side probe1 -----\n{self.say_no_ans}\n")
                self.discussion_process += f"----- say no side probe1 -----\n{self.say_no_ans}\n"
                print(self.say_no_side.memory_lst)
                self.say_no_side.memory_lst = source

                # If the object does exist, the discussion ends
                self.say_no_dict_ans['What is it'] = self.say_no_dict_ans['What is it'].lower()
                if self.say_no_dict_ans['What is it'] == self.config['object'] or self.say_no_dict_ans[
                    'What is it'].find(self.config['object']) != -1 or self.config['object'].find(
                        self.say_no_dict_ans['What is it']) != -1:
                    self.config["debateAnswer"] = "Yes"
                    self.config["Reason"] = self.say_no_dict_ans['Reason']
                    self.config['success'] = True
                    break
                
                # say no debater believes that what exists is other_object, And tell the information to debater who says yes
                self.config['other_object'] = self.say_no_dict_ans['What is it']
                source = self.say_yes_side.memory_lst
                self.say_yes_side.memory_lst = self.say_yes_side.memory_lst + self.config[
                    'say_yes_side_probe2'].replace('##Your_answer##', self.say_yes_dict_ans['Answer']).replace(
                    '##object##', self.config['object']).replace('##other_object##',
                                                                 self.config['other_object']).replace('##color##',
                                                                                                      self.say_yes_side.color).replace(
                    '##absolute_area##', self.say_yes_side.absolute_area).replace('##above##',
                                                                                  self.say_yes_side.below).replace(
                    '##below##', self.say_yes_side.above).replace('##left_side##',
                                                                  self.say_yes_side.right_side).replace(
                    '##right_side##', self.say_yes_side.left_side)

                self.say_yes_ans = self.say_yes_side.ask(self.img).lstrip()
                while self.say_yes_ans.find("Question2: Not") != -1:
                    self.say_yes_ans = self.say_yes_side.ask(self.img).lstrip()

                q1_ans_start = self.say_yes_ans.find("Question1: ")
                q1_ans_end = self.say_yes_ans.find("\nQuestion2: ")
                q1_ans = self.say_yes_ans[q1_ans_start + 11:q1_ans_end]

                self.say_yes_dict_ans = {}
                self.say_yes_dict_ans['Have found the object'] = q1_ans

                q2_ans_start = self.say_yes_ans.find("Question2: ")
                q2_ans_end = self.say_yes_ans.find("\nQuestion3: ")
                q2_ans = self.say_yes_ans[q2_ans_start + 11:q2_ans_end].replace("It's a ","").replace("It's an ","")

                self.say_yes_dict_ans['What is it'] = q2_ans.lower()

                q3_ans_start = self.say_yes_ans.find("Question3: ")
                q3_ans_end = len(self.say_yes_ans)
                q3_ans = self.say_yes_ans[q3_ans_start + 11:q3_ans_end]

                self.say_yes_dict_ans['Reason'] = q3_ans

                print(f"----- say yes side probe2 -----\n{self.say_yes_ans}\n")
                self.discussion_process += f"----- say yes side probe2 -----\n{self.say_yes_ans}\n"
                print(self.say_yes_side.memory_lst)
                self.say_yes_side.memory_lst = source

                # If say yes debater believes that what exists is other_object, discussion ends
                if self.say_yes_dict_ans['What is it'] == self.config['other_object'] or self.say_yes_dict_ans[
                    'What is it'].find(self.config['other_object']) != -1 or self.config['other_object'].find(
                        self.say_yes_dict_ans['What is it']) != -1:
                    self.config["debateAnswer"] = "No"
                    self.config["Reason"] = self.say_yes_dict_ans['Reason']
                    self.config['success'] = True
                    break
                # If say yes debater insists on that what exists is object not other_object, discussion continues
                elif self.say_yes_dict_ans['What is it'] == self.config['object'] or self.say_yes_dict_ans[
                    'What is it'].find(self.config['object']) != -1 or self.config['object'].find(
                        self.say_yes_dict_ans['What is it']) != -1:

                    # Both parties' information will be handed over to Judge for final judgment
                    self.judge_player.memory_lst = self.config['judge_side'].replace('##object##',
                                                                                     self.config['object']).replace(
                        '##other_object##', self.config['other_object']).replace('##color##',
                                                                                 self.say_yes_side.color).replace(
                        '##absolute_area##', self.say_yes_side.absolute_area).replace('##above##',
                                                                                      self.say_yes_side.below).replace(
                        '##below##', self.say_yes_side.above).replace('##left_side##',
                                                                      self.say_yes_side.right_side).replace(
                        '##right_side##', self.say_yes_side.left_side).replace("##Affirmative_reason##",
                                                                               self.say_yes_dict_ans['Reason']).replace(
                        "##Negative_reason##", self.say_no_dict_ans['Reason'])
                    self.judge_ans = self.judge_player.ask(self.img).lstrip()

                    q1_ans_start = self.judge_ans.find("Question1: ")
                    q1_ans_end = self.judge_ans.find("\nQuestion2: ")
                    q1_ans = self.judge_ans[q1_ans_start + 11:q1_ans_end]

                    self.judge_dict_ans = {}
                    self.judge_dict_ans['Which object does judge believe'] = q1_ans.lower()

                    q2_ans_start = self.judge_ans.find("Question2: ")
                    q2_ans_end = len(self.judge_ans)
                    q2_ans = self.judge_ans[q2_ans_start + 11:q2_ans_end]

                    self.judge_dict_ans['Reason'] = q2_ans

                    print(f"----- Judge -----\n{self.judge_ans}\n")
                    self.discussion_process += f"----- Judge -----\n{self.judge_ans}\n"
                    print(self.judge_player.memory_lst)

                    # output
                    if self.judge_dict_ans['Which object does judge believe'] == self.config['object'] or \
                            self.judge_dict_ans['Which object does judge believe'].find(self.config['object']) != -1 or \
                            self.config['object'].find(
                                    self.judge_dict_ans['Which object does judge believe']) != -1:
                        self.config["debateAnswer"] = "Yes"
                        self.config["Reason"] = self.judge_dict_ans['Reason']
                        self.config['success'] = True
                    elif self.judge_dict_ans['Which object does judge believe'] == self.config['other_object'] or \
                            self.judge_dict_ans['Which object does judge believe'].find(
                                    self.config['other_object']) != -1 or self.config['other_object'].find(
                            self.judge_dict_ans['Which object does judge believe']) != -1:
                        self.config["debateAnswer"] = "No"
                        self.config["Reason"] = self.judge_dict_ans['Reason']
                        self.config['success'] = True
                    break
                else:
                    print("'what is it' is not only a object: ", self.say_yes_dict_ans['What is it'],
                          self.config['object'])
                    self.config["debateAnswer"] = "error"
                    self.config["Reason"] = "None"
                    self.config['success'] = True
                    break

        self.print_answer()

if __name__ == "__main__":

    questions_file = open("../data/coco_pope_random.json", "r")
    out_file = "../output/pope_random_gemini_multi.jsonl"
    lines = list(questions_file.readlines())

    for line in tqdm.tqdm(lines):
        print("google_api_key: ",google_api_key)

        # initialization
        discussion_process = ""
        data = json.loads(line)
        debate_topic = data["text"]
        question_id = data["question_id"]
        image_path = "../data/val2014/" + data["image"]
        config = json.load(open(f"./config-prompt.json", "r"))
        config['debate_topic'] = debate_topic
        config['object'] = debate_topic.replace("Is there a ", "").replace("Is there an ","").replace(" in the image?", "")

        # run debate 
        debate = Debate(num_players=3, google_api_key=google_api_key, config=config, temperature=0, sleep_time=1,
                        img=image_path, discussion_process=discussion_process)
        debate.run()

        # output
        with open(out_file, "a") as f:
            f.write(json.dumps({
                "question": debate_topic,
                "answer": debate.config["debateAnswer"],
                "question_id": question_id,
                "image_path": data["image"],
                "discussion_process": debate.discussion_process
            }) + '\n')





