| source | model_name | reasoning_type | context_length | evidence_position | evidence_density | distractor_similarity | long_method | score_field | score_no_evidence | score_oracle | score_long | n | cue_valid | cue_invalid_reason | cue_raw | cue_clipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hotpotqa | qwen3:14b | comparison | 4000 | front | low | unknown | direct | exact_match | 0.0000 | 0.3333 | 0.3333 | 3 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | comparison | 4000 | front | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.3333 | 0.3333 | 3 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | comparison | 8000 | middle | low | unknown | direct | exact_match | 0.5000 | 0.5000 | 0.5000 | 2 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 8000 | middle | low | unknown | retrieve_then_read | exact_match | 0.5000 | 0.5000 | 1.0000 | 2 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | multi_hop | 16000 | end | medium | unknown | direct | exact_match | 0.1250 | 0.5000 | 0.3750 | 8 | True |  | 0.6667 | 0.6667 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | end | medium | unknown | retrieve_then_read | exact_match | 0.1250 | 0.5000 | 0.2500 | 8 | True |  | 0.3333 | 0.3333 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | scattered | medium | unknown | direct | exact_match | 0.0000 | 0.6000 | 0.8000 | 5 | True |  | 1.3333 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.0000 | 0.6000 | 0.4000 | 5 | True |  | 0.6667 | 0.6667 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | front | medium | unknown | direct | exact_match | 0.0000 | 0.5000 | 0.5000 | 10 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | front | medium | unknown | retrieve_then_read | exact_match | 0.0000 | 0.5000 | 0.4000 | 10 | True |  | 0.8000 | 0.8000 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | middle | medium | unknown | direct | exact_match | 0.1111 | 1.0000 | 0.5556 | 9 | True |  | 0.5000 | 0.5000 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | middle | medium | unknown | retrieve_then_read | exact_match | 0.1111 | 1.0000 | 0.5556 | 9 | True |  | 0.5000 | 0.5000 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | end | low | unknown | direct | exact_match | 0.1000 | 0.4000 | 0.5000 | 10 | True |  | 1.3333 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | end | low | unknown | retrieve_then_read | exact_match | 0.1000 | 0.4000 | 0.4000 | 10 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | comparison | 8000 | scattered | low | unknown | direct | exact_match | 0.0000 | 1.0000 | 1.0000 | 2 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | comparison | 8000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.0000 | 1.0000 | 0.5000 | 2 | True |  | 0.5000 | 0.5000 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | front | low | unknown | direct | exact_match | 0.2222 | 0.8889 | 0.4444 | 9 | True |  | 0.3333 | 0.3333 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | front | low | unknown | retrieve_then_read | exact_match | 0.2222 | 0.8889 | 0.4444 | 9 | True |  | 0.3333 | 0.3333 |
| hotpotqa | qwen3:14b | comparison | 4000 | middle | low | unknown | direct | exact_match | 0.6667 | 1.0000 | 1.0000 | 3 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | comparison | 4000 | middle | low | unknown | retrieve_then_read | exact_match | 0.6667 | 1.0000 | 1.0000 | 3 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | end | low | unknown | direct | exact_match | 0.2500 | 0.8333 | 0.6667 | 12 | True |  | 0.7143 | 0.7143 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | end | low | unknown | retrieve_then_read | exact_match | 0.2500 | 0.8333 | 0.4167 | 12 | True |  | 0.2857 | 0.2857 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | scattered | medium | unknown | direct | exact_match | 0.0000 | 0.3333 | 0.3333 | 3 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.0000 | 0.3333 | 0.3333 | 3 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | front | low | unknown | direct | exact_match | 0.2857 | 0.8571 | 0.8571 | 7 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | front | low | unknown | retrieve_then_read | exact_match | 0.2857 | 0.8571 | 0.8571 | 7 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | middle | low | unknown | direct | exact_match | 0.4000 | 0.7000 | 0.5000 | 10 | True |  | 0.3333 | 0.3333 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | middle | low | unknown | retrieve_then_read | exact_match | 0.4000 | 0.7000 | 0.4000 | 10 | True |  | 0.0000 | 0.0000 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | scattered | low | unknown | direct | exact_match | 0.1000 | 0.8000 | 0.5000 | 10 | True |  | 0.5714 | 0.5714 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.1000 | 0.8000 | 0.3000 | 10 | True |  | 0.2857 | 0.2857 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | front | low | unknown | direct | exact_match | 0.4286 | 0.7143 | 0.5714 | 7 | True |  | 0.5000 | 0.5000 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | front | low | unknown | retrieve_then_read | exact_match | 0.4286 | 0.7143 | 0.1429 | 7 | True |  | -1.0000 | 0.0000 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | middle | low | unknown | direct | exact_match | 0.0000 | 0.5000 | 0.5000 | 6 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | middle | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.5000 | 0.1667 | 6 | True |  | 0.3333 | 0.3333 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | scattered | medium | unknown | direct | exact_match | 0.0000 | 0.8000 | 0.8000 | 5 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.0000 | 0.8000 | 0.2000 | 5 | True |  | 0.2500 | 0.2500 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | middle | medium | unknown | direct | exact_match | 0.2500 | 0.5000 | 0.2500 | 4 | True |  | 0.0000 | 0.0000 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | middle | medium | unknown | retrieve_then_read | exact_match | 0.2500 | 0.5000 | 0.5000 | 4 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | comparison | 8000 | end | low | unknown | direct | exact_match | 0.3333 | 0.3333 | 0.3333 | 3 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 8000 | end | low | unknown | retrieve_then_read | exact_match | 0.3333 | 0.3333 | 0.6667 | 3 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | multi_hop | 16000 | scattered | low | unknown | direct | exact_match | 0.3333 | 0.8333 | 0.8333 | 12 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.3333 | 0.8333 | 0.5000 | 12 | True |  | 0.3333 | 0.3333 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | front | medium | unknown | direct | exact_match | 0.0000 | 0.8571 | 0.4286 | 7 | True |  | 0.5000 | 0.5000 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | front | medium | unknown | retrieve_then_read | exact_match | 0.0000 | 0.8571 | 0.2857 | 7 | True |  | 0.3333 | 0.3333 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | end | low | unknown | direct | exact_match | 0.3333 | 0.6667 | 0.6667 | 9 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | end | low | unknown | retrieve_then_read | exact_match | 0.3333 | 0.6667 | 0.4444 | 9 | True |  | 0.3333 | 0.3333 |
| hotpotqa | qwen3:14b | comparison | 8000 | scattered | medium | unknown | direct | exact_match | 0.0000 | 1.0000 | 1.0000 | 1 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | comparison | 8000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.0000 | 1.0000 | 1.0000 | 1 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | front | medium | unknown | direct | exact_match | 0.0000 | 0.6000 | 0.2000 | 5 | True |  | 0.3333 | 0.3333 |
| hotpotqa | qwen3:14b | multi_hop | 16000 | front | medium | unknown | retrieve_then_read | exact_match | 0.0000 | 0.6000 | 0.4000 | 5 | True |  | 0.6667 | 0.6667 |
| hotpotqa | qwen3:14b | comparison | 4000 | middle | medium | unknown | direct | exact_match | 1.0000 | 1.0000 | 1.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 4000 | middle | medium | unknown | retrieve_then_read | exact_match | 1.0000 | 1.0000 | 1.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | multi_hop | 4000 | end | medium | unknown | direct | exact_match | 0.2500 | 0.2500 | 0.0000 | 4 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | multi_hop | 4000 | end | medium | unknown | retrieve_then_read | exact_match | 0.2500 | 0.2500 | 0.0000 | 4 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | multi_hop | 8000 | scattered | low | unknown | direct | exact_match | 0.1111 | 0.5556 | 0.3333 | 9 | True |  | 0.5000 | 0.5000 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.1111 | 0.5556 | 0.4444 | 9 | True |  | 0.7500 | 0.7500 |
| hotpotqa | qwen3:14b | comparison | 16000 | front | low | unknown | direct | exact_match | 0.0000 | 0.0000 | 0.0000 | 2 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 16000 | front | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.0000 | 0.0000 | 2 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | multi_hop | 4000 | middle | low | unknown | direct | exact_match | 0.1250 | 0.7500 | 0.7500 | 8 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 4000 | middle | low | unknown | retrieve_then_read | exact_match | 0.1250 | 0.7500 | 0.5000 | 8 | True |  | 0.6000 | 0.6000 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | middle | medium | unknown | direct | exact_match | 0.2000 | 0.6000 | 0.4000 | 5 | True |  | 0.5000 | 0.5000 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | middle | medium | unknown | retrieve_then_read | exact_match | 0.2000 | 0.6000 | 0.2000 | 5 | True |  | 0.0000 | 0.0000 |
| hotpotqa | qwen3:14b | comparison | 4000 | scattered | low | unknown | direct | exact_match | 0.5000 | 0.0000 | 0.0000 | 2 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 4000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.5000 | 0.0000 | 0.5000 | 2 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 4000 | end | medium | unknown | direct | exact_match | 1.0000 | 1.0000 | 1.0000 | 2 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 4000 | end | medium | unknown | retrieve_then_read | exact_match | 1.0000 | 1.0000 | 1.0000 | 2 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 16000 | middle | medium | unknown | direct | exact_match | 1.0000 | 1.0000 | 1.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 16000 | middle | medium | unknown | retrieve_then_read | exact_match | 1.0000 | 1.0000 | 1.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 16000 | scattered | medium | unknown | direct | exact_match | 0.0000 | 0.0000 | 0.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 16000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.0000 | 0.0000 | 0.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | multi_hop | 8000 | end | medium | unknown | direct | exact_match | 0.0000 | 1.0000 | 1.0000 | 1 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | multi_hop | 8000 | end | medium | unknown | retrieve_then_read | exact_match | 0.0000 | 1.0000 | 1.0000 | 1 | True |  | 1.0000 | 1.0000 |
| hotpotqa | qwen3:14b | comparison | 4000 | end | low | unknown | direct | exact_match | 1.0000 | 1.0000 | 1.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 4000 | end | low | unknown | retrieve_then_read | exact_match | 1.0000 | 1.0000 | 1.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 16000 | middle | low | unknown | direct | exact_match | 1.0000 | 1.0000 | 1.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| hotpotqa | qwen3:14b | comparison | 16000 | middle | low | unknown | retrieve_then_read | exact_match | 1.0000 | 1.0000 | 1.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
