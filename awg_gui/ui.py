"""Main Tkinter application window and settings dialog."""

import queue
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import autostart, settings
from .config_manager import ConfigEntry
from .controller import CONNECTED, CONNECTING, DISCONNECTED, ERROR, Controller
from .i18n import S
from .vpn_service import (
    VpnError,
    disable_autostart,
    enable_autostart,
    is_active,
    is_autostart_enabled,
    restore_original,
)

_INDICATOR_COLORS: dict[str, str] = {
    DISCONNECTED: "gray",
    CONNECTING: "orange",
    CONNECTED: "green",
    ERROR: "red",
}


class App:
    """Main application window."""

    def __init__(self) -> None:
        self._cfg = settings.load()
        self._active_entry: ConfigEntry | None = None

        self._root = tk.Tk()
        self._root.title(S["title"])
        self._root.resizable(False, False)

        self._queue: queue.Queue = queue.Queue()
        self._ctrl = Controller(Path(self._cfg["config_dir"]), self._queue)

        self._status_var = tk.StringVar(value=S["status_disconnected"])
        self._internet_var = tk.StringVar(value="")

        self._build_ui()
        self._load_configs()
        self._sync_initial_status()
        self._ctrl.start_network_checker()
        self._root.after(100, self._drain_queue)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        main = ttk.Frame(self._root, padding=8)
        main.grid(row=0, column=0, sticky="nsew")

        # Treeview + scrollbar
        tree_frame = ttk.Frame(main)
        tree_frame.grid(row=0, column=0, columnspan=4, sticky="nsew")

        self._tree = ttk.Treeview(tree_frame, columns=("server",), height=16, selectmode="browse")
        self._tree.heading("#0", text=S["col_country"])
        self._tree.heading("server", text=S["col_server"])
        self._tree.column("#0", width=300)
        self._tree.column("server", width=80, anchor="center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tree_frame.columnconfigure(0, weight=1)

        # Action buttons
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        self._btn_connect = ttk.Button(btn_frame, text=S["btn_connect"], command=self._on_connect)
        self._btn_switch = ttk.Button(btn_frame, text=S["btn_switch"], command=self._on_connect)
        self._btn_disconnect = ttk.Button(
            btn_frame, text=S["btn_disconnect"], command=self._on_disconnect
        )
        settings_btn = ttk.Button(btn_frame, text=S["btn_settings"], command=self._open_settings)

        self._btn_connect.pack(side="left", padx=(0, 4))
        self._btn_switch.pack(side="left", padx=(0, 4))
        self._btn_disconnect.pack(side="left", padx=(0, 4))
        settings_btn.pack(side="right")

        # Status bar
        status_frame = ttk.Frame(main, relief="sunken")
        status_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        self._indicator = tk.Label(status_frame, text="●", fg="gray", font=("", 14))
        self._indicator.pack(side="left", padx=(4, 2), pady=2)
        ttk.Label(status_frame, textvariable=self._status_var).pack(side="left")
        ttk.Label(status_frame, textvariable=self._internet_var).pack(side="right", padx=8)

    # ── config list ───────────────────────────────────────────────────────────

    def _load_configs(self) -> None:
        self._entries: list[ConfigEntry] = self._ctrl.load_configs()
        self._populate_tree()

    def _populate_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        country_nodes: dict[str, str] = {}
        for idx, entry in enumerate(self._entries):
            if entry.country not in country_nodes:
                nid = self._tree.insert("", "end", text=entry.country, open=True)
                country_nodes[entry.country] = nid
            self._tree.insert(
                country_nodes[entry.country],
                "end",
                text=entry.city or entry.country,
                values=(entry.server_id,),
                iid=f"e{idx}",
            )

    def _selected_entry(self) -> ConfigEntry | None:
        sel = self._tree.selection()
        if not sel or not sel[0].startswith("e"):
            return None
        idx = int(sel[0][1:])
        return self._entries[idx] if 0 <= idx < len(self._entries) else None

    # ── button handlers ───────────────────────────────────────────────────────

    def _on_connect(self) -> None:
        entry = self._selected_entry()
        if not entry:
            messagebox.showwarning(S["dlg_error"], S["err_no_selection"])
            return
        self._set_buttons_enabled(False)
        self._ctrl.connect(entry)

    def _on_disconnect(self) -> None:
        self._set_buttons_enabled(False)
        self._ctrl.disconnect()

    # ── queue drain ───────────────────────────────────────────────────────────

    def _drain_queue(self) -> None:
        while True:
            try:
                event, data = self._queue.get_nowait()
                self._handle_event(event, data)
            except queue.Empty:
                break
        self._root.after(100, self._drain_queue)

    def _handle_event(self, event: str, data: object) -> None:
        if event == "status":
            self._update_status(str(data))
        elif event == "active_entry":
            self._active_entry = data  # type: ignore[assignment]
        elif event == "error":
            messagebox.showerror(S["dlg_error"], str(data))
            self._set_buttons_enabled(True)
        elif event == "internet":
            self._internet_var.set(S["internet_ok"] if data else S["internet_no"])

    # ── status display ────────────────────────────────────────────────────────

    def _update_status(self, status: str) -> None:
        color = _INDICATOR_COLORS.get(status, "gray")
        self._indicator.configure(fg=color)

        if status == CONNECTED and self._active_entry:
            text = f"{S['status_connected']}: {self._active_entry.display_name}"
        elif status == CONNECTING:
            text = S["status_connecting"]
        elif status == ERROR:
            text = S["status_error"]
        else:
            text = S["status_disconnected"]

        self._status_var.set(text)

        if status in (CONNECTED, DISCONNECTED, ERROR):
            self._set_buttons_enabled(True)

    def _sync_initial_status(self) -> None:
        self._update_status(CONNECTED if is_active() else DISCONNECTED)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self._btn_connect.configure(state=state)
        self._btn_switch.configure(state=state)
        self._btn_disconnect.configure(state=state)

    # ── settings dialog ───────────────────────────────────────────────────────

    def _open_settings(self) -> None:
        SettingsDialog(self._root, self._cfg, self._apply_settings)

    def _apply_settings(self, new_cfg: dict) -> None:
        self._cfg = new_cfg
        settings.save(new_cfg)
        self._ctrl._config_dir = Path(new_cfg["config_dir"])
        self._load_configs()

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def _on_close(self) -> None:
        self._ctrl.stop_network_checker()
        self._root.destroy()

    def run(self) -> None:
        self._root.mainloop()


class SettingsDialog:
    """Modal settings window."""

    def __init__(self, parent: tk.Tk, cfg: dict, on_save: object) -> None:
        self._cfg = dict(cfg)
        self._on_save = on_save

        win = tk.Toplevel(parent)
        win.title(S["settings_title"])
        win.resizable(False, False)
        win.grab_set()
        self._win = win

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)

        # Config directory
        ttk.Label(frame, text=S["settings_config_dir"]).grid(row=0, column=0, sticky="w")
        self._dir_var = tk.StringVar(value=cfg["config_dir"])
        ttk.Entry(frame, textvariable=self._dir_var, width=42).grid(row=0, column=1, padx=4)
        ttk.Button(frame, text="…", width=3, command=self._browse).grid(row=0, column=2)

        # VPN autostart checkbox
        try:
            vpn_enabled = is_autostart_enabled()
        except Exception:
            vpn_enabled = False
        self._vpn_auto = tk.BooleanVar(value=vpn_enabled)
        ttk.Checkbutton(frame, text=S["settings_autostart_vpn"], variable=self._vpn_auto).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(10, 0)
        )

        # App autostart checkbox
        self._app_auto = tk.BooleanVar(value=autostart.is_enabled())
        ttk.Checkbutton(frame, text=S["settings_autostart_app"], variable=self._app_auto).grid(
            row=2, column=0, columnspan=3, sticky="w"
        )

        # Restore button
        ttk.Button(frame, text=S["settings_restore"], command=self._restore).grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(10, 0)
        )

        # Save / Cancel
        btn_row = ttk.Frame(frame)
        btn_row.grid(row=4, column=0, columnspan=3, sticky="e", pady=(14, 0))
        ttk.Button(btn_row, text=S["settings_save"], command=self._save).pack(side="left", padx=4)
        ttk.Button(btn_row, text=S["settings_cancel"], command=win.destroy).pack(side="left")

    def _browse(self) -> None:
        d = filedialog.askdirectory(initialdir=self._dir_var.get())
        if d:
            self._dir_var.set(d)

    def _restore(self) -> None:
        try:
            restore_original()
            messagebox.showinfo(S["dlg_info"], S["restore_ok"])
        except VpnError as exc:
            messagebox.showerror(S["dlg_error"], str(exc))

    def _save(self) -> None:
        try:
            if self._vpn_auto.get():
                enable_autostart()
            else:
                disable_autostart()
        except VpnError as exc:
            messagebox.showerror(S["dlg_error"], str(exc))
            return

        if self._app_auto.get():
            autostart.enable()
        else:
            autostart.disable()

        cfg = {**self._cfg, "config_dir": self._dir_var.get()}
        self._on_save(cfg)
        self._win.destroy()
