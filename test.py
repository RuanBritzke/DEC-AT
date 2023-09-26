import tkinter as tk
from customs import widgets as wd

root = tk.Tk()
root.geometry("400x225")
root.title("Label-to-Entry Ratio Example")


def button_clicked():
    print(formulary.get_entry_values())


# Labels and Entries
labels_text = [
    ("Label 1 is a large text so it may have to wrap:", "key1", "float"),
    ("Label 2:", "key2", "flaot"),
    ("Label 3:", "key3", None),
]
formulary = wd.Formulary(root, queries=labels_text)
formulary.pack(side="top", fill="both", expand=True)
button = tk.Button(root, text="Click Me", command=button_clicked)
button.pack(anchor="se")

root.mainloop()
