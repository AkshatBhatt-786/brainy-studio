import customtkinter as ctk
import sqlite3
import os
import threading
from tkinter import ttk, messagebox
from datetime import datetime
from utils import getPath, centerWindow
from ui_components import Colors, PrimaryButton, IconButton
from create_paper import CreatePaper
from cloud_export import CloudPublishUI

class AdminPanel(ctk.CTkToplevel):
    def __init__(self, subject_db):
        super().__init__()
        self.attributes("-topmost", True)
        self.subject_db = subject_db
        self.create_paper = None
        self._init_config()
        self._init_db()
        self._init_ui()
        self._bind_events()
        self._load_initial_data()

    def _init_config(self):
        self.title("Admin Panel - Brainy Studio")
        self.geometry(centerWindow(self, 1200, 800, self._get_window_scaling(), (0, 150)))
        self.configure(fg_color=Colors.BACKGROUND)
        self.cloud_publish_ui = None

    def _init_db(self):
        self.db_path = getPath("database\\brainy-studio.db")
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def _init_ui(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.tab_view = ctk.CTkTabview(
            self.main_frame, width=1160, height=700,
            fg_color=Colors.Cards.BACKGROUND,
            segmented_button_selected_color=Colors.Buttons.PRIMARY,
            segmented_button_unselected_color=Colors.Cards.SECONDARY
        )
        self.tab_view.pack(pady=10)

        self._create_users_tab()
        self._create_workspaces_tab()
        self._create_exams_tab()
        self._create_status_bar()

    def _create_users_tab(self):
        self.users_tab = self.tab_view.add("👥 Users")
        
        header = ctk.CTkFrame(self.users_tab, fg_color="transparent")
        header.pack(fill="x", pady=10)
        
        ctk.CTkLabel(header, text="User Management", 
                    font=("Arial", 20, "bold"),
                    text_color=Colors.Texts.HEADERS).pack(side="left")

        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.pack(side="right")
        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Search users...",
            width=300, border_color=Colors.Inputs.BORDER
        )
        self.search_entry.pack(side="left", padx=5)

        self.users_container = ctk.CTkScrollableFrame(
            self.users_tab, fg_color=Colors.Cards.SECONDARY, 
            width=1120, height=500
        )
        self.users_container.pack(pady=10)

    def _create_workspaces_tab(self):
        self.workspaces_tab = self.tab_view.add("📁 Workspaces")
        split_frame = ctk.CTkFrame(self.workspaces_tab, fg_color="transparent")
        split_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
            background=Colors.Cards.SECONDARY,
            foreground=Colors.Texts.FIELDS,
            fieldbackground=Colors.Cards.SECONDARY,
            rowheight=30,
            font=("Arial", 12))
        style.configure("Treeview.Heading", 
            background=Colors.Cards.BACKGROUND,
            foreground=Colors.Texts.HEADERS,
            font=("Arial", 14, "bold"))
        style.map("Treeview", 
            background=[('selected', Colors.Buttons.PRIMARY)])

        self.workspace_tree = ttk.Treeview(split_frame, show="tree", selectmode="browse")
        self.workspace_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.file_details = ctk.CTkScrollableFrame(
            split_frame, fg_color=Colors.Cards.SECONDARY,
            width=400
        )
        self.file_details.pack(side="right", fill="both", padx=10, pady=10)

        ctk.CTkLabel(self.file_details, 
            text="File Details",
            font=("Arial", 16, "bold"),
            text_color=Colors.Texts.HEADERS
        ).pack(anchor="w", pady=5)
        
        self.detail_labels = {
            'name': self._create_detail_row("Name:"),
            'path': self._create_detail_row("Path:"),
            'size': self._create_detail_row("Size:"),
            'modified': self._create_detail_row("Last Modified:"),
            'created': self._create_detail_row("Created:"),
            'owner': self._create_detail_row("Owner:")
        }
        init_frame = ctk.CTkFrame(self.workspaces_tab, fg_color="transparent")
        init_frame.pack(pady=50)
        ctk.CTkLabel(init_frame, 
                   text="📂 Select a user workspace to begin\nor check user workspace paths",
                   font=("Arial", 16),
                   text_color=Colors.Texts.MUTED).pack()

    def _create_detail_row(self, label):
        frame = ctk.CTkFrame(self.file_details, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        ctk.CTkLabel(frame, text=label, width=120,
                    text_color=Colors.Texts.MUTED).pack(side="left")
        value_label = ctk.CTkLabel(frame, text="", anchor="w")
        value_label.pack(side="left", fill="x", expand=True)
        return value_label

    def _create_exams_tab(self):
        self.exams_tab = self.tab_view.add("📆 Exams")
        self.exam_list = ctk.CTkScrollableFrame(
            self.exams_tab, fg_color=Colors.Cards.SECONDARY,
            width=1120, height=550
        )
        self.exam_list.pack(pady=10)

    def _create_status_bar(self):
        self.status_bar = ctk.CTkFrame(self.main_frame, height=24, fg_color=Colors.Cards.BACKGROUND)
        self.status_bar.pack(fill="x", pady=(0, 10))

        btn_frame = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)

        PrimaryButton(btn_frame, 
                    text="⟳ Refresh", 
                    width=80, height=24,
                    command=self._refresh_all).pack(side="right", padx=5)

        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready", anchor="w")
        self.status_label.pack(side="left", padx=10)

    def _bind_events(self):
        self.search_entry.bind("<KeyRelease>", self._search_users)
        self.workspace_tree.bind("<<TreeviewSelect>>", self._update_file_details)
        self.workspace_tree.bind("<Double-1>", self._on_file_double_click)

    def _load_initial_data(self):
        threading.Thread(target=self._load_users, daemon=True).start()
        threading.Thread(target=self._load_exams, daemon=True).start()

    def _get_db_connection(self):
        return sqlite3.connect(self.db_path)

    def _load_users(self):
        self._set_status("Loading users...")
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, role, workspace_path FROM users ORDER BY id ASC')
            users = cursor.fetchall()
            conn.close()
            self.after(0, lambda: self._display_users(users))
        except Exception as e:
            self._set_status(f"Error loading users: {str(e)}")


    def check_database(self):
        self.cursor.execute("SELECT * FROM users")
        users = self.cursor.fetchall()

        self.cursor.execute("SELECT * FROM exams")
        exams = self.cursor.fetchall()

        if users:
            for user in users:
                print(f"- {user[3]} ({'Exists' if os.path.exists(user[3]) else 'Missing'})")

    def _display_users(self, users):
        for widget in self.users_container.winfo_children():
            widget.destroy()

        if not users:
            empty_frame = ctk.CTkFrame(self.users_container, fg_color="transparent")
            empty_frame.pack(pady=50)
            ctk.CTkLabel(empty_frame, 
                       text="📭 No users found\n\nCreate new users through the examiner interface",
                       font=("Arial", 16),
                       text_color=Colors.Texts.MUTED).pack()
            return

        for user in users:
            self._create_user_card(user)

    def _create_user_card(self, user):
        card = ctk.CTkFrame(
            self.users_container, 
            fg_color=Colors.Cards.BACKGROUND,
            corner_radius=10
        )
        card.pack(fill="x", pady=5, padx=5)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(info_frame, text=f"👤 {user[1]}", 
                    font=("Arial", 14, "bold"),
                    text_color=Colors.Texts.HEADERS).pack(anchor="w")
        
        ctk.CTkLabel(info_frame, 
                    text=f"🆔 {user[0]} | 🛡️ {user[1]} | 📂 {os.path.basename(user[2])}",
                    text_color=Colors.Texts.MUTED).pack(anchor="w")

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right")
        
        PrimaryButton(btn_frame, 
            text="Promote" if user[1] != 'admin' else "Demote",
            width=100, height=30,
            command=lambda u=user: self._toggle_role(u)
        ).pack(side="left", padx=5)
        
        file_btn = IconButton(btn_frame, 
                 command=lambda p=user[2]: self._load_workspace(p))
        file_btn.pack(side="left", padx=5)
        file_btn.configure(text="📂")
        
        delete_btn = IconButton(btn_frame, 
                 command=lambda u=user: self._delete_user(u[0]))
        delete_btn.pack(side="left", padx=5)
        delete_btn.configure(text="🗑️")

    def _toggle_role(self, user):
        new_role = 'admin' if user[1] != 'admin' else 'examiner'
        try:
            self.cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user[0]))
            self.conn.commit()
            messagebox.showinfo("Success", f"User {user[1]} role updated to {new_role}")
            self._load_users()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))

    def _delete_user(self, user_id):
        if messagebox.askyesno("Confirm", "Permanently delete this user?"):
            try:
                self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                self.conn.commit()
                self._load_users()
                messagebox.showinfo("Success", "User deleted successfully")
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", str(e))

    def _load_workspace(self, path):
        self.tab_view.set("📁 Workspaces")
        self._set_status(f"Loading workspace: {path}")
        threading.Thread(target=self._load_directory_tree, args=(path,), daemon=True).start()

    def _load_directory_tree(self, path):
        self.workspace_tree.delete(*self.workspace_tree.get_children())
        self._populate_tree(path, "")
        self._set_status(f"Loaded workspace: {os.path.basename(path)}")

    def _populate_tree(self, parent_path, parent):
        try:
            for item in os.listdir(parent_path):
                item_path = os.path.join(parent_path, item)
                is_dir = os.path.isdir(item_path)
                oid = self.workspace_tree.insert(parent, "end", text=item, values=(item_path,))
                
                if is_dir:
                    self.workspace_tree.insert(oid, "end", text="Loading...")
                    self.workspace_tree.tag_bind(oid, "<<TreeviewOpen>>",
                                                 lambda e, p=item_path, i=oid: 
                                                 self._on_tree_open(p, i))
        except Exception as e:
            self._set_status(f"Error loading directory: {str(e)}")

    def _on_tree_open(self, path, item):
        self.workspace_tree.delete(*self.workspace_tree.get_children(item))
        self._populate_tree(path, item)

    def _update_file_details(self, event):
        item = self.workspace_tree.selection()[0]
        path = self.workspace_tree.item(item, "values")[0]
        
        if os.path.isfile(path):
            try:
                stat = os.stat(path)
                self.detail_labels['name'].configure(text=os.path.basename(path))
                self.detail_labels['path'].configure(text=path)
                self.detail_labels['size'].configure(text=f"{stat.st_size/1024:.2f} KB")
                self.detail_labels['modified'].configure(text=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"))
                self.detail_labels['created'].configure(text=datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M"))
                self.detail_labels['owner'].configure(text="Admin")  # Add actual owner lookup
            except Exception as e:
                self._set_status(f"Error reading file info: {str(e)}")

    def _load_exams(self):
        self._set_status("Loading exams...")
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT exam_id, access_code, subject_code, exam_title, 
                       registration_start, registration_end, publish_time 
                FROM exams ORDER BY publish_time DESC
            ''')
            exams = cursor.fetchall()
            self.after(0, lambda: self._display_exams(exams))
            conn.close()
            self.after(0, lambda exams=exams: self._display_exams(exams))
        except Exception as e:
            self._set_status(f"Error loading exams: {str(e)}")


    def _display_exams(self, exams):
        for widget in self.exam_list.winfo_children():
            widget.destroy()

        if not exams:
            ctk.CTkLabel(self.exam_list,
                         text="📭 No exams found",
                         font=("Arial", 16),
                         text_color=Colors.Texts.MUTED).pack(pady=50)
            return

        for exam in exams:
            card = ctk.CTkFrame(self.exam_list, fg_color=Colors.Cards.BACKGROUND, corner_radius=10)
            card.pack(fill="x", padx=5, pady=5)

            info = f"🆔 Exam ID: {exam[0]} | 🔑 Access Code: {exam[1]} | Title: {exam[2]}"
            dates = f"🗓️ Start: {exam[4]} ➡️ End: {exam[5]} | Published On: {exam[6]}"
            ctk.CTkLabel(card, text=info, font=("Arial", 14, "bold"),
                         text_color=Colors.Texts.HEADERS).pack(anchor="w", padx=10, pady=2)
            ctk.CTkLabel(card, text=dates, text_color=Colors.Texts.MUTED).pack(anchor="w", padx=10)


    def _create_exam_card(self, exam_data):
        card = ctk.CTkFrame(
            self.exam_list, 
            fg_color=Colors.Cards.BACKGROUND, 
            corner_radius=10
        )
        card.pack(fill="x", pady=5, padx=5)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text=f"🆔 {exam_data[0]}", 
                    font=("Arial", 14, "bold"),
                    text_color=Colors.Texts.HEADERS).pack(side="left")
        
        ctk.CTkLabel(header, text=f"🔑 {exam_data[1]}",
                    text_color=Colors.Texts.MUTED).pack(side="left", padx=20)

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", pady=5)
        
        ctk.CTkLabel(body, text=f"📚 {exam_data[2]}", 
                    text_color=Colors.Texts.MUTED).pack(side="left")
        
        ctk.CTkLabel(body, text=f"📝 {exam_data[3]}",
                    text_color=Colors.Texts.MUTED).pack(side="left", padx=20)

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x")
        
        time_str = f"⏰ {exam_data[4]} - {exam_data[5]}"
        ctk.CTkLabel(footer, text=time_str,
                    text_color=Colors.Texts.MUTED).pack(side="left")
        
        ctk.CTkLabel(footer, text=f"🕒 {exam_data[6]}",
                    text_color=Colors.Texts.MUTED).pack(side="right")

    def _on_file_double_click(self, event):
        item = self.workspace_tree.selection()[0]
        path = self.workspace_tree.item(item, "values")[0]
        
        if os.path.isfile(path) and path.endswith(".enc"):
            self._show_cloud_publish_dialog(path)
    
    def _show_edit_paper_publish_dialog(self, file_path):
        if self.cloud_publish_ui is not None:
            self.cloud_publish_ui.destroy()
        
        self.publish_window = ctk.CTkToplevel(self)
        self.publish_window.title("Edit Paper | View Paper")
        self.publish_window.geometry(centerWindow(self, 1200, 800, self._get_window_scaling(), (0, 150)))
        self.publish_window.grab_set()
        
        self.edit_page = CreatePaper(self.publish_window, parent=self, edit_mode=True, file_path=file_path)
        self.edit_page.pack(padx=10, pady=10, fill="both", expand=True)
        self.edit_page_ui = CloudPublishUI(self.publish_window, self, self.subject_db)
        self.edit_page_ui.pack(fill="both", expand=True)
        

    def _show_cloud_publish_dialog(self, file_path):
        if self.cloud_publish_ui is not None:
            self.cloud_publish_ui.destroy()
            self.attributes("-topmost", True)
        
        publish_window = ctk.CTkToplevel(self)
        self.attributes("-topmost", False)
        publish_window.attributes("-topmost", True)
        publish_window.title("Publish to Cloud")
        publish_window.geometry(centerWindow(self, 1200, 800, self._get_window_scaling(), (0, 150)))
        publish_window.grab_set()
        
        self.cloud_publish_ui = CloudPublishUI(publish_window, self, self.subject_db)
        self.cloud_publish_ui.pack(fill="both", expand=True)
        
        self.cloud_publish_ui.file_entry.delete(0, "end")
        self.cloud_publish_ui.file_entry.insert(0, file_path)
        self.cloud_publish_ui.decrypt_file(file_path)

    def _search_users(self, event):
        query = self.search_entry.get().lower()
        for card in self.users_container.winfo_children():
            user_info = card.winfo_children()[0].winfo_children()[0].cget("text").lower()
            card.pack() if query in user_info else card.pack_forget()

    def _set_status(self, message):
        self.status_label.configure(text=message)
        self.update_idletasks()

    def __del__(self):
        self.conn.close()

    def show_workspace(self, path):
        if not os.path.exists(path):
            messagebox.showerror("Error", f"Workspace path not found:\n{path}")
            return

        try:
            if not any(os.scandir(path)):
                self.file_details.delete("1.0", "end")
                self.file_details.insert("end", "Empty workspace directory")
                return
        except PermissionError:
            messagebox.showerror("Error", f"Permission denied:\n{path}")
            return
    
        self.workspace_tree.delete(*self.workspace_tree.get_children())
        self.populate_tree(path, "")

    def _refresh_all(self):
        self._set_status("Refreshing data...")
        threading.Thread(target=self._load_users).start()
        threading.Thread(target=self._load_exams).start()
    
    def redirect(self, page_name, filepath=None):

        if page_name == "home-page":
            self.title("Brainy Studio v1.0.2 (Beta)")
            if self.create_paper is not None:
                self.publish_window.destroy()
                self.create_paper = None