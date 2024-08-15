# HalluciMAD
Interpreting and Mitigating Hallucination in MLLMs through Multi-agent Debate



## Install

1. Clone this repository and navigate to HalluciMAD folder

```shell
git clone https://github.com/LZzz2000/HalluciMAD.git
cd HalluciMAD
```

2. Install Package

```shell
tqdm
time
google-generativeai
Pillow
random
json
```



## Download Dataset

Please download the image package of [val2014](https://cocodataset.org/#download) and extract it to the ```data``` directory.  

The annotation files have been downloaded.

```shell
./HalluciMAD/data/val2014
./HalluciMAD/data/coco_pope_random.json
./HalluciMAD/data/coco_pope_popular.json
./HalluciMAD/data/coco_pope_adversarial.json
./HalluciMAD/data/coco_pope_random_POPER&POPEC.json
```



## Get API Key

Please get ```api_key``` from [Google AI Studio](https://aistudio.google.com/).

```python
google_api_key = '' # add your api_key
```



## Run

1. Enter the ```code``` directory and fill in the ```out_file```. 

2. Run

```python
python multi_eval_pope_gemini.py # Our approach
python sro_eval_pope_gemini.py # Self Reflection Only
python single_eval_pope_gemini.py # Baseline
```



## Evaluation

1. Enter the ```eval``` directory and fill in the ```ans_file```. 

2. Set the ```out```  flag to "True" if you want to output the bad case.
3. Run

```python
python evaluate.py
```

