import tkinter as tk
from tkinter import ttk, messagebox
import csv, random
from datetime import datetime, timedelta

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

# Generate slots (9:00 to 17:00), skip lunch 13:15–14:30
def generate_slots():
    start = datetime.strptime("09:00", "%H:%M")
    end = datetime.strptime("17:00", "%H:%M")
    slots = []
    lunch_start = datetime.strptime("13:15", "%H:%M")
    lunch_end = datetime.strptime("14:30", "%H:%M")

    while start < end:
        one_hour = start + timedelta(hours=1)
        ninety_min = start + timedelta(minutes=90)

        if not (start < lunch_end and one_hour > lunch_start):
            slots.append((start.strftime("%H:%M"), one_hour.strftime("%H:%M")))

        if not (start < lunch_end and ninety_min > lunch_start):
            slots.append((start.strftime("%H:%M"), ninety_min.strftime("%H:%M")))

        start += timedelta(minutes=30)

    return [f"{s}-{e}" for s, e in slots]

SLOTS = generate_slots()


class TimetableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎓 Automated Timetable Scheduler")
        self.root.geometry("950x700")
        self.root.configure(bg="#f2f6ff")

        # Data stores
        self.courses = {}   # courses[branch][sem][code] = [name, faculty, room, hours]
        self.timetable = {} # timetable[branch][sem] = {(day,slot):(course,faculty,room)}

        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="#ffffff",
            foreground="#333333",
            rowheight=28,
            fieldbackground="#f9f9f9",
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background="#4a90e2",
            foreground="white",
            font=("Segoe UI", 11, "bold")
        )
        style.map("Treeview", background=[("selected", "#a8d0ff")])

    def styled_button(self, parent, text, command):
        btn = tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 11, "bold"),
            bg="#4a90e2",
            fg="white",
            padx=18,
            pady=8,
            cursor="hand2"
        )
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.config(bg="#357abd"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#4a90e2"))
        return btn

    def setup_ui(self):
        title = tk.Label(
            self.root,
            text="📅 Timetable Scheduler",
            font=("Segoe UI", 18, "bold"),
            bg="#f2f6ff",
            fg="#333"
        )
        title.pack(pady=15)

        # Form section
        form_frame = tk.Frame(self.root, bg="#f2f6ff")
        form_frame.pack(pady=5)

        labels = ["Course Code", "Course Name", "Faculty", "Room", "Hours/Week"]
        self.entries = {}

        for i, lbl in enumerate(labels):
            tk.Label(
                form_frame,
                text=lbl,
                font=("Segoe UI", 10, "bold"),
                bg="#f2f6ff",
                fg="#444"
            ).grid(row=i, column=0, sticky="e", padx=5, pady=2)

            entry = tk.Entry(form_frame, font=("Segoe UI", 10), width=25, relief="solid", bd=1)
            entry.grid(row=i, column=1, pady=2)
            self.entries[lbl] = entry

        # Branch dropdown
        tk.Label(form_frame, text="Branch", font=("Segoe UI", 10, "bold"),
                 bg="#f2f6ff", fg="#444").grid(row=len(labels), column=0, sticky="e", padx=5, pady=2)
        self.branch_var = tk.StringVar()
        branch_cb = ttk.Combobox(form_frame, textvariable=self.branch_var,
                                 values=["CSE", "DSAI", "ECE"], state="readonly", width=22)
        branch_cb.grid(row=len(labels), column=1, pady=2)
        branch_cb.current(0)

        # Semester dropdown
        tk.Label(form_frame, text="Semester", font=("Segoe UI", 10, "bold"),
                 bg="#f2f6ff", fg="#444").grid(row=len(labels)+1, column=0, sticky="e", padx=5, pady=2)
        self.sem_var = tk.StringVar()
        sem_cb = ttk.Combobox(form_frame, textvariable=self.sem_var,
                              values=[str(i) for i in range(1, 9)], state="readonly", width=22)
        sem_cb.grid(row=len(labels)+1, column=1, pady=2)
        sem_cb.current(0)

        # Add course button
        self.styled_button(self.root, "➕ Add Course", self.add_course).pack(pady=12)

        # Treeview
        self.tree = ttk.Treeview(
            self.root,
            columns=("Day", "Slot", "Course", "Faculty", "Room"),
            show="headings"
        )
        for col in ("Day", "Slot", "Course", "Faculty", "Room"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="center")
        self.tree.pack(pady=10, fill="both", expand=True)

        # Dropdowns for display
        select_frame = tk.Frame(self.root, bg="#f2f6ff")
        select_frame.pack(pady=8)

        tk.Label(select_frame, text="View Branch:", bg="#f2f6ff", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=5)
        self.display_branch = tk.StringVar()
        ttk.Combobox(select_frame, textvariable=self.display_branch,
                     values=["CSE","DSAI","ECE"], state="readonly", width=10).grid(row=0, column=1, padx=5)

        tk.Label(select_frame, text="Semester:", bg="#f2f6ff", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=5)
        self.display_sem = tk.StringVar()
        ttk.Combobox(select_frame, textvariable=self.display_sem,
                     values=[str(i) for i in range(1,9)], state="readonly", width=5).grid(row=0, column=3, padx=5)

        self.styled_button(select_frame, "📖 Show Timetable", self.show_timetable).grid(row=0, column=4, padx=12)

        # Bottom buttons
        btn_frame = tk.Frame(self.root, bg="#f2f6ff")
        btn_frame.pack(pady=15)

        self.styled_button(btn_frame, "⚡ Generate All Timetables", self.generate_timetable).grid(row=0, column=0, padx=12)
        self.styled_button(btn_frame, "📤 Export CSVs", self.export_csv).grid(row=0, column=1, padx=12)


    def add_course(self):
        try:
            code = self.entries["Course Code"].get().strip()
            name = self.entries["Course Name"].get().strip()
            faculty = self.entries["Faculty"].get().strip()
            room = self.entries["Room"].get().strip()
            hours = int(self.entries["Hours/Week"].get().strip())
            branch = self.branch_var.get()
            sem = self.sem_var.get()

            if not code or not name or not faculty or not room:
                raise ValueError("Empty fields")

            if branch not in self.courses:
                self.courses[branch] = {}
            if sem not in self.courses[branch]:
                self.courses[branch][sem] = {}

            self.courses[branch][sem][code] = [name, faculty, room, hours]
            messagebox.showinfo("Success", f"✅ Added {name} ({hours} hrs/week) for {branch} Sem-{sem}")

            for e in self.entries.values():
                e.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Error", f"❌ Invalid input: {e}")


    def generate_timetable(self):
        self.timetable.clear()

        for branch, sems in self.courses.items():
            for sem, courses in sems.items():
                all_slots = [(day, slot) for day in DAYS for slot in SLOTS]
                random.shuffle(all_slots)
                remaining = {code: data[3] for code, data in courses.items()}
                used_today = {day: set() for day in DAYS}
                timetable_branch_sem = {}

                while any(hrs > 0 for hrs in remaining.values()) and all_slots:
                    for code in list(courses.keys()):
                        if remaining[code] <= 0:
                            continue
                        day, slot = random.choice(all_slots)
                        if code in used_today[day]:
                            continue

                        start, end = slot.split("-")
                        s_h, s_m = map(int, start.split(":"))
                        e_h, e_m = map(int, end.split(":"))
                        actual_length = (e_h * 60 + e_m - (s_h * 60 + s_m)) / 60

                        duration = 1.5 if random.random() < 0.7 else 1.0

                        if abs(actual_length - duration) < 0.6 and (day, slot) not in timetable_branch_sem:
                            name, faculty, room, _ = courses[code]
                            timetable_branch_sem[(day, slot)] = (name, faculty, room)
                            remaining[code] -= duration
                            used_today[day].add(code)
                            all_slots.remove((day, slot))

                if branch not in self.timetable:
                    self.timetable[branch] = {}
                self.timetable[branch][sem] = timetable_branch_sem

        messagebox.showinfo("Done", "✅ All timetables generated!")


    def show_timetable(self):
        self.tree.delete(*self.tree.get_children())
        branch = self.display_branch.get()
        sem = self.display_sem.get()

        if branch in self.timetable and sem in self.timetable[branch]:
            def sort_key(item):
                (day, slot) = item[0]
                sh, sm = map(int, slot.split("-")[0].split(":"))
                return (DAYS.index(day), sh, sm)

            for (day, slot), (course, faculty, room) in sorted(self.timetable[branch][sem].items(), key=sort_key):
                self.tree.insert("", "end", values=(day, slot, course, faculty, room))
        else:
            messagebox.showwarning("Not Found", "⚠ No timetable found for this Branch & Semester")


    def export_csv(self):
        for branch, sems in self.timetable.items():
            for sem, table in sems.items():
                fname = f"timetable_{branch}_Sem{sem}.csv"
                with open(fname, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Day", "Slot", "Course", "Faculty", "Room"])
                    for (day, slot), (course, faculty, room) in table.items():
                        writer.writerow([day, slot, course, faculty, room])
        messagebox.showinfo("Exported", "📤 All timetables exported as CSV files!")


if __name__ == "__main__":
    root = tk.Tk()
    app = TimetableApp(root)
    root.mainloop()
