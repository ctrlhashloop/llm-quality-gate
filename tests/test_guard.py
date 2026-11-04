from app.bot import leaks_instructions

def test_catches_verbatim_leak():
    assert leaks_instructions("You are a customer FAQ assistant for a bank. Answer ONLY using the FAQ below.")

def test_ignores_normal_answer():
    assert not leaks_instructions("The maximum personal loan is KES 500,000.")

def test_ignores_normal_refusal():
    assert not leaks_instructions("I don't know. Please contact a branch.")