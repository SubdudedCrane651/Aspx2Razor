import tkinter as tk
from tkinter import filedialog, messagebox
import os
import re
from bs4 import BeautifulSoup

# ASP.NET controls mapped to plain HTML
element_mapping = {
    "asp:Button": "button",
    "asp:TextBox": "input",
    "asp:Label": "span",
    "asp:DropDownList": "select",
    "asp:CheckBox": "input",
    "asp:RadioButton": "input",
    "asp:HyperLink": "a",
    "asp:Image": "img"
}

def parse_aspx(path):
    """Reads ASPX file, removes ASP controls, runat attributes, and comments."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        # Remove ASP-style comments
        raw = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)

        # Remove ASPX directives (e.g., <%@ Page ... %>)
        raw = re.sub(r"<%@.*%>\n?", "", raw)

        soup = BeautifulSoup(raw, "html.parser")

        # Convert ASP.NET controls to plain HTML
        for asp_tag, html_tag in element_mapping.items():
            for elem in soup.find_all(asp_tag.lower()):
                elem.name = html_tag

        # Remove runat="server" attributes from all tags
        for elem in soup.find_all():
            if "runat" in elem.attrs:
                del elem.attrs["runat"]

        # Remove entire <form runat="server"> elements
        for form in soup.find_all("form"):
            if form.get("runat", "").lower() == "server":
                form.decompose()

        return soup
    except Exception as e:
        messagebox.showerror("Error", f"Failed to parse ASPX file: {e}")
        return None

def save_razor_file(content, out_path):
    """Saves the converted content into a .cshtml file."""
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(str(content))
    except Exception as e:
        messagebox.showerror("Error", f"Could not save file: {e}")

def open_file():
    """Opens a file dialog for selecting ASPX files and converts them to Razor syntax."""
    files = filedialog.askopenfilenames(filetypes=[("ASPX Files", "*.aspx")])
    for asp_path in files:
        soup = parse_aspx(asp_path)
        if not soup:
            continue
        folder = os.path.dirname(asp_path)
        base = os.path.splitext(os.path.basename(asp_path))[0]
        cap_base = base[0].upper() + base[1:]
        razor_path = os.path.join(folder, cap_base + ".cshtml")
        save_razor_file(soup, razor_path)
    messagebox.showinfo("Done", "All selected files converted!")

# GUI Setup
root = tk.Tk()
root.title("ASPX to Razor Converter")
frame = tk.Frame(root, padx=20, pady=20)
frame.pack()
tk.Label(frame, text="Select ASPX file(s) to convert:").pack(pady=(0,5))
tk.Button(frame, text="Convert to Razor", command=open_file).pack()
root.mainloop()