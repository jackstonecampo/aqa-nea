import tkinter as tk
from tkinter import filedialog, ttk
from ttkwidgets.autocomplete import AutocompleteCombobox
import os
import csv
from timetable_generator import ScheduleManager, DatabaseManager

class ExportWindow:
    def __init__(self, master, db_file):

        self.db_manager = DatabaseManager(db_file)

        self.master = master
        master.title("Export Data")

        self.label1 = tk.Label(master, text="Select category:")
        self.label1.pack()

        self.category_combobox = AutocompleteCombobox(master)
        self.category_combobox.pack()
        self.category_combobox.bind("<<ComboboxSelected>>", self.populate_items)
        self.category_var = tk.StringVar()

        self.item_combobox = AutocompleteCombobox(master)
        self.item_combobox.pack()

        self.category_combobox.set_completion_list(["Pupil", "Teacher"])


        self.export_button = tk.Button(master, text="Export", command=self.export_data)
        self.export_button.pack()

        self.batch_export_button = tk.Button(master, text="Batch Export", command=self.batch_export_data)
        self.batch_export_button.pack()

        self.export_status_label = tk.Label(master, text="")
        self.export_status_label.pack()

    def populate_items(self, event=None):
        selected_category = self.category_combobox.get()
        if selected_category == "Pupil":
            pupil_names = self.db_manager.get_pupil_names()
            self.item_combobox.set_completion_list(pupil_names)

        elif selected_category == "Teacher":
            teacher_names = self.db_manager.get_teacher_names()
            self.item_combobox.set_completion_list(teacher_names)

    def export_data(self):
        selected_category = self.category_combobox.get()
        selected_item = self.item_combobox.get()

        if selected_category == "Pupil":
            pupil_id = self.db_manager.get_pupil_id(selected_item)
            first_name, last_name = selected_item.split()
            default_filename = f"Pupil{pupil_id}{last_name}{first_name}.csv"
            schedule_data = self.db_manager.get_pupil_schedule(selected_item)

        elif selected_category == "Teacher":
            teacher_id = self.db_manager.get_teacher_id(selected_item)
            first_name, last_name = selected_item.split()
            default_filename = f"Teacher{teacher_id}{last_name}{first_name}.csv"
            schedule_data = self.db_manager.get_teacher_schedule(selected_item)

        if schedule_data:

            export_dir = "Exports"
            os.makedirs(export_dir, exist_ok=True)

            filename = os.path.join(export_dir, default_filename)

            if filename:

                schedule_data.sort(key=lambda x: x['PeriodID'])

                with open(filename, 'w', newline='') as csvfile:
                    fieldnames = ["PeriodID", "GroupID", "ClassroomID", "SubjectID"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    writer.writeheader()
                    for row in schedule_data:
                        writer.writerow(row)
                self.export_status_label.config(text=f"Exported Schedule for {selected_item}")
        
    def batch_export_data(self):
        selected_category = self.category_combobox.get()
        items = []

        if selected_category == "Pupil":
            items = self.db_manager.get_pupil_names()
        elif selected_category == "Teacher":
            items = self.db_manager.get_teacher_names()

        print(items)

        for item in items:
            self.item_combobox.set(item)
            self.export_data()
        self.export_status_label.config(text=f"Exported Schedules for all {selected_category}s")


class TimetableGeneratorApp:
    def __init__(self, master):
        self.master = master
        master.title("Timetable Generator")

        self.frame = tk.Frame(master)
        self.frame.pack(pady=20)

        self.selected_file_textbox = tk.Entry(self.frame, width=55)
        self.selected_file_textbox.grid(row=0, column=2)

        self.select_button = tk.Button(self.frame, text="Select Database File", command=self.select_file)
        self.select_button.grid(row=0, column=1, padx=10)

        self.export_button = tk.Button(master, text="Export Data", command=self.open_export_window)
        self.export_button.pack(side="right", padx=15)

        self.generate_button = tk.Button(master, text="Generate Timetable", command=self.generate_timetable)
        self.generate_button.pack(side="left", padx=25)

        self.progress_label = tk.Label(master, text="")
        self.progress_label.pack(side="left", pady=25)

    def select_file(self):
        filename = filedialog.askopenfilename(initialdir="/", title="Select File", filetypes=(("Database files", "*.db"), ("All files", "*.*")))
        if filename:
            self.selected_file_textbox.delete(0, tk.END)
            self.selected_file_textbox.insert(0, filename)
        self.update_progress("Selected File! Click 'Generate' to begin")
        self.flash_component(self.generate_button, "lime", 2)

    def create_backup(self, path):
        backup_name = os.path.splitext(os.path.basename(path))[0] + "_backup.db"
        directory = os.path.dirname(path)
        backup_path = os.path.join(directory, backup_name)

        if os.path.exists(backup_path):
            os.remove(backup_path)

        with open(path, 'rb') as file:
            content = file.read()

            with open(backup_path, 'wb') as backup:
                backup.write(content)

    def generate_timetable(self):
        db_path = self.selected_file_textbox.get()

        if db_path == "":
            self.update_progress("Please select a file")
            self.master.after(800, lambda: self.update_progress("Select a Database File"))
            self.flash_component(self.select_button, "yellow", 2)
            return
        
        if not os.path.exists(db_path):
            self.update_progress("File does not exist")
            self.master.after(800, lambda: self.update_progress("Select a Database File"))
            self.flash_component(self.selected_file_textbox, "red", 2)
            return

        schedule_manager = ScheduleManager(db_path)

        self.update_progress("Generating timetable...")
        schedule_manager.assign_slots()

        self.update_progress("Creating Backup...")
        self.create_backup(db_path)

        self.update_progress("Saving...")
        schedule_manager.save_to_table()

        self.update_progress("Complete!")
        self.flash_component(self.master, "lime", 2)
        self.flash_component(self.frame, "lime", 2)

    def open_export_window(self):
        db_path = self.selected_file_textbox.get()
        if db_path == "":
            self.update_progress("Please select a file")
            self.master.after(800, lambda: self.update_progress("Select a Database File"))
            self.flash_component(self.select_button, "yellow", 2)
            return
        
        if not os.path.exists(db_path):
            self.update_progress("File does not exist")
            self.master.after(800, lambda: self.update_progress("Select a Database File"))
            self.flash_component(self.selected_file_textbox, "red", 2)
            return
        
        export_window = tk.Toplevel(self.master)
        export_app = ExportWindow(export_window, db_path)

    def update_progress(self, message):
        self.progress_label.config(text=message)
        self.master.update()

    def flash_component(self, component, colour, count):
        original_colour = component.cget("bg")
        component.config(bg=colour)
        self.master.after(200, lambda: component.config(bg=original_colour))
        if count > 1:
            self.master.after(400, lambda: self.flash_component(component, colour, count - 1))

def main():
    root = tk.Tk()
    root.geometry("500x125")
    root.resizable(False, False)
    app = TimetableGeneratorApp(root)
    app.update_progress("Select a Database File")
    root.mainloop()


if __name__ == "__main__":
    main()
