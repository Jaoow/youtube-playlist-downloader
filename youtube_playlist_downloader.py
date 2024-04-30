import os
import youtube_dl
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar, Button, Style, Label, Entry
import threading
import time

MEGABYTE_SIZE = 1048576

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Download de Playlist do YouTube")

        # Estilo
        self.style = Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", padding=6, relief="raised", font=("Arial", 10), background="#4CAF50", foreground="white")
        self.style.configure("TProgressbar", background="green", troughcolor="light green")
        self.style.configure("TLabel", font=("Arial", 12))
        self.style.configure("TEntry", padding=5, font=("Arial", 10))

        # Variáveis de controle
        self.playlist_url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.paste_from_clipboard_var = tk.BooleanVar()

        # Widgets
        self.playlist_url_label = Label(root, text="URL da Playlist:", style="TLabel")
        self.playlist_url_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.playlist_url_entry = Entry(root, textvariable=self.playlist_url_var, width=50, style="TEntry")
        self.playlist_url_entry.grid(row=0, column=1, padx=10, pady=(10, 5))

        self.paste_button = tk.Button(root, text="Colar", command=self.paste_from_clipboard, font=("Arial", 10))
        self.paste_button.grid(row=0, column=2, padx=5, pady=(10, 5), sticky="w")

        self.output_dir_label = Label(root, text="Diretório de Saída:", style="TLabel")
        self.output_dir_label.grid(row=1, column=0, padx=10, pady=(10, 5), sticky="w")

        self.output_dir_entry = Entry(root, textvariable=self.output_dir_var, width=50, style="TEntry")
        self.output_dir_entry.grid(row=1, column=1, padx=10, pady=(10, 5))

        self.browse_button = tk.Button(root, text="Navegar", command=self.browse_output_dir, font=("Arial", 10))
        self.browse_button.grid(row=1, column=2, padx=5, pady=5)

        self.download_button = Button(root, text="Baixar Playlist", command=self.start_download_thread, style="TButton")
        self.download_button.grid(row=2, column=0, columnspan=4, pady=10)

        self.progress_bar = Progressbar(root, orient="horizontal", length=300, mode="determinate", style="TProgressbar")
        self.progress_bar.grid(row=3, column=0, columnspan=4, padx=10, pady=5)

        self.progress_label = tk.Label(root, text="", font=("Arial", 10))
        self.progress_label.grid(row=4, column=0, columnspan=4, padx=10, pady=(0, 5))

    def browse_output_dir(self):
        output_dir = filedialog.askdirectory()
        self.output_dir_var.set(output_dir)

    def paste_from_clipboard(self):
        clipboard_content = self.root.clipboard_get()
        if clipboard_content.startswith("http"):
            self.playlist_url_var.set(clipboard_content)

    def start_download_thread(self):
        playlist_url = self.playlist_url_var.get()
        output_dir = self.output_dir_var.get()

        if not playlist_url:
            messagebox.showerror("Erro", "Por favor, insira a URL da playlist.")
            return
        if not output_dir:
            messagebox.showerror("Erro", "Por favor, selecione o diretório de saída.")
            return
        
        self.download_button.config(state="disabled")

        # Thread para fazer o download da playlist
        download_thread = threading.Thread(target=self.download_playlist, args=(playlist_url, output_dir))
        download_thread.start()

    def download_playlist(self, playlist_url, output_dir):
        # Configure as opções para o youtube-dl
        ydl_opts = {
            "format": "best",
            "outtmpl": os.path.join(output_dir, "%(title)s", "%(title)s.%(ext)s"),
            "writeinfojson": True,
            "progress_hooks": [self.update_progress],
        }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([playlist_url])

            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if file.endswith(".info.json"):
                        json_file_path = os.path.join(root, file)
                        with open(json_file_path, "r", encoding="utf-8") as f:
                            video_info = json.load(f)
                            description = video_info.get("description", "")
                            video_title = video_info.get("title", "")
                            valid_title = self.validate_file_name(video_title)
                            if valid_title:
                                text_file_path = os.path.join(root, f"{valid_title}.txt")
                                with open(text_file_path, "w", encoding="utf-8") as desc_file:
                                    desc_file.write(description)

            progress_info=f"Todos os vídeos da playlist foram baixados para: \n{output_dir}."
            self.progress_label.config(text=progress_info)
            messagebox.showinfo("Sucesso", progress_info)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao baixar os vídeos: {str(e)}")

    def validate_file_name(self, file_name):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            file_name = file_name.replace(char, '')
        return file_name
    
    def extract_file_name(self, path_name):
        file = os.path.basename(path_name)
        file_without_ext = os.path.splitext(file)[0]
        return file_without_ext

    def update_progress(self, d):
        downloaded_file = self.extract_file_name(d['filename'])
        if d["status"] == "downloading":
            if d["total_bytes"] is not None:
                progress_percent = int(float(d["_percent_str"].split()[0].strip("%")))
                downloaded_bytes = int(d["downloaded_bytes"])
                total_bytes = int(d["total_bytes"])
                bytes_remaining = total_bytes - downloaded_bytes
                progress_info = f"Baixando: {downloaded_file}... \n"
                progress_info += f"{downloaded_bytes / (MEGABYTE_SIZE):.2f} MB / {total_bytes / (MEGABYTE_SIZE):.2f} MB, Restante: {bytes_remaining / (MEGABYTE_SIZE):.2f} MB"

                if "eta" in d:
                    eta_seconds = d["eta"]
                    eta_formatted = time.strftime("%H:%M:%S", time.gmtime(eta_seconds))
                    progress_info += f", ETA: {eta_formatted}"

                self.progress_label.config(text=progress_info)
                self.progress_bar["value"] = progress_percent

        elif d["status"] == "finished":
            progress_info = f"Download concluído: \n {downloaded_file}"
            self.progress_label.config(text=progress_info)

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()