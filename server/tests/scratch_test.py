# Server/src/scratch_test.py — delete after testing
import asyncio
from src.graph.assessment_graph import start_conversation, continue_conversation

async def main():
    state = await start_conversation(notes=None)
    print(state)
    print("#############################################################################################################")
    answers = []
    for q in range(1, 10):
        state = await continue_conversation(answers=state["answers"], notes=None, incoming_score=1)
        answers = state["answers"]
        print(answers)
    print("#############################################################################################################")
    print(state["result"])         # Should print a real dict, not crash
    print(state["crisis_support"]) # Should print None or a helpline dict

asyncio.run(main())