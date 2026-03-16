import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class SymulatorStacjiBazowej:
    def __init__(self, root):
        self.root = root
        self.root.title("Symulator Stacji Bazowej - Model M/M/S/K")

        #podział okien
        self.frame_left = tk.Frame(root, padx=10, pady=10)
        self.frame_left.pack(side=tk.LEFT, fill=tk.Y)
        self.frame_mid = tk.Frame(root, padx=10, pady=10)
        self.frame_mid.pack(side=tk.LEFT, fill=tk.Y)
        self.frame_right = tk.Frame(root, padx=10, pady=10)
        self.frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        #parametry wejściowe
        self.frame_params = tk.LabelFrame(self.frame_left, text="Parametry symulacji")
        self.frame_params.pack(fill=tk.X)

        self.params_cfg = [
            ("Liczba kanałów (S)", "10"),
            ("Lambda (λ)", "1.0"),
            ("N (Średnia rozmowa)", "20.0"),
            ("Sigma (σ)", "5.0"),
            ("Min czas", "10.0"),
            ("Maks czas", "30.0"),
            ("Długość kolejki", "10"),
            ("Czas symulacji [s]", "30")
        ]
        self.entries = {}
        for text, default in self.params_cfg:
            row = tk.Frame(self.frame_params)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=text, width=18, anchor="w").pack(side=tk.LEFT)
            ent = tk.Entry(row, width=8)
            ent.insert(0, default)
            ent.pack(side=tk.RIGHT)
            self.entries[text] = ent

        #przyciski sterujące
        self.btn_start = tk.Button(self.frame_left, text="START", command=self.prepare_and_start, bg="#2ecc71",
                                   font=('Arial', 10, 'bold'))
        self.btn_start.pack(pady=(10, 5), fill=tk.X)

        self.btn_pause = tk.Button(self.frame_left, text="PAUZA", command=self.toggle_pause, bg="#f39c12",
                                   font=('Arial', 10, 'bold'), state=tk.DISABLED)
        self.btn_pause.pack(pady=5, fill=tk.X)

        #tabela wyników
        kolumny = ("Sek", "k", "λi", "μi", "Ro", "Q", "W")
        self.tree = ttk.Treeview(self.frame_left, columns=kolumny, show="headings", height=12)
        for col in kolumny:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=45, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)

        #wizualizacja kanałów
        tk.Label(self.frame_mid, text="Status Kanałów", font=("Arial", 10, "bold")).pack()
        self.frame_grid = tk.Frame(self.frame_mid)
        self.frame_grid.pack(pady=5)
        self.rects = []

        self.lbl_queue = tk.Label(self.frame_mid, text="Kolejka: 0/0")
        self.lbl_queue.pack()
        self.q_bar = ttk.Progressbar(self.frame_mid, orient="horizontal", length=150, mode="determinate")
        self.q_bar.pack(pady=5)

        self.lbl_counters = tk.Label(self.frame_mid, text="Obsłużone: 0\nOdrzucone: 0\nCzas: 0s", justify=tk.LEFT)
        self.lbl_counters.pack(pady=10)

        #wykresy
        self.fig, self.ax = plt.subplots(3, 1, figsize=(5, 7))
        self.fig.tight_layout(pad=3.0)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.running = False
        self.paused = False

    def toggle_pause(self):
        if not self.running: return
        self.paused = not self.paused

        if self.paused:
            self.btn_pause.config(text="WZNÓW", bg="#3498db", fg="white")
        else:
            self.btn_pause.config(text="PAUZA", bg="#f39c12", fg="black")
            self.step()

    def prepare_and_start(self):
        if self.running: return
        try:
            #pobranie parametrów
            self.S = int(self.entries["Liczba kanałów (S)"].get())
            self.lamb_val = float(self.entries["Lambda (λ)"].get())
            self.N_val = float(self.entries["N (Średnia rozmowa)"].get())
            sigma = float(self.entries["Sigma (σ)"].get())
            t_min = float(self.entries["Min czas"].get())
            t_max = float(self.entries["Maks czas"].get())
            self.q_max = int(self.entries["Długość kolejki"].get())
            self.sim_time = int(self.entries["Czas symulacji [s]"].get())

            if t_min <= 1.0 or t_max <= 1.0:
                raise ValueError("Min i Maks czas muszą należeć do przedziału (1, INF).")

            #generowanie list par lambdai i mui
            self.lambda_list = []
            self.mu_list = []
            suma_czasu = 0
            while suma_czasu < self.sim_time + 100:
                l_i = np.random.exponential(1.0 / self.lamb_val)
                m_i = np.clip(np.random.normal(self.N_val, sigma), t_min, t_max)
                self.lambda_list.append(l_i)
                self.mu_list.append(m_i)
                suma_czasu += l_i

            self.reszta_czasu = 0.0

            #inicjalizacja
            self.kanaly = [0.0] * self.S
            self.kolejka = []
            self.t = 0
            self.obsluzone_total = 0
            self.odrzucone_total = 0
            self.hist_ro, self.hist_q, self.hist_w = [], [], []
            self.running = True
            self.paused = False

            self.btn_pause.config(state=tk.NORMAL, text="PAUZA", bg="#f39c12", fg="black")

            #czyszczenie UI
            for r in self.rects: r.destroy()
            self.rects = []
            for i in range(self.S):
                r = tk.Label(self.frame_grid, text="WOLNY", bg="#2ecc71", width=12, relief="ridge")
                r.grid(row=i // 2, column=i % 2, padx=2, pady=2)
                self.rects.append(r)
            for item in self.tree.get_children(): self.tree.delete(item)

            self.plik = open("Wyniki.txt", "w", encoding="utf-8")
            self.plik.write(f"Parametry symulacji: S={self.S}, Lambda={self.lamb_val}, N={self.N_val}, Sigma={sigma}, Min={t_min}, Maks={t_max}, Dlugosc kolejki={self.q_max}, Czas={self.sim_time}s\n")
            self.plik.write("Ro\t\tQ\tW\n")

            self.step()
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def step(self):
        #wznów/wstrzymaj
        if not self.running or self.t >= self.sim_time:
            self.running = False
            self.btn_pause.config(state=tk.DISABLED)
            try:
                self.plik.close()
            except:
                pass
            return

        if self.paused:
            return

        self.t += 1

        #zwolnienie kanałów
        for i in range(self.S):
            if self.kanaly[i] > 0:
                self.kanaly[i] = max(0.0, self.kanaly[i] - 1.0)
                if self.kanaly[i] == 0:
                    self.obsluzone_total += 1

        k_count = 0
        mu_do_dodania = []
        last_lambda = 0.0
        last_mu = 0.0

        if self.reszta_czasu >= 1.0:
            self.reszta_czasu -= 1.0
        else:
            suma_kroku = self.reszta_czasu
            while len(self.lambda_list) > 0:
                l_i = self.lambda_list[0]
                if suma_kroku + l_i < 1.0:
                    suma_kroku += l_i
                    last_lambda = self.lambda_list.pop(0)
                    last_mu = self.mu_list.pop(0)
                    mu_do_dodania.append(last_mu)
                    k_count += 1
                else:
                    suma_kroku += l_i
                    self.reszta_czasu = suma_kroku - 1.0
                    last_lambda = self.lambda_list.pop(0)
                    last_mu = self.mu_list.pop(0)
                    mu_do_dodania.append(last_mu)
                    k_count += 1
                    break

        #umieszczenie k elementów w symulatorze
        for mu_j in mu_do_dodania:
            if 0.0 in self.kanaly:
                self.kanaly[self.kanaly.index(0.0)] = mu_j
            elif len(self.kolejka) < self.q_max:
                self.kolejka.append(mu_j)
            else:
                self.odrzucone_total += 1

        #przesunięcie z kolejki do wolnych kanałów
        while len(self.kolejka) > 0 and 0.0 in self.kanaly:
            self.kanaly[self.kanaly.index(0.0)] = self.kolejka.pop(0)

        #obliczenia parametrów Ro, Q, W
        zajete_teraz = sum(1 for k in self.kanaly if k > 0)
        self.hist_ro.append(zajete_teraz)
        self.hist_q.append(len(self.kolejka))

        avg_ro = np.mean(self.hist_ro)
        avg_q = np.mean(self.hist_q)

        przybycia_zaakceptowane = self.obsluzone_total + zajete_teraz + len(self.kolejka)
        lambda_eff = przybycia_zaakceptowane / self.t if self.t > 0 else 0
        avg_w = avg_q / lambda_eff if lambda_eff > 0 else 0
        self.hist_w.append(avg_w)

        #wysłanie wyników do UI i pliku
        self.tree.insert("", tk.END, values=(
            self.t, k_count, f"{last_lambda:.2f}" if k_count > 0 else "-", f"{last_mu:.2f}" if k_count > 0 else "-",
            f"{avg_ro:.4f}", f"{avg_q:.4f}", f"{avg_w:.4f}"
        ))
        self.tree.see(self.tree.get_children()[-1])
        self.plik.write(f"{avg_ro:.4f}\t{avg_q:.4f}\t{avg_w:.4f}\n")

        #aktualizacja wizualizacji
        for i in range(len(self.rects)):
            if self.kanaly[i] > 0:
                self.rects[i].config(bg="#e74c3c", text=f"Czas: {int(self.kanaly[i])}s", fg="white")
            else:
                self.rects[i].config(bg="#2ecc71", text="WOLNY", fg="black")

        self.lbl_counters.config(text=f"Obsłużone: {self.obsluzone_total}\nOdrzucone: {self.odrzucone_total}\nCzas: {self.t}s / {self.sim_time}s")
        self.q_bar['value'] = (len(self.kolejka) / self.q_max) * 100 if self.q_max > 0 else 0
        self.lbl_queue.config(text=f"Kolejka: {len(self.kolejka)} / {self.q_max}")

        data = [self.hist_ro, self.hist_q, self.hist_w]
        titles = [f"Intensywność ruchu ρ = {avg_ro:.2f}", f"Śr. kolejka Q = {avg_q:.2f}",
                  f"Czas oczekiwania W = {avg_w:.2f}"]
        colors = ['#2ecc71', '#e74c3c', '#3498db']

        for i in range(3):
            self.ax[i].clear()
            self.ax[i].plot(data[i], color=colors[i], linewidth=1.5)
            self.ax[i].fill_between(range(len(data[i])), data[i], color=colors[i], alpha=0.2)
            self.ax[i].set_title(titles[i], loc='right', fontsize=9, fontweight='bold')
            self.ax[i].grid(True, linestyle='--', alpha=0.6)

        self.canvas.draw()
        self.root.after(1000, self.step)


if __name__ == "__main__":
    root = tk.Tk()
    app = SymulatorStacjiBazowej(root)
    root.mainloop()