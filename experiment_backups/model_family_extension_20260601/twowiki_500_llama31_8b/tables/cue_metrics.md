| source | model_name | reasoning_type | context_length | evidence_position | evidence_density | distractor_similarity | long_method | score_field | score_no_evidence | score_oracle | score_long | n | cue_valid | cue_invalid_reason | cue_raw | cue_clipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 4000 | front | low | unknown | direct | exact_match | 0.0000 | 0.5909 | 0.3182 | 22 | True |  | 0.5385 | 0.5385 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 4000 | front | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.5909 | 0.1818 | 22 | True |  | 0.3077 | 0.3077 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | middle | low | unknown | direct | exact_match | 0.3333 | 0.8333 | 0.3333 | 6 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | middle | low | unknown | retrieve_then_read | exact_match | 0.3333 | 0.8333 | 0.5000 | 6 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 16000 | end | low | unknown | direct | exact_match | 0.0417 | 0.5833 | 0.2917 | 24 | True |  | 0.4615 | 0.4615 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 16000 | end | low | unknown | retrieve_then_read | exact_match | 0.0417 | 0.5833 | 0.0833 | 24 | True |  | 0.0769 | 0.0769 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 4000 | scattered | low | unknown | direct | exact_match | 0.0000 | 0.6522 | 0.4783 | 23 | True |  | 0.7333 | 0.7333 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 4000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.6522 | 0.1304 | 23 | True |  | 0.2000 | 0.2000 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 8000 | front | low | unknown | direct | exact_match | 0.0435 | 0.6087 | 0.3478 | 23 | True |  | 0.5385 | 0.5385 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 8000 | front | low | unknown | retrieve_then_read | exact_match | 0.0435 | 0.6087 | 0.2174 | 23 | True |  | 0.3077 | 0.3077 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 16000 | middle | low | unknown | direct | exact_match | 0.1538 | 0.5000 | 0.3462 | 26 | True |  | 0.5556 | 0.5556 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 16000 | middle | low | unknown | retrieve_then_read | exact_match | 0.1538 | 0.5000 | 0.1923 | 26 | True |  | 0.1111 | 0.1111 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 4000 | end | low | unknown | direct | exact_match | 0.0000 | 0.5455 | 0.2273 | 22 | True |  | 0.4167 | 0.4167 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 4000 | end | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.5455 | 0.0909 | 22 | True |  | 0.1667 | 0.1667 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | scattered | low | unknown | direct | exact_match | 0.7778 | 0.7778 | 0.4444 | 9 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.7778 | 0.7778 | 0.4444 | 9 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | front | medium | unknown | direct | exact_match | 0.2500 | 0.6250 | 0.2500 | 8 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | front | medium | unknown | retrieve_then_read | exact_match | 0.2500 | 0.6250 | 0.3750 | 8 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 4000 | middle | low | unknown | direct | exact_match | 0.0833 | 0.5417 | 0.2083 | 24 | True |  | 0.2727 | 0.2727 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 4000 | middle | low | unknown | retrieve_then_read | exact_match | 0.0833 | 0.5417 | 0.0833 | 24 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | end | medium | unknown | direct | exact_match | 0.7500 | 0.8333 | 0.7500 | 12 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | end | medium | unknown | retrieve_then_read | exact_match | 0.7500 | 0.8333 | 0.7500 | 12 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | scattered | medium | unknown | direct | exact_match | 0.5000 | 0.7143 | 0.4286 | 14 | True |  | -0.3333 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.5000 | 0.7143 | 0.5000 | 14 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | front | medium | unknown | direct | exact_match | 0.2727 | 0.5455 | 0.3636 | 11 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | front | medium | unknown | retrieve_then_read | exact_match | 0.2727 | 0.5455 | 0.2727 | 11 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 8000 | middle | low | unknown | direct | exact_match | 0.0370 | 0.4815 | 0.2963 | 27 | True |  | 0.5833 | 0.5833 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 8000 | middle | low | unknown | retrieve_then_read | exact_match | 0.0370 | 0.4815 | 0.1111 | 27 | True |  | 0.1667 | 0.1667 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | front | low | unknown | direct | exact_match | 0.7000 | 1.0000 | 0.5000 | 10 | True |  | -0.6667 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | front | low | unknown | retrieve_then_read | exact_match | 0.7000 | 1.0000 | 0.3000 | 10 | True |  | -1.3333 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | middle | medium | unknown | direct | exact_match | 0.3750 | 0.7500 | 0.6250 | 8 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | middle | medium | unknown | retrieve_then_read | exact_match | 0.3750 | 0.7500 | 0.5000 | 8 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | scattered | medium | unknown | direct | exact_match | 0.6154 | 0.5385 | 0.5385 | 13 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.6154 | 0.5385 | 0.6154 | 13 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | front | low | unknown | direct | exact_match | 0.5000 | 1.0000 | 0.6667 | 6 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | front | low | unknown | retrieve_then_read | exact_match | 0.5000 | 1.0000 | 0.3333 | 6 | True |  | -0.3333 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | end | medium | unknown | direct | exact_match | 0.6000 | 0.6000 | 1.0000 | 5 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | end | medium | unknown | retrieve_then_read | exact_match | 0.6000 | 0.6000 | 0.8000 | 5 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | middle | low | unknown | direct | exact_match | 0.2500 | 0.6250 | 0.3750 | 8 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | middle | low | unknown | retrieve_then_read | exact_match | 0.2500 | 0.6250 | 0.3750 | 8 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | end | low | unknown | direct | exact_match | 0.5833 | 0.9167 | 0.5000 | 12 | True |  | -0.2500 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | end | low | unknown | retrieve_then_read | exact_match | 0.5833 | 0.9167 | 0.5833 | 12 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 8000 | end | low | unknown | direct | exact_match | 0.1905 | 0.4762 | 0.2381 | 21 | True |  | 0.1667 | 0.1667 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 8000 | end | low | unknown | retrieve_then_read | exact_match | 0.1905 | 0.4762 | 0.0476 | 21 | True |  | -0.5000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 16000 | scattered | low | unknown | direct | exact_match | 0.0526 | 0.6316 | 0.2632 | 19 | True |  | 0.3636 | 0.3636 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 16000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.0526 | 0.6316 | 0.0526 | 19 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | end | low | unknown | direct | exact_match | 0.3846 | 0.6923 | 0.4615 | 13 | True |  | 0.2500 | 0.2500 |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | end | low | unknown | retrieve_then_read | exact_match | 0.3846 | 0.6923 | 0.3846 | 13 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | scattered | low | unknown | direct | exact_match | 0.3333 | 0.5000 | 0.3333 | 6 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.3333 | 0.5000 | 0.5000 | 6 | True |  | 1.0000 | 1.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | end | medium | unknown | direct | exact_match | 0.6250 | 0.7500 | 0.7500 | 8 | True |  | 1.0000 | 1.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | end | medium | unknown | retrieve_then_read | exact_match | 0.6250 | 0.7500 | 0.7500 | 8 | True |  | 1.0000 | 1.0000 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 8000 | scattered | low | unknown | direct | exact_match | 0.0000 | 0.5000 | 0.0500 | 20 | True |  | 0.1000 | 0.1000 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 8000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.0000 | 0.5000 | 0.0500 | 20 | True |  | 0.1000 | 0.1000 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 16000 | front | low | unknown | direct | exact_match | 0.0741 | 0.6667 | 0.3333 | 27 | True |  | 0.4375 | 0.4375 |
| 2wikimultihopqa | llama3.1:8b | multi_hop | 16000 | front | low | unknown | retrieve_then_read | exact_match | 0.0741 | 0.6667 | 0.2222 | 27 | True |  | 0.2500 | 0.2500 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | middle | medium | unknown | direct | exact_match | 0.4444 | 0.7778 | 0.5556 | 9 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | middle | medium | unknown | retrieve_then_read | exact_match | 0.4444 | 0.7778 | 0.4444 | 9 | True |  | 0.0000 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | end | low | unknown | direct | exact_match | 0.5000 | 0.8750 | 0.6250 | 8 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | end | low | unknown | retrieve_then_read | exact_match | 0.5000 | 0.8750 | 0.6250 | 8 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | scattered | medium | unknown | direct | exact_match | 0.5000 | 0.6667 | 0.5833 | 12 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | scattered | medium | unknown | retrieve_then_read | exact_match | 0.5000 | 0.6667 | 0.6667 | 12 | True |  | 1.0000 | 1.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | front | low | unknown | direct | exact_match | 0.1111 | 0.6667 | 0.2222 | 9 | True |  | 0.2000 | 0.2000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | front | low | unknown | retrieve_then_read | exact_match | 0.1111 | 0.6667 | 0.4444 | 9 | True |  | 0.6000 | 0.6000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | scattered | high | unknown | direct | exact_match | 0.0000 | 0.0000 | 0.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | scattered | high | unknown | retrieve_then_read | exact_match | 0.0000 | 0.0000 | 0.0000 | 1 | False | oracle_not_above_no_evidence |  |  |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | middle | low | unknown | direct | exact_match | 0.5000 | 1.0000 | 0.6250 | 8 | True |  | 0.2500 | 0.2500 |
| 2wikimultihopqa | llama3.1:8b | comparison | 4000 | middle | low | unknown | retrieve_then_read | exact_match | 0.5000 | 1.0000 | 0.7500 | 8 | True |  | 0.5000 | 0.5000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | middle | medium | unknown | direct | exact_match | 0.5556 | 0.8889 | 0.3333 | 9 | True |  | -0.6667 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | middle | medium | unknown | retrieve_then_read | exact_match | 0.5556 | 0.8889 | 0.4444 | 9 | True |  | -0.3333 | 0.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | scattered | low | unknown | direct | exact_match | 0.2500 | 1.0000 | 0.5000 | 8 | True |  | 0.3333 | 0.3333 |
| 2wikimultihopqa | llama3.1:8b | comparison | 16000 | scattered | low | unknown | retrieve_then_read | exact_match | 0.2500 | 1.0000 | 0.7500 | 8 | True |  | 0.6667 | 0.6667 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | front | medium | unknown | direct | exact_match | 0.6667 | 0.7778 | 0.8889 | 9 | True |  | 2.0000 | 1.0000 |
| 2wikimultihopqa | llama3.1:8b | comparison | 8000 | front | medium | unknown | retrieve_then_read | exact_match | 0.6667 | 0.7778 | 0.6667 | 9 | True |  | 0.0000 | 0.0000 |
