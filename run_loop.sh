#!/bin/bash
cd ~/clawd/skills/research-report
mkdir -p output/test/images

MAX_LOOPS=10
LOOP=1

while [ $LOOP -le $MAX_LOOPS ]; do
    echo "=== Loop $LOOP / $MAX_LOOPS ==="
    
    # Run Claude with the prompt
    OUTPUT=$(claude -p --dangerously-skip-permissions "$(cat prompt.md)")
    
    echo "$OUTPUT"
    
    # Check for completion
    if echo "$OUTPUT" | grep -q "SKILL_COMPLETE"; then
        echo "=== COMPLETED at loop $LOOP ==="
        exit 0
    fi
    
    LOOP=$((LOOP + 1))
    sleep 2
done

echo "=== Max loops reached ==="
