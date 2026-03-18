# Midnight Reset Detection Problem - Root Cause Analysis

## Executive Summary

**Problem:** The midnight reset process executes correctly (you can see Teams refresh on screen), but the code **fails to detect** that the refresh completed successfully, causing it to retry and eventually fail.

**Root Cause:** The `shiftloaded.png` image recognition is not finding the "loaded" indicator on screen, even though Teams has actually loaded successfully.

**Impact:** Midnight reset appears to "not work" because detection fails, not because the reset itself fails.

---

## What You're Seeing vs What's Happening

### What You See (Visual):
? Teams Calendar tab opens  
? Dots menu clicks  
? Shifts option clicks  
? Shifts page loads and displays correctly  
? Everything looks fine on screen!

### What the Code Sees (Detection):
? Looking for `shiftloaded.png` on screen  
? Not finding it (even though page is loaded)  
? Waits 1 second and tries again (10 times)  
? Still doesn't find it  
? Assumes reset failed and retries entire process  

**Result:** The code thinks it failed, so it keeps retrying until it hits the 10-attempt limit, then gives up.

---

## The Detection Code

Here's the problematic section in `gui.py` method `refresh_teams_shifts()`:

```python
# Step 4: Wait for Shifts loaded
loaded = False
for _ in range(10):  # Try 10 times (10 seconds total)
    try:
        loaded_img = pyautogui.locateOnScreen('shiftloaded.png', confidence=0.8)
        if loaded_img:
loaded = True
    break
    except pyautogui.ImageNotFoundException:
 # Image not found, continue waiting
        pass
    except Exception as e:
  print(f"[Reset] Error checking for shifts loaded: {e}")
    time.sleep(1)  # Wait 1 second between attempts

if not loaded:
    # Detection failed - retry entire reset process
    self.scan_status_var.set("[Reset] Shifts did not finish loading. Retrying...")
    time.sleep(2)
  continue  # Goes back to attempt 1 of 10
```

**The code waits 10 seconds, checking every second for `shiftloaded.png` to appear on screen. If it never finds it, the code assumes the reset failed.**

---

## Why This Worked Before But Stopped

Several things could have changed:

### 1. Teams UI Updated
Microsoft updates Teams frequently. If the UI changed even slightly:
- The `shiftloaded.png` image no longer matches
- Text font changed
- Button color changed
- Element moved to different position

### 2. Teams Loading Slower
- Teams might be taking longer to load than before
- Network latency increased
- More data to load
- System performance degraded

### 3. Image File Changed/Corrupted
- `shiftloaded.png` file got corrupted
- File was accidentally replaced
- File permissions changed

### 4. Screen Resolution Changed
- If you changed monitors or resolution
- DPI scaling changed
- Image no longer matches pixel-perfect

---

## Diagnostic Steps

### Step 1: Check if `shiftloaded.png` exists

```powershell
ls shiftloaded.png
```

If it doesn't exist, the reset will NEVER work.

### Step 2: Check image size

```powershell
python -c "import cv2; img=cv2.imread('shiftloaded.png'); print(f'Size: {img.shape[1]}x{img.shape[0]} pixels')"
```

- **Too small** (< 30x30): May match too many things
- **Too large** (> 200x200): May be too specific and never match
- **Ideal**: 60x40 to 120x60 pixels

### Step 3: Run the diagnostic tool

```powershell
python diagnose_shiftloaded.py
```

This will:
1. Check if `shiftloaded.png` exists
2. Check its dimensions
3. Ask you to open Teams to the Shifts page
4. Take a screenshot of current state
5. Try to find `shiftloaded.png` at different confidence levels
6. Tell you exactly what's wrong

---

## Likely Scenarios & Solutions

### Scenario A: Image Not Found at ANY Confidence Level

**Diagnosis:** `shiftloaded.png` doesn't match what's on screen

**Cause:** Teams UI changed, image is wrong/outdated

**Solution:** Capture a fresh `shiftloaded.png` image

**Steps:**
1. Open Teams and navigate to Calendar > Shifts
2. Wait for page to FULLY load
3. Identify a UNIQUE visual element that only appears when loaded:
   - "Open shifts" heading
- "Booked shifts" heading
   - A specific button that appears
   - The shifts calendar itself
4. Use Windows Snipping Tool (Win+Shift+S)
5. Capture a small region (60x40 to 120x60 pixels) of that element
6. Save as `shiftloaded.png` in the project directory
7. Run diagnostic again to verify

---

### Scenario B: Image Found But Only at Lower Confidence

**Diagnosis:** Image matches but not at confidence=0.8

**Cause:** Teams UI changed slightly, image is close but not exact

**Solution:** Lower the confidence threshold in code

**Steps:**
1. Run `python diagnose_shiftloaded.py`
2. Note the confidence level where it DOES work (e.g., 0.6)
3. Edit `gui.py` line ~620:

   **Change:**
   ```python
   loaded_img = pyautogui.locateOnScreen('shiftloaded.png', confidence=0.8)
   ```

   **To:**
   ```python
   loaded_img = pyautogui.locateOnScreen('shiftloaded.png', confidence=0.6)
   ```

4. Save and restart the app
5. Test the reset again

---

### Scenario C: Teams Takes Longer Than 10 Seconds to Load

**Diagnosis:** Detection logic times out before Teams finishes loading

**Cause:** Teams performance degraded, needs more time

**Solution:** Increase wait time in detection loop

**Steps:**
1. Edit `gui.py` line ~612:

   **Change:**
   ```python
   for _ in range(10):  # Try 10 times (10 seconds total)
   ```

   **To:**
 ```python
   for _ in range(20):  # Try 20 times (20 seconds total)
   ```

2. Save and restart the app
3. Test the reset again

---

### Scenario D: Wrong Element Being Detected

**Diagnosis:** `shiftloaded.png` captures a generic element that appears in multiple states

**Cause:** Image is too generic or small

**Solution:** Capture a MORE SPECIFIC indicator

**Examples of BAD indicators:**
- Generic "..." dots button (appears everywhere)
- Common icons (calendar, settings, etc.)
- Plain text that appears on multiple pages

**Examples of GOOD indicators:**
- "Open shifts" header (unique to shifts page)
- The shifts calendar grid itself
- "Book" or "Claim" buttons (only on shifts page)

---

## Quick Fix Options

### Option 1: Use Alternative Detection (Recommended for Testing)

Instead of looking for `shiftloaded.png`, wait a fixed time:

**Edit `gui.py` line ~610, replace Step 4 entirely with:**

```python
# Step 4: Wait for Shifts to load (fixed delay)
print("[Reset] Waiting 15 seconds for Shifts to load...")
self.scan_status_var.set("[Reset] Waiting for Shifts to load...")
time.sleep(15)  # Just wait 15 seconds
loaded = True  # Assume it loaded
print("[Reset] Assuming Shifts loaded after 15 second delay")
```

**Pros:**
- Simple
- Will work immediately
- Good for testing if everything else works

**Cons:**
- Not robust (doesn't actually verify loading)
- Might resume too early if Teams is slow
- Might wait too long if Teams is fast

---

### Option 2: Use Multiple Detection Images

Try multiple indicators instead of just one:

```python
# Step 4: Wait for Shifts loaded (try multiple indicators)
loaded = False
indicators = ['shiftloaded.png', 'openshifts.png', 'bookedshifts.png']

for _ in range(15):
    try:
        for indicator in indicators:
            if os.path.exists(indicator):
   loaded_img = pyautogui.locateOnScreen(indicator, confidence=0.7)
     if loaded_img:
           loaded = True
     print(f"[Reset] Found indicator: {indicator}")
   break
        if loaded:
     break
    except pyautogui.ImageNotFoundException:
     pass
 except Exception as e:
        print(f"[Reset] Error checking indicators: {e}")
    time.sleep(1)
```

**Pros:**
- More robust
- Multiple chances to detect
- Fallback if one image fails

**Cons:**
- Requires capturing multiple images
- More complex

---

## Recommended Action Plan

1. **? Run Diagnostic First**
   ```powershell
   python diagnose_shiftloaded.py
   ```
   This will tell you exactly what's wrong.

2. **?? Apply Quick Fix (Option 1)**
   - Replace detection with fixed 15-second delay
   - Test if midnight reset works with this change
   - This confirms detection is the ONLY problem

3. **?? Capture Fresh Image**
   - Follow the guide in Scenario A above
   - Get a good, unique indicator image
   - Test with diagnostic tool

4. **?? Restore Proper Detection**
   - Revert the fixed delay
   - Use the new `shiftloaded.png`
   - Adjust confidence if needed
   - Test thoroughly

---

## Testing the Fix

### Manual Test (Daytime)
1. Click "Test Shift App Reset" button
2. Watch the console output
3. Look for line: `[Reset] Found indicator: shiftloaded.png` or `[Reset] Assuming Shifts loaded after 15 second delay`
4. Check if status changes to "Teams Shifts app refreshed successfully"

### Automatic Test (Midnight)
1. Leave app running overnight
2. Check logs in the morning:
   ```powershell
   python check_midnight_logs.py
   ```
3. Look for success email in your inbox
4. Check if video `midnight_reset.mp4` was created

---

## Prevention

To prevent this from happening again:

1. **Create Multiple Backup Images**
   - Capture 3-4 different loaded indicators
   - Store them with descriptive names
   - Document what each one detects

2. **Lower Confidence Threshold**
   - Use 0.7 instead of 0.8
   - More tolerant of small UI changes

3. **Add Fallback Logic**
   - If primary detection fails, try alternatives
   - Use time-based fallback as last resort

4. **Monitor Detection Success**
   - Log when detection succeeds/fails
   - Alert if failure rate increases
   - Indicates Teams UI changed

---

## Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Midnight reset trigger | ? Working | Fires at midnight correctly |
| UI automation (click sequence) | ? Working | Teams refreshes successfully |
| Visual result | ? Working | You can see it work on screen |
| **Detection of completion** | ? BROKEN | Can't find `shiftloaded.png` |
| 5 AM resumption | ? Working | Schedules correctly |

**The ONLY problem is the detection step. Everything else works perfectly.**

---

## Next Steps

Run this command and tell me what it says:

```powershell
python diagnose_shiftloaded.py
```

Then we'll know exactly how to fix it!
