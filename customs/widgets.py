import re
import tkinter as tk
from tkinter import ttk
from typing import Literal

class Formulary:

    def __init__(self, master, queries: list[tuple[str, Literal['any', 'float']]]) -> None:
        self.container = tk.Frame(master, background='gray')
        self.container.columnconfigure(0, weight=4, minsize=80)
        self.container.columnconfigure(1, weight=1, minsize=40)
        self.container.bind("<Configure>", self.on_container_configure)

        self.values = dict()
        self.labels = []
        self.entries = []
        for i, (text, type_) in enumerate(queries):
            label = tk.Label(self.container, text = text, background='white', anchor='w', justify='left')
            self.labels.append(label)
            if type_ is None:
                entry = ttk.Entry(self.container)
            else:
                entry = FloatEntry(self.container)
            self.entries.append(label)
            label.grid(row = i, column=0, sticky='nsew', padx=5, pady=5)
            entry.grid(row = i, column=1, sticky="nsew", padx=(0,5), pady=5)

    def on_container_configure(self, event):
        self.container.after(1, self.update_wraplengths)

    def update_wraplengths(self):
        label : tk.Label
        entry : ttk.Entry
        for label in self.labels:
            label.config(wraplength = label.winfo_width())
            
    def grid(self,
                *,
                column: int, 
                row : int, 
                ipadx:  None | int = 0,
                ipady: None | int = 0,
                padx: None | int = 0,
                pady: None | int = 0,
                sticky: None | str | tuple[str, str]= "nsew",
                in_ : None | tk.Misc = None,
                **kwargs) -> None:

        self.container.grid(
            column = column,
            row = row,
            ipadx = ipadx,
            ipady = ipady,
            padx = padx, 
            pady = pady,
            sticky = sticky[1],
            in_ = in_,
            **kwargs)

    def pack(self,
            *,
            after : None | tk.Misc = None,
            anchor : None | str = None,
            before : None | str = None,
            expand : bool = False,
            fill: Literal['none', 'x', 'y', 'both'] = 'none',
            side: Literal['left', 'right', 'top', 'botton'] = 'left', 
            ipadx:  None | int = 0,
            ipady: None | int = 0,
            padx: None | int | tuple[int, int] = 0,
            pady: None | int | tuple[int, int] = 0,
            in_ : None | tk.Misc = None,
            **kwargs):
        
        self.container.pack(
            after=after,
            anchor=anchor, 
            before=before,
            expand=expand,
            fill=fill,
            side=side,
            ipadx=ipadx,
            ipady=ipady,
            padx=padx,
            pady=pady,
            in_ = in_
        )

class FloatEntry(ttk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, validate="key", **kwargs)
        vcmd = (self.register(self.on_validate), "%P")
        self.config(validatecommand= vcmd)

    def on_validate(self, P):
        return self.validate(P)
    
    def validate(self, string):
        regex = re.compile(r"(\+|\-)?[0-9,]*$")
        result = regex.match(string)
        return (string == ""
                or (string.count('+') <= 1
                    and string.count('-') <= 1
                    and string.count(',') <= 1
                    and result is not None
                    and result.group(0) != ""))
    
    @property
    def get_entry(self):
        return float(self.get().replace(",", "."))
    
class CustomNotebook(ttk.Notebook):
    """A ttk Notebook with close buttons on each tab"""

    __initialized = False

    def __init__(self, *args, **kwargs):
        if not self.__initialized:
            self.__initialize_custom_style()
            self.__inititialized = True

        kwargs["style"] = "CustomNotebook"
        ttk.Notebook.__init__(self, *args, **kwargs)

        self._active = None

        self.bind("<ButtonPress-1>", self.on_close_press, True)
        self.bind("<ButtonRelease-1>", self.on_close_release)

    def on_close_press(self, event):
        """Called when the button is pressed over the close button"""

        element = self.identify(event.x, event.y)

        if "close" in element:
            index = self.index("@%d,%d" % (event.x, event.y))
            self.state(["pressed"])
            self._active = index
            return "break"

    def on_close_release(self, event):
        """Called when the button is released"""
        if not self.instate(["pressed"]):
            return

        element = self.identify(event.x, event.y)
        if "close" not in element:
            # user moved the mouse off of the close button
            return

        index = self.index("@%d,%d" % (event.x, event.y))

        if self._active == index:
            closed_tab_text = self.tab(index, "text")
            self.forget(index)
            self.event_generate("<<NotebookTabClosed>>", data=closed_tab_text)

        self.state(["!pressed"])
        self._active = None

    def __initialize_custom_style(self):
        style = ttk.Style()
        self.images = (
            tk.PhotoImage(
                "img_close",
                data="""
                R0lGODlhCAAIAMIBAAAAADs7O4+Pj9nZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
                """,
            ),
            tk.PhotoImage(
                "img_closeactive",
                data="""
                R0lGODlhCAAIAMIEAAAAAP/SAP/bNNnZ2cbGxsbGxsbGxsbGxiH5BAEKAAQALAAA
                AAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU5kEJADs=
                """,
            ),
            tk.PhotoImage(
                "img_closepressed",
                data="""
                R0lGODlhCAAIAMIEAAAAAOUqKv9mZtnZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
            """,
            ),
        )

        style.element_create(
            "close",
            "image",
            "img_close",
            ("active", "pressed", "!disabled", "img_closepressed"),
            ("active", "!disabled", "img_closeactive"),
            border=8,
            sticky="",
        )
        style.layout("CustomNotebook", [("CustomNotebook.client", {"sticky": "nswe"})])
        style.layout(
            "CustomNotebook.Tab",
            [
                (
                    "CustomNotebook.tab",
                    {
                        "sticky": "nswe",
                        "children": [
                            (
                                "CustomNotebook.padding",
                                {
                                    "side": "top",
                                    "sticky": "nswe",
                                    "children": [
                                        (
                                            "CustomNotebook.focus",
                                            {
                                                "side": "top",
                                                "sticky": "nswe",
                                                "children": [
                                                    (
                                                        "CustomNotebook.label",
                                                        {"side": "left", "sticky": ""},
                                                    ),
                                                    (
                                                        "CustomNotebook.close",
                                                        {"side": "left", "sticky": ""},
                                                    ),
                                                ],
                                            },
                                        )
                                    ],
                                },
                            )
                        ],
                    },
                )
            ],
        )