"""
gui_client.py — SHA-256 Dogrulama Sistemi
Modern UI: CustomTkinter tabanli, navy-dark tema
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading, subprocess, sys, os, time, datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Tema ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Renk paleti (navy-dark) ───────────────────────────────────────────────────
C = {
    "bg":        "#0f1623",   # ana zemin
    "sidebar":   "#141c2e",   # sol panel
    "card":      "#1a2236",   # kart zemini
    "card2":     "#202944",   # vurgu kart
    "border":    "#263354",   # ince kenarlik
    "accent":    "#3b82f6",   # mavi
    "accent2":   "#8b5cf6",   # mor
    "green":     "#22c55e",
    "red":       "#ef4444",
    "yellow":    "#f59e0b",
    "t1":        "#e2e8f0",   # birincil yazi
    "t2":        "#94a3b8",   # ikincil yazi
    "t3":        "#475569",   # soluk yazi
    "log_bg":    "#0d131f",   # log zemini
}

FONT       = "Segoe UI"
MONO_FONT  = "Consolas"


def ts():
    return datetime.datetime.now().strftime("%H:%M:%S")


# ══════════════════════════════════════════════════════════════════════════════
class Sidebar(ctk.CTkFrame):
    """Sol navigasyon cubugu."""

    NAV = [
        ("server", "Server",  "⚙"),
        ("news",   "Haber",   "📰"),
        ("audio",  "Ses",     "🎙"),
    ]

    def __init__(self, master, on_select, **kw):
        super().__init__(master, width=200, fg_color=C["sidebar"],
                         corner_radius=0, **kw)
        self.pack_propagate(False)
        self.on_select = on_select
        self._btns = {}
        self._build()

    def _build(self):
        # Logo
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(24, 4))

        ctk.CTkLabel(logo_frame, text="HashVerify",
                     font=(FONT, 22, "bold"),
                     text_color=C["accent"]).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="Haber & Ses Dogrulama",
                     font=(FONT, 10),
                     text_color=C["t3"]).pack(anchor="w")

        # Ayirici
        ctk.CTkFrame(self, height=1, fg_color=C["border"]).pack(
            fill="x", padx=16, pady=16)

        # Nav butonlari
        for key, label, icon in self.NAV:
            btn = ctk.CTkButton(
                self, text=f"  {icon}   {label}",
                font=(FONT, 13),
                anchor="w",
                fg_color="transparent",
                text_color=C["t2"],
                hover_color=C["card2"],
                corner_radius=10,
                height=42,
                command=lambda k=key: self.on_select(k),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self._btns[key] = btn

        # Server durumu (alt)
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=16, pady=20)

        ctk.CTkFrame(self, height=1, fg_color=C["border"]).pack(
            side="bottom", fill="x", padx=16, pady=(0, 0))

        self.dot = ctk.CTkLabel(bottom, text="●  Server Kapali",
                                font=(FONT, 11),
                                text_color=C["red"])
        self.dot.pack(anchor="w")

    def highlight(self, active_key):
        for key, btn in self._btns.items():
            if key == active_key:
                btn.configure(fg_color=C["card2"], text_color=C["accent"])
            else:
                btn.configure(fg_color="transparent", text_color=C["t2"])

    def set_server_status(self, running: bool):
        if running:
            self.dot.configure(text="●  Server Aktif", text_color=C["green"])
        else:
            self.dot.configure(text="●  Server Kapali", text_color=C["red"])


# ══════════════════════════════════════════════════════════════════════════════
class LogBox(ctk.CTkFrame):
    """Renk kodlu, scroll'lu log bileseni."""

    TAGS = {
        "ok":   C["green"],
        "err":  C["red"],
        "warn": C["yellow"],
        "info": C["accent"],
        "ts":   C["t3"],
        "sep":  C["border"],
        "dim":  C["t3"],
    }

    def __init__(self, master, height=10, **kw):
        super().__init__(master, fg_color=C["log_bg"],
                         corner_radius=10, border_width=1,
                         border_color=C["border"], **kw)

        self._txt = tk.Text(
            self, bg=C["log_bg"], fg=C["t1"],
            font=(MONO_FONT, 10), relief="flat",
            height=height, padx=12, pady=10,
            wrap="word", bd=0,
            insertbackground=C["accent"],
            selectbackground=C["card2"],
        )
        self._txt.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)

        sb = ctk.CTkScrollbar(self, command=self._txt.yview)
        sb.pack(side="right", fill="y", padx=(0, 4), pady=4)
        self._txt.configure(yscrollcommand=sb.set)

        for tag, color in self.TAGS.items():
            self._txt.tag_config(tag, foreground=color)
        self._txt.tag_config("bold", font=(MONO_FONT, 10, "bold"))

    def write(self, text, tag=""):
        def _w():
            self._txt.insert("end", f"[{ts()}] ", "ts")
            self._txt.insert("end", text + "\n", tag)
            self._txt.see("end")
        self._txt.after(0, _w)

    def write_raw(self, text):
        """Subprocess ciktisini akillica renklendir."""
        def _w():
            upper = text.upper()
            if any(k in upper for k in ("[OK]", "BASARILI", "ENROLLED", "SAME")):
                tag = "ok"
            elif any(k in upper for k in ("[HATA]", "BASARISIZ", "ERROR", "FARKLI", "FAIL")):
                tag = "err"
            elif any(k in upper for k in ("[WARN]", "UYARI", "ZATEN")):
                tag = "warn"
            elif any(k in upper for k in ("[INFO]", "[DEBUG]", "HASH", "BASLATILIYOR")):
                tag = "info"
            elif "===" in text or "---" in text:
                tag = "sep"
            else:
                tag = "dim"
            self._txt.insert("end", text if text.endswith("\n") else text + "\n", tag)
            self._txt.see("end")
        self._txt.after(0, _w)

    def separator(self):
        self._txt.after(0, lambda: (
            self._txt.insert("end", "  " + "─" * 48 + "\n", "sep"),
            self._txt.see("end")
        ))

    def clear(self):
        self._txt.delete("1.0", "end")


# ══════════════════════════════════════════════════════════════════════════════
def _section_label(parent, text):
    ctk.CTkLabel(parent, text=text, font=(FONT, 11, "bold"),
                 text_color=C["t3"]).pack(anchor="w", pady=(12, 4))


def _accent_line(parent):
    ctk.CTkFrame(parent, height=2, fg_color=C["accent"],
                 corner_radius=1).pack(fill="x", pady=(0, 16))


def _card(parent, **kw):
    return ctk.CTkFrame(parent, fg_color=C["card"],
                        corner_radius=14, **kw)


def _primary_btn(parent, text, cmd, color=None, w=180):
    color = color or C["accent"]
    return ctk.CTkButton(
        parent, text=text, command=cmd,
        font=(FONT, 12, "bold"),
        fg_color=color, hover_color=_darken(color),
        corner_radius=10, height=38, width=w,
        text_color="#ffffff",
    )


def _ghost_btn(parent, text, cmd):
    return ctk.CTkButton(
        parent, text=text, command=cmd,
        font=(FONT, 11),
        fg_color="transparent",
        border_width=1, border_color=C["border"],
        text_color=C["t2"],
        hover_color=C["card2"],
        corner_radius=8, height=32,
    )


def _darken(hex_color, amount=20):
    """Basit renk koyulastirma."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r, g, b = max(0, r - amount), max(0, g - amount), max(0, b - amount)
    return f"#{r:02x}{g:02x}{b:02x}"


# ══════════════════════════════════════════════════════════════════════════════
class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("HashVerify")
        self.geometry("1120x720")
        self.minsize(960, 620)
        self.configure(fg_color=C["bg"])

        self._server_proc = None
        self.news_enroll_file = None
        self.news_verify_file = None

        self._build()
        self._show("server")

    # ── Iskelet ───────────────────────────────────────────────────────────────
    def _build(self):
        self.sidebar = Sidebar(self, on_select=self._show)
        self.sidebar.pack(side="left", fill="y")

        self.main = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

        self._pages = {}
        builders = {
            "server": self._build_server,
            "news":   self._build_news,
            "audio":  self._build_audio,
        }
        for name, builder in builders.items():
            frame = ctk.CTkFrame(self.main, fg_color=C["bg"], corner_radius=0)
            builder(frame)
            self._pages[name] = frame

    def _show(self, name):
        for p in self._pages.values():
            p.pack_forget()
        self._pages[name].pack(fill="both", expand=True)
        self.sidebar.highlight(name)

    # ── Sayfa basligi ─────────────────────────────────────────────────────────
    def _page_title(self, parent, title, subtitle=""):
        h = ctk.CTkFrame(parent, fg_color="transparent")
        h.pack(fill="x", padx=28, pady=(24, 0))
        ctk.CTkLabel(h, text=title, font=(FONT, 24, "bold"),
                     text_color=C["t1"]).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(h, text=subtitle, font=(FONT, 11),
                         text_color=C["t2"]).pack(anchor="w", pady=(2, 0))
        _accent_line(ctk.CTkFrame(parent, fg_color="transparent",
                                  height=10).pack(fill="x", padx=28) or parent)

    # ══════════════════════════════════════════════════════════════════════════
    # SERVER SAYFASI
    # ══════════════════════════════════════════════════════════════════════════
    def _build_server(self, p):
        ctk.CTkLabel(p, text="Server Yonetimi", font=(FONT, 24, "bold"),
                     text_color=C["t1"]).pack(anchor="w", padx=28, pady=(24, 0))
        ctk.CTkLabel(p, text="Sunucuyu baslatip durdurun — istemci baglantilari burada yonetilir.",
                     font=(FONT, 11), text_color=C["t2"]).pack(anchor="w", padx=28)
        ctk.CTkFrame(p, height=2, fg_color=C["accent"]).pack(fill="x", padx=28, pady=12)

        # Kontroller
        ctrl = _card(p)
        ctrl.pack(fill="x", padx=28, pady=(0, 12))

        row = ctk.CTkFrame(ctrl, fg_color="transparent")
        row.pack(pady=16)
        _primary_btn(row, "▶  Serveri Baslat", self.start_server,
                     color=C["green"]).pack(side="left", padx=8)
        _primary_btn(row, "■  Serveri Durdur", self.stop_server,
                     color=C["red"]).pack(side="left", padx=8)

        # Log
        log_frame = _card(p)
        log_frame.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        lh = ctk.CTkFrame(log_frame, fg_color="transparent")
        lh.pack(fill="x", padx=8, pady=(10, 4))
        ctk.CTkLabel(lh, text="Sunucu Kayitlari", font=(FONT, 11, "bold"),
                     text_color=C["t2"]).pack(side="left")
        _ghost_btn(lh, "Temizle",
                   lambda: self.server_log.clear()).pack(side="right", padx=4)

        self.server_log = LogBox(log_frame, height=14)
        self.server_log.pack(fill="both", expand=True, padx=8, pady=(0, 10))

    # ══════════════════════════════════════════════════════════════════════════
    # HABER DOGRULAMA SAYFASI
    # ══════════════════════════════════════════════════════════════════════════
    def _build_news(self, p):
        ctk.CTkLabel(p, text="Haber Dogrulama", font=(FONT, 24, "bold"),
                     text_color=C["t1"]).pack(anchor="w", padx=28, pady=(24, 0))
        ctk.CTkLabel(p, text="HashVerify ile haberin SHA-256 hash'i karsilastiriliyor — manipulasyon aninda tespit edilir.",
                     font=(FONT, 11), text_color=C["t2"]).pack(anchor="w", padx=28)
        ctk.CTkFrame(p, height=2, fg_color=C["accent"]).pack(fill="x", padx=28, pady=12)

        # ── Iki kart yan yana ─────────────────────────────────────────────────
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=(0, 10))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        # — Kart 1: Enroll
        enroll_card = _card(row)
        enroll_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(enroll_card, text="ADIM 1 — Orijinal Kaydi",
                     font=(FONT, 13, "bold"), text_color=C["accent"]).pack(anchor="w", padx=14, pady=(14, 2))
        ctk.CTkLabel(enroll_card,
                     text="Referans alinacak orijinal haber\ndosyasini secin ve kaydedin.",
                     font=(FONT, 11), text_color=C["t2"], justify="left").pack(anchor="w", padx=14)

        ctk.CTkFrame(enroll_card, height=1,
                     fg_color=C["border"]).pack(fill="x", padx=14, pady=10)

        self.enroll_path_lbl = ctk.CTkLabel(
            enroll_card, text="Henuz dosya secilmedi.",
            font=(FONT, 10), text_color=C["t3"],
            wraplength=280, anchor="w"
        )
        self.enroll_path_lbl.pack(anchor="w", padx=14, pady=(0, 8))

        eb = ctk.CTkFrame(enroll_card, fg_color="transparent")
        eb.pack(pady=(0, 14))
        _primary_btn(eb, "Dosya Sec", self.load_news_enroll,
                     color=C["accent2"], w=130).pack(side="left", padx=4)
        _primary_btn(eb, "Kaydet (Enroll)", self.enroll_news,
                     color=C["accent"], w=148).pack(side="left", padx=4)

        # — Kart 2: Verify
        verify_card = _card(row)
        verify_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(verify_card, text="ADIM 2 — Dogrula",
                     font=(FONT, 13, "bold"), text_color=C["green"]).pack(anchor="w", padx=14, pady=(14, 2))
        ctk.CTkLabel(verify_card,
                     text="Dogrulugundan emin olmak istediginiz\nhaber dosyasini secin.",
                     font=(FONT, 11), text_color=C["t2"], justify="left").pack(anchor="w", padx=14)

        ctk.CTkFrame(verify_card, height=1,
                     fg_color=C["border"]).pack(fill="x", padx=14, pady=10)

        self.verify_path_lbl = ctk.CTkLabel(
            verify_card, text="Henuz dosya secilmedi.",
            font=(FONT, 10), text_color=C["t3"],
            wraplength=280, anchor="w"
        )
        self.verify_path_lbl.pack(anchor="w", padx=14, pady=(0, 8))

        vb = ctk.CTkFrame(verify_card, fg_color="transparent")
        vb.pack(pady=(0, 14))
        _primary_btn(vb, "Dosya Sec", self.load_news_verify,
                     color=C["accent2"], w=130).pack(side="left", padx=4)
        _primary_btn(vb, "Dogrula (Verify)", self.verify_news,
                     color=C["green"], w=148).pack(side="left", padx=4)

        # ── Sonuc banner ──────────────────────────────────────────────────────
        self.news_banner = ctk.CTkFrame(p, fg_color=C["card"], corner_radius=10,
                                        border_width=1, border_color=C["border"])
        self.news_banner.pack(fill="x", padx=28, pady=(0, 10))
        self.news_banner_lbl = ctk.CTkLabel(
            self.news_banner, text="Henuz bir dogrulama yapilmadi.",
            font=(FONT, 12, "bold"), text_color=C["t3"]
        )
        self.news_banner_lbl.pack(pady=10)

        # ── Log ───────────────────────────────────────────────────────────────
        log_frame = _card(p)
        log_frame.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        lh = ctk.CTkFrame(log_frame, fg_color="transparent")
        lh.pack(fill="x", padx=8, pady=(10, 4))
        ctk.CTkLabel(lh, text="Islem Kayitlari", font=(FONT, 11, "bold"),
                     text_color=C["t2"]).pack(side="left")
        _ghost_btn(lh, "Temizle",
                   lambda: self.news_log.clear()).pack(side="right", padx=4)

        self.news_log = LogBox(log_frame, height=8)
        self.news_log.pack(fill="both", expand=True, padx=8, pady=(0, 10))

    # ══════════════════════════════════════════════════════════════════════════
    # SES DOGRULAMA SAYFASI
    # ══════════════════════════════════════════════════════════════════════════
    def _build_audio(self, p):
        ctk.CTkLabel(p, text="Ses Dogrulama", font=(FONT, 24, "bold"),
                     text_color=C["t1"]).pack(anchor="w", padx=28, pady=(24, 0))
        ctk.CTkLabel(p, text="Sesinizi kaydedin ve hash karsilastirmasiyla kimliginizi dogrulayin.",
                     font=(FONT, 11), text_color=C["t2"]).pack(anchor="w", padx=28)
        ctk.CTkFrame(p, height=2, fg_color=C["accent"]).pack(fill="x", padx=28, pady=12)

        guide = _card(p)
        guide.pack(fill="x", padx=28, pady=(0, 12))

        steps = [
            ("1", "Ses Kaydi 1 (Enroll) butonuna basin", C["accent"]),
            ("2", "5 saniye boyunca konusun veya belirli bir kelimeyi soyleyin.", C["t2"]),
            ("3", "Ses Kaydi 2 (Verify) butonuna basin ve ayni seyi tekrarlayin.", C["t2"]),
            ("4", "Sistem hashlerinizi karsilastirir ve sonucu bildirir.", C["green"]),
        ]
        for num, txt, color in steps:
            r = ctk.CTkFrame(guide, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=3)
            ctk.CTkFrame(r, width=26, height=26, corner_radius=13,
                         fg_color=C["card2"]).pack(side="left")
            # Numara bazit Label olarak ortala
            ctk.CTkLabel(guide.winfo_children()[-1].winfo_children()[-1] if False else r,
                         text=num, font=(FONT, 11, "bold"),
                         text_color=C["accent"]).pack(side="left")
            ctk.CTkLabel(r, text=txt, font=(FONT, 11),
                         text_color=color).pack(side="left", padx=8)

        ctk.CTkFrame(guide, height=1, fg_color=C["border"]).pack(
            fill="x", padx=12, pady=10)

        btn_row = ctk.CTkFrame(guide, fg_color="transparent")
        btn_row.pack(pady=(4, 14))
        _primary_btn(btn_row, "🎙  Ses Kaydi 1  (Enroll)",
                     lambda: self.record_audio(1),
                     color=C["accent"], w=230).pack(side="left", padx=10)
        _primary_btn(btn_row, "🔍  Ses Kaydi 2  (Verify)",
                     lambda: self.record_audio(2),
                     color=C["green"], w=230).pack(side="left", padx=10)

        # Log
        log_frame = _card(p)
        log_frame.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        lh = ctk.CTkFrame(log_frame, fg_color="transparent")
        lh.pack(fill="x", padx=8, pady=(10, 4))
        ctk.CTkLabel(lh, text="Islem Kayitlari", font=(FONT, 11, "bold"),
                     text_color=C["t2"]).pack(side="left")
        _ghost_btn(lh, "Temizle",
                   lambda: self.audio_log.clear()).pack(side="right", padx=4)

        self.audio_log = LogBox(log_frame, height=14)
        self.audio_log.pack(fill="both", expand=True, padx=8, pady=(0, 10))

    # ══════════════════════════════════════════════════════════════════════════
    # SUBPROCESS
    # ══════════════════════════════════════════════════════════════════════════
    def _run(self, cmd_list, log: LogBox, store_server=False, on_finish=None):
        def task():
            try:
                proc = subprocess.Popen(
                    [sys.executable] + cmd_list,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace",
                    cwd=PROJECT_DIR
                )
                if store_server:
                    self._server_proc = proc
                output_lines = []
                for line in proc.stdout:
                    output_lines.append(line)
                    log.write_raw(line)
                proc.wait()
                if store_server:
                    self._server_proc = None
                    self.sidebar.set_server_status(False)
                if on_finish:
                    log._txt.after(0, lambda: on_finish("".join(output_lines)))
            except Exception as e:
                log.write(f"Hata: {e}", "err")
        threading.Thread(target=task, daemon=True).start()

    # ── Server ────────────────────────────────────────────────────────────────
    def start_server(self):
        if self._server_proc and self._server_proc.poll() is None:
            self.server_log.write("Server zaten calisiyor.", "warn")
            return
        self.server_log.separator()
        self.server_log.write("Server baslatiliyor...", "info")
        self.sidebar.set_server_status(True)
        self._run([os.path.join(PROJECT_DIR, "server_master.py")],
                  self.server_log, store_server=True)

    def stop_server(self):
        if not self._server_proc:
            self.server_log.write("Calisir durumda server yok.", "warn")
            return
        try:
            self.server_log.write("Server sonlandiriliyor...", "warn")
            self._server_proc.terminate()
            time.sleep(0.5)
            if self._server_proc and self._server_proc.poll() is None:
                self._server_proc.kill()
            self._server_proc = None
            self.server_log.write("Server basariyla durduruldu.", "ok")
            self.sidebar.set_server_status(False)
        except Exception as e:
            self.server_log.write(f"Server durdurma hatasi: {e}", "err")

    # ── Haber ─────────────────────────────────────────────────────────────────
    def load_news_enroll(self):
        path = filedialog.askopenfilename(
            title="Orijinal Haber Dosyasini Sec",
            filetypes=[("Metin Dosyalari", "*.txt"), ("Tum Dosyalar", "*.*")]
        )
        if path:
            self.news_enroll_file = path
            self.enroll_path_lbl.configure(
                text=f"  {os.path.basename(path)}", text_color=C["accent"]
            )
            self.news_log.write(f"Enroll dosyasi secildi: {os.path.basename(path)}", "info")
        else:
            self.news_log.write("Dosya secimi iptal edildi.", "warn")

    def load_news_verify(self):
        path = filedialog.askopenfilename(
            title="Dogrulanacak Haber Dosyasini Sec",
            filetypes=[("Metin Dosyalari", "*.txt"), ("Tum Dosyalar", "*.*")]
        )
        if path:
            self.news_verify_file = path
            self.verify_path_lbl.configure(
                text=f"  {os.path.basename(path)}", text_color=C["green"]
            )
            self.news_log.write(f"Verify dosyasi secildi: {os.path.basename(path)}", "info")
        else:
            self.news_log.write("Dosya secimi iptal edildi.", "warn")

    def _server_check(self) -> bool:
        """Server porta dinliyor mu? Degil ise log'a uyari yaz ve False dondur."""
        import socket as _sock
        try:
            with _sock.create_connection(("127.0.0.1", 5000), timeout=1):
                return True
        except OSError:
            self.news_log.separator()
            self.news_log.write("SERVER CALISMIYOR!", "err")
            self.news_log.write("Lutfen once 'Server' sekmesine gidip 'Serveri Baslat' butonuna basin.", "warn")
            self.news_banner_lbl.configure(
                text="[!] Server baslatilmadi — once Server sekmesinden serveri baslatiniz.",
                text_color=C["yellow"]
            )
            return False

    def enroll_news(self):
        if not self.news_enroll_file:
            self.news_log.write("Once enroll icin dosya secin!", "err")
            return
        if not self._server_check():
            return
        self.news_log.separator()
        fname = os.path.basename(self.news_enroll_file)
        self.news_log.write(f"Hash hesaplaniyor: {fname}", "info")
        self.news_banner_lbl.configure(text="Isleniyor...", text_color=C["yellow"])
        file_path = self.news_enroll_file   # kapatmak icin kopyala

        def task():
            try:
                import sys as _sys
                if PROJECT_DIR not in _sys.path:
                    _sys.path.insert(0, PROJECT_DIR)
                from client_slave import run_client
                ok, msg = run_client("news-enroll", [file_path])
                if ok:
                    self.news_log.write(f"[OK] Haber basariyla kaydedildi.", "ok")
                    self.news_log.write("Bu metin orijinal kaynak olarak referans alinacaktir.", "info")
                    self.news_banner_lbl.after(0, lambda: self.news_banner_lbl.configure(
                        text="[OK] Haber sisteme kaydedildi — referans olusturuldu.",
                        text_color=C["green"]
                    ))
                else:
                    self.news_log.write(f"[HATA] Kayit basarisiz: {msg}", "err")
                    self.news_banner_lbl.after(0, lambda: self.news_banner_lbl.configure(
                        text="[HATA] Kayit basarisiz — detay icin log'u inceleyin.",
                        text_color=C["red"]
                    ))
            except Exception as e:
                self.news_log.write(f"Beklenmedik hata: {e}", "err")
        threading.Thread(target=task, daemon=True).start()

    def verify_news(self):
        if not self.news_verify_file:
            self.news_log.write("Once verify icin dosya secin!", "err")
            return
        if not self._server_check():
            return
        self.news_log.separator()
        fname = os.path.basename(self.news_verify_file)
        self.news_log.write(f"Dogrulama baslatiliyor: {fname}", "info")
        self.news_banner_lbl.configure(text="Karsilastiriliyor...", text_color=C["yellow"])
        file_path = self.news_verify_file   # kapatmak icin kopyala

        def task():
            try:
                import sys as _sys
                if PROJECT_DIR not in _sys.path:
                    _sys.path.insert(0, PROJECT_DIR)
                from client_slave import run_client
                ok, msg = run_client("news-verify", [file_path])
                if ok:
                    self.news_log.write("[OK] DOGRULAMA BASARILI", "ok")
                    self.news_log.write("Icerik eslesiyor: Haber orijinal ve degistirilmemis.", "ok")
                    self.news_banner_lbl.after(0, lambda: self.news_banner_lbl.configure(
                        text="[OK]  DOGRULAMA BASARILI — Haber orijinal, icerigi degistirilmemis!",
                        text_color=C["green"]
                    ))
                else:
                    self.news_log.write("[HATA] DOGRULAMA BASARISIZ", "err")
                    self.news_log.write("Icerik farkli: Haber degistirilmis veya manipule edilmis!", "err")
                    self.news_banner_lbl.after(0, lambda: self.news_banner_lbl.configure(
                        text="[HATA]  DOGRULAMA BASARISIZ — Haber farkli veya manipule edilmis!",
                        text_color=C["red"]
                    ))
            except Exception as e:
                self.news_log.write(f"Beklenmedik hata: {e}", "err")
        threading.Thread(target=task, daemon=True).start()



    # ── Ses ──────────────────────────────────────────────────────────────────
    def record_audio(self, step):
        mode = "enroll" if step == 1 else "verify"
        label = "Enroll" if step == 1 else "Verify"
        self.audio_log.separator()
        self.audio_log.write(
            f"Ses Kaydi ({label}) baslatiliyor — 5 saniye konusun...", "info"
        )
        self._run([os.path.join(PROJECT_DIR, "client_slave.py"), mode, "5"],
                  self.audio_log)


# ── Giris ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
