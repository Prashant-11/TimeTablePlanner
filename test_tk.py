import tkinter as tk
from tkinter import ttk, messagebox
import sys

def main():
    print("Creating root window...")
    root = tk.Tk()
    root.title("Test Window")
    
    print("Creating label...")
    label = ttk.Label(root, text="Test")
    label.pack()
    
    print("Starting mainloop...")
    root.mainloop()

if __name__ == "__main__":
    try:
        print("Starting test app...")
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
