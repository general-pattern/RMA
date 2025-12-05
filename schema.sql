PRAGMA foreign_keys = ON;

-- Users (for authentication)
CREATE TABLE IF NOT EXISTS users (
    UserID          INTEGER PRIMARY KEY AUTOINCREMENT,
    Username        TEXT NOT NULL UNIQUE,
    PasswordHash    TEXT NOT NULL,
    FullName        TEXT NOT NULL,
    Email           TEXT NOT NULL,
    Role            TEXT DEFAULT 'user',
    CreatedOn       TEXT NOT NULL,
    LastLogin       TEXT
);

-- Customers
CREATE TABLE IF NOT EXISTS customers (
    CustomerID      INTEGER PRIMARY KEY AUTOINCREMENT,
    CustomerName    TEXT NOT NULL,
    ContactName     TEXT,
    ContactEmail    TEXT
);

-- RMAs (header)
CREATE TABLE IF NOT EXISTS rmas (
    RMAID                 INTEGER PRIMARY KEY AUTOINCREMENT,
    CustomerID            INTEGER NOT NULL,
    CreatedByUserID       INTEGER,
    DateOpened            TEXT NOT NULL,
    DateClosed            TEXT,
    ClosedBy              TEXT,
    Status                TEXT NOT NULL DEFAULT 'Pending',
    ReturnType            TEXT,
    InternalOwnerID       INTEGER,
    Acknowledged          INTEGER DEFAULT 0,
    AcknowledgedOn        TEXT,
    CustomerComplaintDesc TEXT,
    InternalNotes         TEXT,
    NotesLastModified     TEXT,
    NotesModifiedBy       TEXT,
    CreditMemoNumber      TEXT,
    CreditApproved        INTEGER DEFAULT 0,
    CreditApprovedOn      TEXT,
    CreditApprovedBy      TEXT,
    FOREIGN KEY (CustomerID) REFERENCES customers(CustomerID),
    FOREIGN KEY (InternalOwnerID) REFERENCES users(UserID),
    FOREIGN KEY (CreatedByUserID) REFERENCES users(UserID)
);

-- RMA lines
CREATE TABLE IF NOT EXISTS rma_lines (
    RMALineID       INTEGER PRIMARY KEY AUTOINCREMENT,
    RMAID           INTEGER NOT NULL,
    PartNumber      TEXT,
    ToolNumber      TEXT,
    ItemDescription TEXT,
    QtyAffected     INTEGER,
    POLotNumber     TEXT,
    TotalCost       REAL,
    FOREIGN KEY (RMAID) REFERENCES rmas(RMAID) ON DELETE CASCADE
);

-- Status history
CREATE TABLE IF NOT EXISTS status_history (
    StatusHistID    INTEGER PRIMARY KEY AUTOINCREMENT,
    RMAID           INTEGER NOT NULL,
    Status          TEXT NOT NULL,
    ChangedBy       TEXT,
    ChangedOn       TEXT NOT NULL,
    Comment         TEXT,
    FOREIGN KEY (RMAID) REFERENCES rmas(RMAID) ON DELETE CASCADE
);

-- Notes history
CREATE TABLE IF NOT EXISTS notes_history (
    NoteHistID      INTEGER PRIMARY KEY AUTOINCREMENT,
    RMAID           INTEGER NOT NULL,
    NotesContent    TEXT,
    ModifiedBy      TEXT,
    ModifiedOn      TEXT NOT NULL,
    FOREIGN KEY (RMAID) REFERENCES rmas(RMAID) ON DELETE CASCADE
);

-- Attachments
CREATE TABLE IF NOT EXISTS attachments (
    AttachmentID    INTEGER PRIMARY KEY AUTOINCREMENT,
    RMAID           INTEGER NOT NULL,
    RMALineID       INTEGER,
    FilePath        TEXT NOT NULL,
    AttachmentType  TEXT,
    AddedBy         TEXT,
    DateAdded       TEXT NOT NULL,
    FOREIGN KEY (RMAID) REFERENCES rmas(RMAID) ON DELETE CASCADE,
    FOREIGN KEY (RMALineID) REFERENCES rma_lines(RMALineID) ON DELETE CASCADE
);

-- Dispositions
CREATE TABLE IF NOT EXISTS dispositions (
    DispositionID       INTEGER PRIMARY KEY AUTOINCREMENT,
    RMALineID           INTEGER NOT NULL,
    Disposition         TEXT,
    FailureCode         TEXT,
    FailureDescription  TEXT,
    RootCause           TEXT,
    CorrectiveAction    TEXT,
    QtyScrap            INTEGER,
    QtyRework           INTEGER,
    QtyReplace          INTEGER,
    DateDispositioned   TEXT,
    DispositionBy       TEXT,
    FOREIGN KEY (RMALineID) REFERENCES rma_lines(RMALineID) ON DELETE CASCADE
);
