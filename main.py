import tkinter as tk
from tkinter import filedialog, messagebox
import os
import re
from bs4 import BeautifulSoup

# Mapping ASP.NET controls to standard HTML for Razor
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
    """Reads ASPX file, removes directives, ASP comments, and extracts Razor-compatible elements."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        # Remove ASPX directives (e.g., <%@ Page ... %>) and ASP-style comments
        raw = re.sub(r"<%@.*%>\n?", "", raw)
        raw = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)

        soup = BeautifulSoup(raw, "html.parser")

        # Convert ASP.NET controls to standard HTML equivalents
        for asp_tag, html_tag in element_mapping.items():
            for elem in soup.find_all(asp_tag.lower()):
                elem.name = html_tag

        # Remove runat="server" attributes
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

def parse_cs(path):
    """Extracts properties and event handlers from .aspx.cs for Razor integration."""
    events, props = {}, []
    if not os.path.exists(path):
        return events, props
    try:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()

        # Extract model properties
        props = [f"public {typ} {name} {{ get; set; }}" for typ, name in re.findall(r"public\s+(\w+)\s+(\w+);", code)]

        # Extract event handler methods
        events = {evt: f"public IActionResult {evt}() {{ return View(); }}" for evt in re.findall(r"protected\s+void\s+(\w+)\(object sender,\s*EventArgs e\)", code)}

    except Exception as e:
        messagebox.showerror("Error", f"Error parsing code-behind: {e}")

    return events, props

def merge_razor_code(soup, events, props):
    """Generates Razor-compatible @code block with extracted properties and event handlers."""
    razor_code = "\n@functions {\n"

    # Add model properties
    if props:
        razor_code += "\n    " + "\n    ".join(props) + "\n"

    # Add event handlers
    if events:
        razor_code += "\n    " + "\n    ".join(events.values()) + "\n"

    razor_code += "}\n"

    return str(soup) + razor_code

def save_razor_file(content, out_path):
    """Saves the converted Razor content into a .cshtml file."""
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        messagebox.showerror("Error", f"Could not save file: {e}")

def open_file():
    """Opens a file dialog, selects ASPX files, extracts .aspx.cs logic, and converts them to Razor syntax."""
    files = filedialog.askopenfilenames(filetypes=[("ASPX Files", "*.aspx")])
    for asp_path in files:
        cs_path = asp_path.replace(".aspx", ".cs")

        # Parse ASPX file and code-behind file
        soup = parse_aspx(asp_path)
        events, props = parse_cs(cs_path)

        if not soup:
            continue

        # Merge Razor logic
        razor_content = merge_razor_code(soup, events, props)

        # Save the Razor file
        folder = os.path.dirname(asp_path)
        base = os.path.splitext(os.path.basename(asp_path))[0]
        cap_base = base[0].upper() + base[1:]
        razor_path = os.path.join(folder, cap_base + ".cshtml")

        save_razor_file(razor_content, razor_path)

    messagebox.showinfo("Done", "All selected files converted!")

# GUI Setup
root = tk.Tk()
root.title("ASPX to Razor Converter")
frame = tk.Frame(root, padx=20, pady=20)
frame.pack()
tk.Label(frame, text="Select ASPX file(s) to convert:").pack(pady=(0,5))
tk.Button(frame, text="Convert to Razor", command=open_file).pack()
root.mainloop()