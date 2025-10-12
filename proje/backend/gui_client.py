import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading, subprocess, sys, os, time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Doğrulama Sistemi - Modern 3D GUI")
        self.geometry("900x600")

        self.tabview = ctk.CTkTabview(self, width=850, height=550)
        self.tabview.pack(pady=20, padx=20, fill="both", expand=True)

        self.tab_server = self.tabview.add("Server")
        self.tab_audio = self.tabview.add("Ses Doğrulama")
        self.tab_news = self.tabview.add("Haber Doğrulama")

        self._build_server_tab()
        self._build_audio_tab()
        self._build_news_tab()

        # Ses kayıt dosyaları
        self.audio_file1 = None
        self.audio_file2 = None

        # process reference (GUI ile başlatılan server için)
        self._server_proc = None

        # haber için yüklenmiş dosya yolu
        self.loaded_news = None

    # ---------------- Server ----------------
    def _build_server_tab(self):
        frame = ctk.CTkFrame(self.tab_server)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        lbl = ctk.CTkLabel(frame, text="Server Kontrol", font=("Arial", 18, "bold"))
        lbl.pack(pady=10)

        btn_start = ctk.CTkButton(frame, text="Server Başlat", command=self.start_server)
        btn_start.pack(pady=5)

        btn_stop = ctk.CTkButton(frame, text="Server Durdur", command=self.stop_server)
        btn_stop.pack(pady=5)

        self.server_log = tk.Text(frame, height=15, bg="#1e1e1e", fg="white")
        self.server_log.pack(fill="both", expand=True, pady=10)

        clear_btn = ctk.CTkButton(frame, text="Log Temizle", command=lambda: self._clear_log(self.server_log))
        clear_btn.pack(pady=5)

    # ---------------- Ses ----------------
    def _build_audio_tab(self):
        frame = ctk.CTkFrame(self.tab_audio)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        lbl = ctk.CTkLabel(frame, text="Ses Doğrulama", font=("Arial", 18, "bold"))
        lbl.pack(pady=10)

        btn_enroll = ctk.CTkButton(frame, text="Ses Kaydı 1", command=lambda: self.record_audio(1))
        btn_enroll.pack(pady=5)

        btn_verify = ctk.CTkButton(frame, text="Ses Kaydı 2 & Verify", command=lambda: self.record_audio(2))
        btn_verify.pack(pady=5)

        self.audio_log = tk.Text(frame, height=15, bg="#1e1e1e", fg="white")
        self.audio_log.pack(fill="both", expand=True, pady=10)

        clear_btn = ctk.CTkButton(frame, text="Log Temizle", command=lambda: self._clear_log(self.audio_log))
        clear_btn.pack(pady=5)

    # ---------------- Haber ----------------
    # ---------------- Haber ----------------
    def _build_news_tab(self):
        frame = ctk.CTkFrame(self.tab_news)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        lbl = ctk.CTkLabel(frame, text="Haber Doğrulama (SHA256)", font=("Arial", 18, "bold"))
        lbl.pack(pady=10)

        btn_load_enroll = ctk.CTkButton(frame, text="Haber Yükle (Enroll)", command=self.load_news_enroll)
        btn_load_enroll.pack(pady=5)

        btn_load_verify = ctk.CTkButton(frame, text="Haber Yükle (Verify)", command=self.load_news_verify)
        btn_load_verify.pack(pady=5)

        btn_enroll = ctk.CTkButton(frame, text="Haber Kaydı (Enroll)", command=self.enroll_news)
        btn_enroll.pack(pady=5)

        btn_verify = ctk.CTkButton(frame, text="Haber Doğrula (Verify)", command=self.verify_news)
        btn_verify.pack(pady=5)

        self.news_log = tk.Text(frame, height=15, bg="#1e1e1e", fg="white")
        self.news_log.pack(fill="both", expand=True, pady=10)

        clear_btn = ctk.CTkButton(frame, text="Log Temizle", command=lambda: self._clear_log(self.news_log))
        clear_btn.pack(pady=5)

        # dosya yolları
        self.news_enroll_file = None
        self.news_verify_file = None

    def load_news_enroll(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.news_log.insert(tk.END, f"[INFO] Haber ENROLL dosyası seçildi: {file_path}\n")
            self.news_enroll_file = file_path
        else:
            self.news_log.insert(tk.END, "[ERROR] Enroll için dosya seçilmedi.\n")

    def load_news_verify(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.news_log.insert(tk.END, f"[INFO] Haber VERIFY dosyası seçildi: {file_path}\n")
            self.news_verify_file = file_path
        else:
            self.news_log.insert(tk.END, "[ERROR] Verify için dosya seçilmedi.\n")

    def enroll_news(self):
        if not self.news_enroll_file:
            self.news_log.insert(tk.END, "[ERROR] Önce ENROLL dosyası yükleyin.\n")
            return
        self.news_log.insert(tk.END, f"[INFO] Haber ENROLL başlatılıyor: {self.news_enroll_file}\n")
        client_script = os.path.join(PROJECT_DIR, "client_slave.py")
        self._run_command([client_script, "news-enroll", self.news_enroll_file], self.news_log)

    def verify_news(self):
        if not self.news_verify_file:
            self.news_log.insert(tk.END, "[ERROR] Önce VERIFY dosyası yükleyin.\n")
            return
        self.news_log.insert(tk.END, f"[INFO] Haber VERIFY başlatılıyor: {self.news_verify_file}\n")
        client_script = os.path.join(PROJECT_DIR, "client_slave.py")
        self._run_command([client_script, "news-verify", self.news_verify_file], self.news_log)


    # ---------------- Utils ----------------
    def _clear_log(self, log_widget):
        log_widget.delete("1.0", tk.END)

    def _run_command(self, cmd_list, log_widget, store_proc_as=None):
        """
        cmd_list: örn: [r"C:\...\client_slave.py", "enroll", "5"]
        sys.executable ile çağırır ve cwd=PROJECT_DIR ayarlar.
        Eğer store_proc_as == "server", process self._server_proc olarak kaydedilir.
        """
        def task():
            try:
                full_cmd = [sys.executable] + cmd_list
                proc = subprocess.Popen(
                    full_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=PROJECT_DIR
                )
                if store_proc_as == "server":
                    self._server_proc = proc
                for line in proc.stdout:
                    log_widget.insert(tk.END, line)
                    log_widget.see(tk.END)
                proc.wait()
                if store_proc_as == "server":
                    self._server_proc = None
            except Exception as e:
                log_widget.insert(tk.END, f"[ERROR] {e}\n")
        threading.Thread(target=task, daemon=True).start()

    # ---------------- Server ----------------
    def start_server(self):
        if self._server_proc and self._server_proc.poll() is None:
            self.server_log.insert(tk.END, "[WARN] Server zaten çalışıyor.\n")
            return

        self.server_log.insert(tk.END, "[INFO] Server başlatılıyor...\n")
        server_script = os.path.join(PROJECT_DIR, "server_master.py")
        self._run_command([server_script], self.server_log, store_proc_as="server")

    def stop_server(self):
        if self._server_proc:
            try:
                self.server_log.insert(tk.END, "[INFO] Server sonlandırılıyor...\n")
                self._server_proc.terminate()
                time.sleep(0.5)
                if self._server_proc and self._server_proc.poll() is None:
                    self._server_proc.kill()
                self._server_proc = None
                self.server_log.insert(tk.END, "[INFO] Server durduruldu.\n")
            except Exception as e:
                self.server_log.insert(tk.END, f"[ERROR] Server durdurma hatası: {e}\n")
        else:
            self.server_log.insert(tk.END, "[WARN] Server çalışmıyor.\n")

    # ---------------- Ses ----------------
    def record_audio(self, step):
        client_script = os.path.join(PROJECT_DIR, "client_slave.py")
        if step == 1:
            self.audio_log.insert(tk.END, "[INFO] Ses Kaydı 1 (Enroll) başlatılıyor...\n")
            self._run_command([client_script, "enroll", "5"], self.audio_log)
        else:
            self.audio_log.insert(tk.END, "[INFO] Ses Kaydı 2 (Verify) başlatılıyor...\n")
            self._run_command([client_script, "verify", "5"], self.audio_log)


if __name__ == "__main__":
    app = App()
    app.mainloop()
