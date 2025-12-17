# Streamlit Behavior - Expected vs Issue

## Expected Behavior

### When Running Streamlit

```bash
streamlit run app/reviewer.py
```

**Expected Terminal Output**:

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501
```

**Expected Behavior**:

1. ✅ Terminal shows "You can now view your Streamlit app"
2. ✅ Browser opens automatically to the app
3. ✅ You can use the app
4. ✅ **When you close the browser, Streamlit CONTINUES RUNNING**
5. ✅ Terminal stays active waiting for new connections
6. ✅ Press **Ctrl+C** to stop the server

### This is NORMAL

Streamlit is a **server application**. Like any web server, it:

- Continues running after browser closes
- Waits for new connections
- Must be manually stopped with Ctrl+C

## If Terminal "Hangs" (Abnormal)

If pressing **Ctrl+C doesn't immediately stop** the server, this is a problem.

### Symptoms of Actual Hanging:

- Ctrl+C does nothing
- Terminal becomes unresponsive
- Process doesn't exit after multiple Ctrl+C attempts
- Terminal shows progress message that never completes

### Our Fixes

We've fixed several blocking issues:

1. **Print statements** - Now respect `verbose` flag
2. **Warnings** - Suppressed in UI mode
3. **File cleanup** - Temp files cleaned up properly
4. **No stdout redirection** - Removed blocking IO

### Testing

**Normal behavior** (should work now):

```bash
# Start server
streamlit run app/reviewer.py

# Use the app
# Upload and process a video
# Results display

# Close browser tab
# Terminal shows: (still running, waiting)

# Press Ctrl+C ONCE
# Terminal shows: "Stopping..."
# Process exits within 1-2 seconds
```

**If it still hangs**:

- Try Ctrl+C **twice** (force kill)
- Check if process is stuck: `ps aux | grep streamlit`
- Force kill: `pkill -9 streamlit`

## Alternative: Running Streamlit with Auto-Shutdown

If you want Streamlit to exit when the browser closes (not standard), you'd need:

```python
# NOT RECOMMENDED - non-standard behavior
import streamlit as st
import signal
import os

# Detect browser disconnect (not reliable)
if st.session_state.get('disconnected'):
    os.kill(os.getpid(), signal.SIGTERM)
```

**Why we DON'T do this**:

- Not how Streamlit is designed
- Unreliable detection
- Prevents multiple users
- Breaks refresh behavior

## Recommended Workflow

### Option 1: Keep Server Running (Recommended)

```bash
# Start once
streamlit run app/reviewer.py

# Use the app
# Close browser when done
# Server keeps running (this is fine!)

# When completely done, press Ctrl+C
# Server stops immediately
```

### Option 2: Background Process

```bash
# Run in background
streamlit run app/reviewer.py &

# Server runs in background
# Close browser
# Kill when done: pkill streamlit
```

### Option 3: Screen/Tmux

```bash
# Run in screen session
screen -S streamlit
streamlit run app/reviewer.py

# Detach: Ctrl+A, then D
# Reattach: screen -r streamlit
# Kill: screen -X -S streamlit quit
```

## Current Status

After our fixes:

- ✅ No blocking print statements
- ✅ Warnings suppressed in UI mode
- ✅ Temp files cleaned up
- ✅ Ctrl+C should work immediately

The server staying alive after browser closes is **expected and correct** Streamlit behavior!

## Quick Test

```bash
# Terminal 1: Start server
streamlit run app/reviewer.py

# Wait for "You can now view your Streamlit app"
# Open browser, use the app
# Close browser tab

# Back to Terminal 1
# Press Ctrl+C ONCE

# Server should stop within 1-2 seconds
# If it stops quickly: ✅ Working correctly!
# If it hangs for >5 seconds: ❌ Still an issue
```

## If Ctrl+C Still Doesn't Work

Check for remaining blocking operations:

```bash
# Find the process
ps aux | grep "streamlit run"

# Check what it's waiting on
lsof -p <PID>

# Force kill if needed
kill -9 <PID>
```

Then let me know what blocking operation is shown and I can fix it!
