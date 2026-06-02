| source | model_name | reasoning_type | context_length | evidence_position | evidence_density | distractor_similarity | long_method | score_field | score_no_evidence | score_oracle | score_long | n | cue_valid | cue_invalid_reason | cue_raw | cue_clipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2wikimultihopqa | gemma3:12b | multi_hop | 4000 | front | low | unknown | direct | exact_match | 0.0455 | 0.6818 | 0.2727 | 22 | True |  | 0.3571 | 0.3571 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 4000 | front | low | unknown | retrieve_then_read | exact_match | 0.0455 | 0.6818 | 0.4091 | 22 | True |  | 0.5714 | 0.5714 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | middle | low | unknown | direct | exact_match | 0.5000 | 0.8333 | 0.6667 | 6 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | middle | low | unknown | retrieve_then_read | exact_match | 0.5000 | 0.8333 | 0.6667 | 6 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 16000 | end | low | unknown | direct | exact_match | 0.0417 | 0.5417 | 0.2917 | 24 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 16000 | end | low | unknown | retrieve_then_read | exact_match | 0.0417 | 0.5417 | 0.2500 | 24 | True |  | 0.4167 | 0.4167 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 4000 | scattered | low | unknown | direct | exact_match | 0.0435 | 0.6522 | 0.5217 | 23 | True |  | 0.7857 | 0.7857 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 4000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.0435 | 0.6522 | 0.3478 | 23 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 8000 | front | low | unknown | direct | exact_match | 0.0000 | 0.6957 | 0.2609 | 23 | True |  | 0.3750 | 0.3750 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 8000 | front | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.6957 | 0.2609 | 23 | True |  | 0.3750 | 0.3750 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 16000 | middle | low | unknown | direct | exact_match | 0.0385 | 0.5385 | 0.3077 | 26 | True |  | 0.5385 | 0.5385 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 16000 | middle | low | unknown | retrieve_then_read | exact_match | 0.0385 | 0.5385 | 0.1923 | 26 | True |  | 0.3077 | 0.3077 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 4000 | end | low | unknown | direct | exact_match | 0.0455 | 0.4091 | 0.3182 | 22 | True |  | 0.7500 | 0.7500 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 4000 | end | low | unknown | retrieve_then_read | exact_match | 0.0455 | 0.4091 | 0.1364 | 22 | True |  | 0.2500 | 0.2500 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | scattered | low | unknown | direct | exact_match | 0.6667 | 0.7778 | 0.5556 | 9 | True |  | -1.0000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.6667 | 0.7778 | 0.5556 | 9 | True |  | -1.0000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | front | medium | unknown | direct | exact_match | 0.5000 | 1.0000 | 0.6250 | 8 | True |  | 0.2500 | 0.2500 |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | front | medium | unknown | retrieve_then_read | exact_match | 0.5000 | 1.0000 | 0.7500 | 8 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 4000 | middle | low | unknown | direct | exact_match | 0.0000 | 0.6667 | 0.2500 | 24 | True |  | 0.3750 | 0.3750 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 4000 | middle | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.6667 | 0.3333 | 24 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | end | medium | unknown | direct | exact_match | 0.3333 | 0.8333 | 0.5833 | 12 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | end | medium | unknown | retrieve_then_read | exact_match | 0.3333 | 0.8333 | 0.5833 | 12 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | scattered | medium | unknown | direct | exact_match | 0.3571 | 0.6429 | 0.3571 | 14 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.3571 | 0.6429 | 0.4286 | 14 | True |  | 0.2500 | 0.2500 |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | front | medium | unknown | direct | exact_match | 0.5455 | 0.7273 | 0.7273 | 11 | True |  | 1.0000 | 1.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | front | medium | unknown | retrieve_then_read | exact_match | 0.5455 | 0.7273 | 0.4545 | 11 | True |  | -0.5000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 8000 | middle | low | unknown | direct | exact_match | 0.0000 | 0.4815 | 0.3704 | 27 | True |  | 0.7692 | 0.7692 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 8000 | middle | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.4815 | 0.3333 | 27 | True |  | 0.6923 | 0.6923 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | front | low | unknown | direct | exact_match | 0.7000 | 1.0000 | 0.5000 | 10 | True |  | -0.6667 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | front | low | unknown | retrieve_then_read | exact_match | 0.7000 | 1.0000 | 0.4000 | 10 | True |  | -1.0000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | middle | medium | unknown | direct | exact_match | 0.7500 | 0.6250 | 0.5000 | 8 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | middle | medium | unknown | retrieve_then_read | exact_match | 0.7500 | 0.6250 | 0.6250 | 8 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | scattered | medium | unknown | direct | exact_match | 0.5385 | 0.9231 | 0.6154 | 13 | True |  | 0.2000 | 0.2000 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.5385 | 0.9231 | 0.6923 | 13 | True |  | 0.4000 | 0.4000 |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | front | low | unknown | direct | exact_match | 0.6667 | 1.0000 | 0.5000 | 6 | True |  | -0.5000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | front | low | unknown | retrieve_then_read | exact_match | 0.6667 | 1.0000 | 0.5000 | 6 | True |  | -0.5000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | end | medium | unknown | direct | exact_match | 0.8000 | 0.8000 | 0.8000 | 5 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | end | medium | unknown | retrieve_then_read | exact_match | 0.8000 | 0.8000 | 0.8000 | 5 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | middle | low | unknown | direct | exact_match | 0.6250 | 0.8750 | 0.3750 | 8 | True |  | -1.0000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | middle | low | unknown | retrieve_then_read | exact_match | 0.6250 | 0.8750 | 0.7500 | 8 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | end | low | unknown | direct | exact_match | 0.4167 | 1.0000 | 0.5000 | 12 | True |  | 0.1429 | 0.1429 |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | end | low | unknown | retrieve_then_read | exact_match | 0.4167 | 1.0000 | 0.6667 | 12 | True |  | 0.4286 | 0.4286 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 8000 | end | low | unknown | direct | exact_match | 0.0476 | 0.4762 | 0.4286 | 21 | True |  | 0.8889 | 0.8889 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 8000 | end | low | unknown | retrieve_then_read | exact_match | 0.0476 | 0.4762 | 0.3333 | 21 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 16000 | scattered | low | unknown | direct | exact_match | 0.0526 | 0.6316 | 0.4211 | 19 | True |  | 0.6364 | 0.6364 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 16000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.0526 | 0.6316 | 0.0526 | 19 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | end | low | unknown | direct | exact_match | 0.6923 | 0.6923 | 0.7692 | 13 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | end | low | unknown | retrieve_then_read | exact_match | 0.6923 | 0.6923 | 0.5385 | 13 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | scattered | low | unknown | direct | exact_match | 0.5000 | 1.0000 | 0.5000 | 6 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.5000 | 1.0000 | 0.1667 | 6 | True |  | -0.6667 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | end | medium | unknown | direct | exact_match | 0.5000 | 0.8750 | 0.3750 | 8 | True |  | -0.3333 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | end | medium | unknown | retrieve_then_read | exact_match | 0.5000 | 0.8750 | 0.7500 | 8 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 8000 | scattered | low | unknown | direct | exact_match | 0.0000 | 0.4500 | 0.1500 | 20 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 8000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.4500 | 0.0500 | 20 | True |  | 0.1111 | 0.1111 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 16000 | front | low | unknown | direct | exact_match | 0.0741 | 0.7037 | 0.4074 | 27 | True |  | 0.5294 | 0.5294 |
| 2wikimultihopqa | gemma3:12b | multi_hop | 16000 | front | low | unknown | retrieve_then_read | exact_match | 0.0741 | 0.7037 | 0.2222 | 27 | True |  | 0.2353 | 0.2353 |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | middle | medium | unknown | direct | exact_match | 0.6667 | 0.5556 | 0.4444 | 9 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | middle | medium | unknown | retrieve_then_read | exact_match | 0.6667 | 0.5556 | 0.6667 | 9 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | end | low | unknown | direct | exact_match | 0.5000 | 1.0000 | 0.5000 | 8 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | end | low | unknown | retrieve_then_read | exact_match | 0.5000 | 1.0000 | 0.6250 | 8 | True |  | 0.2500 | 0.2500 |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | scattered | medium | unknown | direct | exact_match | 0.4167 | 0.9167 | 0.4167 | 12 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.4167 | 0.9167 | 0.4167 | 12 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | front | low | unknown | direct | exact_match | 0.8889 | 0.8889 | 0.6667 | 9 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | front | low | unknown | retrieve_then_read | exact_match | 0.8889 | 0.8889 | 0.5556 | 9 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | scattered | high | unknown | direct | exact_match | 1.0000 | 1.0000 | 1.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | scattered | high | unknown | retrieve_then_read | exact_match | 1.0000 | 1.0000 | 1.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | middle | low | unknown | direct | exact_match | 0.6250 | 1.0000 | 0.7500 | 8 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | gemma3:12b | comparison | 4000 | middle | low | unknown | retrieve_then_read | exact_match | 0.6250 | 1.0000 | 0.7500 | 8 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | middle | medium | unknown | direct | exact_match | 0.5556 | 0.8889 | 0.7778 | 9 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | middle | medium | unknown | retrieve_then_read | exact_match | 0.5556 | 0.8889 | 0.7778 | 9 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | scattered | low | unknown | direct | exact_match | 0.6250 | 0.8750 | 0.6250 | 8 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 16000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.6250 | 0.8750 | 0.7500 | 8 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | front | medium | unknown | direct | exact_match | 0.7778 | 1.0000 | 0.6667 | 9 | True |  | -0.5000 | 0.0000 |
| 2wikimultihopqa | gemma3:12b | comparison | 8000 | front | medium | unknown | retrieve_then_read | exact_match | 0.7778 | 1.0000 | 0.4444 | 9 | True |  | -1.5000 | 0.0000 |
