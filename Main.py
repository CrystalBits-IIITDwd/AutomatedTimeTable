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
        self.root.geometry("1100x750")
        self.root.configure(bg="#f0f3f7")

        # Data stores
        self.courses = {}
        self.timetable = {}
        self.occupied_rooms = {}

        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("Treeview",
                        background="#ffffff",
                        foreground="#333333",
                        rowheight=28,
                        fieldbackground="#ffffff",
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background="#0052cc",
                        foreground="white",
                        font=("Segoe UI", 11, "bold"))
        style.map("Treeview",
                  background=[("selected", "#cce0ff")])

    def styled_button(self, parent, text, command, color="#0052cc"):
        btn = tk.Label(parent,
                       text=text,
                       font=("Segoe UI", 11, "bold"),
                       bg=color,
                       fg="white",
                       padx=20,
                       pady=10,
                       cursor="hand2",
                       relief="flat")
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.config(bg="#003d99"))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn

    def setup_ui(self):
        # Header
        title_frame = tk.Frame(self.root, bg="#0052cc", height=70)
        title_frame.pack(fill="x")
        title = tk.Label(title_frame,
                        text="📅 Automated Timetable Scheduler",
                        font=("Segoe UI", 22, "bold"),
                        bg="#0052cc",
                        fg="white")
        title.pack(pady=15)

        # Main container
        container = tk.Frame(self.root, bg="#f0f3f7")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        # Left panel: Course entry form
        form_frame = tk.LabelFrame(container,
                                   text="➕ Add New Course",
                                   font=("Segoe UI", 13, "bold"),
                                   bg="#ffffff", fg="#222",
                                   padx=20, pady=10,
                                   relief="groove")
        form_frame.place(x=10, y=10, width=400, height=400)

        labels = ["Course Code", "Course Name", "Faculty", "Room", "Hours/Week"]
        self.entries = {}
        for i, lbl in enumerate(labels):
            tk.Label(form_frame, text=lbl, font=("Segoe UI", 10, "bold"),
                    bg="#ffffff", fg="#444").grid(row=i, column=0, sticky="e", padx=8, pady=6)
            entry = tk.Entry(form_frame, font=("Segoe UI", 10), width=28,
                             relief="solid", bd=1, bg="#f9f9f9")
            entry.grid(row=i, column=1, pady=6, padx=5)
            self.entries[lbl] = entry

        # Branch + Semester
        tk.Label(form_frame, text="Branch", font=("Segoe UI", 10, "bold"),
                bg="#ffffff").grid(row=len(labels), column=0, sticky="e", padx=8, pady=6)
        self.branch_var = tk.StringVar()
        branch_cb = ttk.Combobox(form_frame, textvariable=self.branch_var,
                                values=["CSE", "DSAI", "ECE"],
                                state="readonly", width=25)
        branch_cb.grid(row=len(labels), column=1, pady=6)

        tk.Label(form_frame, text="Semester", font=("Segoe UI", 10, "bold"),
                bg="#ffffff").grid(row=len(labels)+1, column=0, sticky="e", padx=8, pady=6)
        self.sem_var = tk.StringVar()
        sem_cb = ttk.Combobox(form_frame, textvariable=self.sem_var,
                            values=[str(i) for i in range(1, 9)],
                            state="readonly", width=25)
        sem_cb.grid(row=len(labels)+1, column=1, pady=6)

        # Buttons row
        btn_frame = tk.Frame(container, bg="#f0f3f7")
        btn_frame.place(x=10, y=430, width=400)

        self.styled_button(btn_frame, "➕ Add Course", self.add_course).grid(row=0, column=0, padx=10, pady=10)
        self.styled_button(btn_frame, "⚡ Generate All", self.generate_timetable, color="#28a745").grid(row=0, column=1, padx=10, pady=10)

        self.styled_button(btn_frame, "📖 Show Timetable", self.show_timetable, color="#6f42c1").grid(row=1, column=0, padx=10, pady=10)
        self.styled_button(btn_frame, "📤 Export CSV", self.export_csv, color="#e83e8c").grid(row=1, column=1, padx=10, pady=10)

        # Right panel: Timetable display
        table_frame = tk.LabelFrame(container,
                                    text="📊 Timetable Viewer",
                                    font=("Segoe UI", 13, "bold"),
                                    bg="#ffffff", fg="#222",
                                    relief="groove")
        table_frame.place(x=430, y=10, width=640, height=670)

        # Dropdowns for viewing timetable
        filter_frame = tk.Frame(table_frame, bg="#ffffff")
        filter_frame.pack(fill="x", pady=5)

        tk.Label(filter_frame, text="Branch:", font=("Segoe UI", 10, "bold"),
                 bg="#ffffff").grid(row=0, column=0, padx=5)
        self.display_branch = tk.StringVar()
        ttk.Combobox(filter_frame, textvariable=self.display_branch,
                     values=["CSE", "DSAI", "ECE"], state="readonly", width=12).grid(row=0, column=1, padx=5)

        tk.Label(filter_frame, text="Semester:", font=("Segoe UI", 10, "bold"),
                 bg="#ffffff").grid(row=0, column=2, padx=5)
        self.display_sem = tk.StringVar()
        ttk.Combobox(filter_frame, textvariable=self.display_sem,
                     values=[str(i) for i in range(1, 9)], state="readonly", width=12).grid(row=0, column=3, padx=5)

        # Treeview
        self.tree = ttk.Treeview(table_frame,
                                columns=("Day", "Slot", "Course", "Faculty", "Room"),
                                show="headings", height=20)
        for col in ("Day", "Slot", "Course", "Faculty", "Room"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(padx=10, pady=10, fill="both", expand=True)

        # Zebra row styles
        self.tree.tag_configure('oddrow', background="#f9f9f9")
        self.tree.tag_configure('evenrow', background="#eef6ff")

    # === Logic methods ===
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
        self.occupied_rooms.clear()
        unscheduled = []

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
                        success = False
                        for _ in range(100):
                            if not all_slots:
                                break
                            day, slot = random.choice(all_slots)
                            room = courses[code][2]
                            if code in used_today[day]:
                                continue
                            if (day, slot) in self.occupied_rooms and room in self.occupied_rooms[(day, slot)]:
                                continue
                            name, faculty, room, _ = courses[code]
                            timetable_branch_sem[(day, slot)] = (name, faculty, room)
                            remaining[code] -= 1.0
                            used_today[day].add(code)
                            if (day, slot) not in self.occupied_rooms:
                                self.occupied_rooms[(day, slot)] = set()
                            self.occupied_rooms[(day, slot)].add(room)
                            all_slots.remove((day, slot))
                            success = True
                            break
                        if not success:
                            unscheduled.append((branch, sem, courses[code][0]))
                if branch not in self.timetable:
                    self.timetable[branch] = {}
                self.timetable[branch][sem] = timetable_branch_sem

        if unscheduled:
            warn_list = "\n".join([f"{b} Sem-{s}: {c}" for b, s, c in unscheduled])
            messagebox.showwarning("Unscheduled Courses",
                                   f"⚠ Some courses couldn’t be fully scheduled:\n\n{warn_list}")
        else:
            messagebox.showinfo("Done", "✅ All timetables generated (no room collisions)!")

    def show_timetable(self):
        self.tree.delete(*self.tree.get_children())
        branch = self.display_branch.get()
        sem = self.display_sem.get()
        if branch in self.timetable and sem in self.timetable[branch]:
            def sort_key(item):
                (day, slot) = item[0]
                sh, sm = map(int, slot.split("-")[0].split(":"))
                return (DAYS.index(day), sh, sm)
            for idx, ((day, slot), (course, faculty, room)) in enumerate(
                    sorted(self.timetable[branch][sem].items(), key=sort_key)):
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                self.tree.insert("", "end", values=(day, slot, course, faculty, room), tags=(tag,))
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
