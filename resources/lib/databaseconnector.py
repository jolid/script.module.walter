import os
IGNORE_UNIQUE_ERRORS = True
SILENT_STATEMENTS = True
DATABASE_VERSION = 1
def str2bool(v):
		return v.lower() in ("yes", "true", "t", "1")
class DatabaseClass:
	def __init__(self, db_file='', sql_path=''):
		self.db_file = db_file
		self.sql_path = sql_path
		self._connect()


	def _runSQLFile(self, f):
		sql_path = os.path.join(self.sql_path, f)
		print "With file: %s" % sql_path

		if os.path.exists(sql_path):
			sql_file = open(sql_path, 'r')
			sql_text = sql_file.read()
			sql_stmts = sql_text.split(';')
			for s in sql_stmts:
				if s is not None and len(s.strip()) > 0:
					self.execute(s)

	def _create_db(self):
		print "Initilizing " +  self.db_file
		self._runSQLFile('schema.sql')

	def _connect(self):
		print "Connecting to " + self.db_file
		try:
			from sqlite3 import dbapi2 as database
			print "Loading sqlite3 as DB engine"
		except:
			from pysqlite2 import dbapi2 as database
			print "Loading pysqlite2 as DB engine"
		print "Connecting to SQLite on: " + self.db_file
		self.DBH = database.connect(self.db_file)
		self.DBC = self.DBH.cursor()
		try:		
			row = self.query("SELECT version, (version < ?) AS outdated FROM rw_version ORDER BY version DESC LIMIT 1", [DATABASE_VERSION])
			outdated = str2bool(str(row[1]))
			if outdated:
				print "Database outdated"
				self._create_db()
				'''print "Upgrading database"
				for v in range(row[0]+1, DATABASE_VERSION+1):
					upgrade_file = "upgrade.sqlite.%s.sql" % str(v)
					self.runSQLFile(upgrade_file)
				self.commit()'''
				
			print "Database version: " + str(DATABASE_VERSION)
		except:
			self._create_db()
		
	def commit(self):
		print "Commiting to database"
		self.DBH.commit()

	def query(self, SQL, data=None, force_double_array=False):
		if data:
			self.DBC.execute(SQL, data)
		else:
			self.DBC.execute(SQL)
		rows = self.DBC.fetchall()
		if(len(rows)==1 and not force_double_array):
			return rows[0]
		else:
			return rows

	def execute(self, SQL, data=[]):
		try:
			if data:
				self.DBC.execute(SQL, data)
			else:
				self.DBC.execute(SQL)
			try:
				self.lastrowid = self.DBC.lastrowid
			except:
				self.lastrowid = None
		except Exception, e:
			if IGNORE_UNIQUE_ERRORS and re.match('column (.)+ is not unique$', str(e)):				
				return None
			print '******SQL ERROR: %s' % e

