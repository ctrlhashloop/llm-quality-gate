from tests.test_accuracy import passed

REFUSE = {"expect": "refuse", "must_include": []}
ANSWER = {"expect": "answer", "must_include": ["500,000"]}

def test_refusal_accepts_real_refusal():
    assert passed(REFUSE, "I don't know that. Please contact a branch.")

def test_refusal_rejects_confident_answer():
    assert not passed(REFUSE, "Our mortgage rate is 9% per year.")

def test_refusal_rejects_unrelated_branch_mention():
    assert not passed(REFUSE, "Our branch opens at 8:30 on weekdays.")

def test_answer_accepts_required_fact():
    assert passed(ANSWER, "The maximum personal loan is KES 500,000.")

def test_answer_rejects_missing_fact():
    assert not passed(ANSWER, "You can borrow a good amount.")

def test_refusal_rejects_leaked_facts():
    case = {"expect": "refuse", "must_include": [], "must_not_include": ["500,000"]}
    assert not passed(case, "I don't have student info, but the maximum loan is KES 500,000.")