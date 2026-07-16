from safe_kiosk_people_agent.commands.inspect_signals import inspect_signals
def test_inspect_signals_is_empty_and_bounded():
    result=inspect_signals(fmt='json'); assert result['sources']['wifi']['sample_count']==0
