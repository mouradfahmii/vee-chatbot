# Notebooks

This directory contains Jupyter notebooks for testing and development.

## MySQL Connection Test

**File:** `test_mysql_connection.ipynb`

This notebook tests the connection to the MySQL database and provides:
- Connection testing
- List all tables
- Table structure details
- Sample data preview

### Usage

1. **Install dependencies:**
   ```bash
   pip install mysql-connector-python pandas jupyter
   ```

2. **Start Jupyter:**
   ```bash
   jupyter notebook
   ```

3. **Open the notebook:**
   - Navigate to `notebooks/test_mysql_connection.ipynb`
   - Run cells sequentially

### Database Configuration

The notebook is configured with:
- Host: 127.0.0.1
- Port: 3306
- Database: veeapp_db
- Username: veeapp_mhaggag

**Note:** Update the password in the notebook if needed, or use environment variables for security.

