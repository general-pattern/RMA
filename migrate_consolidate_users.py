#!/usr/bin/env python3
"""
Consolidate internal_owners into users table
This migration will:
1. Add IsOwner column to users
2. Add AssignedToUserID column to rmas
3. Migrate data from internal_owners to users
4. Update all references
5. Drop internal_owners table
"""

import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = "rma.db"

def migrate():
    print("="*70)
    print("🔄 Consolidating internal_owners into users...")
    print("="*70)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    try:
        # 1. Add IsOwner column to users
        print("\n1️⃣ Adding IsOwner column to users...")
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IsOwner INTEGER DEFAULT 0")
            print("   ✓ IsOwner column added")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  IsOwner already exists: {e}")
        
        # 2. Add AssignedToUserID column to rmas
        print("\n2️⃣ Adding AssignedToUserID column to rmas...")
        try:
            cur.execute("ALTER TABLE rmas ADD COLUMN AssignedToUserID INTEGER")
            print("   ✓ AssignedToUserID column added")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  AssignedToUserID already exists: {e}")
        
        # 3. Get all internal owners
        print("\n3️⃣ Migrating internal owners to users...")
        try:
            cur.execute("SELECT * FROM internal_owners")
            owners = cur.fetchall()
            print(f"   Found {len(owners)} owners to migrate")
        except sqlite3.OperationalError:
            print("   ⚠️  internal_owners table doesn't exist - skipping owner migration")
            owners = []
        
        migrated = 0
        created = 0
        
        for owner in owners:
            owner_email = owner['OwnerEmail']
            owner_name = owner['OwnerName']
            owner_id = owner['OwnerID']
            
            # Check if user with this email exists
            cur.execute("SELECT UserID FROM users WHERE Email = ?", (owner_email,))
            existing_user = cur.fetchone()
            
            if existing_user:
                # Mark existing user as owner
                cur.execute("UPDATE users SET IsOwner = 1 WHERE Email = ?", (owner_email,))
                user_id = existing_user['UserID']
                print(f"   ✓ Marked existing user as owner: {owner_name}")
                migrated += 1
            else:
                # Create user account for this owner
                username = owner_email.split('@')[0]
                
                # Check if username exists
                cur.execute("SELECT UserID FROM users WHERE Username = ?", (username,))
                if cur.fetchone():
                    username = f"{username}_{owner_id}"
                
                password_hash = generate_password_hash("ChangeMe123!")
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                cur.execute("""
                    INSERT INTO users (Username, PasswordHash, FullName, Email, Role, IsOwner, CreatedOn)
                    VALUES (?, ?, ?, ?, 'user', 1, ?)
                """, (username, password_hash, owner_name, owner_email, now))
                
                user_id = cur.lastrowid
                print(f"   ✓ Created user account: {owner_name} (username: {username}, password: ChangeMe123!)")
                created += 1
            
            # Update rmas.AssignedToUserID where InternalOwnerID matches
            cur.execute("""
                UPDATE rmas
                SET AssignedToUserID = ?
                WHERE InternalOwnerID = ?
            """, (user_id, owner_id))
        
        print(f"\n   Summary: {migrated} existing users marked as owners, {created} new users created")
        
        # 4. Update rma_owners table if it exists
        print("\n4️⃣ Updating rma_owners table...")
        try:
            # Check if rma_owners exists and has OwnerID column
            cur.execute("PRAGMA table_info(rma_owners)")
            columns = [col[1] for col in cur.fetchall()]
            
            if 'OwnerID' in columns:
                # Create new table structure
                cur.execute("""
                    CREATE TABLE rma_owners_new (
                        RMAOwnerID      INTEGER PRIMARY KEY AUTOINCREMENT,
                        RMAID           INTEGER NOT NULL,
                        UserID          INTEGER NOT NULL,
                        IsPrimary       INTEGER DEFAULT 0,
                        AssignedOn      TEXT NOT NULL,
                        AssignedBy      INTEGER,
                        FOREIGN KEY (RMAID) REFERENCES rmas(RMAID) ON DELETE CASCADE,
                        FOREIGN KEY (UserID) REFERENCES users(UserID) ON DELETE CASCADE,
                        FOREIGN KEY (AssignedBy) REFERENCES users(UserID),
                        UNIQUE(RMAID, UserID)
                    )
                """)
                
                # Migrate data
                cur.execute("""
                    INSERT INTO rma_owners_new (RMAID, UserID, IsPrimary, AssignedOn, AssignedBy)
                    SELECT ro.RMAID, u.UserID, ro.IsPrimary, ro.AssignedOn, ro.AssignedBy
                    FROM rma_owners ro
                    JOIN internal_owners o ON ro.OwnerID = o.OwnerID
                    JOIN users u ON o.OwnerEmail = u.Email
                """)
                
                # Drop old and rename
                cur.execute("DROP TABLE rma_owners")
                cur.execute("ALTER TABLE rma_owners_new RENAME TO rma_owners")
                print("   ✓ rma_owners updated")
            else:
                print("   ✓ rma_owners already uses UserID")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  rma_owners issue: {e}")
        
        # 5. Update owner_notification_preferences if it exists
        print("\n5️⃣ Updating notification preferences...")
        try:
            cur.execute("PRAGMA table_info(owner_notification_preferences)")
            columns = [col[1] for col in cur.fetchall()]
            
            if 'OwnerID' in columns:
                cur.execute("""
                    CREATE TABLE owner_notification_preferences_new (
                        PrefID          INTEGER PRIMARY KEY AUTOINCREMENT,
                        UserID          INTEGER NOT NULL UNIQUE,
                        EmailEnabled    INTEGER DEFAULT 1,
                        Frequency       TEXT DEFAULT 'daily',
                        RMAAge          INTEGER DEFAULT 3,
                        LastSent        TEXT,
                        FOREIGN KEY (UserID) REFERENCES users(UserID) ON DELETE CASCADE
                    )
                """)
                
                cur.execute("""
                    INSERT INTO owner_notification_preferences_new (UserID, EmailEnabled, Frequency, RMAAge, LastSent)
                    SELECT u.UserID, p.EmailEnabled, p.Frequency, p.RMAAge, p.LastSent
                    FROM owner_notification_preferences p
                    JOIN internal_owners o ON p.OwnerID = o.OwnerID
                    JOIN users u ON o.OwnerEmail = u.Email
                """)
                
                cur.execute("DROP TABLE owner_notification_preferences")
                cur.execute("ALTER TABLE owner_notification_preferences_new RENAME TO owner_notification_preferences")
                print("   ✓ Notification preferences updated")
            else:
                print("   ✓ Notification preferences already use UserID")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  Notification preferences issue: {e}")
        
        # 6. Drop internal_owners table
        print("\n6️⃣ Cleaning up...")
        try:
            cur.execute("DROP TABLE IF EXISTS internal_owners")
            print("   ✓ Dropped internal_owners table")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  {e}")
        
        # 7. Create indexes
        print("\n7️⃣ Creating indexes...")
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_isowner ON users(IsOwner)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_rmas_assigned ON rmas(AssignedToUserID)")
            print("   ✓ Indexes created")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  {e}")
        
        conn.commit()
        
        print("\n" + "="*70)
        print("✅ Migration completed successfully!")
        print("="*70)
        print("\nSummary:")
        print(f"  • {migrated + created} users are now owners")
        print(f"  • AssignedToUserID column added to rmas")
        print(f"  • internal_owners table removed")
        
        if created > 0:
            print(f"\n⚠️  {created} new user(s) created with password: ChangeMe123!")
            print("   They will need to reset their password on first login")
        
        print("\nNext steps:")
        print("  1. Test the app: python app.py")
        print("  2. If it works, deploy: git add . && git commit && git push")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
