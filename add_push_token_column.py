from app import create_app, db
from sqlalchemy import text, inspect

app = create_app()

with app.app_context():
    try:
        # Create an inspector
        inspector = inspect(db.engine)
        print("Checking for 'user' table...")
        
        # Check if table exists
        if not inspector.has_table("user"):
            print("Table 'user' does not exist!")
        else:
            # Get columns
            columns = [col['name'] for col in inspector.get_columns("user")]
            print(f"Columns found: {columns}")
            
            if 'push_token' not in columns:
                print("Adding push_token column to user table...")
                with db.engine.connect() as connection:
                    # Use standard SQL for adding column
                    connection.execute(text("ALTER TABLE user ADD COLUMN push_token VARCHAR(255)"))
                    connection.commit()
                print("Column added successfully.")
            else:
                print("push_token column already exists.")
                
    except Exception as e:
        print(f"Error: {e}")
