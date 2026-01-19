import sys
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QHeaderView, QLineEdit, QPushButton, QStackedWidget, QMessageBox,
                            QTableWidget, QTableWidgetItem, QComboBox, QDateEdit, QDialog, 
                            QGridLayout, QRadioButton, QButtonGroup, QStackedWidget, QTextEdit)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtGui import QFont, QColor
from pathlib import Path

from database import services

LOAN_PERIOD_DAYS = 28
GRACE_PERIOD_DAYS = 14

class LibraryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Library Management System")
        self.resize(800, 600)
        
        # Session state
        self.current_user = None
        self.is_staff = False
        self.db_name = "database/library.db"
        
        # Create stacked widget for different views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create all the screens
        self.login_screen = self.create_login_screen()
        self.patron_dashboard = self.create_patron_dashboard()
        self.staff_dashboard = self.create_staff_dashboard()
        self.register_screen = self.create_register_screen()
        
        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.login_screen)
        self.stacked_widget.addWidget(self.register_screen)
        self.stacked_widget.addWidget(self.patron_dashboard)
        self.stacked_widget.addWidget(self.staff_dashboard)
        
        # Start with login screen
        self.stacked_widget.setCurrentWidget(self.login_screen)

        # Dark mode (off by default)
        self.dark_mode = False

        # css coloring for Dark/Light mode
        self.stylesheets = {
            "light": """
                /* Main Window */
                QMainWindow {
                    background-color: #f5f7fa;
                }

                QDialog {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                }

                QDialog QLabel {
                    color: #333333;
                }
                
                /* Text */
                QLabel, QLineEdit, QComboBox, QTableWidget, QRadioButton {
                    color: #333333;
                }
                
                /* Buttons */
                QPushButton {
                    background-color: #5D9CEC;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 15px;
                    border: none;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #4A89DC;
                }
                QPushButton:pressed {
                    background-color: #3B7DD8;
                }
                
                /* Tables */
                QTableWidget {
                    background-color: white;
                    border-radius: 4px;
                    gridline-color: #e0e0e0;
                    alternate-background-color: #f8f9fa;
                    border-right: 1px solid palette(mid);
                    padding: 5px;
                }
                QHeaderView::section {
                    background-color: #5D9CEC;
                    border-right: 1px solid #d0d0d0;
                    border-bottom: 1px solid #d0d0d0;
                    color: white;
                    padding: 5px;
                    border: none;
                }
                
                /* Inputs */
                QLineEdit, QComboBox, QDateEdit {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px;
                    background: white;
                }
            """,
            
            "dark": """
                /* Main Window */
                QMainWindow {
                    background-color: #1e1e2e;
                }

                QDialog {
                    background-color: #383D4C;
                    border: 1px solid #444444;
                }
                
                QDialog QLabel {
                    color: #e0e0e0;
                }                
                
                /* Text */
                QLabel, QLineEdit, QComboBox, QTableWidget, QRadioButton {
                    color: #e0e0e0;
                }
                
                /* Buttons */
                QPushButton {
                    background-color: #14467D;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 15px;
                    border: none;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #285B94;
                }
                QPushButton:pressed {
                    background-color: #042040;
                }
                
                /* Tables */
                QTableWidget {
                    background-color: #2a2a3a;
                    border-radius: 4px;
                    gridline-color: #444444;
                    alternate-background-color: #323242;
                    border-right: 1px solid palette(mid);
                    padding: 5px;
                }
                QHeaderView::section {
                    background-color: #14467D;
                    border-right: 1px solid #3a3a3a;
                    border-bottom: 1px solid #3a3a3a;
                    color: white;
                    padding: 5px;
                    border: none;
                }
                
                /* Inputs */
                QLineEdit, QComboBox, QDateEdit {
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 5px;
                    background: #1e1e2e;
                    color: white;
                }

                /* Dropdown background */
                QComboBox QAbstractItemView {
                    background-color: #2a2a3a;
                    color: white;
                    border: 1px solid #444;
                    selection-background-color: #14467D;
                    padding: 0px;
                }

                QComboBox QAbstractItemView::item {
                    padding: 4px;
                    margin: 0px;
                }
                
            """
        }

        # Apply initial theme
        self.apply_theme()
    
        # Add theme toggle button to both for patron and staff view
        self.add_theme_toggle()
    
    # ----------------------
    # Screen Creation Methods
    # ----------------------

    # Helper function to check get patron_id for dashboard creation
    def get_current_user_id(self):
        """Returns the ID of the currently logged-in patron"""
        return self.current_user  # Ensure this is properly set during login
    
    def create_login_screen(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.login_id_input = QLineEdit()
        self.login_id_input.setPlaceholderText("Enter your ID or Email")
        
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.handle_login)
        
        register_btn = QPushButton("Register")
        register_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.register_screen))
        
        label = (QLabel("Library Login"))
        label.setAlignment(Qt.AlignCenter)
        font = QFont("Arial", 33, QFont.Bold)
        label.setFont(font)

        layout.addWidget(label)
        layout.addWidget(self.login_id_input)
        layout.addWidget(login_btn)
        layout.addWidget(register_btn)
        
        widget.setLayout(layout)
        return widget
    
    def create_register_screen(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.reg_first_name = QLineEdit(placeholderText="First Name")
        self.reg_last_name = QLineEdit(placeholderText="Last Name")
        self.reg_email = QLineEdit(placeholderText="Email")
        
        register_btn = QPushButton("Complete Registration")
        register_btn.clicked.connect(self.handle_registration)
        
        back_btn = QPushButton("Back to Login")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.login_screen))
        
        layout.addWidget(QLabel("New Patron Registration"))
        layout.addWidget(self.reg_first_name)
        layout.addWidget(self.reg_last_name)
        layout.addWidget(self.reg_email)
        layout.addWidget(register_btn)
        layout.addWidget(back_btn)
        
        widget.setLayout(layout)
        return widget
    
    def create_patron_dashboard(self):
        """Patron View"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QHBoxLayout()
        self.patron_greeting = QLabel()
        self.patron_greeting.setFont(QFont("Arial", 14, QFont.Bold))
        
        logout_btn = QPushButton("Logout")
        logout_btn.setFixedWidth(100)
        logout_btn.clicked.connect(self.handle_logout)
        
        header.addWidget(self.patron_greeting)
        header.addStretch()
        header.addWidget(logout_btn)
        
        # Button Grid
        btn_grid = QGridLayout()
        btn_grid.setSpacing(10)
        
        buttons = [
            ("📚 Browse Items", self.show_available_items),
            ("💬 Need help browsing?", self.show_staff_help_dialog),
            ("🔄 Borrow Item", self.show_borrow_dialog),
            ("📥 Return Item", self.show_return_dialog),
            ("🕒 My History", self.show_patron_history),
            ("📅 Events", self.show_upcoming_events),
            ("📋 My Registrations", self.show_my_registrations),
            ("🎁 Donate Item", self.show_donate_dialog),
            ("💳 Pay Fines", self.show_pay_fines_dialog),
            ("📜 Request Item", self.show_request_dialog),
            ("🤝 Volunteer with us!", self.become_volunteer)
        ]
        
        for i, (text, handler) in enumerate(buttons):
            btn = QPushButton(text)
            btn.setMinimumHeight(40)
            btn.clicked.connect(handler)
            btn_grid.addWidget(btn, i//2, i%2)
        
        # Results Table
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers) # This is to prevent accidental editing of 
        # tables/data upon viewing (Though it does not directly affect the database, this is for convienence)
        
        layout.addLayout(header)
        layout.addLayout(btn_grid)
        layout.addWidget(self.results_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_staff_dashboard(self):
        """Staff View"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QHBoxLayout()
        self.staff_greeting = QLabel()
        self.staff_greeting.setFont(QFont("Arial", 14, QFont.Bold))
        
        logout_btn = QPushButton("Logout")
        logout_btn.setFixedWidth(100)
        logout_btn.clicked.connect(self.handle_logout)
        
        header.addWidget(self.staff_greeting)
        header.addStretch()
        header.addWidget(logout_btn)
        
        # Button Grid
        btn_grid = QGridLayout()
        btn_grid.setSpacing(10)
        
        buttons = [
            ("📚 Browse Items", self.show_available_items),
            ("🕒 Patron History", self.show_patron_history),
            ("📅 Events", self.show_upcoming_events),
            ("➕ Add Item", self.show_add_item_dialog),
            ("📋 Manage Requests", self.show_requests),
            ("🔍 Check Overdue Items", self.show_overdue_items), # replace handle_overdue_check to be able to view all overdue items
            ("🎉 Create Event", self.show_create_event_dialog),
            ("📝 Add Staff Record", self.show_add_staff_record_dialog),
            ("🚪 Request Leave", self.request_leave) # change to be a quit / request leave button for all staff
            # replace quit_volunteering function --> request_leave
        ]

        
        for i, (text, handler) in enumerate(buttons):
            btn = QPushButton(text)
            btn.setMinimumHeight(40)
            btn.clicked.connect(handler)
            btn_grid.addWidget(btn, i//3, i%3)
        
        # Results Table
        self.staff_results_table = QTableWidget()
        self.staff_results_table.setAlternatingRowColors(True)
        self.staff_results_table.verticalHeader().setVisible(False)
        self.staff_results_table.setEditTriggers(QTableWidget.NoEditTriggers) # This is to prevent accidental editing of 
        # tables/data upon viewing (Though it does not directly affect the database, this is for convienence)
        
        layout.addLayout(header)
        layout.addLayout(btn_grid)
        layout.addWidget(self.staff_results_table)
        
        widget.setLayout(layout)
        return widget
    
    # ----------------------
    # Session Management
    # ----------------------
    
    def handle_login(self):
        """Log in handler, Can log in using ID or Email"""
        identifier = self.login_id_input.text().strip()
        if not identifier:
            QMessageBox.warning(self, "Error", "Please enter your ID or email")
            return
        
        try:
            patron = services.find_patron_with_staff(identifier, db_name=self.db_name)
            
            if patron:
                self.current_user = {
                    'id': patron['id'],
                    'first_name': patron['first_name'],
                    'last_name': patron['last_name']
                }
                self.is_staff = bool(patron['is_staff'])
                
                if self.is_staff:
                    self.staff_greeting.setText(f"Staff: {patron['first_name']} {patron['last_name']}")
                    self.stacked_widget.setCurrentWidget(self.staff_dashboard)
                else:
                    self.patron_greeting.setText(f"Welcome, {patron['first_name']}!")
                    self.stacked_widget.setCurrentWidget(self.patron_dashboard)
                
            else:
                QMessageBox.warning(self, "Error", "User not found")
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid ID format")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Login failed: {str(e)}")
    
    def handle_registration(self):
        """Registration Window handler"""
        first = self.reg_first_name.text().strip()
        last = self.reg_last_name.text().strip()
        email = self.reg_email.text().strip()
        
        if not all([first, last, email]):
            QMessageBox.warning(self, "Error", "All fields are required")
            return
        
        result = services.add_patron(first, last, email, db_name=self.db_name)
        
        if result["status"] == "success":
            QMessageBox.information(
                self, 
                "Success", 
                f"Registration successful!\nYour random ID is: {result['id']}\n"
                "Please save this number for future logins."
            )
            self.stacked_widget.setCurrentWidget(self.login_screen)
            self.login_id_input.setText(str(result['id']))  # Auto-fill the login field
        else:
            QMessageBox.warning(self, "Error", result["message"])

    def cancel_event_registration(self, registration_id):
        """Cancel an event registration"""
        if QMessageBox.question(
            self, "Confirm Cancellation",
            "Are you sure you want to cancel this registration?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            return
            
        try:
            services.cancel_event_registration(registration_id, db_name=self.db_name)
            QMessageBox.information(self, "Cancelled", "Registration cancelled successfully")

            # refresh whichever view is currently showing
            if hasattr(self, 'current_registration_view'):
                self.show_my_registrations()
            else:
                self.show_upcoming_events()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to cancel registration: {str(e)}")
    
    def handle_logout(self):
        """Session logout handler"""
        self.current_user = None
        self.is_staff = False
        self.stacked_widget.setCurrentWidget(self.login_screen)
        self.login_id_input.clear()
        # make sure to clear tables from previously logged in Patron
        self.results_table.clearContents()
        self.results_table.setRowCount(0)

        self.staff_results_table.clearContents()
        self.staff_results_table.setRowCount(0)
    
    # Display overdue items
    def handle_overdue_check(self):
        """Check for overdue items and update status"""
        lost_items = services.check_overdue_items(self.db_name)
        if lost_items:
            msg = f"Check complete! {len(lost_items)} item(s) marked as lost."
        else:
            msg = "No New overdue items found."
        QMessageBox.information(self, "Overdue Check", msg)
    
    def show_overdue_items(self):
        try:
            today = datetime.now().strftime("%Y-%m-%d")

            if self.is_staff:
                items = services.get_overdue_items(today=today, db_name=self.db_name)

                table = self.staff_results_table
                table.clearContents()
                table.setRowCount(len(items))
                table.setColumnCount(8)
                table.setHorizontalHeaderLabels([
                    "Item ID", "Title", "Creator", "Type", "Status",
                    "Patron ID", "Name", "Due Date"
                ])
            
                for row, item in enumerate(items):
                    table.setItem(row, 0, QTableWidgetItem(str(item["item_id"])))
                    table.setItem(row, 1, QTableWidgetItem(item["title"]))
                    table.setItem(row, 2, QTableWidgetItem(item["creator"]))
                    table.setItem(row, 3, QTableWidgetItem(item["type"]))
                    table.setItem(row, 4, QTableWidgetItem(item["status"]))
                    table.setItem(row, 5, QTableWidgetItem(str(item["patron_id"])))
                    table.setItem(row, 6, QTableWidgetItem(f"{item['first_name']} {item['last_name']}"))
                    table.setItem(row, 7, QTableWidgetItem(item["due_date"]))

                table.resizeColumnsToContents()
                table.horizontalHeader().setStretchLastSection(False)

            if len(items) == 0:
                QMessageBox.information(self, "Overdue Items", "No overdue items found.")

            else:
                QMessageBox.information(self, "Overdue Items", "Staff only view available for patrons yet.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load overdue items: {str(e)}")
    


    def become_volunteer(self):
        """Handle volunteer signup"""
        # Check if already staff
        if self.is_staff:
            QMessageBox.warning(self, "Already Staff", 
                            "You're already a staff member! Volunteers must be regular patrons.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Volunteer",
            "Are you sure you want to become a volunteer?\n"
            "You'll need to log in again to access volunteer features.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                services.add_volunteer(self.current_user['id'], db_name=self.db_name)
                QMessageBox.information(self, "Welcome!",
                                    "You're now a volunteer staff member!\n"
                                    "Please log in again to access volunteer features.")
                self.handle_logout()  # Force logout to help with session maintenance and unintentional back tracking
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                f"Failed to register: {str(e)}")
                
   
    # NEW FUNCTION --> handle staff leave distinctly
    def request_leave(self):
        """Any staff can request to leave. Volunteers can immediately quit."""
        if not services.is_volunteer(self.current_user['id'], db_name=self.db_name):
            if services.is_manager(self.current_user['id'], db_name=self.db_name):
                try:
                    QMessageBox.information(self, "Leave Request", "Please speak to the Department Head to terminate your position.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to update status: {str(e)}")
            else: 
                try:
                    QMessageBox.information(self, "Leave Request", "Please speak to a Manager to terminate your position.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to update status: {str(e)}")
        else:
            reply = QMessageBox.question(
            self, "Confirm Quit",
            "Are you sure you want to stop volunteering?\n"
            "You'll need to log in again.",
            QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    services.remove_volunteer(self.current_user['id'], db_name=self.db_name)
                    QMessageBox.information(self, "Thank You", 
                                    "We appreciate your volunteer service!\n"
                                    "Please log in again.")
                    self.handle_logout() # Force logout to help with session maintenance and unintentional back tracking
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to update status: {str(e)}")
                
    def register_for_event(self, event_id):
        try:
            if services.register_for_event(self.current_user['id'], event_id, db_name=self.db_name):
                QMessageBox.information(self, "Success", "Registration confirmed!")
                self.show_upcoming_events()  # Refresh view
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
    
    # ----------------------
    # Patron Functionality
    # ----------------------
    
    def show_available_items(self):
        """Show items with status 'Available' and 'Checked Out' for both Patron and Staff and 'Lost' for staff"""
        
        try:
            items = services.get_items_with_display_status(self.is_staff, db_name=self.db_name)
            # Display formatting
            table = self.staff_results_table if self.is_staff else self.results_table
            table.setRowCount(len(items))
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["ID", "Title", "Creator", "Type", "Status"])
            
            for row, item in enumerate(items):
                status = item['display_status']
                
                table.setItem(row, 0, QTableWidgetItem(str(item['item_id'])))
                table.setItem(row, 1, QTableWidgetItem(item['title']))
                table.setItem(row, 2, QTableWidgetItem(item['creator']))
                table.setItem(row, 3, QTableWidgetItem(item['type']))
                
                # Color coding
                status_item = QTableWidgetItem(status.capitalize())
                if status == 'available':
                    status_item.setBackground(QColor(200, 255, 200)) # Light green
                    status_item.setForeground(QColor(0, 100, 0))
                elif status == 'checked_out':
                    status_item.setBackground(QColor(255, 229, 204)) # Light orange
                    status_item.setForeground(QColor(153, 76, 0)) 
                elif status == 'lost':
                    status_item.setBackground(QColor(255, 204, 204)) # Light red
                
                table.setItem(row, 4, status_item)
            
            # Auto-resize columns
            table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load items: {str(e)}")
    
    # Patron can search by title or item ID to borrow a specific item
    def show_borrow_dialog(self):
        """Borrow Item Prompt"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Borrow Item")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Option selection
        option_group = QButtonGroup()
        rb_combo = QRadioButton("Select from list")
        rb_id = QRadioButton("Enter Item ID")
        rb_title = QRadioButton("Search by title")

        rb_combo.setChecked(True)  # Default selection

        option_group.addButton(rb_combo)
        option_group.addButton(rb_id)
        option_group.addButton(rb_title)

        # Widget stack
        self.borrow_stack = QStackedWidget()

        # Combo box panel
        combo_panel = QWidget()
        combo_layout = QVBoxLayout(combo_panel)
        self.item_combo = QComboBox()
        items = services.get_available_items(db_name=self.db_name)
        for item in items:
            self.item_combo.addItem(f"{item['title']} (ID: {item['item_id']})", item['item_id'])
        combo_layout.addWidget(self.item_combo)

        # ID input panel
        id_panel = QWidget()
        id_layout = QVBoxLayout(id_panel)
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter item ID")
        id_layout.addWidget(self.id_input)

        # Search by title panel
        title_panel = QWidget()
        title_layout = QVBoxLayout(title_panel)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter title to search")
        
        search_button = QPushButton("Search")
        self.title_results = QComboBox()  # Dropdown to display search results
        self.title_results.setEnabled(False)  # Disabled until a search is performed

        search_button.clicked.connect(self.search_by_title)

        title_layout.addWidget(self.title_input)
        title_layout.addWidget(search_button)
        title_layout.addWidget(self.title_results)

        title_panel.setLayout(title_layout)

        # Add panels to stack
        self.borrow_stack.addWidget(combo_panel)  # Index 0
        self.borrow_stack.addWidget(id_panel)  # Index 1
        self.borrow_stack.addWidget(title_panel)  # Index 2

        # Button row
        btn_row = QHBoxLayout()
        borrow_btn = QPushButton("Borrow")
        cancel_btn = QPushButton("Cancel")

        # Connections
        rb_combo.toggled.connect(lambda: self.borrow_stack.setCurrentIndex(0))
        rb_id.toggled.connect(lambda: self.borrow_stack.setCurrentIndex(1))
        rb_title.toggled.connect(lambda: self.borrow_stack.setCurrentIndex(2))
        cancel_btn.clicked.connect(dialog.close)
        borrow_btn.clicked.connect(lambda: self.process_borrow(dialog))

        # Layout
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(borrow_btn)

        layout.addWidget(QLabel("Select borrowing method:"))
        layout.addWidget(rb_combo)
        layout.addWidget(rb_id)
        layout.addWidget(rb_title)
        layout.addWidget(self.borrow_stack)
        layout.addLayout(btn_row)

        dialog.exec_()

    def search_by_title(self):
        """Fetch items matching the entered title"""
        title_query = self.title_input.text().strip()
        if not title_query:
            QMessageBox.warning(self, "Warning", "Please enter a title to search.")
            return

        try: 
            results = services.search_available_items_by_title(title_query, db_name=self.db_name)
            self.title_results.clear()
            if results:
                for item in results:
                    display_text = f"{item['title']} by {item['creator']} (ID: {item['item_id']})"
                    self.title_results.addItem(display_text, item["item_id"])
                self.title_results.setEnabled(True)
            else:
                self.title_results.addItem("No results found")
                self.title_results.setEnabled(False)
        except Exception as e: 
            QMessageBox.warning(self, "Error", f"Search failed: {str(e)}")

    def process_borrow(self, dialog):
        """Handle borrowing through different methods"""
        if self.borrow_stack.currentIndex() == 0:  # Combo box selected
            item_id = self.item_combo.currentData()
        
        elif self.borrow_stack.currentIndex() == 1:  # ID input
            try:
                item_id = int(self.id_input.text())
                if not services.get_item(item_id, db_name=self.db_name):  # Ensure the item exists
                    QMessageBox.warning(dialog, "Error", "Invalid item ID")
                    return
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Please enter a valid numeric ID")
                return
        
        elif self.borrow_stack.currentIndex() == 2:  # Search by title selected
            item_id = self.title_results.currentData()  # Retrieve selected item's ID
            if item_id is None:
                QMessageBox.warning(dialog, "Error", "Please select a valid item")
                return

        try:
            due_date = services.borrow_item(self.current_user['id'], item_id, db_name=self.db_name)
            QMessageBox.information(dialog, "Success", f"Item borrowed! Due: {due_date}")
            dialog.close()
        except ValueError as e:
            QMessageBox.warning(dialog, "Error", str(e))

    
    def show_return_dialog(self):
        """Similar to borrow dialog but shows currently checked out items"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Return Item")
        
        layout = QVBoxLayout()
        try: 
            items = services.get_checked_out_items_for_patron(
                self.current_user["id"], 
                db_name=self.db_name
            )
        except Exception as e: 
            QMessageBox.warning(self, "Error", f"Failed to load items: {str(e)}")
            dialog.close()
            return
        
        if not items:
            QMessageBox.information(self, "Info", "You have no items to return")
            dialog.close()
            return
        
        item_combo = QComboBox()
        for item in items:
            item_combo.addItem(f"{item['title']} ({item['type']})", item['item_id'])
        
        return_btn = QPushButton("Return")
        return_btn.clicked.connect(lambda: self.return_selected_item(item_combo.currentData(), dialog))
        
        layout.addWidget(QLabel("Select item to return:"))
        layout.addWidget(item_combo)
        layout.addWidget(return_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def return_selected_item(self, item_id, dialog):
        try:
            result = services.return_item(self.current_user["id"], item_id, db_name=self.db_name)

            if result.get("status") == "lost":
                cost = result["replacement_cost"]
                reply = QMessageBox.question(
                    self, "Lost Item",
                    f"This item was marked as lost!\n\n"
                    f"Replacement cost: ${cost:.2f}\n\n"
                    "Would you like to pay the fine now?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    services.process_lost_item_payment(
                        self.current_user["id"],
                        item_id=item_id,
                        db_name=self.db_name
                    )
                    QMessageBox.information(
                        self, "Success",
                        f"Payment processed and item #{item_id} returned!"
                    )
                else:
                    QMessageBox.information(self, "Not Paid", "You can pay the fine later from the fines/payment option.")
                return

            if result.get("status") == "returned_late":
                QMessageBox.warning(
                    self, "Late Return",
                    f"Item returned late! You must pay the replacement cost of ${result['replacement_cost']:.2f}"
                )
            else:
                QMessageBox.information(self, "Success", "Item returned successfully!")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Return failed: {str(e)}")

        finally:
            dialog.close()
            self.show_available_items()


    
    def show_patron_history(self):
        """Show borrowing history - all patrons for staff, current patron for regular users"""
        
        if self.is_staff:
        # Staff sees complete history with patron names
            history = services.get_all_borrowing_history(self.is_staff, db_name=self.db_name)
                    
            # Update table headers for staff view
            headers = ["Patron", "Title", "Creator", "Type", "Checkout", "Return", "Status"]
            self.display_history(history, headers)
        else:
            # Regular user sees only their own history
            history = services.get_borrowing_history(self.current_user['id'], db_name=self.db_name)
            headers = ["Title", "Creator", "Type", "Checkout", "Return"]
            self.display_history(history, headers)

    
    def show_upcoming_events(self):
        try:
            events = services.get_upcoming_events(
                include_past=self.is_staff, 
                db_name=self.db_name
            )
            self.display_events(events)
        except Exception as e: 
            QMessageBox.warning(self, "Error", f"Failed to load events: {str(e)}")
    
    # main_window.py  
    def show_my_registrations(self):
        """Show current patron's event registrations"""
        try:
            self.results_table.setRowCount(0)
            
            # Get all registrations for current patron
            registrations = services.get_registrations_for_patron(
                self.current_user["id"], 
                db_name=self.db_name
            )
            
            self.results_table.setRowCount(len(registrations))
            self.results_table.setColumnCount(5)
            self.results_table.setHorizontalHeaderLabels(
                ["Event", "Date", "Room", "Audience", "Cancel"]
            )
            
            today = datetime.today().date()  # Get today's date

            for row, reg in enumerate(registrations):
                event = dict(reg)  # Convert sqlite3.Row to dict (This is to allow use of .get() py function)
                
                # Event details
                self.results_table.setItem(row, 0, QTableWidgetItem(reg['eventName']))
                self.results_table.setItem(row, 1, QTableWidgetItem(reg['date']))
                self.results_table.setItem(row, 2, QTableWidgetItem(reg['roomNum']))
                self.results_table.setItem(row, 3, QTableWidgetItem(reg.get('audience', 'All')))
                
                # Convert event date to datetime object for comparison
                event_date = datetime.strptime(reg['date'], "%Y-%m-%d").date()

                if event_date > today:  # Only add "Cancel" button for future events
                    cancel_btn = QPushButton("Cancel")
                    cancel_btn.clicked.connect(
                        lambda _, rid=reg['registration_id']: self.cancel_event_registration(rid)
                    )
                    cancel_btn.setStyleSheet("""
                        QPushButton {background-color: #b04848; color: #242020;}
                        QPushButton:hover {background-color: #de6a6a;}
                        QPushButton:pressed {background-color: #633e3e;}
                    """)
                    self.results_table.setCellWidget(row, 4, cancel_btn)
            
            # Adjust column widths -- RESPONSIVE 
            self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.results_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load registrations: {str(e)}")

    def show_pay_fines_dialog(self):
        """Show fines payment dialog"""
        services.check_overdue_items(db_name=self.db_name)
        fines = services.get_patron_fines(self.current_user['id'], db_name=self.db_name)
        
        if fines <= 0:
            QMessageBox.information(self, "No Fines", "You have no outstanding fines!")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Pay Fines")
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel(f"Total Fines: ${fines:.2f}"))
        
        pay_btn = QPushButton("Confirm Payment")
        pay_btn.clicked.connect(lambda: self.process_payment(fines, dialog))
        
        layout.addWidget(pay_btn)
        dialog.setLayout(layout)
        dialog.exec_()

    # 'Confirm payment' => onClick => process_payment
    # After paying payment, item is available again 
    def process_payment(self, amount, dialog=None, item_id=None):
        
        try:
            updated = services.process_lost_item_payment(
                self.current_user["id"],
                item_id=item_id,
                db_name=self.db_name
            )
            
            message = (f"Payment of ${amount:.2f} processed!\n"
                    f"Item #{item_id} is now available." if item_id 
                    else "All fines paid!")
            QMessageBox.information(self, "Payment Complete!", message)
            
            if dialog:
                dialog.close()
            self.show_available_items()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Payment failed: {str(e)}")

    # Prompt for Patrons to donate items to library
    def show_donate_dialog(self):
        """Item Donation Prompt"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Donate Item")
        layout = QVBoxLayout()
        
        title_input = QLineEdit(placeholderText="Title")
        creator_input = QLineEdit(placeholderText="Creator/Author")
        type_combo = QComboBox()
        type_combo.addItems(["Physical Book", "Online Book", "Journal", "Vinyl", "DVD", "Magazine", "CD" "Other"])
        
        donate_btn = QPushButton("Donate Item")
        donate_btn.clicked.connect(lambda: self.process_donation(
            title_input.text(),
            creator_input.text(),
            type_combo.currentText(),
            dialog
        ))
        
        layout.addWidget(QLabel("Title:"))
        layout.addWidget(title_input)
        layout.addWidget(QLabel("Creator:"))
        layout.addWidget(creator_input)
        layout.addWidget(QLabel("Type:"))
        layout.addWidget(type_combo)
        layout.addWidget(donate_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def process_donation(self, title, creator, item_type, dialog):
        if not title:
            QMessageBox.warning(dialog, "Error", "Title is required")
            return
            
        try:
            # Add with $0 replacement cost for donations
            services.add_item(title, creator, item_type, 0.00, db_name=self.db_name)
            QMessageBox.information(dialog, "Thank You", "Item donated successfully!")
            dialog.close()
        except Exception as e:
            QMessageBox.warning(dialog, "Error", f"Donation failed: {str(e)}")

    # Submit acquisition request
    def show_request_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Request New Item")
        layout = QVBoxLayout()
        
        # Input fields
        title_input = QLineEdit(placeholderText="Title")
        type_combo = QComboBox()
        type_combo.addItems(["Physical Book", "Online Book", "Journal", "Vinyl", "DVD", "Magazine", "CD", "Audiobook", "Other"])
        creator_input = QLineEdit(placeholderText="Author/Creator")
        
        submit_btn = QPushButton("Submit Request")
        submit_btn.clicked.connect(lambda: self.process_request(
            title_input.text(),
            type_combo.currentText(),
            creator_input.text(),
            dialog
        ))
        
        # Layout
        layout.addWidget(QLabel("Title:"))
        layout.addWidget(title_input)
        layout.addWidget(QLabel("Type:"))
        layout.addWidget(type_combo)
        layout.addWidget(QLabel("Creator:"))
        layout.addWidget(creator_input)
        layout.addWidget(submit_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def process_request(self, title, item_type, creator, dialog):
        if not all([title, item_type]):
            QMessageBox.warning(dialog, "Error", "Title and Type are required")
            return
        
        try:
            services.submit_acquisition_request(
                self.current_user['id'],
                item_type,
                creator,
                title,
                db_name=self.db_name
            )
            QMessageBox.information(dialog, "Success", "Request submitted successfully!")
            dialog.close()
        except Exception as e:
            QMessageBox.warning(dialog, "Error", f"Failed to submit request: {str(e)}")

    # Ask a Librarian for help
    def show_staff_help_dialog(self):
        """Show dialog for staff-assisted browsing (This is the Librarian help functionality)"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Staff-Assisted Browsing")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Category selection
        layout.addWidget(QLabel("Select category you wish to browse:"))
        
        category_combo = QComboBox()
        category_combo.addItems([
            "Physical Book", 
            "Online Book", 
            "Journal", 
            "Magazine", 
            "Vinyl",
            "DVD",
            "CD",
            "Audiobook",
            "Other"
        ])
        layout.addWidget(category_combo)
        
        # Results table
        results_table = QTableWidget()
        results_table.setAlternatingRowColors(True)
        results_table.verticalHeader().setVisible(False)
        layout.addWidget(results_table)
        
        # Search button
        search_btn = QPushButton("Find Items")
        search_btn.clicked.connect(lambda: self.populate_help_table(
            category_combo.currentText(),
            results_table
        ))
        layout.addWidget(search_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def populate_help_table(self, item_type, table_widget):
        """Populate table with items of selected type, used for staff help prompt"""
        try:
            items = services.get_items_by_type_for_help(item_type, db_name=self.db_name)

            table_widget.setRowCount(len(items))
            table_widget.setColumnCount(4)
            table_widget.setHorizontalHeaderLabels(["ID", "Title", "Creator", "Status"])

            for row, item in enumerate(items):
                table_widget.setItem(row, 0, QTableWidgetItem(str(item["item_id"])))
                table_widget.setItem(row, 1, QTableWidgetItem(item["title"]))
                table_widget.setItem(row, 2, QTableWidgetItem(item["creator"]))

                status = item["display_status"]
                status_item = QTableWidgetItem(status)

                if status == "available":
                    status_item.setBackground(QColor(144, 238, 144))
                    status_item.setForeground(QColor(0, 100, 0))
                elif status == "checked_out":
                    status_item.setBackground(QColor(255, 165, 0))
                    status_item.setForeground(QColor(153, 76, 0))

                table_widget.setItem(row, 3, status_item)

            table_widget.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load items: {str(e)}")

        
    # ----------------------
    # Staff Functionality
    # ----------------------
    
    def show_add_item_dialog(self):
        """Item addition Prompt"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Item")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        title_input = QLineEdit(placeholderText="Title")
        type_combo = QComboBox()
        type_combo.addItems(["Physical Book", "Online Book", "Journal", "Vinyl", "DVD", "Magazine", "CD", "Audiobook", "Other"])
        cost_input = QLineEdit(placeholderText="Replacement Cost")
        creator_input = QLineEdit(placeholderText="Creator")
        
        # Create and set the validator
        cost_validator = QDoubleValidator(0, 9999, 2)
        cost_validator.setNotation(QDoubleValidator.StandardNotation)
        cost_input.setValidator(cost_validator)
        
        add_btn = QPushButton("Add Item")
        add_btn.clicked.connect(lambda: self.add_new_item(
            title_input.text(),
            type_combo.currentText(),
            creator_input.text(),
            float(cost_input.text()) if cost_input.text() else 0,  # Handle empty input
            dialog
        ))
        
        layout.addWidget(QLabel("Title:"))
        layout.addWidget(title_input)
        layout.addWidget(QLabel("Creator:"))
        layout.addWidget(creator_input)
        layout.addWidget(QLabel("Type:"))
        layout.addWidget(type_combo)
        layout.addWidget(QLabel("Replacement Cost:"))
        layout.addWidget(cost_input)
        layout.addWidget(add_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def add_new_item(self, title, creator, item_type, cost, dialog):
        # Validate inputs
        if not title:
            QMessageBox.warning(self, "Error", "Title is required")
            return
            
        if cost <= 0:
            QMessageBox.warning(self, "Error", "Cost must be positive")
            return
            
        try:
            item_id = services.add_item(title, creator, item_type, cost, db_name=self.db_name)
            QMessageBox.information(self, "Success", f"Item added successfully! ID: {item_id}")
            dialog.close()
            self.show_available_items()  # Refresh the list
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add item: {str(e)}")
    
    def show_requests(self):
        if not self.is_staff:
            QMessageBox.warning(self, "Access Denied", "Only staff can manage requests")
            return
        
        if services.is_volunteer(self.current_user['id'], db_name=self.db_name):
            QMessageBox.warning(
                self, 
                "Access Denied", 
                "Volunteers cannot manage acquisition requests.\n"
                "Only regular staff members have this privilege."
            )
            return
        
        try:
            requests = services.show_acquisition_requests(db_name=self.db_name)
            
            self.staff_results_table.clearContents()
            self.staff_results_table.setRowCount(len(requests))
            self.staff_results_table.setColumnCount(7)
            # Reordered headers
            headers = ["ID", "Patron", "Title", "Creator", "Type", "Status", "Actions"]
            self.staff_results_table.setHorizontalHeaderLabels(headers)
            
            for row, req in enumerate(requests):
                creator = req['creator'] if 'creator' in req.keys() and req['creator'] else 'N/A'
                
                # Column order matches headers:
                self.staff_results_table.setItem(row, 0, QTableWidgetItem(str(req['request_id'])))
                self.staff_results_table.setItem(row, 1, QTableWidgetItem(f"{req['first_name']} {req['last_name']}"))
                self.staff_results_table.setItem(row, 2, QTableWidgetItem(req['title']))
                self.staff_results_table.setItem(row, 3, QTableWidgetItem(creator))
                self.staff_results_table.setItem(row, 4, QTableWidgetItem(req['item_type']))
                
                # Status with color coding :D
                status_item = QTableWidgetItem(req['request_status'])
                if req['request_status'] == 'approved':
                    status_item.setBackground(QColor(144, 238, 144))
                    status_item.setForeground(QColor(0, 100, 0))
                elif req['request_status'] == 'denied':
                    status_item.setBackground(QColor(255, 111, 111))
                    status_item.setForeground(QColor(55, 0, 0))
                self.staff_results_table.setItem(row, 5, status_item)
                
                # Action buttons for pending requests
                if req['request_status'] == 'Pending':
                    btn_layout = QHBoxLayout()
                    btn_widget = QWidget()
                    
                    approve_btn = QPushButton("✓")
                    approve_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #00BC00;
                            color: white;
                            border-radius: 4px;
                            min-width: 30px;
                            max-width: 30px;
                        }
                    """)
                    approve_btn.clicked.connect(lambda _, r=req['request_id']: self.update_request_status(r, 'approved'))
                    
                    deny_btn = QPushButton("✗")
                    deny_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #7C2323;
                            color: white;
                            border-radius: 4px;
                            min-width: 30px;
                            max-width: 30px;
                        }
                    """)
                    deny_btn.clicked.connect(lambda _, r=req['request_id']: self.update_request_status(r, 'denied'))
                    
                    btn_layout.addWidget(approve_btn)
                    btn_layout.addWidget(deny_btn)
                    btn_layout.setContentsMargins(0, 0, 0, 0)
                    btn_widget.setLayout(btn_layout)
                    
                    self.staff_results_table.setCellWidget(row, 6, btn_widget)
                else:
                    self.staff_results_table.setItem(row, 6, QTableWidgetItem(""))
        except Exception as e: 
            QMessageBox.warning(self, "Error", f"Failed to load request: {str(e)}")
                    
        finally:
            self.staff_results_table.resizeColumnsToContents()


    def approve_request(self, request_id):
        try:
            if not self.is_staff:
                raise ValueError("Only staff can approve requests")
            
            services.approve_acquisition_request(request_id, self.current_user['id'], db_name=self.db_name)
            QMessageBox.information(self, "Approved", "Request approved successfully!")
            self.show_requests()  # Refresh view
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Approval failed: {str(e)}")

    def update_request_status(self, request_id, new_status):
        """Updates status of Acquisition Requests"""
        try:
            result = services.update_acquisition_request_status(
                request_id,
                new_status,
                db_name=self.db_name
            )

            if not result["updated"]:
                if result["reason"] == "not_found":
                    QMessageBox.warning(self, "Error", "Request not found")
                elif result["reason"] == "not_pending":
                    QMessageBox.warning(self, "Error", f"Request already {result['current_status']}")
                return

            QMessageBox.information(self, "Success", f"Request {new_status} successfully!")
            self.show_requests()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update request: {str(e)}")


    # Volunteers are not allowed to create an event, only regular staff are
    def show_create_event_dialog(self):
        """Event creation Prompt"""

        # Handle volunteers - not allowed to make an event
        if services.is_volunteer(self.current_user['id'], db_name=self.db_name):
            QMessageBox.warning(
                self, 
                "Access Denied",
                "Volunteers are not allowed to organize events.\n"
                "Only regular staff members have this privilege."
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Event")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        name_input = QLineEdit(placeholderText="Event Name")
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setMinimumDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        room_input = QLineEdit(placeholderText="Room Number")
        audience_input = QLineEdit(placeholderText="Target audience")
        
        create_btn = QPushButton("Create Event")
        create_btn.clicked.connect(lambda: self.create_new_event(
            name_input.text(),
            date_input.date().toString('yyyy-MM-dd'),
            room_input.text(),
            audience_input.text(),
            dialog
        ))
        
        layout.addWidget(QLabel("Event Name:"))
        layout.addWidget(name_input)
        layout.addWidget(QLabel("Date:"))
        layout.addWidget(date_input)
        layout.addWidget(QLabel("Room Number:"))
        layout.addWidget(room_input)
        layout.addWidget(QLabel("Audience:"))
        layout.addWidget(audience_input)
        layout.addWidget(create_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def create_new_event(self, name, date, room, audience, dialog):
        """Creating Event functionality (Used for Create event prompt)"""
        if not all([name, date, room]):
            QMessageBox.warning(self, "Error", "All fields are required")
            return
        
        try:
            event_id = services.create_event(self.current_user['id'], name, date, room, audience, db_name=self.db_name)
            QMessageBox.information(self, "Success", f"Event created successfully! ID: {event_id}")
            dialog.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create event: {str(e)}")

    def show_add_staff_record_dialog(self):
        if not services.is_manager(self.current_user["id"], db_name=self.db_name):
            QMessageBox.warning(self, "Access Denied",
                                "You cannot add staff records.\nOnly managers have this privilege.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Staff Record")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout()

        staff_label = QLabel("Staff Member:")
        self.staff_combo = QComboBox()

        # populate with staff 
        try:
            staff_members = services.get_all_staff_members(db_name=self.db_name)
            for staff in staff_members:
                self.staff_combo.addItem(f"{staff['first_name']} {staff['last_name']}", staff["id"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load staff list: {str(e)}")
            dialog.close()
            return

        # Record type
        type_label = QLabel("Record Type:")
        self.record_type = QComboBox()
        self.record_type.addItems(["Note", "Warning", "Commendation", "Training", "Leave Request", "Performance Review"])
        
        # Details
        details_label = QLabel("Details:")
        self.record_details = QTextEdit()
        self.record_details.setMaximumHeight(100)
        
        # Buttons
        btn_layout = QHBoxLayout()
        submit_btn = QPushButton("Add Record")
        submit_btn.clicked.connect(lambda: self.process_staff_record(dialog))
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.close)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(submit_btn)
        
        # Build layout
        layout.addWidget(staff_label)
        layout.addWidget(self.staff_combo)
        layout.addWidget(type_label)
        layout.addWidget(self.record_type)
        layout.addWidget(details_label)
        layout.addWidget(self.record_details)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def process_staff_record(self, dialog):
        """Updating Staff Record Table functionality (Used for Add staff record prompt)"""
        staff_id = self.staff_combo.currentData()
        record_type = self.record_type.currentText()
        details = self.record_details.toPlainText()
        
        if not details.strip():
            QMessageBox.warning(dialog, "Error", "Please enter record details")
            return
        
        try:
            services.add_staff_record(
                staff_id=staff_id,
                record_type=record_type,
                details=details,
                db_name=self.db_name
            )
            QMessageBox.information(dialog, "Success", "Staff record added successfully!")
            dialog.close()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Failed to add record: {str(e)}")
    
    # ----------------------
    # Display Helpers
    # ----------------------
    
    def display_items(self, items):
        """Display items in a table format"""
        table = self.staff_results_table if self.is_staff else self.results_table
        
        table.setRowCount(len(items))
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Title", "Type", "Status"])
        
        for row, item in enumerate(items):
            # Get status
            status = item['display_status'] if 'display_status' in item.keys() else item['status']
            
            table.setItem(row, 0, QTableWidgetItem(str(item['item_id'])))
            table.setItem(row, 1, QTableWidgetItem(item['title']))
            table.setItem(row, 2, QTableWidgetItem(item['type']))
            table.setItem(row, 3, QTableWidgetItem(status))

    def display_events(self, events):
        table = self.staff_results_table if self.is_staff else self.results_table
        table.setRowCount(len(events))
        
        if self.is_staff:
            table.setColumnCount(6)
            headers = ["ID", "Event", "Date", "Room", "Audience", "Status"]
        else:
            table.setColumnCount(5)
            headers = ["Event", "Date", "Room", "Audience", "Register"]
        
        table.setHorizontalHeaderLabels(headers)
        
        for row, event in enumerate(events):
            # Similar case, allow the usage of .get() py function
            e = event if isinstance(event, dict) else dict(event)
            
            if self.is_staff:
                # Staff view
                table.setItem(row, 0, QTableWidgetItem(str(e["event_id"])))
                table.setItem(row, 1, QTableWidgetItem(e["eventName"]))
                table.setItem(row, 2, QTableWidgetItem(e["date"]))
                table.setItem(row, 3, QTableWidgetItem(e["roomNum"]))
                table.setItem(row, 4, QTableWidgetItem(e.get("audience", "All")))
                
                status = e.get('event_status', 'Upcoming')
                status_item = QTableWidgetItem(status)
                if status == 'No Longer Available':
                    status_item.setBackground(QColor(150, 150, 150))
                    status_item.setForeground(QColor(250, 250, 250))
                else:
                    status_item.setBackground(QColor(200, 255, 200))
                    status_item.setForeground(QColor(0, 100, 0))
                table.setItem(row, 5, status_item)
            else: 
                # Patron view
                table.setItem(row, 0, QTableWidgetItem(e["eventName"]))
                table.setItem(row, 1, QTableWidgetItem(e["date"]))
                table.setItem(row, 2, QTableWidgetItem(e["roomNum"]))
                table.setItem(row, 3, QTableWidgetItem(e.get("audience", "All")))
                
                # Add register button to register for events
                btn = QPushButton("Register")
                eid = e["event_id"]
                btn.clicked.connect(lambda _, eid=eid: self.register_for_event(eid))
                btn.setStyleSheet("""
                    QPushButton {background-color: #9ac953; color: #222420;}
                    QPushButton:hover {background-color: #aad46c;}
                    QPushButton:pressed {background-color: #64734e;}
                """)
                table.setCellWidget(row, 4, btn)
        
        table.resizeColumnsToContents()

    def display_history(self, history, headers=None):
        """Shows Loan/Return Item history in a table format"""
        table = self.staff_results_table if self.is_staff else self.results_table
        table.clearContents() 
        table.setRowCount(0)

        if not headers:
            headers = ["Patron", "Title", "Creator", "Type", "Checkout Date", "Return Date", "Status"]
        
        table.setRowCount(len(history))
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        for row, record in enumerate(history):
            # Staff view has additional columns
            if self.is_staff:
                return_date = record['returnDate'] if 'returnDate' in record.keys() and record['returnDate'] else 'Not Returned'
                status = "Active" if return_date == 'Not Returned' else "Returned/Paid"
                
                table.setItem(row, 0, QTableWidgetItem(record['patron_name']))
                table.setItem(row, 1, QTableWidgetItem(record['title']))
                table.setItem(row, 2, QTableWidgetItem(record['creator']))
                table.setItem(row, 3, QTableWidgetItem(record['type']))
                table.setItem(row, 4, QTableWidgetItem(record['checkoutDate']))
                table.setItem(row, 5, QTableWidgetItem(str(return_date)))
                table.setItem(row, 6, QTableWidgetItem(status))
            else:
                # Regular patron view
                return_date = record['returnDate'] if 'returnDate' in record.keys() and record['returnDate'] else 'Not Returned'
                
                table.setItem(row, 0, QTableWidgetItem(record['title']))
                table.setItem(row, 1, QTableWidgetItem(record['type']))
                table.setItem(row, 2, QTableWidgetItem(record['creator']))
                table.setItem(row, 3, QTableWidgetItem(record['checkoutDate']))
                table.setItem(row, 4, QTableWidgetItem(str(return_date)))

        table.resizeColumnsToContents()

    def apply_theme(self):
        """Apply the current theme stylesheet"""
        theme = "dark" if self.dark_mode else "light"
        self.setStyleSheet(self.stylesheets[theme])
        
        # Update fonts
        font = QFont("Segoe UI", 10) if sys.platform == "win32" else QFont("Arial", 12)
        self.setFont(font)

    def add_theme_toggle(self):
        """Add theme toggle button to both dashboards"""
        # For patron dashboard
        self.theme_btn_patron = QPushButton("🌙 Dark Mode")
        self.theme_btn_patron.clicked.connect(self.toggle_theme)
        self.patron_dashboard.layout().insertWidget(1, self.theme_btn_patron)
        
        # For staff dashboard
        self.theme_btn_staff = QPushButton("🌙 Dark Mode")
        self.theme_btn_staff.clicked.connect(self.toggle_theme)
        self.staff_dashboard.layout().insertWidget(1, self.theme_btn_staff)

    def toggle_theme(self):
        """Switch between light and dark themes"""
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        
        # Update button text
        text = "☀️ Light Mode" if self.dark_mode else "🌙 Dark Mode"
        self.theme_btn_patron.setText(text)
        self.theme_btn_staff.setText(text)

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = LibraryApp()
    window.show()
    sys.exit(app.exec_())