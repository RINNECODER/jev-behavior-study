"""Run final decisions using the actual saved prerequisite choices from phase one.
Usage: python run_decision_pipeline.py results/<limits-study> [--plan-only]
"""
import sys
from pathlib import Path
from behavior_study import run
from limits_study import pipeline_cases,HYPOTHESES

if __name__=='__main__':
    if len(sys.argv)<2:raise SystemExit(__doc__)
    source=Path(sys.argv.pop(1))
    run(lambda:pipeline_cases(source),'decision-pipeline',20260921,HYPOTHESES,
        method='Final decision inputs are derived from the actual corresponding prerequisite response plus original scenario facts, with no correction or grading-label leakage. Other trials and conversation history are excluded. Shuffled final-phase requests, fresh opener, no retries. Each prerequisite has exactly one final decision; repetitions measure conditional stability, not independent task coverage.')
