import sqlite3
from datetime import datetime, timedelta
import random
import time

from .connection import get_db_connection

LOAN_PERIOD_DAYS = 28
GRACE_PERIOD_DAYS = 14

## PATRON MANAGEMENT FUNCTIONS ##

def add_patron(first_name, last_name, email, db_name=None):
    """Add a new patron to the system"""
    conn = get_db_connection(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM Patron WHERE email = ?", (email,))
        if cursor.fetchone():
            return {"status": "error", "message": "Email Already Exists!"}
    except sqlite3.Error:
        pass
    
    # loop with a timeout to generate random ID for patron
    start_time = time.time()
    max_duration = 3  # Max seconds to try
    attempts = 0
    
    while True:
        attempts += 1
        patron_id = random.randint(1000, 9999)  
        try:
            cursor.execute(
                "INSERT INTO Patron (id, first_name, last_name, email) VALUES (?, ?, ?, ?)",
                (patron_id, first_name, last_name, email)
            )
            conn.commit()
            return {"status": "success", "id": patron_id}
            
        except sqlite3.IntegrityError as e:
            if time.time() - start_time > max_duration:
                return {"status": "error", "message": "ID Generation timed out, Please Try Again."}
            time.sleep(min(0.1 * (1.5 ** attempts), 1.0))  # Max 1 second delay
        
        except Exception as e:
            return {"status": "error", "message": f"Database error: {str(e)}"}

def get_patron(patron_id, db_name=None):
    """Retrieve patron information"""
    conn = get_db_connection(db_name)
    try:
        patron = conn.execute(
            "SELECT first_name, last_name, email FROM Patron WHERE id = ?", 
            (patron_id,)
        ).fetchone()
        return dict(patron) if patron else None
    finally:
        conn.close()

## ITEM MANAGEMENT FUNCTIONS ##

def add_item(title, item_type, creator, replacement_cost, status="available", db_name=None):
    """Add a new item to the library inventory"""
    conn = get_db_connection(db_name)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Items (title, type, creator, replacement_cost, status) VALUES (?, ?, ?, ?, ?)",
            (title, item_type, creator, replacement_cost, status)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_item(item_id, db_name=None):
    """Retrieve complete item information"""
    conn = get_db_connection(db_name)
    try:
        item = conn.execute("SELECT * FROM Items WHERE item_id = ?", (item_id,)).fetchone()
        return dict(item) if item else None
    finally:
        conn.close()

def get_available_items(db_name=None):
    """Get all items with status 'available'"""
    conn = get_db_connection(db_name)
    try:
        items = conn.execute(
            "SELECT * FROM Items WHERE status = 'available'"
        ).fetchall()
        return [dict(item) for item in items]
    finally:
        conn.close()

def submit_acquisition_request(patron_id, item_type, creator, title, db_name=None):
    """Patron submits a request for the library to acquire an item"""
    conn = get_db_connection(db_name)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO AcquisitionRequest 
            (requested_by, request_status, item_type, creator, title) 
            VALUES (?, 'Pending', ?, ?, ?)""",
            (patron_id, item_type, creator, title)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def update_acquisition_request_status(request_id, new_status, db_name=None):
    """
    Update an acquisition request from Pending -> approved/denied.
    Returns a dict like:
      {"updated": True}
      {"updated": False, "reason": "not_found" | "not_pending", "current_status": "..."}
    """
    if new_status not in ("approved", "denied"):
        raise ValueError("new_status must be 'approved' or 'denied'")

    conn = get_db_connection(db_name)
    try:
        row = conn.execute(
            "SELECT request_status FROM AcquisitionRequest WHERE request_id = ?",
            (request_id,)
        ).fetchone()

        if not row:
            return {"updated": False, "reason": "not_found"}

        if row["request_status"] != "Pending":
            return {"updated": False, "reason": "not_pending", "current_status": row["request_status"]}

        conn.execute(
            """
            UPDATE AcquisitionRequest
            SET request_status = ?
            WHERE request_id = ? AND request_status = 'Pending'
            """,
            (new_status, request_id)
        )
        conn.commit()
        return {"updated": True}
    except:
        conn.rollback()
        raise
    finally:
        conn.close()


## BORROWING SYSTEM FUNCTIONS ##

def borrow_item(patron_id, item_id, db_name=None):
    """Patron Loan item function"""
    conn = get_db_connection(db_name)
    try:
        # Check if item is available
        item = conn.execute("SELECT * FROM Items WHERE item_id = ?", (item_id,)).fetchone()
        if not item:
            raise ValueError("Item not found")
        if item['status'] != 'available':
            raise ValueError("Item is not available for borrowing")
        
        # Check if patron already has an item borrowed
        active_loan = conn.execute(
            """SELECT * FROM BorrowingHistory 
            WHERE id = ? AND returnDate IS NULL""",
            (patron_id,)
        ).fetchone()
        if active_loan:
            raise ValueError("You already borrow an item, Please return it first to borrow a new item.")
        
        # Calculate due date
        checkout_date = datetime.now().strftime('%Y-%m-%d')
        due_date = (datetime.now() + timedelta(days=LOAN_PERIOD_DAYS)).strftime('%Y-%m-%d')
        
        # Update item status
        conn.execute(
            "UPDATE Items SET status = 'checked_out' WHERE item_id = ?",
            (item_id,)
        )
        
        # Create borrowing record
        conn.execute(
            """INSERT INTO BorrowingHistory 
            (id, item_id, checkoutDate) 
            VALUES (?, ?, ?)""",
            (patron_id, item_id, checkout_date)
        )
        
        conn.commit()
        return due_date
    finally:
        conn.close()

# in services.py 
def return_item(patron_id, item_id, db_name=None):
    """Return item back to the library"""
    conn = get_db_connection(db_name)
    try:
        # Get item status first
        item_status = conn.execute(
            "SELECT status FROM Items WHERE item_id = ?", 
            (item_id,)
        ).fetchone()
        
        if not item_status:
            raise ValueError("Item not found")
            
        if item_status['status'] == 'lost':
            return {"status": "lost", "replacement_cost": get_item(item_id, db_name=db_name)['replacement_cost']}
            
        loan = conn.execute(
            """SELECT * FROM BorrowingHistory 
            WHERE id = ? AND item_id = ? AND returnDate IS NULL""",
            (patron_id, item_id)
        ).fetchone()
        
        if not loan:
            raise ValueError("No active loan found")
            
        # Process the return
        return_date = datetime.now().strftime('%Y-%m-%d')
        conn.execute(
            """UPDATE BorrowingHistory SET returnDate = ? 
            WHERE id = ? AND item_id = ? AND returnDate IS NULL""",
            (return_date, patron_id, item_id)
        )
        
        conn.execute(
            "UPDATE Items SET status = 'available' WHERE item_id = ?",
            (item_id,)
        )
        conn.commit()
        
        # Check for late return
        checkout_date = datetime.strptime(loan['checkoutDate'], '%Y-%m-%d')
        due_date = checkout_date + timedelta(days=LOAN_PERIOD_DAYS)
        return_date_obj = datetime.strptime(return_date, '%Y-%m-%d')
        
        if return_date_obj > due_date:
            item = get_item(item_id, db_name=db_name)
            return {"status": "returned_late", "replacement_cost": item['replacement_cost']}
        
        return {"status": "returned"}
        
    finally:
        conn.close()

# Check for items that need to be considered lost
# If an item is not returned after the loan and grace period then its marked as lost
def check_overdue_items(db_name=None):
    """A scan function to check item dates and declare them lost based on conditions"""
    conn = get_db_connection(db_name)
    try:
        # Get all checked out items without a return date
        loans = conn.execute(
            """SELECT bh.*, i.replacement_cost 
            FROM BorrowingHistory bh
            JOIN Items i ON bh.item_id = i.item_id
            WHERE bh.returnDate IS NULL"""
        ).fetchall()
        
        today = datetime.now()
        lost_items = []
        
        for loan in loans:
            checkout_date = datetime.strptime(loan['checkoutDate'], '%Y-%m-%d')
            due_date = checkout_date + timedelta(days=LOAN_PERIOD_DAYS)
            lost_date = due_date + timedelta(days=GRACE_PERIOD_DAYS)
            
            if today > lost_date:
                # Mark item as lost
                conn.execute(
                    "UPDATE Items SET status = 'lost' WHERE item_id = ?",
                    (loan['item_id'],)
                )
                lost_items.append(loan['item_id'])
        
        conn.commit()
        return lost_items
    finally:
        conn.close()

## STAFF MANAGEMENT FUNCTIONS ##

def add_staff(patron_id, position, salary, db_name=None):
    """Add a staff member (must be an existing patron)"""
    conn = get_db_connection(db_name)
    try:
        # Verify patron exists
        patron = get_patron(patron_id)
        if not patron:
            raise ValueError("Patron not found")
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Staff (id, position, salary) VALUES (?, ?, ?)",
            (patron_id, position, salary)
        )
        conn.commit()
        return patron_id
    except sqlite3.IntegrityError:
        raise ValueError("Staff member already exists or invalid patron ID")
    finally:
        conn.close()

def add_staff_record(staff_id, record_type, details, db_name=None):
    """Add a record for a staff member"""
    conn = get_db_connection(db_name)
    try:
        date = datetime.now().strftime('%Y-%m-%d')
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO StaffRecords 
            (staff_id, record_type, details, date) 
            VALUES (?, ?, ?, ?)""",
            (staff_id, record_type, details, date)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def approve_acquisition_request(request_id, staff_id, db_name=None):
    """Staff approves an acquisition request"""
    conn = get_db_connection(db_name)
    try:
        # Verify staff exists
        staff = conn.execute("SELECT * FROM Staff WHERE id = ?", (staff_id,)).fetchone()
        if not staff:
            raise ValueError("Staff member not found")
        
        conn.execute(
            """UPDATE AcquisitionRequest 
            SET request_status = 'approved' 
            WHERE request_id = ?""",
            (request_id,)
        )
        conn.commit()
    finally:
        conn.close()

def show_acquisition_requests(db_name=None):
    conn = get_db_connection(db_name)
    try:
        requests = conn.execute(
            """
            SELECT ar.request_id, p.first_name, p.last_name, ar.title,
                ar.creator, ar.item_type, ar.request_status
            FROM AcquisitionRequest ar
            JOIN Patron p ON ar.requested_by = p.id
            ORDER BY
                CASE WHEN ar.request_status = 'Pending' THEN 0 ELSE 1 END, 
                ar.request_id DESC
            """
        ).fetchall()
        return [dict(r) for r in requests]
    finally:
        conn.close()

## EVENT MANAGEMENT FUNCTIONS ##

def create_event(organizer_id, event_name, event_date, room_num, audience, db_name=None):
    """Create a new library event"""
    conn = get_db_connection(db_name)
    try:
        # Verify organizer is staff
        staff = conn.execute("SELECT * FROM Staff WHERE id = ?", (organizer_id,)).fetchone()
        if not staff:
            raise ValueError("Only staff members can organize events")
        
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO Events 
            (organizer, eventName, date, roomNum, audience) 
            VALUES (?, ?, ?, ?, ?)""",
            (organizer_id, event_name, event_date, room_num, audience)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_upcoming_events(include_past=False, db_name=None):
    """Get all upcoming events (without IDs)"""
    conn = get_db_connection(db_name)
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        if include_past:
            # Staff view - all events with status
            events = conn.execute("""
                SELECT *, 
                    CASE WHEN date < ? THEN 'No Longer Available' 
                         ELSE 'Upcoming' 
                    END as event_status
                FROM Events
                ORDER BY date DESC
            """, (today,)).fetchall()
        else:
            # Patron view - only future (upcoming) events
            events = conn.execute("""
                SELECT * FROM Events 
                WHERE date >= ?
                ORDER BY date
            """, (today,)).fetchall()
        return [dict(event) for event in events]
    finally:
        conn.close()


def register_for_event(patron_id, event_id, db_name=None):
    """Register a patron for an event"""
    conn = get_db_connection(db_name)
    try:
        # Check if event exists and is upcoming
        event = conn.execute("""
            SELECT 1 FROM Events 
            WHERE event_id = ? AND date >= date('now')
        """, (event_id,)).fetchone()
        
        if not event:
            raise ValueError("Event not found or no longer available")
            
        # Check if already registered
        existing = conn.execute("""
            SELECT 1 FROM EventRegistrations 
            WHERE event_id = ? AND patron_id = ?
        """, (event_id, patron_id)).fetchone()
        
        if existing:
            raise ValueError("Already registered for this event")
            
        # Create registration
        conn.execute("""
            INSERT INTO EventRegistrations 
            (event_id, patron_id, registration_date) 
            VALUES (?, ?, date('now'))
        """, (event_id, patron_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        raise ValueError("Registration failed") from e
    finally:
        conn.close()

def get_event(event_id, db_name=None):
    """Get complete event information by ID"""
    conn = get_db_connection(db_name)
    try:
        event = conn.execute("""
            SELECT * FROM Events 
            WHERE event_id = ?
        """, (event_id,)).fetchone()
        return dict(event) if event else None
    finally:
        conn.close()


def get_event_registrations(event_id=None, patron_id=None, db_name=None):
    """Get registrations with optional filters"""
    conn = get_db_connection(db_name)
    try:
        query = """
            SELECT er.*, e.eventName, p.first_name, p.last_name 
            FROM EventRegistrations er
            JOIN Events e ON er.event_id = e.event_id
            JOIN Patron p ON er.patron_id = p.id
        """
        params = []
        
        if event_id and patron_id:
            query += " WHERE er.event_id = ? AND er.patron_id = ?"
            params.extend([event_id, patron_id])
        elif event_id:
            query += " WHERE er.event_id = ?"
            params.append(event_id)
        elif patron_id:
            query += " WHERE er.patron_id = ?"
            params.append(patron_id)
            
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()



## REPORTING FUNCTIONS ##

def get_borrowing_history(patron_id=None, db_name=None):
    """Get borrowing history for a patron (all for staff)"""
    conn = get_db_connection(db_name)
    try:
        if patron_id:
            # Query for specific patron
            return conn.execute("""
                SELECT i.title, i.creator, i.type, bh.checkoutDate, bh.returnDate 
                FROM BorrowingHistory bh
                JOIN Items i ON bh.item_id = i.item_id
                WHERE bh.id = ?
                ORDER BY bh.checkoutDate DESC
            """, (patron_id,)).fetchall()
        else:
            # Query for all patrons (staff view)
            return conn.execute("""
                SELECT bh.*, i.title, i.type, 
                       p.first_name || ' ' || p.last_name as patron_name
                FROM BorrowingHistory bh
                JOIN Items i ON bh.item_id = i.item_id
                JOIN Patron p ON bh.id = p.id
                ORDER BY bh.checkoutDate DESC
            """).fetchall()
    finally:
        conn.close()

# Limit access to staff records so only Managers can access them
def is_manager(patron_id, db_name=None):
    """Check if a patron is a Manager"""
    conn = get_db_connection(db_name)
    try:
        result = conn.execute("""
            SELECT 1 FROM Staff 
            WHERE id = ? AND position = 'Manager'
        """, (patron_id,)).fetchone()
        return result is not None
    finally:
        conn.close()

def is_volunteer(patron_id, db_name=None):
    """Check if a patron is a volunteer staff member"""
    conn = get_db_connection(db_name)
    try:
        result = conn.execute("""
            SELECT 1 FROM Staff 
            WHERE id = ? AND position = 'Volunteer'
        """, (patron_id,)).fetchone()
        return result is not None
    finally:
        conn.close()

def add_volunteer(patron_id, db_name=None):
    """Register a patron as a volunteer"""
    conn = get_db_connection(db_name)
    try:
        conn.execute("""
            INSERT INTO Staff (id, position, salary)
            VALUES (?, 'Volunteer', 0)
        """, (patron_id,))
        conn.commit()
    finally:
        conn.close()

def remove_volunteer(patron_id, db_name=None):
    """Remove volunteer status"""
    conn = get_db_connection(db_name)
    try:
        conn.execute("""
            DELETE FROM Staff 
            WHERE id = ? AND position = 'Volunteer'
        """, (patron_id,))
        conn.commit()
    finally:
        conn.close()

def get_patron_fines(patron_id, db_name=None):
    """Calculate total replacement costs for lost items"""
    conn = get_db_connection(db_name)
    try:
        # Get all lost items that were checked out by this patron
        lost_items = conn.execute(
            """SELECT i.replacement_cost 
            FROM BorrowingHistory bh
            JOIN Items i ON bh.item_id = i.item_id
            WHERE bh.id = ? AND i.status = 'lost'""",
            (patron_id,)
        ).fetchall()
        
        total_replacement_cost = sum(item['replacement_cost'] for item in lost_items)
        return total_replacement_cost
    finally:
        conn.close()

def find_patron_with_staff(identifier: str, db_name=None):
    """
    Return patron info + is_staff given an identifier (ID digits or email).
    Returns dict: {id, first_name, last_name, is_staff} or None if not found
    """
    identifier = (identifier or "").strip()
    if not identifier: 
        return None
    
    conn = get_db_connection(db_name)
    try: 
        if identifier.isdigit(): 
            row = conn.execute(
                """
                SELECT p.id, p.first_name, p.last_name, 
                    CASE WHEN s.id IS NULL THEN 0 ELSE 1 END AS is_staff
                FROM Patron p
                LEFT JOIN Staff s ON p.id = s.id
                WHERE p.id = ?
                """,
                (int(identifier), )
            ).fetchone()
        else: 
            row = conn.execute(
                """
                SELECT p.id, p.first_name, p.last_name, 
                    CASE WHEN s.id IS NULL THEN 0 ELSE 1 END AS is_staff
                    FROM Patron p
                    LEFT JOIN Staff s ON p.id = s.id
                    WHERE p.email = ?
                """,
                (identifier,)
            ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_all_staff_members(db_name=None):
    """Return all staff as list of dicts: {id, first_name, last_name}."""
    conn = get_db_connection(db_name)
    try:
        rows = conn.execute(
            """
            SELECT s.id, p.first_name, p.last_name
            FROM Staff s
            JOIN Patron p ON s.id = p.id
            ORDER BY p.last_name, p.first_name
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def cancel_event_registration(registration_id, db_name=None):
    """Cancel an event registration by registration_id"""
    conn = get_db_connection(db_name)
    try:
        cur = conn.execute(
            "DELETE FROM EventRegistrations WHERE registration_id = ?",
            (registration_id,)
        )
        conn.commit()

        if cur.rowcount == 0:
            raise ValueError("Registration not found")
        
        return True
    finally:
        conn.close()

def get_overdue_items(today=None, db_name=None):
    """
    Staff view: all overdue items + patron info
    Return: list[dict]
    """
    conn = get_db_connection(db_name)
    try:
        today = today or datetime.now().strftime("%Y-%m-%d")
        
        rows = conn.execute(
            """
            SELECT i.item_id, i.title, i.creator, i.type, i.status,
                bh.id as patron_id, p.first_name, p.last_name,
                bh.checkoutDate,
                date(bh.checkoutDate, '+' || ? || ' days') as due_date
            FROM Items i
            JOIN BorrowingHistory bh ON i.item_id = bh.item_id
            JOIN Patron p ON bh.id = p.id
            WHERE bh.returnDate IS NULL
                AND date(bh.checkoutDate, '+' || ? || ' days') < ?
            """,
            (LOAN_PERIOD_DAYS, LOAN_PERIOD_DAYS, today),
        ).fetchall()

        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_items_with_display_status(is_staff: bool, db_name=None):
    conn = get_db_connection(db_name)
    try:
        if is_staff:
            rows = conn.execute(
                """
                SELECT i.*,
                    CASE
                        WHEN i.status = 'lost' THEN 'lost'
                        WHEN bh.returnDate IS NULL AND bh.id IS NOT NULL THEN 'checked_out'
                        ELSE i.status
                    END as display_status
                FROM Items i
                LEFT JOIN BorrowingHistory bh
                    ON i.item_id = bh.item_id AND bh.returnDate IS NULL
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT i.*,
                    CASE
                        WHEN bh.returnDate IS NULL AND bh.id IS NOT NULL THEN 'checked_out'
                        ELSE i.status
                    END as display_status
                FROM Items i
                LEFT JOIN BorrowingHistory bh
                    ON i.item_id = bh.item_id AND bh.returnDate IS NULL
                WHERE i.status IN ('available', 'checked_out')
                """
            ).fetchall()

        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_items_by_type_for_help(item_type: str, db_name=None):
    """For help prompt: items of a given type that are available/checked_out, with display_status."""
    conn = get_db_connection(db_name)
    try:
        rows = conn.execute(
            """
            SELECT i.item_id, i.title, i.creator,
                CASE
                    WHEN bh.returnDate IS NULL AND bh.id IS NOT NULL THEN 'checked_out'
                    ELSE i.status
                END as display_status
            FROM Items i
            LEFT JOIN BorrowingHistory bh
                ON i.item_id = bh.item_id AND bh.returnDate IS NULL
            WHERE i.type = ?
              AND i.status IN ('available', 'checked_out')
            """,
            (item_type,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

    
def search_available_items_by_title(title_query: str, db_name:None):
    """Return available items whose title matches the query (LIKE %query%)"""
    title_query = (title_query or "").strip()
    if not title_query: 
        return []
    
    conn = get_db_connection(db_name)
    try: 
        rows = conn.execute(
            """
            SELECT item_id, title, creator FROM Items
            WHERE title LIKE ? AND status = "available"
            """, (f"%{title_query}%",)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_checked_out_items_for_patron(patron_id, db_name=None):
    "Return items checked out by current user"
    conn = get_db_connection(db_name)
    try: 
        rows = conn.execute(
            """
            SELECT i.item_id, i.title, i.type
            FROM BorrowingHistory bh
            JOIN Items i ON bh.item_id = i.item_id
            WHERE bh.id = ? AND bh.returnDate IS NULL
            """,
            (patron_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally: 
        conn.close()
 
def get_all_borrowing_history(is_staff: bool, patron_id=None, db_name=None):
    """Show borrowing history - all patrons for staff, current patron for regular users"""
    conn = get_db_connection(db_name)
    try:
        if is_staff:
            rows = conn.execute(
                """
                SELECT bh.*, i.title, i.creator, i.type,
                    p.first_name || ' ' || p.last_name as patron_name, i.status
                FROM BorrowingHistory bh
                JOIN Items i ON bh.item_id = i.item_id
                JOIN Patron p ON bh.id = p.id
                ORDER BY bh.checkoutDate DESC
                """
            ).fetchall()
            return [dict(r) for r in rows]
    finally:
        conn.close()

def get_registrations_for_patron(patron_id, db_name=None):
    """
    Returns a patron's registrations with event details needed for the UI: 
    registration_id, event_id, eventName, date, roomNum, audience
    """

    conn = get_db_connection(db_name)
    try: 
        rows = conn.execute(
            """
            SELECT er.registration_id, e.event_id, e.eventName, e.date, e.roomNum, e.audience
            FROM EventRegistrations er
            JOIN Events e ON er.event_id = e.event_id
            WHERE er.patron_id = ?
            ORDER BY e.date
            """,
            (patron_id, ),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def process_lost_item_payment(patron_id, item_id=None, db_name=None):
    """
    After payment, mark lost item(s) as returned and make them available again.
    If item_id is provided, process that specific item. Otherwise process all lost
    items currently checked out by patron_id.
    Returns number of items updated.
    """
    conn = get_db_connection(db_name)
    try:
        return_date = datetime.now().strftime("%Y-%m-%d")

        if item_id is not None:
            # Ensure this patron actually has this lost item unreturned
            loan = conn.execute(
                """
                SELECT 1
                FROM BorrowingHistory bh
                JOIN Items i ON i.item_id = bh.item_id
                WHERE bh.id = ?
                  AND bh.item_id = ?
                  AND bh.returnDate IS NULL
                  AND i.status = 'lost'
                """,
                (patron_id, item_id),
            ).fetchone()
            if not loan:
                raise ValueError("No active lost-item loan found for this patron and item.")

            conn.execute(
                """
                UPDATE BorrowingHistory
                SET returnDate = ?
                WHERE id = ? AND item_id = ? AND returnDate IS NULL
                """,
                (return_date, patron_id, item_id),
            )
            conn.execute(
                "UPDATE Items SET status = 'available' WHERE item_id = ?",
                (item_id,),
            )
            conn.commit()
            return 1

        # Otherwise: pay all lost items for this patron
        conn.execute(
            """
            UPDATE BorrowingHistory
            SET returnDate = ?
            WHERE id = ?
              AND returnDate IS NULL
              AND item_id IN (SELECT item_id FROM Items WHERE status = 'lost')
            """,
            (return_date, patron_id),
        )

        cur = conn.execute(
            """
            UPDATE Items
            SET status = 'available'
            WHERE status = 'lost'
              AND item_id IN (
                SELECT item_id FROM BorrowingHistory
                WHERE id = ? AND returnDate = ?
              )
            """,
            (patron_id, return_date),
        )

        conn.commit()
        return cur.rowcount
    except:
        conn.rollback()
        raise
    finally:
        conn.close()
