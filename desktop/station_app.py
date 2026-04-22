import argparse
import threading
from datetime import datetime

import requests
import tkinter as tk
from tkinter import ttk, messagebox


class StationApp:
    def __init__(self, root, base_url, station_type, station_name, station_key):
        self.root = root
        self.base_url = base_url.rstrip('/')
        self.station_type = station_type
        self.station_name = station_name
        self.station_key = station_key

        self.root.title(f'Sistema de Marcas - {station_name}')
        self.root.geometry('900x620')
        self.root.configure(bg='#f3f6fb')

        self._build_ui()
        self._update_clock()
        self.fetch_recent_marks_async()

    def _build_ui(self):
        header = tk.Frame(self.root, bg='#003366', height=80)
        header.pack(fill='x')

        title = tk.Label(
            header,
            text=f'Estacion de {self.station_name}',
            fg='white',
            bg='#003366',
            font=('Segoe UI', 18, 'bold')
        )
        title.pack(side='left', padx=20, pady=20)

        self.clock_label = tk.Label(
            header,
            text='',
            fg='white',
            bg='#003366',
            font=('Consolas', 14, 'bold')
        )
        self.clock_label.pack(side='right', padx=20)

        body = tk.Frame(self.root, bg='#f3f6fb')
        body.pack(fill='both', expand=True, padx=20, pady=20)

        mark_card = tk.LabelFrame(body, text='Registrar marca', bg='white', padx=16, pady=16)
        mark_card.pack(fill='x', pady=(0, 16))

        tk.Label(mark_card, text='Identificacion', bg='white', fg='#003366', font=('Segoe UI', 11, 'bold')).pack(anchor='w')

        self.identification_entry = tk.Entry(mark_card, font=('Segoe UI', 14), width=30)
        self.identification_entry.pack(fill='x', pady=8)
        self.identification_entry.focus_set()
        self.identification_entry.bind('<Return>', lambda event: self.register_mark_async())

        button_row = tk.Frame(mark_card, bg='white')
        button_row.pack(fill='x')

        self.mark_btn = tk.Button(
            button_row,
            text='Registrar Marca',
            bg='#cc0000',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            relief='flat',
            command=self.register_mark_async
        )
        self.mark_btn.pack(side='left')

        self.refresh_btn = tk.Button(
            button_row,
            text='Actualizar lista',
            bg='#0a58ca',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            command=self.fetch_recent_marks_async
        )
        self.refresh_btn.pack(side='left', padx=10)

        self.status_var = tk.StringVar(value='Listo para marcar')
        status = tk.Label(mark_card, textvariable=self.status_var, bg='white', fg='#444', font=('Segoe UI', 10))
        status.pack(anchor='w', pady=(10, 0))

        list_card = tk.LabelFrame(body, text='Ultimas marcas', bg='white', padx=16, pady=16)
        list_card.pack(fill='both', expand=True)

        columns = ('identificacion', 'nombre', 'fecha_hora')
        self.tree = ttk.Treeview(list_card, columns=columns, show='headings', height=12)
        self.tree.heading('identificacion', text='Identificacion')
        self.tree.heading('nombre', text='Nombre Completo')
        self.tree.heading('fecha_hora', text='Fecha y Hora')

        self.tree.column('identificacion', width=140, anchor='center')
        self.tree.column('nombre', width=370, anchor='w')
        self.tree.column('fecha_hora', width=180, anchor='center')

        scroll = ttk.Scrollbar(list_card, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')

    def _headers(self):
        return {
            'Content-Type': 'application/json',
            'X-Station-Key': self.station_key,
        }

    def _update_clock(self):
        self.clock_label.config(text=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        self.root.after(1000, self._update_clock)

    def _set_loading(self, loading):
        state = 'disabled' if loading else 'normal'
        self.mark_btn.config(state=state)
        self.refresh_btn.config(state=state)

    def register_mark_async(self):
        identification = self.identification_entry.get().strip()
        if not identification:
            messagebox.showwarning('Dato requerido', 'Ingrese una identificacion.')
            return

        self._set_loading(True)
        self.status_var.set('Registrando marca...')

        def worker():
            try:
                response = requests.post(
                    f'{self.base_url}/attendance/station-api/{self.station_type}/mark/',
                    json={'identificacion': identification},
                    headers=self._headers(),
                    timeout=8,
                )
                data = response.json()
            except requests.RequestException as exc:
                self.root.after(0, lambda: self._on_error(f'Error de conexion: {exc}'))
                return
            except ValueError:
                self.root.after(0, lambda: self._on_error('Respuesta invalida del servidor.'))
                return

            self.root.after(0, lambda: self._on_mark_response(response.status_code, data))

        threading.Thread(target=worker, daemon=True).start()

    def _on_mark_response(self, status_code, data):
        self._set_loading(False)

        if status_code >= 400 or not data.get('ok'):
            self.status_var.set(data.get('message', 'No se pudo registrar la marca.'))
            messagebox.showerror('Error', data.get('message', 'No se pudo registrar la marca.'))
            return

        self.status_var.set(data.get('message', 'Marca registrada correctamente.'))
        self.identification_entry.delete(0, tk.END)
        self.identification_entry.focus_set()
        self.fetch_recent_marks_async()

    def fetch_recent_marks_async(self):
        self.status_var.set('Consultando ultimas marcas...')

        def worker():
            try:
                response = requests.get(
                    f'{self.base_url}/attendance/station-api/{self.station_type}/recent/',
                    headers=self._headers(),
                    timeout=8,
                )
                data = response.json()
            except requests.RequestException as exc:
                self.root.after(0, lambda: self._on_error(f'Error de conexion: {exc}'))
                return
            except ValueError:
                self.root.after(0, lambda: self._on_error('Respuesta invalida del servidor.'))
                return

            self.root.after(0, lambda: self._on_recent_response(response.status_code, data))

        threading.Thread(target=worker, daemon=True).start()

    def _on_recent_response(self, status_code, data):
        if status_code >= 400 or not data.get('ok'):
            self._on_error(data.get('message', 'No se pudo consultar la lista.'))
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for item in data.get('items', []):
            self.tree.insert('', 'end', values=(
                item.get('identificacion', ''),
                item.get('nombre_completo', ''),
                item.get('fecha_hora', ''),
            ))

        self.status_var.set('Lista actualizada')

    def _on_error(self, message):
        self._set_loading(False)
        self.status_var.set(message)


def parse_args():
    parser = argparse.ArgumentParser(description='App de marcacion para estaciones Windows')
    parser.add_argument('--server', default='http://127.0.0.1:8000', help='URL base del servidor Django')
    parser.add_argument('--station', choices=['personal', 'estudiante'], required=True, help='Tipo de estacion')
    parser.add_argument('--key', required=True, help='Clave API de la estacion')
    return parser.parse_args()


def launch_station(base_url, station_type, station_key):
    station_name = 'Personal (Docentes y Administrativos)' if station_type == 'personal' else 'Estudiantes'

    root = tk.Tk()
    StationApp(
        root=root,
        base_url=base_url,
        station_type=station_type,
        station_name=station_name,
        station_key=station_key,
    )
    root.mainloop()


def main():
    args = parse_args()
    launch_station(args.server, args.station, args.key)


if __name__ == '__main__':
    main()
