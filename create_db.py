import sqlite3

database_name = "mr_companion.db"

def create_schema(conn):
    
    cursor = conn.cursor()

    # enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        userID TEXT PRIMARY KEY,
        fullName TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        passwordHash TEXT NOT NULL,
        phoneNumber TEXT,
        accountStatus TEXT DEFAULT 'active'
            CHECK(accountStatus IN ('active', 'inactive', 'suspended')),
        createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Client
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Client (
        userID TEXT PRIMARY KEY,
        dateOfBirth DATE NOT NULL,
        address TEXT,
        medicalNotes TEXT,
        FOREIGN KEY(userID) REFERENCES Users(userID) ON DELETE CASCADE
    );
    """)

    # Caregiver
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Caregiver (
        userID TEXT PRIMARY KEY,
        relationshipToClient TEXT,
        FOREIGN KEY(userID) REFERENCES Users(userID) ON DELETE CASCADE
    );
    """)

    # Admin
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Admin (
        userID TEXT PRIMARY KEY,
        employeeID TEXT NOT NULL UNIQUE,
        FOREIGN KEY(userID) REFERENCES Users(userID) ON DELETE CASCADE
    );
    """)

    # CaregiverClient
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CaregiverClient (
        caregiverID TEXT,
        clientID TEXT,
        PRIMARY KEY (caregiverID, clientID),
        FOREIGN KEY(caregiverID) REFERENCES Caregiver(userID) ON DELETE CASCADE,
        FOREIGN KEY(clientID) REFERENCES Client(userID) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cc_clientID ON CaregiverClient(clientID);")

    # Subscriptions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Subscriptions (
        subscriptionID TEXT PRIMARY KEY,
        clientID TEXT UNIQUE,
        planType TEXT NOT NULL CHECK(planType IN ('standard', 'premium')),
        expiryDate DATE NOT NULL,
        FOREIGN KEY(clientID) REFERENCES Client(userID) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_clientID ON Subscriptions(clientID);")

    # Payment
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Payment (
        paymentID TEXT PRIMARY KEY,
        subscriptionID TEXT,
        amount REAL NOT NULL,
        paymentDate DATETIME,
        paymentMethod TEXT CHECK(paymentMethod IN ('credit_card', 'bank_transfer', 'debit_card')),
        paymentStatus TEXT NOT NULL,
        FOREIGN KEY(subscriptionID) REFERENCES Subscriptions(subscriptionID) ON DELETE CASCADE
    );
    """)

    # Device
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Device (
        deviceID TEXT PRIMARY KEY,
        serialNumber TEXT UNIQUE,
        clientID TEXT,
        status TEXT,
        batteryLevel INTEGER CHECK(batteryLevel BETWEEN 0 AND 100),
        wifiStatus TEXT,
        FOREIGN KEY(clientID) REFERENCES Client(userID) ON DELETE SET NULL
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_clientID ON Device(clientID);")

    # EmergencyContact
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS EmergencyContact (
        contactID TEXT PRIMARY KEY,
        clientID TEXT,
        name TEXT,
        phoneNumber TEXT,
        relationship TEXT,
        priorityOrder INTEGER,
        FOREIGN KEY(clientID) REFERENCES Client(userID) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ec_clientID ON EmergencyContact(clientID);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ec_client_priority ON EmergencyContact(clientID, priorityOrder);")

    # EventType
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS EventType (
        eventTypeID INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        severityLevel TEXT NOT NULL CHECK(severityLevel IN ('critical', 'info'))
    );
    """)

    # Event
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Event (
        eventID TEXT PRIMARY KEY,
        deviceID TEXT,
        eventTypeID INTEGER,
        eventTimestamp DATETIME NOT NULL,
        notes TEXT,
        FOREIGN KEY(deviceID) REFERENCES Device(deviceID) ON DELETE CASCADE,
        FOREIGN KEY(eventTypeID) REFERENCES EventType(eventTypeID)
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_device_time ON Event(deviceID, eventTimestamp);")

    # EventContact
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS EventContact (
        eventID TEXT,
        contactID TEXT,
        notifiedAt DATETIME NOT NULL,
        acknowledgedAt DATETIME,
        status TEXT,
        PRIMARY KEY (eventID, contactID),
        FOREIGN KEY(eventID) REFERENCES Event(eventID) ON DELETE CASCADE,
        FOREIGN KEY(contactID) REFERENCES EmergencyContact(contactID) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eventcontact_contactID ON EventContact(contactID);")

    conn.commit()


def main():
    conn = sqlite3.connect(database_name)
    try:
        create_schema(conn)
        print(f"Schema created successfully in '{database_name}'")
    finally:
        conn.close()

def print_schema():
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    # get all tables
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name;
    """)

    tables = cursor.fetchall()

    for (table_name,) in tables:
        print(f"\nTable: {table_name}")

        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()

        for col in columns:
            cid, name, col_type, notnull, default_value, pk = col
            print(f"  - {name} ({col_type})"
                  f"{' PRIMARY KEY' if pk else ''}"
                  f"{' NOT NULL' if notnull else ''}"
                  f"{' DEFAULT ' + str(default_value) if default_value else ''}")
    conn.close()

if __name__ == "__main__":
    main()
    print_schema()