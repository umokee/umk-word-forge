MASTERY_LEVELS = {
    0: "Not started",
    1: "Introduction",
    2: "Recognition",
    3: "Recall",
    4: "Context",
    5: "Sentence Builder",
    6: "Free Production",
    7: "Listening",
}

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

PARTS_OF_SPEECH = ["noun", "verb", "adj", "adv", "prep", "conj", "pron", "det", "intj"]

CONSECUTIVE_CORRECT_TO_LEVEL_UP = 3
CONSECUTIVE_WRONG_TO_LEVEL_DOWN = 2
LOW_STABILITY_THRESHOLD = 0.5

COVERAGE_THRESHOLDS = [
    (100, 50), (300, 65), (500, 72), (1000, 80),
    (2000, 86), (3000, 90), (5000, 95), (10000, 98),
]

EXERCISE_TIME_ESTIMATES = {
    1: 4, 2: 4, 3: 10, 4: 10,
    5: 20, 6: 30, 7: 30,
}
