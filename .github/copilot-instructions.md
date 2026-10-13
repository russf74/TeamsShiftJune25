# Copilot Instructions

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## General Guidelines
- This project is a professional Windows desktop application in Python using Tkinter for GUI, SQLite for database, OpenCV and pytesseract for OCR/image processing, pyautogui/pywinauto for automation, and Gmail for email alerts. Please generate robust, production-quality code with clear separation of concerns and error handling.
- Never run terminal commands without a hard timeout. Prefer short, deterministic checks; do not leave long-running or unbounded scripts that can freeze the session.

## Shift Detection Rules
- Do not infer whether a shift is open from tile color. Any tile in rows above the user's own row can be an available/open shift regardless of color.
- In the user's own row, a grey tile beginning with 'A' means the user is available, not that an open shift exists.
