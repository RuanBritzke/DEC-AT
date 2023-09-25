from pandastable import *

class MyCustomToolBar(Frame):
    def __init__(self, parent=None, parentapp=None):
        Frame.__init__(self, parent, width=600, height=40)
        self.parentframe = parent
        self.paretnapp = parentapp
        img = images.save_proj()
        addButton(self, "Save", self.paretnapp.save, img, "save")
        return

class MyCustonPandasTable(Table):
    def __init__(self, *args, **kwargs):
        Table.__init__(self, *args, **kwargs)

    def show(self, callback=None):
        """Adds column header and scrollbars and combines them with
        the current table adding all to the master frame provided in constructor.
        Table is then redrawn."""

        # Add the table and header to the frame
        self.rowheader = RowHeader(self.parentframe, self)
        self.colheader = ColumnHeader(self.parentframe, self, bg="gray25")
        self.rowindexheader = IndexHeader(self.parentframe, self, bg="gray75")
        self.Yscrollbar = AutoScrollbar(
            self.parentframe, orient=VERTICAL, command=self.set_yviews
        )
        self.Yscrollbar.grid(row=1, column=2, rowspan=1, sticky="news", pady=0, ipady=0)
        self.Xscrollbar = AutoScrollbar(
            self.parentframe, orient=HORIZONTAL, command=self.set_xviews
        )
        self.Xscrollbar.grid(row=2, column=1, columnspan=1, sticky="news")
        self["xscrollcommand"] = self.Xscrollbar.set
        self["yscrollcommand"] = self.Yscrollbar.set
        self.colheader["xscrollcommand"] = self.Xscrollbar.set
        self.rowheader["yscrollcommand"] = self.Yscrollbar.set
        self.parentframe.rowconfigure(1, weight=1)
        self.parentframe.columnconfigure(1, weight=1)

        self.rowindexheader.grid(row=0, column=0, rowspan=1, sticky="news")
        self.colheader.grid(row=0, column=1, rowspan=1, sticky="news")
        self.rowheader.grid(row=1, column=0, rowspan=1, sticky="news")
        self.grid(row=1, column=1, rowspan=1, sticky="news", pady=0, ipady=0)

        self.adjustColumnWidths()
        # bind redraw to resize, may trigger redraws when widgets added
        self.parentframe.bind("<Configure>", self.resized)  # self.redrawVisible)
        self.colheader.xview("moveto", 0)
        self.xview("moveto", 0)
        if self.showtoolbar == True:
            self.toolbar = MyCustomToolBar(self.parentframe, self)
            self.toolbar.grid(row=0, column=3, rowspan=2, sticky="news")
        if self.showstatusbar == True:
            self.statusbar = statusBar(self.parentframe, self)
            self.statusbar.grid(row=3, column=0, columnspan=2, sticky="ew")
        # self.redraw(callback=callback)
        self.currwidth = self.parentframe.winfo_width()
        self.currheight = self.parentframe.winfo_height()
        if hasattr(self, "pf"):
            self.pf.updateData()
        return