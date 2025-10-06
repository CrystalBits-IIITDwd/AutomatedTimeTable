# ui.py
import tkinter as tk
from tkinter import ttk, messagebox
from .scheduler import TimetableScheduler
from .utils import export_to_csv, DAYS

class TimetableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎓 Automated Timetable Scheduler")
        self.root.geometry("1450x750")
        self.root.configure(bg="#f0f3f7")

        self.courses = {}
        self.timetable = {}

        self.setup_styles()
        self.setup_ui()

    # === STYLING ===
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
        style.map("Treeview", background=[("selected", "#cce0ff")])

    def styled_button(self, parent, text, command, color="#0052cc"):
        btn = tk.Label(parent, text=text, font=("Segoe UI", 11, "bold"),
                       bg=color, fg="white", padx=20, pady=10,
                       cursor="hand2", relief="flat")
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.config(bg="#003d99"))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn

    # === GUI SETUP ===
    def setup_ui(self):
        # --- TITLE ---
        title_frame = tk.Frame(self.root, bg="#0052cc", height=70)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="📅 Automated Timetable Scheduler",
                 font=("Segoe UI", 22, "bold"), bg="#0052cc", fg="white").pack(pady=15)

        container = tk.Frame(self.root, bg="#f0f3f7")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        # ===== ADD COURSE SECTION =====
        form_frame = tk.LabelFrame(container, text="➕ Add New Course",
                                   font=("Segoe UI", 13, "bold"),
                                   bg="#ffffff", fg="#222",
                                   padx=20, pady=10, relief="groove")
        form_frame.place(x=10, y=10, width=420, height=520)

        labels = ["Course Code", "Course Name", "Faculty", "Class Room",
                  "Lecture Hours", "Tutorial Hours", "Lab Hours"]
        self.entries = {}
        for i, lbl in enumerate(labels):
            tk.Label(form_frame, text=lbl, font=("Segoe UI", 10, "bold"),
                     bg="#ffffff", fg="#444").grid(row=i, column=0, sticky="e", padx=8, pady=6)
            entry = tk.Entry(form_frame, font=("Segoe UI", 10), width=28,
                             relief="solid", bd=1, bg="#f9f9f9")
            entry.grid(row=i, column=1, pady=6, padx=5)
            self.entries[lbl] = entry

        lab_row = labels.index("Lab Hours")
        tk.Label(form_frame, text="Lab Room", font=("Segoe UI", 10, "bold"),
                 bg="#ffffff", fg="#444").grid(row=lab_row+1, column=0, sticky="e", padx=8, pady=6)
        lab_entry = tk.Entry(form_frame, font=("Segoe UI", 10), width=28,
                             relief="solid", bd=1, bg="#f9f9f9")
        lab_entry.grid(row=lab_row+1, column=1, pady=6, padx=5)
        self.entries["Lab Room"] = lab_entry

        base_row = lab_row + 2
        tk.Label(form_frame, text="Branch", font=("Segoe UI", 10, "bold"),
                 bg="#ffffff").grid(row=base_row, column=0, sticky="e", padx=8, pady=6)
        self.branch_var = tk.StringVar()
        branch_cb = ttk.Combobox(form_frame, textvariable=self.branch_var,
                                 values=["CSE", "DSAI", "ECE"], state="readonly", width=25)
        branch_cb.grid(row=base_row, column=1, pady=6)
        branch_cb.current(0)

        tk.Label(form_frame, text="Semester", font=("Segoe UI", 10, "bold"),
                 bg="#ffffff").grid(row=base_row+1, column=0, sticky="e", padx=8, pady=6)
        self.sem_var = tk.StringVar()
        sem_cb = ttk.Combobox(form_frame, textvariable=self.sem_var,
                              values=[str(i) for i in range(1, 9)], state="readonly", width=25)
        sem_cb.grid(row=base_row+1, column=1, pady=6)
        sem_cb.current(0)

        # --- Buttons ---
        btn_frame = tk.Frame(container, bg="#f0f3f7")
        btn_frame.place(x=10, y=540, width=420)
        self.styled_button(btn_frame, "➕ Add Course", self.add_course).grid(row=0, column=0, padx=10, pady=10)
        self.styled_button(btn_frame, "⚡ Generate All", self.generate_all, color="#28a745").grid(row=0, column=1, padx=10, pady=10)
        self.styled_button(btn_frame, "📖 Show Timetable", self.show_timetable, color="#6f42c1").grid(row=1, column=0, padx=10, pady=10)
        self.styled_button(btn_frame, "📤 Export CSV", self.export_csv, color="#e83e8c").grid(row=1, column=1, padx=10, pady=10)

        # ===== TIMETABLE VIEWER =====
        table_frame = tk.LabelFrame(container, text="📊 Timetable Viewer",
                                    font=("Segoe UI", 13, "bold"),
                                    bg="#ffffff", fg="#222",
                                    relief="groove")
        table_frame.place(x=450, y=10, width=760, height=700)

        filter_frame = tk.Frame(table_frame, bg="#ffffff")
        filter_frame.pack(fill="x", pady=5)

        tk.Label(filter_frame, text="Branch:", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=0, column=0, padx=5)
        self.display_branch = tk.StringVar()
        display_branch_cb = ttk.Combobox(filter_frame, textvariable=self.display_branch,
                                         values=["CSE", "DSAI", "ECE"], state="readonly", width=12)
        display_branch_cb.grid(row=0, column=1, padx=5)
        display_branch_cb.current(0)

        tk.Label(filter_frame, text="Semester:", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=0, column=2, padx=5)
        self.display_sem = tk.StringVar()
        display_sem_cb = ttk.Combobox(filter_frame, textvariable=self.display_sem,
                                      values=[str(i) for i in range(1, 9)], state="readonly", width=12)
        display_sem_cb.grid(row=0, column=3, padx=5)
        display_sem_cb.current(0)

        tree_container = tk.Frame(table_frame)
        tree_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(tree_container,
                                 columns=("Day", "Slot", "Code", "Course", "Faculty", "Type", "Room"),
                                 show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")

        h_scroll = tk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        v_scroll = tk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure('oddrow', background="#f9f9f9")
        self.tree.tag_configure('evenrow', background="#eef6ff")

        # ===== EDIT / REMOVE =====
        edit_frame = tk.LabelFrame(container, text="🛠 Edit / Remove Courses",
                                   font=("Segoe UI", 13, "bold"), bg="#ffffff", fg="#222",
                                   padx=20, pady=10, relief="groove")
        edit_frame.place(x=1220, y=10, width=250, height=700)

        tk.Label(edit_frame, text="Branch:", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.edit_branch_var = tk.StringVar()
        edit_branch_cb = ttk.Combobox(edit_frame, textvariable=self.edit_branch_var,
                                      values=["CSE", "DSAI", "ECE"], state="readonly", width=18)
        edit_branch_cb.grid(row=1, column=0, padx=5, pady=5)
        edit_branch_cb.current(0)

        tk.Label(edit_frame, text="Semester:", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.edit_sem_var = tk.StringVar()
        edit_sem_cb = ttk.Combobox(edit_frame, textvariable=self.edit_sem_var,
                                   values=[str(i) for i in range(1, 9)], state="readonly", width=18)
        edit_sem_cb.grid(row=3, column=0, padx=5, pady=5)
        edit_sem_cb.current(0)

        tk.Label(edit_frame, text="Course Code:", font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.edit_course_var = tk.StringVar()
        self.course_cb = ttk.Combobox(edit_frame, textvariable=self.edit_course_var, state="readonly", width=18)
        self.course_cb.grid(row=5, column=0, padx=5, pady=5)
        self.styled_button(edit_frame, "🔄 Load", self.load_course_for_edit, color="#17a2b8").grid(row=6, column=0, padx=5, pady=5)

        self.styled_button(edit_frame, "💾 Save", self.save_course_edit, color="#007bff").grid(row=7, column=0, padx=5, pady=5)
        self.styled_button(edit_frame, "❌ Remove", self.remove_course, color="#dc3545").grid(row=8, column=0, padx=5, pady=5)
        self.styled_button(edit_frame, "🔃 Refresh", self.refresh_course_list, color="#6c757d").grid(row=9, column=0, padx=5, pady=5)

    # === LOGIC ===
    def add_course(self):
        try:
            code = self.entries["Course Code"].get().strip()
            name = self.entries["Course Name"].get().strip()
            faculty = self.entries["Faculty"].get().strip()
            class_room = self.entries["Class Room"].get().strip()
            lab_room = self.entries["Lab Room"].get().strip()
            lec = int(self.entries["Lecture Hours"].get().strip() or 0)
            tut = int(self.entries["Tutorial Hours"].get().strip() or 0)
            lab = int(self.entries["Lab Hours"].get().strip() or 0)
            branch = self.branch_var.get()
            sem = self.sem_var.get()

            if not all([code, name, faculty, class_room, branch, sem]):
                raise ValueError("Empty fields detected. Class Room is required.")
            if lab > 0 and not lab_room:
                raise ValueError("Lab room required for non-zero Lab Hours")

            # ===== DYNAMIC ROOM LOGIC =====
            room = lab_room if lab > 0 else class_room

            self.courses.setdefault(branch, {}).setdefault(sem, {})
            self.courses[branch][sem][code] = {
                "name": name, "faculty": faculty,
                "class_room": class_room, "lab_room": lab_room,
                "lecture_hours": lec, "tutorial_hours": tut, "lab_hours": lab,
                "room": room
            }
            messagebox.showinfo("Success", f"✅ Added {name} ({lec}/{tut}/{lab}) hrs/week for {branch} Sem-{sem}")
            for e in self.entries.values():
                e.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"❌ Invalid input: {e}")

    def refresh_course_list(self):
        branch = self.edit_branch_var.get()
        sem = self.edit_sem_var.get()
        if branch in self.courses and sem in self.courses[branch]:
            course_codes = list(self.courses[branch][sem].keys())
            self.course_cb['values'] = course_codes
            if course_codes:
                self.course_cb.current(0)
        else:
            self.course_cb['values'] = []
            self.edit_course_var.set("")
            messagebox.showinfo("No Courses", "⚠ No courses found for selected Branch & Semester")

    def load_course_for_edit(self):
        branch = self.edit_branch_var.get()
        sem = self.edit_sem_var.get()
        code = self.edit_course_var.get()
        if not (branch and sem and code):
            messagebox.showwarning("Missing", "⚠ Please select branch, semester and course")
            return
        try:
            data = self.courses[branch][sem][code]
            for key, entry in self.entries.items():
                entry.delete(0, tk.END)
            self.entries["Course Code"].insert(0, code)
            self.entries["Course Name"].insert(0, data["name"])
            self.entries["Faculty"].insert(0, data["faculty"])
            self.entries["Class Room"].insert(0, data["class_room"])
            self.entries["Lab Room"].insert(0, data.get("lab_room", ""))
            self.entries["Lecture Hours"].insert(0, data["lecture_hours"])
            self.entries["Tutorial Hours"].insert(0, data["tutorial_hours"])
            self.entries["Lab Hours"].insert(0, data["lab_hours"])
            self.branch_var.set(branch)
            self.sem_var.set(sem)
            messagebox.showinfo("Loaded", f"✅ Course {code} loaded for editing.")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Could not load course: {e}")

    def save_course_edit(self):
        try:
            self.add_course()
            messagebox.showinfo("Saved", "✅ Course changes saved successfully!")
            self.refresh_course_list()
        except Exception as e:
            messagebox.showerror("Error", f"❌ {e}")

    def remove_course(self):
        branch = self.edit_branch_var.get()
        sem = self.edit_sem_var.get()
        code = self.edit_course_var.get()
        if not (branch and sem and code):
            messagebox.showwarning("Missing", "⚠ Please select branch, semester and course first.")
            return
        try:
            if messagebox.askyesno("Confirm", f"Are you sure you want to remove {code}?"):
                del self.courses[branch][sem][code]
                if not self.courses[branch][sem]:
                    del self.courses[branch][sem]
                if not self.courses[branch]:
                    del self.courses[branch]
                messagebox.showinfo("Removed", f"🗑 Course {code} removed successfully.")
                self.refresh_course_list()
        except KeyError:
            messagebox.showerror("Error", "❌ Course not found.")
        except Exception as e:
            messagebox.showerror("Error", f"❌ {e}")

    # === TIMETABLE ===
    def generate_all(self):
        scheduler = TimetableScheduler(self.courses)
        self.timetable, unscheduled = scheduler.generate_timetable(notify=False)
        if self.timetable:
            b = next(iter(self.timetable))
            s = next(iter(self.timetable[b]))
            self.display_branch.set(b)
            self.display_sem.set(s)
        if unscheduled:
            warn_list = "\n".join([f"{b} Sem-{s}: {c} ({t})" for b, s, c, t in unscheduled])
            messagebox.showwarning("Unscheduled Courses", f"⚠ Some couldn’t be scheduled:\n\n{warn_list}")
        else:
            messagebox.showinfo("Done", "✅ All timetables generated successfully!")

    def show_timetable(self):
        self.tree.delete(*self.tree.get_children())
        branch = self.display_branch.get()
        sem = self.display_sem.get()
        if not branch or not sem:
            messagebox.showwarning("Select", "⚠ Please select Branch and Semester first")
            return
        if branch in self.timetable and sem in self.timetable[branch]:
            sorted_items = sorted(
                self.timetable[branch][sem].items(),
                key=lambda kv: (DAYS.index(kv[0][0]), kv[0][1])
            )
            for idx, ((day, slot), (code, name, faculty, ctype, room)) in enumerate(sorted_items):
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                self.tree.insert("", "end",
                                 values=(day, slot, code, name, faculty, ctype, room),
                                 tags=(tag,))
            for col in self.tree["columns"]:
                max_width = max([len(str(self.tree.set(k, col))) for k in self.tree.get_children()] + [len(col)])
                self.tree.column(col, width=max(100, min(max_width*10, 400)))
        else:
            messagebox.showwarning("Not Found", "⚠ No timetable found for this Branch & Semester")

    def export_csv(self):
        export_to_csv(self.timetable)
        messagebox.showinfo("Exported", "✅ All timetables exported to CSV successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    app = TimetableApp(root)
    root.mainloop()
