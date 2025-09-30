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
        self.root.geometry("850x650")
        self.root.configure(bg="#f2f6ff")

        self.courses = {}
        self.timetable = {}

        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Treeview styling
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
        """Helper to create modern buttons with hover effects"""
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

        # Add course button
        self.styled_button(self.root, "➕ Add Course", self.add_course).pack(pady=12)

        # Timetable view
        self.tree = ttk.Treeview(
            self.root,
            columns=("Day", "Slot", "Course", "Faculty", "Room"),
            show="headings"
        )
        for col in ("Day", "Slot", "Course", "Faculty", "Room"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="center")
        self.tree.pack(pady=10, fill="both", expand=True)

        # Bottom buttons
        btn_frame = tk.Frame(self.root, bg="#f2f6ff")
        btn_frame.pack(pady=15)

        self.styled_button(btn_frame, "⚡ Generate Timetable", self.generate_timetable).grid(row=0, column=0, padx=12)
        self.styled_button(btn_frame, "📤 Export CSV", self.export_csv).grid(row=0, column=1, padx=12)

    def add_course(self):
        try:
            code = self.entries["Course Code"].get().strip()
            name = self.entries["Course Name"].get().strip()
            faculty = self.entries["Faculty"].get().strip()
            room = self.entries["Room"].get().strip()
            hours = int(self.entries["Hours/Week"].get().strip())

            if not code or not name or not faculty or not room:
                raise ValueError("Empty fields")

            self.courses[code] = [name, faculty, room, hours]
            messagebox.showinfo("Success", f"✅ Course {name} ({hours} hrs/week) added")

            for e in self.entries.values():
                e.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"❌ Invalid input: {e}")

    def generate_timetable(self):
        self.tree.delete(*self.tree.get_children())
        self.timetable.clear()

        all_slots = [(day, slot) for day in DAYS for slot in SLOTS]
        random.shuffle(all_slots)

        remaining = {code: data[3] for code, data in self.courses.items()}
        used_today = {day: set() for day in DAYS}

        while any(hrs > 0 for hrs in remaining.values()) and all_slots:
            for code in list(self.courses.keys()):
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

                if abs(actual_length - duration) < 0.6 and (day, slot) not in self.timetable:
                    name, faculty, room, _ = self.courses[code]
                    self.timetable[(day, slot)] = (name, faculty, room)
                    remaining[code] -= duration
                    used_today[day].add(code)
                    all_slots.remove((day, slot))

        def sort_key(item):
            (day, slot) = item[0]
            sh, sm = map(int, slot.split("-")[0].split(":"))
            return (DAYS.index(day), sh, sm)

        for (day, slot), (course, faculty, room) in sorted(self.timetable.items(), key=sort_key):
            self.tree.insert("", "end", values=(day, slot, course, faculty, room))

    def export_csv(self):
        with open("weekly_timetable.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Day", "Slot", "Course", "Faculty", "Room"])
            for (day, slot), (course, faculty, room) in self.timetable.items():
                writer.writerow([day, slot, course, faculty, room])


if __name__ == "__main__":
    root = tk.Tk()
    app = TimetableApp(root)
    root.mainloop()
