import os
import unittest
from unittest.mock import patch
from pathlib import Path

BASE = Path(__file__).resolve().parent
ASSETS = ["away_icon.png","shiftloaded.png","shifts_selected.png","shifts_unselected.png","dots.png"]

class TestMidnightAssets(unittest.TestCase):
    def test_assets_exist(self):
        missing=[n for n in ASSETS if not (BASE/n).is_file()]
        self.assertEqual(missing, [])

class TestMidnightContract(unittest.TestCase):
    def setUp(self):
        self.src=(BASE/"gui.py").read_text(encoding="utf-8",errors="replace")
    def test_methods(self):
        self.assertIn("def refresh_teams_shifts", self.src)
        self.assertIn("def trigger_shift_app_reset", self.src)

    def test_templates(self):
        self.assertIn("away_icon.png", self.src)
        self.assertIn("shiftloaded.png", self.src)
        self.assertNotIn("calendar_tab.png", self.src)
        self.assertIn("find_and_click_template", self.src)
        self.assertIn("confidence=0.7", self.src)
    def test_timer(self):
        self.assertIn("now.hour == 0", self.src)
        self.assertIn("_last_refresh_date", self.src)
    def test_unavailable(self):
        self.assertIn("unavailable", self.src)

class FakeVar:
    def __init__(self): self.values=[]
    def set(self,v): self.values.append(v)
    def get(self): return self.values[-1] if self.values else ""
class FakeApp:
    def __init__(self):
        self.scan_status_var=FakeVar(); self.timer_running=True; self.scanning_on=True; self._scanning=False; self.after_calls=[]; self.start_countdown_calls=0
        self._record_screen_video=lambda *a,**k: None
    def after(self, ms, cb): self.after_calls.append((ms,cb))
    def start_countdown(self): self.start_countdown_calls += 1

def bind_refresh():
    src=(BASE/"gui.py").read_text(encoding="utf-8",errors="replace").splitlines(True)
    s=next(i for i,l in enumerate(src) if l.startswith("    def refresh_teams_shifts"))
    e=next(j for j in range(s+1,len(src)) if src[j].startswith("    def ") or (src[j].startswith("def ") and not src[j].startswith(" ")))
    body="".join(src[s:e])
    ded="".join([ln[4:] if ln.startswith("    ") else ln for ln in body.splitlines(True)])
    ns={}
    exec("class H:\n" + "".join([("    "+x) if x.strip() else x for x in ded.splitlines(True)]), ns)
    return ns["H"].refresh_teams_shifts

class TestFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.refresh=staticmethod(bind_refresh())
    def setUp(self): self.app=FakeApp()
    def test_success(self):
        def fake(path, confidence=0.9, pause=0.25, screenshot=None):
            name=os.path.basename(path)
            return {"away_icon.png":(1,1),"shifts_unselected.png":(2,2),"shiftloaded.png":(3,3)}.get(name)
        with patch("time.sleep", return_value=None), patch("automation.find_and_click_template", side_effect=fake), patch("email_alert.send_email_alert", return_value=True) as em, patch("threading.Thread") as th:
            th.side_effect=lambda *a,**k: type("T",(),{"start":lambda self: None})()
            self.refresh(self.app)
        self.assertFalse(self.app.timer_running)
        self.assertIn("refreshed successfully", " ".join(self.app.scan_status_var.values).lower())
        self.assertTrue(self.app.after_calls)
        em.assert_called()
        self.app.after_calls[0][1]()
        self.assertTrue(self.app.timer_running)
        self.assertEqual(self.app.start_countdown_calls, 1)

    def test_failure(self):
        with patch("time.sleep", return_value=None), patch("automation.find_and_click_template", return_value=None), patch("email_alert.send_email_alert", return_value=True) as em, patch("threading.Thread") as th:
            th.side_effect=lambda *a,**k: type("T",(),{"start":lambda self: None})()
            self.refresh(self.app)
        self.assertIn("failed after 10 attempts", " ".join(self.app.scan_status_var.values).lower())
        self.assertTrue(em.called)
        self.assertFalse(self.app.timer_running)

if __name__ == "__main__":
    unittest.main(verbosity=2)

