#!/usr/bin/env python3

import sqlite3
from datetime import datetime

def debug_september_20():
    conn = sqlite3.connect('shifts.db')
    c = conn.cursor()
    
    print('=== ALL ENTRIES FOR 2025-09-20 ===')
    c.execute('SELECT * FROM shifts WHERE date = ?', ('2025-09-20',))
    entries = c.fetchall()
    
    for entry in entries:
        print(f'ID: {entry[0]}, Date: {entry[1]}, Type: {entry[2]}, Alerted: {entry[3]}, Count: {entry[4]}, Source: {entry[5]}, Created: {entry[6]}')
    
    print(f'\nTotal entries: {len(entries)}')
    
    # Check what the daily summary logic does
    print('\n=== DAILY SUMMARY LOGIC CHECK ===')
    c.execute("SELECT date, shift_type, count FROM shifts WHERE date >= date('now') ORDER BY date, shift_type")
    future_shifts = c.fetchall()
    
    sept20_shifts = [shift for shift in future_shifts if shift[0] == '2025-09-20']
    for shift in sept20_shifts:
        print(f'Date: {shift[0]}, Type: {shift[1]}, Count: {shift[2]}')
    
    # Check availability for this date
    print('\n=== AVAILABILITY CHECK ===')
    c.execute('SELECT * FROM availability WHERE date = ?', ('2025-09-20',))
    availability = c.fetchall()
    if availability:
        for avail in availability:
            print(f'Date: {avail[1]}, Available: True')
    else:
        print('No availability set for 2025-09-20')
    
    # Analyze the problem
    print('\n=== PROBLEM ANALYSIS ===')
    open_shifts = [e for e in entries if e[2] == 'open']
    booked_shifts = [e for e in entries if e[2] == 'booked']
    
    print(f'Open shift entries: {len(open_shifts)}')
    print(f'Booked shift entries: {len(booked_shifts)}')
    
    if open_shifts and booked_shifts:
        print('ISSUE: Both open and booked shifts exist for same date!')
        print('This should not happen - you cannot have an open shift on a day you are booked.')
    
    conn.close()

if __name__ == "__main__":
    debug_september_20()
