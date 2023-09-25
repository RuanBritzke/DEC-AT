import tkinter as tk
from customs import widgets as wd

root = tk.Tk()
root.geometry("400x225")
root.title("Label-to-Entry Ratio Example")

# Labels and Entries
labels_text = [("Label 1 is a large text so it may have to wrap:", 'float'), ("Label 2:", 'flaot'), ("Label 3:", None)]
wd.Formulary(root, queries=labels_text).pack(fill='x', expand=True)

root.mainloop()