import sqlite3

db_path = 'C:/VS code projects/Makeathon/makeathon/users.db'

def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            email_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            demographics TEXT,
            psychology TEXT,
            experience TEXT,
            marketing TEXT,
            history TEXT
        );
    ''')
    conn.commit()
    conn.close()

def add_user(email_id, password):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO profiles (email_id, password) VALUES (?, ?)
        ''', (email_id, password))
        conn.commit()
        conn.close()
    except:
        print("User already exists")
        conn.commit()
        conn.close()

def load_profile(email_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT demographics, psychology, experience, marketing, history FROM profiles WHERE email_id = ?
    ''', (email_id,))
    profile = c.fetchone()
    conn.close()
    return profile

def append_to_profile_column(email_id, column_name, data):
    '''
    Appends new information to one of emographics, psychology, experience, marketing columns
    '''
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    ## Get the current value in the column
    c.execute('''
        SELECT {} FROM profiles WHERE email_id = ?
    '''.format(column_name), (email_id,))
    
    current_value = c.fetchone()[0]
    if current_value is None:
        new_value = data
    else:
        new_value = data
    c.execute('''
        UPDATE profiles SET {} = ? WHERE email_id = ?
    '''.format(column_name), (new_value, email_id))
    conn.commit()
    conn.close()

def display_profile_table():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT * FROM profiles
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

def delete_user(email_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        DELETE FROM profiles WHERE email_id = ?
    ''', (email_id,))
    conn.commit()
    conn.close()

def get_all_emails(exclude):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT email_id FROM profiles WHERE email_id != ?
    ''', (exclude,))
    emails = c.fetchall()
    conn.close()
    return emails

def does_email_exist(email):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT email_id FROM profiles WHERE email_id = ?
    ''', (email,))
    rows = c.fetchall()
    conn.close()
    return len(rows) > 0

def persona_to_text(email, file_name):
    '''
    Save the profile to a well structured text file .txt
    '''
    profile = load_profile(email)
    text = f"Email: {email}\n"
    text += f"Demographics: {profile[0]}\n\n"
    text += f"Psychology: {profile[1]}\n\n"
    text += f"Experience: {profile[2]}\n\n"
    text += f"Marketing: {profile[3]}\n\n"
    text += f"History: {profile[4]}\n\n"

    ## Write to a text file
    with open(f"{file_name}.txt", "w") as f:
        f.write(text)

def history_to_text(emails, file_name):
    '''
    Save the history of all emails to a text file
    '''
    text = ""
    for email in emails:
        profile = load_profile(email)
        text += f"Email: {email}\n"
        text += f"History: {profile[4]}\n"
        text += "\n"

    ## Write to a text file
    with open(f"{file_name}.txt", "w") as f:
        f.write(text)
