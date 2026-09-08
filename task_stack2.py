#!/usr/bin/env python3

from django import setup
setup()


if True:
    from tkinter import Tk


class TaskStackApp2:

    def __init__(self, root):
        self.root = root




def main():
    root = Tk()
    TaskStackApp2(root)
    root.mainloop()

if __name__ == "__main__":
    main()