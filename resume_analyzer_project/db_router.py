class NoDBRouter:
    """
    A router to prevent database operations in a serverless environment.
    This is used for Vercel deployment where we don't want to use a database.
    """
    
    def db_for_read(self, model, **hints):
        """
        Attempts to read models go to /dev/null.
        """
        return None
    
    def db_for_write(self, model, **hints):
        """
        Attempts to write models go to /dev/null.
        """
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both objects are in the default db.
        """
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure no migrations are run.
        """
        return False
