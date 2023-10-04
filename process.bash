#!/bin/bash
grep -v -E '^[0-9]' $1 > $1_clean
python summary.py --write_topics $1_topics.json --write_company_annotated $1_company_annotated.json --write_summarized_topics $1_summarized_topics.json  --transcript $1_clean > $1.html
