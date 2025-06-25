import flet as ft
import yt_dlp
import os
import sys
import re
from typing import Optional

def main(page: ft.Page):
    # Configuration de base de la page
    page.title = "YouTube Downloader"
    page.window_width = 500
    page.window_height = 500
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Variables
    download_path = os.path.join(os.path.expanduser("~"), "Downloads")
    ffmpeg_path: Optional[str] = None

    # Trouver FFmpeg local
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)
    
    possible_ffmpeg_paths = [
        os.path.join(base_path, "bin", "ffmpeg.exe"),
        os.path.join(base_path, "ffmpeg.exe"),
        os.path.join(base_path, "ffmpeg")
    ]
    
    for path in possible_ffmpeg_paths:
        if os.path.exists(path):
            ffmpeg_path = path
            break

    # Éléments UI
    url_field = ft.TextField(
        label="URL YouTube",
        width=400,
        autofocus=True
    )
    
    path_field = ft.TextField(
        label="Dossier de destination",
        value=download_path,
        width=320,
        read_only=True
    )
    
    browse_button = ft.ElevatedButton(
        "Parcourir",
        on_click=lambda _: browse_folder()
    )
    
    download_type = ft.Dropdown(
        label="Type de téléchargement",
        width=400,
        options=[
            ft.dropdown.Option("video", "Vidéo"),
            ft.dropdown.Option("audio", "Audio (MP3)"),
        ],
        value="video"
    )
    
    quality_options = ft.Dropdown(
        label="Qualité",
        width=400,
        options=[
            ft.dropdown.Option("best", "Meilleure qualité"),
            ft.dropdown.Option("1080", "1080p"),
            ft.dropdown.Option("720", "720p"),
            ft.dropdown.Option("480", "480p"),
            ft.dropdown.Option("360", "360p"),
        ],
        value="best"
    )
    
    status_text = ft.Text(
        "Entrez une URL YouTube et cliquez sur Télécharger",
        color=ft.colors.BLUE
    )
    
    progress_bar = ft.ProgressBar(
        width= 395,
        value=0,
        color=ft.colors.BLUE,
        bgcolor=ft.colors.GREY_300
    )
    
    progress_text = ft.Text("0%", width=400, text_align=ft.TextAlign.CENTER)
    
    download_button = ft.ElevatedButton(
        "Télécharger",
        icon=ft.icons.DOWNLOAD,
        on_click=lambda _: download_media()
    )

    # File Picker
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    
    def browse_folder():
        def on_dialog_result(e: ft.FilePickerResultEvent):
            if e.path:
                nonlocal download_path
                download_path = e.path
                path_field.value = download_path
                page.update()
        
        file_picker.get_directory_path(dialog_title="Choisir un dossier de destination")
        file_picker.on_result = on_dialog_result
    
    def update_progress(d):
        if d['status'] == 'downloading':
            # Nettoyage du pourcentage pour enlever les caractères non désirés
            percent_str = d.get('_percent_str', "0%")
            
            # Extraction numérique avec regex
            percent_match = re.search(r'(\d+\.?\d*)%', percent_str)
            if percent_match:
                percent = float(percent_match.group(1))
                progress = percent / 100
                
                # Mise à jour de l'UI
                progress_bar.value = progress
                progress_text.value = f"{percent:.1f}%"
                page.update()
    
    def download_media():
        url = url_field.value.strip()
        dl_type = download_type.value
        quality = quality_options.value
        
        if not url:
            status_text.value = "Veuillez entrer une URL YouTube"
            status_text.color = ft.colors.RED
            page.update()
            return
        
        status_text.value = "Téléchargement en cours..."
        status_text.color = ft.colors.BLUE
        progress_bar.value = 0
        progress_text.value = "0%"
        download_button.disabled = True
        page.update()

        ydl_opts = {
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'quiet': True,
            'progress_hooks': [update_progress],
        }

        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path

        if dl_type == "audio":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            if quality == "best":
                ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            else:
                ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if dl_type == "audio":
                status_text.value = "✅ Audio MP3 téléchargé avec succès!"
            else:
                status_text.value = f"✅ Vidéo ({quality}p) téléchargée avec succès!"
            status_text.color = ft.colors.GREEN
        except Exception as e:
            status_text.value = f"❌ Erreur : {str(e)}"
            status_text.color = ft.colors.RED
        finally:
            download_button.disabled = False
            page.update()

    # Ajout des éléments à la page
    page.add(
        ft.Column(
            [
                ft.Text("Téléchargeur YouTube", size=20, weight=ft.FontWeight.BOLD),
                url_field,
                ft.Row([path_field, browse_button], alignment=ft.MainAxisAlignment.CENTER),
                download_type,
                quality_options,
                download_button,
                status_text,
                progress_bar,
                progress_text
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

if __name__ == "__main__":
    ft.app(target=main)