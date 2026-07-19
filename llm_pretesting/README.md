# LLMs for psycholinguistic pretesting
Official repository of the paper: "Large Language Models for Psycholinguistic Plausibility Pretesting" (Findings of EACL 2024) (arxiv: [pdf](https://arxiv.org/pdf/2402.05455.pdf))

To use our repo to create plausibility ratings from GPT4 follow the following steps:
1. Install the **Openai** library in your environment.
2. Run: `export OPENAI_API_KEY="YOUR_API_KEY"`
3. Run: `python llm_pretest/openai/llm_pretest_openai.py -i path_to_data -o path_to_outputs`

The data should be a *.jsonl* file, where each line is a dictionary with the following keys: *sample_id*, *sentence*, *human_results*.

These ratings can be used for coarse filtering methods (thresholds for example) but not for finegrained filtering methods
(for example t-test between two sentences).