| source | model_name | reasoning_type | context_length | evidence_position | evidence_density | distractor_similarity | long_method | score_field | score_no_evidence | score_oracle | score_long | n | cue_valid | cue_invalid_reason | cue_raw | cue_clipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2wikimultihopqa | qwen3:14b | multi_hop | 4000 | front | low | unknown | direct | exact_match | 0.0000 | 0.5455 | 0.3636 | 22 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 4000 | front | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.5455 | 0.3636 | 22 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | middle | low | unknown | direct | exact_match | 0.5000 | 1.0000 | 0.5000 | 6 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | middle | low | unknown | retrieve_then_read | exact_match | 0.5000 | 1.0000 | 0.5000 | 6 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 16000 | end | low | unknown | direct | exact_match | 0.0000 | 0.6667 | 0.4583 | 24 | True |  | 0.6875 | 0.6875 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 16000 | end | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.6667 | 0.2917 | 24 | True |  | 0.4375 | 0.4375 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 4000 | scattered | low | unknown | direct | exact_match | 0.0000 | 0.3913 | 0.4783 | 23 | True |  | 1.2222 | 1.0000 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 4000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.3913 | 0.2174 | 23 | True |  | 0.5556 | 0.5556 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 8000 | front | low | unknown | direct | exact_match | 0.0435 | 0.5652 | 0.2174 | 23 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 8000 | front | low | unknown | retrieve_then_read | exact_match | 0.0435 | 0.5652 | 0.1739 | 23 | True |  | 0.2500 | 0.2500 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 16000 | middle | low | unknown | direct | exact_match | 0.1154 | 0.4231 | 0.3077 | 26 | True |  | 0.6250 | 0.6250 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 16000 | middle | low | unknown | retrieve_then_read | exact_match | 0.1154 | 0.4231 | 0.1923 | 26 | True |  | 0.2500 | 0.2500 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 4000 | end | low | unknown | direct | exact_match | 0.0000 | 0.6364 | 0.3636 | 22 | True |  | 0.5714 | 0.5714 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 4000 | end | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.6364 | 0.2273 | 22 | True |  | 0.3571 | 0.3571 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | scattered | low | unknown | direct | exact_match | 0.5556 | 0.8889 | 0.4444 | 9 | True |  | -0.3333 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.5556 | 0.8889 | 0.3333 | 9 | True |  | -0.6667 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | front | medium | unknown | direct | exact_match | 0.5000 | 1.0000 | 0.7500 | 8 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | front | medium | unknown | retrieve_then_read | exact_match | 0.5000 | 1.0000 | 1.0000 | 8 | True |  | 1.0000 | 1.0000 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 4000 | middle | low | unknown | direct | exact_match | 0.0417 | 0.5417 | 0.3750 | 24 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 4000 | middle | low | unknown | retrieve_then_read | exact_match | 0.0417 | 0.5417 | 0.3333 | 24 | True |  | 0.5833 | 0.5833 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | end | medium | unknown | direct | exact_match | 0.3333 | 0.7500 | 0.9167 | 12 | True |  | 1.4000 | 1.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | end | medium | unknown | retrieve_then_read | exact_match | 0.3333 | 0.7500 | 0.8333 | 12 | True |  | 1.2000 | 1.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | scattered | medium | unknown | direct | exact_match | 0.4286 | 0.7857 | 0.7857 | 14 | True |  | 1.0000 | 1.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.4286 | 0.7857 | 0.5714 | 14 | True |  | 0.4000 | 0.4000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | front | medium | unknown | direct | exact_match | 0.1818 | 0.5455 | 0.3636 | 11 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | front | medium | unknown | retrieve_then_read | exact_match | 0.1818 | 0.5455 | 0.3636 | 11 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 8000 | middle | low | unknown | direct | exact_match | 0.0370 | 0.4815 | 0.3333 | 27 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 8000 | middle | low | unknown | retrieve_then_read | exact_match | 0.0370 | 0.4815 | 0.2593 | 27 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | front | low | unknown | direct | exact_match | 0.6000 | 1.0000 | 0.8000 | 10 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | front | low | unknown | retrieve_then_read | exact_match | 0.6000 | 1.0000 | 0.6000 | 10 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | middle | medium | unknown | direct | exact_match | 0.6250 | 0.6250 | 0.5000 | 8 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | middle | medium | unknown | retrieve_then_read | exact_match | 0.6250 | 0.6250 | 0.3750 | 8 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | scattered | medium | unknown | direct | exact_match | 0.3846 | 0.8462 | 0.7692 | 13 | True |  | 0.8333 | 0.8333 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.3846 | 0.8462 | 0.6923 | 13 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | front | low | unknown | direct | exact_match | 0.6667 | 1.0000 | 0.5000 | 6 | True |  | -0.5000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | front | low | unknown | retrieve_then_read | exact_match | 0.6667 | 1.0000 | 0.6667 | 6 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | end | medium | unknown | direct | exact_match | 1.0000 | 0.8000 | 0.8000 | 5 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | end | medium | unknown | retrieve_then_read | exact_match | 1.0000 | 0.8000 | 1.0000 | 5 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | middle | low | unknown | direct | exact_match | 0.5000 | 0.7500 | 0.6250 | 8 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | middle | low | unknown | retrieve_then_read | exact_match | 0.5000 | 0.7500 | 0.5000 | 8 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | end | low | unknown | direct | exact_match | 0.3333 | 0.7500 | 0.5000 | 12 | True |  | 0.4000 | 0.4000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | end | low | unknown | retrieve_then_read | exact_match | 0.3333 | 0.7500 | 0.5000 | 12 | True |  | 0.4000 | 0.4000 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 8000 | end | low | unknown | direct | exact_match | 0.0476 | 0.3333 | 0.3333 | 21 | True |  | 1.0000 | 1.0000 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 8000 | end | low | unknown | retrieve_then_read | exact_match | 0.0476 | 0.3333 | 0.1905 | 21 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 16000 | scattered | low | unknown | direct | exact_match | 0.0526 | 0.4737 | 0.0526 | 19 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 16000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.0526 | 0.4737 | 0.0000 | 19 | True |  | -0.1250 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | end | low | unknown | direct | exact_match | 0.4615 | 0.8462 | 0.6923 | 13 | True |  | 0.6000 | 0.6000 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | end | low | unknown | retrieve_then_read | exact_match | 0.4615 | 0.8462 | 0.4615 | 13 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | scattered | low | unknown | direct | exact_match | 0.6667 | 0.8333 | 0.5000 | 6 | True |  | -1.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.6667 | 0.8333 | 0.3333 | 6 | True |  | -2.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | end | medium | unknown | direct | exact_match | 0.5000 | 0.7500 | 1.0000 | 8 | True |  | 2.0000 | 1.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | end | medium | unknown | retrieve_then_read | exact_match | 0.5000 | 0.7500 | 0.8750 | 8 | True |  | 1.5000 | 1.0000 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 8000 | scattered | low | unknown | direct | exact_match | 0.0500 | 0.4000 | 0.1000 | 20 | True |  | 0.1429 | 0.1429 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 8000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.0500 | 0.4000 | 0.1000 | 20 | True |  | 0.1429 | 0.1429 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 16000 | front | low | unknown | direct | exact_match | 0.0000 | 0.6296 | 0.4074 | 27 | True |  | 0.6471 | 0.6471 |
| 2wikimultihopqa | qwen3:14b | multi_hop | 16000 | front | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.6296 | 0.1481 | 27 | True |  | 0.2353 | 0.2353 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | middle | medium | unknown | direct | exact_match | 0.3333 | 0.7778 | 0.4444 | 9 | True |  | 0.2500 | 0.2500 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | middle | medium | unknown | retrieve_then_read | exact_match | 0.3333 | 0.7778 | 0.4444 | 9 | True |  | 0.2500 | 0.2500 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | end | low | unknown | direct | exact_match | 0.5000 | 0.8750 | 0.6250 | 8 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | end | low | unknown | retrieve_then_read | exact_match | 0.5000 | 0.8750 | 0.5000 | 8 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | scattered | medium | unknown | direct | exact_match | 0.5833 | 0.8333 | 0.5833 | 12 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.5833 | 0.8333 | 0.7500 | 12 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | front | low | unknown | direct | exact_match | 0.5556 | 0.8889 | 0.3333 | 9 | True |  | -0.6667 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | front | low | unknown | retrieve_then_read | exact_match | 0.5556 | 0.8889 | 0.4444 | 9 | True |  | -0.3333 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | scattered | high | unknown | direct | exact_match | 0.0000 | 0.0000 | 0.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | scattered | high | unknown | retrieve_then_read | exact_match | 0.0000 | 0.0000 | 0.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | middle | low | unknown | direct | exact_match | 0.8750 | 1.0000 | 0.8750 | 8 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 4000 | middle | low | unknown | retrieve_then_read | exact_match | 0.8750 | 1.0000 | 0.8750 | 8 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | middle | medium | unknown | direct | exact_match | 0.4444 | 0.6667 | 0.5556 | 9 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | middle | medium | unknown | retrieve_then_read | exact_match | 0.4444 | 0.6667 | 0.5556 | 9 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | scattered | low | unknown | direct | exact_match | 0.6250 | 1.0000 | 1.0000 | 8 | True |  | 1.0000 | 1.0000 |
| 2wikimultihopqa | qwen3:14b | comparison | 16000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.6250 | 1.0000 | 0.8750 | 8 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | front | medium | unknown | direct | exact_match | 0.4444 | 1.0000 | 0.6667 | 9 | True |  | 0.4000 | 0.4000 |
| 2wikimultihopqa | qwen3:14b | comparison | 8000 | front | medium | unknown | retrieve_then_read | exact_match | 0.4444 | 1.0000 | 0.8889 | 9 | True |  | 0.8000 | 0.8000 |
