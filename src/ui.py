# ui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from .scheduler import TimetableScheduler, ExamScheduler
from .csv_import import load_classrooms, load_courses
from .utils import export_to_csv, export_exam_schedule, DAYS

class TimetableApp:
    def __init__(self, notebook):
        self.notebook = notebook
        self.setup_styles()
        
        # data stores
        self.courses = {}     # structure: courses[branch][sem][code] = {...}
        self.classrooms = []  # list of classroom dicts
        self.timetable = {}
        self.exam_schedule = []
        
        self.setup_class_tab()
        self.setup_exam_tab()

    def setup_styles(self):
        style = ttk.Style()
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

    def create_scrollable_frame(self, parent):
        """Create a scrollable frame with canvas and scrollbar"""
        # Create main frame
        main_frame = tk.Frame(parent)
        main_frame.pack(fill="both", expand=True)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_frame, bg="#f0f3f7")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f3f7")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel binding
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        return scrollable_frame

    def setup_class_tab(self):
        """Setup class timetable scheduling tab."""
        class_frame = ttk.Frame(self.notebook)
        self.notebook.add(class_frame, text="🏫 Class Scheduling")
        
        # Create scrollable container
        container = self.create_scrollable_frame(class_frame)
        
        # Title
        title_frame = tk.Frame(container, bg="#0052cc", height=70)
        title_frame.pack(fill="x", pady=(0, 15))
        tk.Label(title_frame, text="📅 Automated Timetable Scheduler",
                 font=("Segoe UI", 22, "bold"), bg="#0052cc", fg="white").pack(pady=15)

        # Main content frame
        content_frame = tk.Frame(container, bg="#f0f3f7")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Left panel - Forms and controls
        left_panel = tk.Frame(content_frame, bg="#f0f3f7")
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        # Toggle: manual vs CSV
        toggle_frame = tk.Frame(left_panel, bg="#f0f3f7")
        toggle_frame.pack(fill="x", pady=(0, 10))
        
        self.import_mode = tk.StringVar(value="manual")
        tk.Radiobutton(toggle_frame, text="Manual Add", variable=self.import_mode, value="manual",
                       bg="#f0f3f7", command=self._on_mode_change).pack(side="left", padx=5)
        tk.Radiobutton(toggle_frame, text="Import CSVs", variable=self.import_mode, value="csv",
                       bg="#f0f3f7", command=self._on_mode_change).pack(side="left", padx=5)

        # CSV buttons (hidden until CSV mode)
        self.csv_btn_frame = tk.Frame(left_panel, bg="#f0f3f7")
        self.styled_button(self.csv_btn_frame, "Load Classrooms CSV", 
                          self.load_classrooms_csv, color="#28a745").pack(side="left", padx=2)
        self.styled_button(self.csv_btn_frame, "Load Courses CSV", 
                          self.load_courses_csv, color="#28a745").pack(side="left", padx=2)
        self.csv_btn_frame.pack_forget()  # hide initially

        # ADD COURSE form
        form_frame = tk.LabelFrame(left_panel, text="➕ Add New Course",
                                   font=("Segoe UI", 13, "bold"),
                                   bg="#ffffff", fg="#222",
                                   padx=20, pady=10, relief="groove")
        form_frame.pack(fill="x", pady=(0, 10))

        labels = ["Course Code", "Course Name", "Faculty", "Class Room",
                  "Lecture Hours", "Tutorial Hours", "Lab Hours"]
        self.entries = {}
        for i, lbl in enumerate(labels):
            row_frame = tk.Frame(form_frame, bg="#ffffff")
            row_frame.pack(fill="x", pady=5)
            
            tk.Label(row_frame, text=lbl, font=("Segoe UI", 10, "bold"),
                     bg="#ffffff", fg="#444", width=15, anchor="e").pack(side="left", padx=(0, 10))
            entry = tk.Entry(row_frame, font=("Segoe UI", 10), width=25,
                             relief="solid", bd=1, bg="#f9f9f9")
            entry.pack(side="left", fill="x", expand=True)
            self.entries[lbl] = entry

        # Lab Room
        lab_row_frame = tk.Frame(form_frame, bg="#ffffff")
        lab_row_frame.pack(fill="x", pady=5)
        tk.Label(lab_row_frame, text="Lab Room", font=("Segoe UI", 10, "bold"),
                 bg="#ffffff", fg="#444", width=15, anchor="e").pack(side="left", padx=(0, 10))
        lab_entry = tk.Entry(lab_row_frame, font=("Segoe UI", 10), width=25,
                             relief="solid", bd=1, bg="#f9f9f9")
        lab_entry.pack(side="left", fill="x", expand=True)
        self.entries["Lab Room"] = lab_entry

        # Branch, Semester, Type
        combo_frame = tk.Frame(form_frame, bg="#ffffff")
        combo_frame.pack(fill="x", pady=5)
        
        # Branch
        branch_frame = tk.Frame(combo_frame, bg="#ffffff")
        branch_frame.pack(fill="x", pady=2)
        tk.Label(branch_frame, text="Branch", font=("Segoe UI", 10, "bold"),
                 bg="#ffffff", width=15, anchor="e").pack(side="left", padx=(0, 10))
        self.branch_var = tk.StringVar()
        branch_cb = ttk.Combobox(branch_frame, textvariable=self.branch_var,
                                 values=["CSE-A", "CSE-B", "CSE", "DSAI", "ECE", "ALL"], 
                                 state="readonly", width=23)
        branch_cb.pack(side="left", fill="x", expand=True)
        branch_cb.current(0)

        # Semester
        sem_frame = tk.Frame(combo_frame, bg="#ffffff")
        sem_frame.pack(fill="x", pady=2)
        tk.Label(sem_frame, text="Semester", font=("Segoe UI", 10, "bold"),
                 bg="#ffffff", width=15, anchor="e").pack(side="left", padx=(0, 10))
        self.sem_var = tk.StringVar()
        sem_cb = ttk.Combobox(sem_frame, textvariable=self.sem_var,
                              values=[str(i) for i in range(1, 9)], state="readonly", width=23)
        sem_cb.pack(side="left", fill="x", expand=True)
        sem_cb.current(0)

        # Course Type
        type_frame = tk.Frame(combo_frame, bg="#ffffff")
        type_frame.pack(fill="x", pady=2)
        tk.Label(type_frame, text="Course Type", font=("Segoe UI", 10, "bold"),
                 bg="#ffffff", width=15, anchor="e").pack(side="left", padx=(0, 10))
        self.type_var = tk.StringVar(value="core")
        type_cb = ttk.Combobox(type_frame, textvariable=self.type_var,
                               values=["core", "elective", "minor"], state="readonly", width=23)
        type_cb.pack(side="left", fill="x", expand=True)

        # Action Buttons
        btn_frame = tk.Frame(left_panel, bg="#f0f3f7")
        btn_frame.pack(fill="x", pady=10)
        
        self.styled_button(btn_frame, "➕ Add Course", self.add_course).pack(fill="x", pady=2)
        self.styled_button(btn_frame, "⚡ Generate Timetable", self.generate_all, color="#28a745").pack(fill="x", pady=2)
        self.styled_button(btn_frame, "📖 Show Timetable", self.show_timetable, color="#6f42c1").pack(fill="x", pady=2)
        self.styled_button(btn_frame, "📤 Export CSV", self.export_csv, color="#e83e8c").pack(fill="x", pady=2)

        # Edit/Remove Section
        edit_frame = tk.LabelFrame(left_panel, text="🛠 Edit / Remove Courses",
                                   font=("Segoe UI", 13, "bold"), bg="#ffffff", fg="#222",
                                   padx=20, pady=10, relief="groove")
        edit_frame.pack(fill="x", pady=(10, 0))

        # Branch selection for edit
        edit_branch_frame = tk.Frame(edit_frame, bg="#ffffff")
        edit_branch_frame.pack(fill="x", pady=5)
        tk.Label(edit_branch_frame, text="Branch:", font=("Segoe UI", 10, "bold"), 
                 bg="#ffffff", width=10, anchor="e").pack(side="left", padx=(0, 10))
        self.edit_branch_var = tk.StringVar()
        self.edit_branch_cb = ttk.Combobox(edit_branch_frame, textvariable=self.edit_branch_var,
                                      values=["CSE-A", "CSE-B", "CSE", "DSAI", "ECE"], 
                                      state="readonly", width=15)
        self.edit_branch_cb.pack(side="left", fill="x", expand=True)
        self.edit_branch_cb.current(0)

        # Semester selection for edit
        edit_sem_frame = tk.Frame(edit_frame, bg="#ffffff")
        edit_sem_frame.pack(fill="x", pady=5)
        tk.Label(edit_sem_frame, text="Semester:", font=("Segoe UI", 10, "bold"), 
                 bg="#ffffff", width=10, anchor="e").pack(side="left", padx=(0, 10))
        self.edit_sem_var = tk.StringVar()
        self.edit_sem_cb = ttk.Combobox(edit_sem_frame, textvariable=self.edit_sem_var,
                                   values=[str(i) for i in range(1, 9)], state="readonly", width=15)
        self.edit_sem_cb.pack(side="left", fill="x", expand=True)
        self.edit_sem_cb.current(0)

        # Course selection for edit
        edit_course_frame = tk.Frame(edit_frame, bg="#ffffff")
        edit_course_frame.pack(fill="x", pady=5)
        tk.Label(edit_course_frame, text="Course:", font=("Segoe UI", 10, "bold"), 
                 bg="#ffffff", width=10, anchor="e").pack(side="left", padx=(0, 10))
        self.edit_course_var = tk.StringVar()
        self.course_cb = ttk.Combobox(edit_course_frame, textvariable=self.edit_course_var, 
                                     state="readonly", width=15)
        self.course_cb.pack(side="left", fill="x", expand=True)

        # Edit action buttons
        edit_btn_frame = tk.Frame(edit_frame, bg="#ffffff")
        edit_btn_frame.pack(fill="x", pady=10)
        
        self.styled_button(edit_btn_frame, "🔃 Refresh List", self.refresh_course_list, color="#6c757d").pack(side="left", fill="x", expand=True, padx=2)
        self.styled_button(edit_btn_frame, "🔄 Load Course", self.load_course_for_edit, color="#17a2b8").pack(side="left", fill="x", expand=True, padx=2)
        
        edit_btn_frame2 = tk.Frame(edit_frame, bg="#ffffff")
        edit_btn_frame2.pack(fill="x", pady=5)
        self.styled_button(edit_btn_frame2, "💾 Save Changes", self.save_course_edit, color="#007bff").pack(side="left", fill="x", expand=True, padx=2)
        self.styled_button(edit_btn_frame2, "❌ Remove Course", self.remove_course, color="#dc3545").pack(side="left", fill="x", expand=True, padx=2)

        # Right panel - Timetable viewer
        right_panel = tk.Frame(content_frame, bg="#f0f3f7")
        right_panel.pack(side="left", fill="both", expand=True)

        # Timetable viewer
        table_frame = tk.LabelFrame(right_panel, text="📊 Timetable Viewer",
                                    font=("Segoe UI", 13, "bold"),
                                    bg="#ffffff", fg="#222",
                                    relief="groove")
        table_frame.pack(fill="both", expand=True)

        # Filter frame
        filter_frame = tk.Frame(table_frame, bg="#ffffff")
        filter_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(filter_frame, text="Branch:", font=("Segoe UI", 10, "bold"), bg="#ffffff").pack(side="left", padx=5)
        self.display_branch = tk.StringVar()
        self.display_branch_cb = ttk.Combobox(filter_frame, textvariable=self.display_branch,
                                         values=["CSE-A", "CSE-B", "CSE", "DSAI", "ECE"], 
                                         state="readonly", width=12)
        self.display_branch_cb.pack(side="left", padx=5)
        self.display_branch_cb.current(0)

        tk.Label(filter_frame, text="Semester:", font=("Segoe UI", 10, "bold"), bg="#ffffff").pack(side="left", padx=5)
        self.display_sem = tk.StringVar()
        self.display_sem_cb = ttk.Combobox(filter_frame, textvariable=self.display_sem,
                                      values=[str(i) for i in range(1, 9)], state="readonly", width=12)
        self.display_sem_cb.pack(side="left", padx=5)
        self.display_sem_cb.current(0)

        # Treeview with scrollbars
        tree_container = tk.Frame(table_frame)
        tree_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(tree_container,
                                 columns=("Day", "Slot", "Code", "Course", "Faculty", "Type", "Room"),
                                 show="headings")
        
        # Configure columns
        columns = {
            "Day": 80, "Slot": 120, "Code": 100, 
            "Course": 200, "Faculty": 150, "Type": 80, "Room": 80
        }
        for col, width in columns.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")

        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # Grid layout for tree and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Configure tag colors including combined courses
        self.tree.tag_configure('oddrow', background="#f9f9f9")
        self.tree.tag_configure('evenrow', background="#eef6ff")
        self.tree.tag_configure('combined', background="#e8f5e8")  # Light green for combined courses

    def setup_exam_tab(self):
        """Setup exam scheduling tab."""
        exam_frame = ttk.Frame(self.notebook)
        self.notebook.add(exam_frame, text="📝 Exam Scheduling")
        
        # Create scrollable container
        container = self.create_scrollable_frame(exam_frame)
        
        # Title
        title_frame = tk.Frame(container, bg="#dc3545", height=70)
        title_frame.pack(fill="x", pady=(0, 15))
        tk.Label(title_frame, text="📝 Automatic Exam Scheduler",
                 font=("Segoe UI", 22, "bold"), bg="#dc3545", fg="white").pack(pady=15)

        # Content frame
        content_frame = tk.Frame(container, bg="#f0f3f7")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Controls frame
        control_frame = tk.Frame(content_frame, bg="#f0f3f7")
        control_frame.pack(fill="x", pady=10)
        
        self.styled_button(control_frame, "🎯 Generate Exam Schedule", 
                          self.generate_exam_schedule, color="#dc3545").pack(side="left", padx=5)
        self.styled_button(control_frame, "📤 Export Exam CSV", 
                          self.export_exam_csv, color="#e83e8c").pack(side="left", padx=5)
        
        # Info frame
        info_frame = tk.LabelFrame(content_frame, text="ℹ️ Exam Information",
                                  font=("Segoe UI", 12, "bold"), bg="#ffffff",
                                  padx=10, pady=10)
        info_frame.pack(fill="x", pady=10)
        
        info_text = """• Exam slots: 9:00-12:00, 14:00-17:00, 18:00-21:00
• No two exams for same branch/semester at same time
• Room capacity constraints enforced
• Labs typically not included in theory exams"""
        
        tk.Label(info_frame, text=info_text, font=("Segoe UI", 10), 
                 bg="#ffffff", justify="left", anchor="w").pack(fill="x")
        
        # Exam schedule display
        table_frame = tk.LabelFrame(content_frame, text="📊 Exam Schedule",
                                   font=("Segoe UI", 13, "bold"), bg="#ffffff",
                                   relief="groove")
        table_frame.pack(fill="both", expand=True, pady=10)

        tree_container = tk.Frame(table_frame)
        tree_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.exam_tree = ttk.Treeview(tree_container,
                                 columns=("Day", "Time Slot", "Course Code", "Course Name", 
                                         "Branch", "Semester", "Room"),
                                 show="headings")
        
        columns = {
            "Day": 80, "Time Slot": 120, "Course Code": 120, 
            "Course Name": 200, "Branch": 80, "Semester": 80, "Room": 100
        }
        
        for col, width in columns.items():
            self.exam_tree.heading(col, text=col)
            self.exam_tree.column(col, width=width, anchor="center")
        
        v_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.exam_tree.yview)
        h_scroll = ttk.Scrollbar(tree_container, orient="horizontal", command=self.exam_tree.xview)
        self.exam_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Grid layout
        self.exam_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        self.exam_tree.tag_configure('oddrow', background="#f9f9f9")
        self.exam_tree.tag_configure('evenrow', background="#fff0f0")

    # --- UI helpers ---
    def _on_mode_change(self):
        mode = self.import_mode.get()
        if mode == "csv":
            self.csv_btn_frame.pack(fill="x", pady=5)
        else:
            self.csv_btn_frame.pack_forget()

    def load_classrooms_csv(self):
        path = filedialog.askopenfilename(title="Select Classrooms CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        classrooms = load_classrooms(path)
        if classrooms:
            self.classrooms = classrooms
            messagebox.showinfo("Loaded", f"✅ Loaded {len(classrooms)} classrooms.")
        else:
            messagebox.showwarning("No Data", "⚠ No classrooms loaded.")

    def load_courses_csv(self):
        path = filedialog.askopenfilename(title="Select Courses CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return

        normalized, courses_dict = load_courses(path)
        if normalized:
            self.courses = courses_dict
            # Update branch comboboxes
            branches = list(courses_dict.keys())
            self.display_branch_cb['values'] = branches
            self.edit_branch_cb['values'] = branches
            if branches:
                self.display_branch_cb.current(0)
                self.edit_branch_cb.current(0)
            messagebox.showinfo("Success", f"✅ Loaded {len(normalized)} course entries")
        else:
            messagebox.showwarning("No Data", "⚠ No courses loaded.")

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
            course_type = self.type_var.get()

            if not all([code, name, faculty, branch, sem]):
                raise ValueError("Empty required fields detected.")
            if lab > 0 and not lab_room:
                raise ValueError("Lab room required for non-zero Lab Hours")

            self.courses.setdefault(branch, {}).setdefault(sem, {})
            self.courses[branch][sem][code] = {
                "name": name, "faculty": faculty,
                "class_room": class_room, "lab_room": lab_room,
                "lecture_hours": lec, "tutorial_hours": tut, "lab_hours": lab,
                "students": 0,  # manual add doesn't have students field
                "type": course_type
            }
            messagebox.showinfo("Success", f"✅ Added {name} for {branch} Sem-{sem}")
            
            # Clear form
            for e in self.entries.values():
                e.delete(0, tk.END)
            self.refresh_course_list()
            
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
            self.entries["Course Name"].insert(0, data.get("name", ""))
            self.entries["Faculty"].insert(0, data.get("faculty", ""))
            self.entries["Class Room"].insert(0, data.get("class_room", ""))
            self.entries["Lab Room"].insert(0, data.get("lab_room", ""))
            self.entries["Lecture Hours"].insert(0, data.get("lecture_hours", 0))
            self.entries["Tutorial Hours"].insert(0, data.get("tutorial_hours", 0))
            self.entries["Lab Hours"].insert(0, data.get("lab_hours", 0))
            self.branch_var.set(branch)
            self.sem_var.set(sem)
            self.type_var.set(data.get("type", "core"))
            messagebox.showinfo("Loaded", f"✅ Course {code} loaded for editing.")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Could not load course: {e}")

    def save_course_edit(self):
        try:
            # Get the original code before potentially changing it
            original_code = self.edit_course_var.get()
            original_branch = self.edit_branch_var.get()
            original_sem = self.edit_sem_var.get()
            
            # Use add_course logic which will overwrite
            self.add_course()
            
            # If code was changed, remove the old entry
            new_code = self.entries["Course Code"].get().strip()
            if (original_code != new_code and 
                original_branch in self.courses and 
                original_sem in self.courses[original_branch] and
                original_code in self.courses[original_branch][original_sem]):
                del self.courses[original_branch][original_sem][original_code]
                
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

    # TIMETABLE generation and viewing
    def generate_all(self):
        if not self.courses:
            messagebox.showwarning("Warning", "Please add courses first (manually or via CSV)")
            return
            
        scheduler = TimetableScheduler(self.courses, classrooms=self.classrooms)
        self.timetable, unscheduled = scheduler.generate_timetable(notify=False)
        
        if self.timetable:
            branches = list(self.timetable.keys())
            self.display_branch_cb['values'] = branches
            if branches:
                self.display_branch.set(branches[0])
                sems = list(self.timetable[branches[0]].keys())
                if sems:
                    self.display_sem.set(sems[0])
        
        if unscheduled:
            warn_list = "\n".join([f"{b} Sem-{s}: {c} ({t})" for b, s, c, t in unscheduled])
            messagebox.showwarning("Unscheduled Courses", f"⚠ Some couldn't be scheduled:\n\n{warn_list}")
        else:
            branches = list(self.timetable.keys())
            branch_info = ", ".join(branches)
            messagebox.showinfo(
                "Success", 
                f"✅ All timetables generated successfully!\n"
                f"Branches: {branch_info}\n"
                f"Total timetables: {sum(len(sems) for sems in self.timetable.values())}"
            )

    def show_timetable(self):
        self.tree.delete(*self.tree.get_children())
        branch = self.display_branch.get()
        sem = self.display_sem.get()
        if not branch or not sem:
            messagebox.showwarning("Select", "⚠ Please select Branch and Semester first")
            return

        if branch in self.timetable and sem in self.timetable[branch]:
            table = self.timetable[branch][sem]
            
            # Sort by day and time slot
            sorted_items = sorted(table.items(), key=lambda kv: (DAYS.index(kv[0][0]), kv[0][1]))
            
            for idx, ((day, slot), (code, name, faculty, ctype, room)) in enumerate(sorted_items):
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                
                # NEW: Highlight combined courses for CSE sections
                if branch in ["CSE-A", "CSE-B"] and self._is_combined_course(branch, sem, code):
                    tag = 'combined'
                
                self.tree.insert("", "end",
                                 values=(day, slot, code, name, faculty, ctype, room),
                                 tags=(tag,))
            
            # Auto-resize columns
            self._auto_resize_columns()
        else:
            messagebox.showwarning("Not Found", "⚠ No timetable found for this Branch & Semester")

    def _is_combined_course(self, branch, sem, code):
        """Check if a course is combined between CSE-A and CSE-B."""
        if branch not in ["CSE-A", "CSE-B"]:
            return False
        
        other_branch = "CSE-B" if branch == "CSE-A" else "CSE-A"
        
        # Check if course exists in both branches at the same time
        if (branch in self.timetable and sem in self.timetable[branch] and
            other_branch in self.timetable and sem in self.timetable[other_branch]):
            
            # Get all slots for this course in current branch
            current_slots = [slot for slot, (c_code, _, _, _, _) in self.timetable[branch][sem].items() 
                            if c_code == code]
            
            # Check if any slot exists in other branch for same course
            for slot in current_slots:
                if (slot in self.timetable[other_branch][sem] and 
                    self.timetable[other_branch][sem][slot][0] == code):
                    return True
        
        return False

    def _auto_resize_columns(self):
        """Auto-resize treeview columns to fit content."""
        for col in self.tree["columns"]:
            max_width = max(
                [len(str(self.tree.heading(col)['text']))] +
                [len(str(self.tree.set(k, col))) for k in self.tree.get_children()]
            )
            self.tree.column(col, width=min(max_width * 10, 300))

    def export_csv(self):
        if not self.timetable:
            messagebox.showwarning("Warning", "Please generate timetable first")
            return
        result = export_to_csv(self.timetable)
        messagebox.showinfo("Exported", result)

    def generate_exam_schedule(self):
        if not self.courses:
            messagebox.showwarning("Warning", "Please load courses first")
            return
            
        exam_scheduler = ExamScheduler(self.courses, self.classrooms)
        self.exam_schedule = exam_scheduler.generate_exam_schedule()
        
        # Display in treeview
        self.exam_tree.delete(*self.exam_tree.get_children())
        for idx, exam in enumerate(self.exam_schedule):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            self.exam_tree.insert("", "end", values=(
                exam['day'], exam['slot'], exam['code'], exam['name'],
                exam['branch'], exam['semester'], exam['room']
            ), tags=(tag,))
        
        messagebox.showinfo("Success", f"Generated exam schedule with {len(self.exam_schedule)} exams")

    def export_exam_csv(self):
        if not hasattr(self, 'exam_schedule') or not self.exam_schedule:
            messagebox.showwarning("Warning", "No exam schedule to export")
            return
            
        result = export_exam_schedule(self.exam_schedule)
        messagebox.showinfo("Exported", result)