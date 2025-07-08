"""
Local Storage - Handles offline caching of print jobs using SQLite.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging


class LocalStorage:
    """Handles local storage of print jobs for offline resilience."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize local storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.logger = logging.getLogger(__name__)
        
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Default database location
            data_dir = Path.home() / "PrintAgent" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "print_jobs.db"
        
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS print_jobs (
                        id TEXT PRIMARY KEY,
                        job_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        uploaded_at TIMESTAMP NULL,
                        upload_attempts INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending'
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_status 
                    ON print_jobs(status)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_created_at 
                    ON print_jobs(created_at)
                """)
                
                conn.commit()
                
                self.logger.info(f"Local database initialized: {self.db_path}")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def store_print_job(self, job_data: Dict[str, Any]) -> str:
        """Store a print job locally."""
        try:
            job_id = str(uuid.uuid4())
            job_json = json.dumps(job_data)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO print_jobs (id, job_data, status)
                    VALUES (?, ?, 'pending')
                """, (job_id, job_json))
                
                conn.commit()
            
            self.logger.debug(f"Print job stored locally: {job_id}")
            return job_id
            
        except Exception as e:
            self.logger.error(f"Error storing print job: {e}")
            raise
    
    def get_pending_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pending print jobs that need to be uploaded."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT id, job_data, upload_attempts
                    FROM print_jobs 
                    WHERE status = 'pending'
                    ORDER BY created_at ASC
                    LIMIT ?
                """, (limit,))
                
                jobs = []
                for row in cursor:
                    job_data = json.loads(row['job_data'])
                    job_data['_local_id'] = row['id']
                    job_data['_upload_attempts'] = row['upload_attempts']
                    jobs.append(job_data)
                
                return jobs
                
        except Exception as e:
            self.logger.error(f"Error getting pending jobs: {e}")
            return []
    
    def mark_as_uploaded(self, job_id: str):
        """Mark a job as successfully uploaded."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE print_jobs 
                    SET status = 'uploaded', uploaded_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (job_id,))
                
                conn.commit()
            
            self.logger.debug(f"Job marked as uploaded: {job_id}")
            
        except Exception as e:
            self.logger.error(f"Error marking job as uploaded: {e}")
    
    def mark_upload_failed(self, job_id: str):
        """Mark a job upload as failed and increment attempts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE print_jobs 
                    SET upload_attempts = upload_attempts + 1
                    WHERE id = ?
                """, (job_id,))
                
                conn.commit()
            
            self.logger.debug(f"Job upload failed, attempts incremented: {job_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating failed job: {e}")
    
    def cleanup_old_jobs(self, days: int = 30):
        """Clean up old uploaded jobs."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM print_jobs 
                    WHERE status = 'uploaded' 
                    AND uploaded_at < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old jobs")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old jobs: {e}")
    
    def get_statistics(self) -> Dict[str, int]:
        """Get storage statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        status,
                        COUNT(*) as count
                    FROM print_jobs 
                    GROUP BY status
                """)
                
                stats = {}
                for row in cursor:
                    stats[row[0]] = row[1]
                
                # Add total count
                cursor = conn.execute("SELECT COUNT(*) FROM print_jobs")
                stats['total'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}
    
    def retry_failed_jobs(self, max_attempts: int = 5):
        """Reset failed jobs for retry if under max attempts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE print_jobs 
                    SET status = 'pending'
                    WHERE status = 'failed' 
                    AND upload_attempts < ?
                """, (max_attempts,))
                
                retry_count = cursor.rowcount
                conn.commit()
            
            if retry_count > 0:
                self.logger.info(f"Reset {retry_count} failed jobs for retry")
                
        except Exception as e:
            self.logger.error(f"Error retrying failed jobs: {e}")
    
    def purge_failed_jobs(self, max_attempts: int = 5):
        """Remove jobs that have exceeded max upload attempts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM print_jobs 
                    WHERE upload_attempts >= ?
                """, (max_attempts,))
                
                purged_count = cursor.rowcount
                conn.commit()
            
            if purged_count > 0:
                self.logger.warning(f"Purged {purged_count} jobs that exceeded max attempts")
                
        except Exception as e:
            self.logger.error(f"Error purging failed jobs: {e}")
    
    def get_database_size(self) -> int:
        """Get database file size in bytes."""
        try:
            return self.db_path.stat().st_size
        except Exception:
            return 0
    
    def vacuum_database(self):
        """Optimize database by running VACUUM."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                conn.commit()
            
            self.logger.info("Database vacuumed successfully")
            
        except Exception as e:
            self.logger.error(f"Error vacuuming database: {e}")
