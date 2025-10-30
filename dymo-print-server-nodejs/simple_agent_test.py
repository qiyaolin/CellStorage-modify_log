import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from production_print_agent import ProductionPrintAgent

print("Testing print agent...")
agent = ProductionPrintAgent()

print("Health check...")
status = agent.health_check()
print(f"Result: {status}")

print("Testing job polling...")
for i in range(3):
    print(f"Cycle {i+1}")
    jobs = agent.get_pending_jobs()
    print(f"Jobs found: {len(jobs)}")
    time.sleep(2)

print("Test complete!")